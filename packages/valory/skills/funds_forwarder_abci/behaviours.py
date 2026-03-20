# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2026 Valory AG
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
# ------------------------------------------------------------------------------

"""This module contains the behaviours of the FundsForwarderAbciApp."""

from abc import ABC
from typing import Dict, Generator, List, Optional, Set, Type, cast

from packages.valory.contracts.erc20.contract import ERC20TokenContract
from packages.valory.contracts.gnosis_safe.contract import (
    GnosisSafeContract,
    SafeOperation,
)
from packages.valory.contracts.multisend.contract import (
    MultiSendContract,
    MultiSendOperation,
)
from packages.valory.protocols.contract_api import ContractApiMessage
from packages.valory.protocols.ledger_api import LedgerApiMessage
from packages.valory.skills.abstract_round_abci.behaviours import (
    AbstractRoundBehaviour,
    BaseBehaviour,
)
from packages.valory.skills.funds_forwarder_abci.models import (
    FundsForwarderParams,
    ZERO_ADDRESS,
)
from packages.valory.skills.funds_forwarder_abci.payloads import FundsForwarderPayload
from packages.valory.skills.funds_forwarder_abci.rounds import (
    FundsForwarderAbciApp,
    FundsForwarderRound,
    SynchronizedData,
)
from packages.valory.skills.transaction_settlement_abci.payload_tools import (
    hash_payload_to_hex,
)

SAFE_TX_GAS = 0
ETHER_VALUE = 0


class FundsForwarderBaseBehaviour(BaseBehaviour, ABC):
    """Base behaviour for the funds_forwarder_abci skill."""

    @property
    def synchronized_data(self) -> SynchronizedData:
        """Return the synchronized data."""
        return cast(SynchronizedData, super().synchronized_data)

    @property
    def params(self) -> FundsForwarderParams:
        """Return the params."""
        return cast(FundsForwarderParams, super().params)

    def _get_safe_tx_hash(
        self,
        to_address: str,
        data: bytes,
        value: int = ETHER_VALUE,
        operation: int = SafeOperation.CALL.value,
    ) -> Generator[None, None, Optional[str]]:
        """Prepares and returns the safe tx hash."""
        response = yield from self.get_contract_api_response(
            performative=ContractApiMessage.Performative.GET_STATE,  # type: ignore
            contract_address=self.synchronized_data.safe_contract_address,
            contract_id=str(GnosisSafeContract.contract_id),
            contract_callable="get_raw_safe_transaction_hash",
            to_address=to_address,
            value=value,
            data=data,
            safe_tx_gas=SAFE_TX_GAS,
            operation=operation,
        )
        if response.performative != ContractApiMessage.Performative.STATE:
            self.context.logger.error(
                f"Couldn't get safe hash. "
                f"Expected {ContractApiMessage.Performative.STATE}, "
                f"received {response.performative.value}."
            )
            return None
        tx_hash = cast(str, response.state.body["tx_hash"])[2:]
        return tx_hash

    def _to_multisend(
        self, transactions: List[Dict]
    ) -> Generator[None, None, Optional[str]]:
        """Transform payload to MultiSend."""
        multi_send_txs = []
        for transaction in transactions:
            transaction = {
                "operation": transaction.get("operation", MultiSendOperation.CALL),
                "to": transaction["to"],
                "value": transaction["value"],
                "data": transaction.get("data", b""),
            }
            multi_send_txs.append(transaction)

        response = yield from self.get_contract_api_response(
            performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
            contract_address=self.params.multisend_address,
            contract_id=str(MultiSendContract.contract_id),
            contract_callable="get_tx_data",
            multi_send_txs=multi_send_txs,
        )
        if response.performative != ContractApiMessage.Performative.RAW_TRANSACTION:
            self.context.logger.error(
                f"Couldn't compile the multisend tx. "
                f"Expected {ContractApiMessage.Performative.RAW_TRANSACTION}, "
                f"received {response.performative.value}."
            )
            return None

        multisend_data_str = cast(str, response.raw_transaction.body["data"])[2:]
        tx_data = bytes.fromhex(multisend_data_str)
        tx_hash = yield from self._get_safe_tx_hash(
            self.params.multisend_address,
            tx_data,
            operation=SafeOperation.DELEGATE_CALL.value,
        )
        if tx_hash is None:
            return None

        payload_data = hash_payload_to_hex(
            safe_tx_hash=tx_hash,
            ether_value=ETHER_VALUE,
            safe_tx_gas=SAFE_TX_GAS,
            operation=SafeOperation.DELEGATE_CALL.value,
            to_address=self.params.multisend_address,
            data=tx_data,
        )
        return payload_data


class FundsForwarderBehaviour(FundsForwarderBaseBehaviour):
    """Behaviour that checks balances and transfers excess funds to the service owner."""

    matching_round = FundsForwarderRound

    def async_act(self) -> Generator:
        """Implement the act."""
        with self.context.benchmark_tool.measure(self.behaviour_id).local():
            tx_hash = yield from self._get_tx_hash()
            if tx_hash is None:
                tx_submitter = None
            else:
                tx_submitter = self.matching_round.auto_round_id()
            payload = FundsForwarderPayload(
                sender=self.context.agent_address,
                tx_submitter=tx_submitter,
                tx_hash=tx_hash,
            )
        with self.context.benchmark_tool.measure(self.behaviour_id).consensus():
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()
        self.set_done()

    def _get_tx_hash(  # pylint: disable=too-many-return-statements
        self,
    ) -> Generator[None, None, Optional[str]]:
        """Get the transaction hash for funds forwarding."""
        # Step 1: Validate service owner
        service_owner = self.synchronized_data.service_owner
        if not service_owner or service_owner == ZERO_ADDRESS:
            self.context.logger.warning(
                "Service owner is empty or zero address. Skipping funds forwarding."
            )
            return None

        expected_owner = self.params.expected_service_owner_address
        if service_owner.lower() != expected_owner.lower():
            self.context.logger.warning(
                f"Service owner {service_owner} does not match "
                f"expected owner {expected_owner}. Skipping funds forwarding."
            )
            return None

        # Step 2: Check token limits are configured
        if not self.params.funds_forwarder_token_config:
            self.context.logger.info(
                "No token limits configured. Skipping funds forwarding."
            )
            return None

        target_address = service_owner

        # Step 3: Build transfer transactions
        transactions = yield from self._build_transfer_txs(target_address)
        if not transactions:
            self.context.logger.info("No excess funds to forward.")
            return None

        # Step 4: Build the safe transaction
        if len(transactions) == 1:
            tx = transactions[0]
            tx_hash = yield from self._get_safe_tx_hash(
                to_address=tx["to"],
                data=tx.get("data", b""),
                value=tx["value"],
            )
            if tx_hash is None:
                return None
            return hash_payload_to_hex(
                safe_tx_hash=tx_hash,
                ether_value=tx["value"],
                safe_tx_gas=SAFE_TX_GAS,
                to_address=tx["to"],
                data=tx.get("data", b""),
            )

        return (yield from self._to_multisend(transactions))

    def _build_transfer_txs(
        self, target_address: str
    ) -> Generator[None, None, List[Dict]]:
        """Build transfer transactions for all tokens exceeding thresholds."""
        transactions: List[Dict] = []

        for token_address, limits in self.params.funds_forwarder_token_config.items():
            retain = limits["retain_balance"]
            max_transfer = limits["max_transfer"]

            if token_address.lower() == ZERO_ADDRESS.lower():
                # Native token
                balance = yield from self._get_native_balance()
            else:
                # ERC20 token
                balance = yield from self._get_erc20_balance(token_address)

            if balance is None:
                self.context.logger.warning(
                    f"Could not get balance for {token_address}. Skipping."
                )
                continue

            min_transfer = limits.get("min_transfer", 0)

            if balance < retain + min_transfer:
                continue

            transfer_amount = min(max_transfer, balance - retain)

            self.context.logger.info(
                f"Token {token_address}: balance={balance}, "
                f"retain={retain}, transferring={transfer_amount} "
                f"to {target_address}"
            )

            if token_address.lower() == ZERO_ADDRESS.lower():
                # Native transfer
                transactions.append(
                    {
                        "to": target_address,
                        "value": transfer_amount,
                        "data": b"",
                    }
                )
            else:
                # ERC20 transfer
                tx_data = yield from self._build_erc20_transfer(
                    token_address, target_address, transfer_amount
                )
                if tx_data is not None:
                    transactions.append(
                        {
                            "to": token_address,
                            "value": ETHER_VALUE,
                            "data": tx_data,
                        }
                    )

        return transactions

    def _get_native_balance(self) -> Generator[None, None, Optional[int]]:
        """Get the native token balance of the safe."""
        ledger_api_response = yield from self.get_ledger_api_response(
            performative=LedgerApiMessage.Performative.GET_STATE,  # type: ignore
            ledger_callable="get_balance",
            account=self.synchronized_data.safe_contract_address,
        )
        if ledger_api_response.performative != LedgerApiMessage.Performative.STATE:
            self.context.logger.error(
                f"Couldn't get native balance. "
                f"Expected {LedgerApiMessage.Performative.STATE.value}, "  # type: ignore
                f"received {ledger_api_response.performative.value}."
            )
            return None
        balance = cast(int, ledger_api_response.state.body.get("get_balance_result"))
        return balance

    def _get_erc20_balance(
        self, token_address: str
    ) -> Generator[None, None, Optional[int]]:
        """Get the ERC20 token balance of the safe."""
        response = yield from self.get_contract_api_response(
            performative=ContractApiMessage.Performative.GET_STATE,  # type: ignore
            contract_address=token_address,
            contract_id=str(ERC20TokenContract.contract_id),
            contract_callable="check_balance",
            account=self.synchronized_data.safe_contract_address,
        )
        if response.performative != ContractApiMessage.Performative.STATE:
            self.context.logger.error(
                f"Couldn't get ERC20 balance for {token_address}."
            )
            return None
        return cast(int, response.state.body["token"])

    def _build_erc20_transfer(
        self, token_address: str, to_address: str, amount: int
    ) -> Generator[None, None, Optional[bytes]]:
        """Build an ERC20 transfer transaction."""
        response = yield from self.get_contract_api_response(
            performative=ContractApiMessage.Performative.GET_STATE,  # type: ignore
            contract_address=token_address,
            contract_id=str(ERC20TokenContract.contract_id),
            contract_callable="get_transfer_tx_data",
            receiver=to_address,
            amount=amount,
        )
        if response.performative != ContractApiMessage.Performative.STATE:
            self.context.logger.error(
                f"Couldn't build ERC20 transfer tx for {token_address}."
            )
            return None
        data_hex = cast(str, response.state.body["data"])
        return bytes.fromhex(data_hex[2:])


class FundsForwarderRoundBehaviour(AbstractRoundBehaviour):
    """This behaviour manages the consensus stages for the funds_forwarder_abci skill."""

    initial_behaviour_cls = FundsForwarderBehaviour
    abci_app_cls = FundsForwarderAbciApp
    behaviours: Set[Type[BaseBehaviour]] = {
        FundsForwarderBehaviour,  # type: ignore
    }
