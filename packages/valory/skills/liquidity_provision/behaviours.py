# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021 Valory AG
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

"""This module contains the behaviours for the 'liquidity_provision' skill."""
import binascii
import json
import pprint
from abc import ABC
from typing import Generator, Optional, Set, Type, cast

from aea_ledger_ethereum import EthereumApi
from hexbytes import HexBytes

from packages.valory.contracts.gnosis_safe.contract import (
    GnosisSafeContract,
    SafeOperation,
)
from packages.valory.contracts.multisend.contract import (
    MultiSendContract,
    MultiSendOperation,
)
from packages.valory.contracts.uniswap_v2_erc20.contract import UniswapV2ERC20Contract
from packages.valory.contracts.uniswap_v2_router_02.contract import (
    UniswapV2Router02Contract,
)
from packages.valory.protocols.contract_api import ContractApiMessage
from packages.valory.skills.abstract_round_abci.behaviours import (
    AbstractRoundBehaviour,
    BaseState,
)
from packages.valory.skills.abstract_round_abci.utils import BenchmarkTool
from packages.valory.skills.liquidity_provision.models import Params, SharedState
from packages.valory.skills.liquidity_provision.payloads import (
    StrategyEvaluationPayload,
    StrategyType,
)
from packages.valory.skills.liquidity_provision.rounds import (
    EnterPoolRandomnessRound,
    EnterPoolSelectKeeperRound,
    EnterPoolTransactionHashRound,
    EnterPoolTransactionSendRound,
    EnterPoolTransactionSignatureRound,
    EnterPoolTransactionValidationRound,
    ExitPoolRandomnessRound,
    ExitPoolSelectKeeperRound,
    ExitPoolTransactionHashRound,
    ExitPoolTransactionSendRound,
    ExitPoolTransactionSignatureRound,
    ExitPoolTransactionValidationRound,
    LiquidityProvisionAbciApp,
    PeriodState,
    StrategyEvaluationRound,
)
from packages.valory.skills.price_estimation_abci.behaviours import (
    RandomnessBehaviour as RandomnessBehaviourPriceEstimation,
)
from packages.valory.skills.price_estimation_abci.behaviours import (
    ResetAndPauseBehaviour,
    ResetBehaviour,
    SelectKeeperBehaviour,
)
from packages.valory.skills.price_estimation_abci.payloads import (
    FinalizationTxPayload,
    SignaturePayload,
    TransactionHashPayload,
    ValidatePayload,
)


ETHER_VALUE = 0  # TOFIX
SAFE_TX_GAS = 4000000  # TOFIX
MAX_ALLOWANCE = 2 ** 256 - 1
CURRENT_BLOCK_TIMESTAMP = 0  # TOFIX
WETH_ADDRESS = "0x610178dA211FEF7D417bC0e6FeD39F05609AD788"
TOKEN_A_ADDRESS = "0x0DCd1Bf9A1b36cE34237eEaFef220932846BCD82"  # nosec
TOKEN_B_ADDRESS = "0x9A676e781A523b5d0C0e43731313A708CB607508"  # nosec

benchmark_tool = BenchmarkTool()


class LiquidityProvisionBaseBehaviour(BaseState, ABC):
    """Base state behaviour for the liquidity provision skill."""

    @property
    def period_state(self) -> PeriodState:
        """Return the period state."""
        return cast(PeriodState, cast(SharedState, self.context.state).period_state)

    @property
    def params(self) -> Params:
        """Return the params."""
        return cast(Params, self.context.params)


class TransactionSignatureBaseBehaviour(LiquidityProvisionBaseBehaviour):
    """Signature base behaviour."""

    def async_act(self) -> Generator:
        """
        Do the action.

        Steps:
        - Request the signature of the transaction hash.
        - Send the signature as a transaction and wait for it to be mined.
        - Wait until ABCI application transitions to the next round.
        - Go to the next behaviour state (set done event).
        """

        with benchmark_tool.measure(
            self,
        ).local():
            self.context.logger.info(
                f"Consensus reached on {self.state_id} tx hash: {self.period_state.most_voted_tx_hash}"
            )
            signature_hex = yield from self._get_safe_tx_signature()
            payload = SignaturePayload(self.context.agent_address, signature_hex)

        with benchmark_tool.measure(
            self,
        ).consensus():
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()

    def _get_safe_tx_signature(self) -> Generator[None, None, str]:
        # is_deprecated_mode=True because we want to call Account.signHash,
        # which is the same used by gnosis-py
        safe_tx_hash_bytes = binascii.unhexlify(
            self.period_state.most_voted_tx_hash[:64]
        )
        signature_hex = yield from self.get_signature(
            safe_tx_hash_bytes, is_deprecated_mode=True
        )
        # remove the leading '0x'
        signature_hex = signature_hex[2:]
        self.context.logger.info(f"Signature: {signature_hex}")
        return signature_hex


class TransactionSendBaseBehaviour(LiquidityProvisionBaseBehaviour):
    """Finalize state."""

    def async_act(self) -> Generator[None, None, None]:
        """
        Do the action.

        Steps:
        - If the agent is the keeper, then prepare the transaction and send it.
        - Otherwise, wait until the next round.
        - If a timeout is hit, set exit A event, otherwise set done event.
        """
        if self.context.agent_address != self.period_state.most_voted_keeper_address:
            yield from self._not_sender_act()
        else:
            yield from self._sender_act()

    def _not_sender_act(self) -> Generator:
        """Do the non-sender action."""
        with benchmark_tool.measure(
            self,
        ).consensus():
            yield from self.wait_until_round_end()
        self.set_done()

    def _sender_act(self) -> Generator[None, None, None]:
        """Do the sender action."""

        with benchmark_tool.measure(
            self,
        ).local():
            self.context.logger.info(
                "I am the designated sender, attempting to send the safe transaction..."
            )
            tx_digest = yield from self._send_safe_transaction()
            if tx_digest is None:
                self.context.logger.info(  # pragma: nocover
                    "Did not succeed with finalising the transaction!"
                )
            else:
                self.context.logger.info(f"Finalization tx digest: {tx_digest}")
                self.context.logger.debug(
                    f"Signatures: {pprint.pformat(self.period_state.participant_to_signature)}"
                )
            payload = FinalizationTxPayload(self.context.agent_address, tx_digest)

        with benchmark_tool.measure(
            self,
        ).consensus():
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()

    def _send_safe_transaction(self) -> Generator[None, None, Optional[str]]:
        """Send a Safe transaction using the participants' signatures."""
        strategy = self.period_state.most_voted_strategy
        contract_api_msg = yield from self.get_contract_api_response(
            performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
            contract_address=self.period_state.safe_contract_address,
            contract_id=str(GnosisSafeContract.contract_id),
            contract_callable="get_raw_safe_transaction",
            sender_address=self.context.agent_address,
            owners=tuple(self.period_state.participants),
            to_address=self.period_state.multisend_contract_address,
            value=ETHER_VALUE,  # TOFIX: value, operation, safe_nonce, safe_tx_gas need to be configurable and synchronised
            data=bytes.fromhex(self.period_state.most_voted_tx_data),
            operation=SafeOperation.DELEGATE_CALL.value,
            safe_tx_gas=strategy["safe_tx_gas"],
            safe_nonce=strategy["safe_nonce"],
            signatures_by_owner={
                key: payload.signature
                for key, payload in self.period_state.participant_to_signature.items()
            },
        )
        if (
            contract_api_msg.performative
            != ContractApiMessage.Performative.RAW_TRANSACTION
        ):  # pragma: nocover
            self.context.logger.warning("get_raw_safe_transaction unsuccessful!")
            return None
        tx_digest = yield from self.send_raw_transaction(
            contract_api_msg.raw_transaction
        )
        return tx_digest


class TransactionValidationBaseBehaviour(LiquidityProvisionBaseBehaviour):
    """ValidateTransaction."""

    def async_act(self) -> Generator:
        """
        Do the action.

        Steps:
        - Validate that the transaction hash provided by the keeper points to a valid transaction.
        - Send the transaction with the validation result and wait for it to be mined.
        - Wait until ABCI application transitions to the next round.
        - Go to the next behaviour state (set done event).
        """

        with benchmark_tool.measure(
            self,
        ).local():
            is_correct = yield from self.has_transaction_been_sent()
            payload = ValidatePayload(self.context.agent_address, is_correct)

        with benchmark_tool.measure(
            self,
        ).consensus():
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()

    def has_transaction_been_sent(self) -> Generator[None, None, Optional[bool]]:
        """Contract deployment verification."""
        strategy = self.period_state.most_voted_strategy
        response = yield from self.get_transaction_receipt(
            self.period_state.final_tx_hash,
            self.params.retry_timeout,
            self.params.retry_attempts,
        )
        if response is None:  # pragma: nocover
            self.context.logger.info(
                f"tx {self.period_state.final_tx_hash} receipt check timed out!"
            )
            return None
        is_settled = EthereumApi.is_transaction_settled(response)
        if not is_settled:  # pragma: nocover
            self.context.logger.info(
                f"tx {self.period_state.final_tx_hash} not settled!"
            )
            return False
        contract_api_msg = yield from self.get_contract_api_response(
            performative=ContractApiMessage.Performative.GET_STATE,  # type: ignore
            contract_address=self.period_state.safe_contract_address,
            contract_id=str(GnosisSafeContract.contract_id),
            contract_callable="verify_tx",
            tx_hash=self.period_state.final_tx_hash,
            owners=tuple(self.period_state.participants),
            to_address=self.period_state.multisend_contract_address,
            value=ETHER_VALUE,  # TOFIX: value, operation, safe_nonce and safe_tx_gas should be part of synchronised params
            data=bytes.fromhex(self.period_state.most_voted_tx_data),
            operation=SafeOperation.DELEGATE_CALL.value,
            safe_tx_gas=strategy["safe_tx_gas"],
            safe_nonce=strategy["safe_nonce"],
            signatures_by_owner={
                key: payload.signature
                for key, payload in self.period_state.participant_to_signature.items()
            },
        )
        if contract_api_msg.performative != ContractApiMessage.Performative.STATE:
            return False  # pragma: nocover
        verified = cast(bool, contract_api_msg.state.body["verified"])
        verified_log = (
            f"Verified result: {verified}"
            if verified
            else f"Verified result: {verified}, all: {contract_api_msg.state.body}"
        )
        self.context.logger.info(verified_log)
        return verified


def get_strategy_update() -> dict:
    """Get a strategy update."""
    strategy = {
        "action": StrategyType.GO,
        "safe_nonce": 0,
        "safe_tx_gas": SAFE_TX_GAS,
        "deadline": CURRENT_BLOCK_TIMESTAMP + 300,  # 5 min into future
        "chain": "Ethereum",
        "base": {
            "ticker": "WETH",
            "address": WETH_ADDRESS,
            "amount_in_a": 10 ** 4,
            "amount_in_b": 10 ** 4,
        },
        "pair": {
            "token_a": {
                "ticker": "TKA",
                "address": TOKEN_A_ADDRESS,
                "amount_desired": 10 ** 3,
                "amount_out_min": 10 ** 3,
                "amount_desired_min": 10 ** 2,
                # If any, only token_a can be the native one (ETH, FTM...)
                "is_native": False,
            },
            "token_b": {
                "ticker": "TKB",
                "address": TOKEN_B_ADDRESS,
                "amount_desired": 10 ** 3,
                "amount_out_min": 10 ** 3,
                "amount_desired_min": 10 ** 2,
            },
        },
        "liquidity_to_remove": 1,  # TOFIX
    }
    return strategy


class StrategyEvaluationBehaviour(LiquidityProvisionBaseBehaviour):
    """Evaluate the financial strategy."""

    state_id = "strategy_evaluation"
    matching_round = StrategyEvaluationRound

    def async_act(self) -> Generator:
        """Do the action."""

        with benchmark_tool.measure(
            self,
        ).local():

            strategy = get_strategy_update()
            if strategy["action"] == StrategyType.WAIT:  # pragma: nocover
                self.context.logger.info("Current strategy is still optimal. Waiting.")

            if strategy["action"] == StrategyType.GO:
                self.context.logger.info(
                    "Performing strategy update: moving into "
                    + f"{strategy['pair']['token_a']['ticker']}-{strategy['pair']['token_b']['ticker']} (pool {self.period_state.router_contract_address})"
                )
            strategy["action"] = strategy["action"].value  # type: ignore
            payload = StrategyEvaluationPayload(self.context.agent_address, strategy)

        with benchmark_tool.measure(
            self,
        ).consensus():
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()


class EnterPoolTransactionHashBehaviour(LiquidityProvisionBaseBehaviour):
    """Prepare the 'enter pool' multisend tx."""

    state_id = "enter_pool_tx_hash"
    matching_round = EnterPoolTransactionHashRound

    def async_act(self) -> Generator:
        """
        Do the action.

        Steps:
        - Request the transaction hash for the safe transaction. This is the hash that needs to be signed by a threshold of agents.
        - Send the transaction hash as a transaction and wait for it to be mined.
        - Wait until ABCI application transitions to the next round.
        - Go to the next behaviour state (set done event).
        """

        with benchmark_tool.measure(
            self,
        ).local():

            strategy = self.period_state.most_voted_strategy

            # Prepare a uniswap tx list. We should check what token balances we have at this point.
            # It is possible that we don't need to swap. For now let's assume we have just USDT
            # and always swap back to it.
            multi_send_txs = []

            # Add allowance for base token (always non-native)
            contract_api_msg = yield from self.get_contract_api_response(
                performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                contract_address=strategy["base"]["address"],
                contract_id=str(UniswapV2ERC20Contract.contract_id),
                contract_callable="get_method_data",
                method_name="approve",
                spender=self.period_state.router_contract_address,
                # We are setting the max (default) allowance here, but it would be better to calculate the minimum required value (but for that we might need some prices).
                value=MAX_ALLOWANCE,
            )
            allowance_base_data = cast(
                bytes, contract_api_msg.raw_transaction.body["data"]
            )
            multi_send_txs.append(
                {
                    "operation": MultiSendOperation.CALL,
                    "to": strategy["base"]["address"],
                    "value": 0,
                    "data": HexBytes(allowance_base_data.hex()),
                }
            )

            # Swap first token (can be native or not)
            method_name = (
                "swap_exact_tokens_for_ETH"
                if strategy["pair"]["token_a"]["is_native"]
                else "swap_exact_tokens_for_tokens"
            )
            contract_api_msg = yield from self.get_contract_api_response(
                performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                contract_address=self.period_state.router_contract_address,
                contract_id=str(UniswapV2Router02Contract.contract_id),
                contract_callable="get_method_data",
                method_name=method_name,
                amount_in=int(strategy["base"]["amount_in_a"]),
                amount_out_min=int(strategy["pair"]["token_a"]["amount_out_min"]),
                path=[
                    strategy["base"]["address"],
                    strategy["pair"]["token_a"]["address"],
                ],
                to=self.period_state.safe_contract_address,
                deadline=strategy["deadline"],
            )
            swap_a_data = cast(bytes, contract_api_msg.raw_transaction.body["data"])
            multi_send_txs.append(
                {
                    "operation": MultiSendOperation.CALL,
                    "to": self.period_state.router_contract_address,
                    "value": 0,
                    "data": HexBytes(swap_a_data.hex()),
                }
            )

            # Swap second token (always non-native)
            contract_api_msg = yield from self.get_contract_api_response(
                performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                contract_address=self.period_state.router_contract_address,
                contract_id=str(UniswapV2Router02Contract.contract_id),
                contract_callable="get_method_data",
                method_name="swap_exact_tokens_for_tokens",
                amount_in=int(strategy["base"]["amount_in_b"]),
                amount_out_min=int(strategy["pair"]["token_b"]["amount_out_min"]),
                path=[
                    strategy["base"]["address"],
                    strategy["pair"]["token_b"]["address"],
                ],
                to=self.period_state.safe_contract_address,
                deadline=strategy["deadline"],
            )
            swap_b_data = cast(bytes, contract_api_msg.raw_transaction.body["data"])
            multi_send_txs.append(
                {
                    "operation": MultiSendOperation.CALL,
                    "to": self.period_state.router_contract_address,
                    "value": 0,
                    "data": HexBytes(swap_b_data.hex()),
                }
            )

            # Add allowance for token A (only if not native)
            if not strategy["pair"]["token_a"]["is_native"]:
                contract_api_msg = yield from self.get_contract_api_response(
                    performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                    contract_address=strategy["pair"]["token_a"]["address"],
                    contract_id=str(UniswapV2ERC20Contract.contract_id),
                    contract_callable="get_method_data",
                    method_name="approve",
                    spender=self.period_state.router_contract_address,
                    # We are setting the max (default) allowance here, but it would be better to calculate the minimum required value (but for that we might need some prices).
                    value=MAX_ALLOWANCE,
                )
                allowance_a_data = cast(
                    bytes, contract_api_msg.raw_transaction.body["data"]
                )
                multi_send_txs.append(
                    {
                        "operation": MultiSendOperation.CALL,
                        "to": strategy["pair"]["token_a"]["address"],
                        "value": 0,
                        "data": HexBytes(allowance_a_data.hex()),
                    }
                )

            # Add allowance for token B (always non-native)
            contract_api_msg = yield from self.get_contract_api_response(
                performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                contract_address=strategy["pair"]["token_b"]["address"],
                contract_id=str(UniswapV2ERC20Contract.contract_id),
                contract_callable="get_method_data",
                method_name="approve",
                spender=self.period_state.router_contract_address,
                # We are setting the max (default) allowance here, but it would be better to calculate the minimum required value (but for that we might need some prices).
                value=MAX_ALLOWANCE,
            )
            allowance_b_data = cast(
                bytes, contract_api_msg.raw_transaction.body["data"]
            )
            multi_send_txs.append(
                {
                    "operation": MultiSendOperation.CALL,
                    "to": strategy["pair"]["token_b"]["address"],
                    "value": 0,
                    "data": HexBytes(allowance_b_data.hex()),
                }
            )

            # Add liquidity
            if strategy["pair"]["token_a"]["is_native"]:
                contract_api_msg = yield from self.get_contract_api_response(
                    performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                    contract_address=self.period_state.router_contract_address,
                    contract_id=str(UniswapV2Router02Contract.contract_id),
                    contract_callable="get_method_data",
                    method_name="add_liquidity_ETH",
                    token=strategy["pair"]["token_b"]["address"],
                    amount_token_desired=int(
                        strategy["pair"]["token_b"]["amount_desired"]
                    ),
                    amount_token_min=int(
                        strategy["pair"]["token_b"]["amount_desired_min"]
                    ),  # Review this factor. For now, we don't want to lose more than 1% here.
                    amount_ETH_min=int(
                        strategy["pair"]["token_a"]["amount_desired_min"]
                    ),  # Review this factor. For now, we don't want to lose more than 1% here.
                    to=self.period_state.safe_contract_address,
                    deadline=strategy["deadline"],  # 5 min into the future
                )
                liquidity_data = cast(
                    bytes, contract_api_msg.raw_transaction.body["data"]
                )
                multi_send_txs.append(
                    {
                        "operation": MultiSendOperation.CALL,
                        "to": self.period_state.router_contract_address,
                        "value": int(strategy["pair"]["token_a"]["amount_desired"]),
                        "data": HexBytes(liquidity_data.hex()),
                    }
                )

            else:
                contract_api_msg = yield from self.get_contract_api_response(
                    performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                    contract_address=self.period_state.router_contract_address,
                    contract_id=str(UniswapV2Router02Contract.contract_id),
                    contract_callable="get_method_data",
                    method_name="add_liquidity",
                    token_a=strategy["pair"]["token_a"]["address"],
                    token_b=strategy["pair"]["token_b"]["address"],
                    amount_a_desired=int(strategy["pair"]["token_a"]["amount_desired"]),
                    amount_b_desired=int(strategy["pair"]["token_b"]["amount_desired"]),
                    amount_a_min=int(
                        strategy["pair"]["token_a"]["amount_desired_min"]
                    ),  # Review this factor. For now, we don't want to lose more than 10% here.
                    amount_b_min=int(
                        strategy["pair"]["token_b"]["amount_desired_min"]
                    ),  # Review this factor. For now, we don't want to lose more than 10% here.
                    to=self.period_state.safe_contract_address,
                    deadline=strategy["deadline"],  # 5 min into the future
                )
                liquidity_data = cast(
                    bytes, contract_api_msg.raw_transaction.body["data"]
                )
                multi_send_txs.append(
                    {
                        "operation": MultiSendOperation.CALL,
                        "to": self.period_state.router_contract_address,
                        "value": 0,
                        "data": HexBytes(liquidity_data.hex()),
                    }
                )

            # Get the tx list data from multisend contract
            contract_api_msg = yield from self.get_contract_api_response(
                performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                contract_address=self.period_state.safe_contract_address,
                contract_id=str(MultiSendContract.contract_id),
                contract_callable="get_tx_data",
                multi_send_txs=multi_send_txs,
            )
            multisend_data = cast(str, contract_api_msg.raw_transaction.body["data"])
            multisend_data = multisend_data[2:]
            self.context.logger.info(f"Multisend data: {multisend_data}")
            # Get the tx hash from Gnosis Safe contract
            contract_api_msg = yield from self.get_contract_api_response(
                performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                contract_address=self.period_state.safe_contract_address,
                contract_id=str(GnosisSafeContract.contract_id),
                contract_callable="get_raw_safe_transaction_hash",
                to_address=self.period_state.multisend_contract_address,
                value=ETHER_VALUE,
                data=bytes.fromhex(multisend_data),
                operation=SafeOperation.DELEGATE_CALL.value,
                safe_tx_gas=strategy["safe_tx_gas"],
                safe_nonce=strategy["safe_nonce"],
            )
            safe_tx_hash = cast(str, contract_api_msg.raw_transaction.body["tx_hash"])
            safe_tx_hash = safe_tx_hash[2:]
            self.context.logger.info(f"Hash of the Safe transaction: {safe_tx_hash}")
            payload = TransactionHashPayload(
                sender=self.context.agent_address,
                tx_hash=json.dumps(
                    {"tx_hash": safe_tx_hash, "tx_data": multisend_data}
                ),  # TOFIX
            )

        with benchmark_tool.measure(
            self,
        ).consensus():
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()


class EnterPoolTransactionSignatureBehaviour(TransactionSignatureBaseBehaviour):
    """Sign the 'enter pool' multisend tx."""

    state_id = "enter_pool_tx_signature"
    matching_round = EnterPoolTransactionSignatureRound


class EnterPoolTransactionSendBehaviour(TransactionSendBaseBehaviour):
    """Send the 'enter pool' multisend tx."""

    state_id = "enter_pool_tx_send"
    matching_round = EnterPoolTransactionSendRound


class EnterPoolTransactionValidationBehaviour(TransactionValidationBaseBehaviour):
    """Validate the 'enter pool' multisend tx."""

    state_id = "enter_pool_tx_validation"
    matching_round = EnterPoolTransactionValidationRound


class EnterPoolRandomnessBehaviour(RandomnessBehaviourPriceEstimation):
    """Get randomness."""

    state_id = "enter_pool_randomness"
    matching_round = EnterPoolRandomnessRound


class EnterPoolSelectKeeperBehaviour(SelectKeeperBehaviour):
    """'exit pool' select keeper."""

    state_id = "enter_pool_select_keeper"
    matching_round = EnterPoolSelectKeeperRound


class ExitPoolTransactionHashBehaviour(LiquidityProvisionBaseBehaviour):
    """Prepare the 'exit pool' multisend tx."""

    state_id = "exit_pool_tx_hash"
    matching_round = ExitPoolTransactionHashRound

    def async_act(self) -> Generator:
        """
        Do the action.

        Steps:
        - Request the transaction hash for the safe transaction. This is the hash that needs to be signed by a threshold of agents.
        - Send the transaction hash as a transaction and wait for it to be mined.
        - Wait until ABCI application transitions to the next round.
        - Go to the next behaviour state (set done event).
        """

        with benchmark_tool.measure(
            self,
        ).local():

            strategy = self.period_state.most_voted_strategy

            # Prepare a uniswap tx list. We should check what token balances we have at this point.
            # It is possible that we don't need to swap. For now let's assume we have just USDT
            # and always swap back to it.
            multi_send_txs = []

            # Remove liquidity
            if strategy["pair"]["token_a"]["is_native"]:

                contract_api_msg = yield from self.get_contract_api_response(
                    performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                    contract_address=self.period_state.router_contract_address,
                    contract_id=str(UniswapV2Router02Contract.contract_id),
                    contract_callable="get_method_data",
                    method_name="remove_liquidity_ETH",
                    token=strategy["pair"]["token_b"]["address"],
                    liquidity=strategy["liquidity_to_remove"],
                    amount_token_min=int(
                        strategy["pair"]["token_b"]["amount_desired_min"]
                    ),  # FIX, get actual amount
                    amount_ETH_min=int(
                        strategy["pair"]["token_a"]["amount_desired_min"]
                    ),
                    to=self.period_state.safe_contract_address,
                    deadline=strategy["deadline"],
                )
                liquidity_data = cast(
                    bytes, contract_api_msg.raw_transaction.body["data"]
                )
                multi_send_txs.append(
                    {
                        "operation": MultiSendOperation.CALL,
                        "to": self.period_state.multisend_contract_address,
                        "value": 0,
                        "data": HexBytes(liquidity_data.hex()),
                    }
                )

            else:

                contract_api_msg = yield from self.get_contract_api_response(
                    performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                    contract_address=self.period_state.router_contract_address,
                    contract_id=str(UniswapV2Router02Contract.contract_id),
                    contract_callable="get_method_data",
                    method_name="remove_liquidity",
                    token_a=strategy["pair"]["token_a"]["address"],
                    token_b=strategy["pair"]["token_b"]["address"],
                    liquidity=strategy["liquidity_to_remove"],
                    amount_a_min=int(strategy["pair"]["token_a"]["amount_desired_min"]),
                    amount_b_min=int(strategy["pair"]["token_b"]["amount_desired_min"]),
                    to=self.period_state.safe_contract_address,
                    deadline=strategy["deadline"],
                )
                liquidity_data = cast(
                    bytes, contract_api_msg.raw_transaction.body["data"]
                )
                multi_send_txs.append(
                    {
                        "operation": MultiSendOperation.CALL,
                        "to": self.period_state.multisend_contract_address,
                        "value": 0,
                        "data": HexBytes(liquidity_data.hex()),
                    }
                )

            # Remove allowance for token A (only if it is not native)
            if not strategy["pair"]["token_a"]["is_native"]:
                contract_api_msg = yield from self.get_contract_api_response(
                    performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                    contract_address=strategy["pair"]["token_a"]["address"],
                    contract_id=str(UniswapV2ERC20Contract.contract_id),
                    contract_callable="get_method_data",
                    method_name="approve",
                    spender=self.period_state.router_contract_address,
                    value=0,
                )
                allowance_a_data = cast(
                    bytes, contract_api_msg.raw_transaction.body["data"]
                )
                multi_send_txs.append(
                    {
                        "operation": MultiSendOperation.CALL,
                        "to": self.period_state.multisend_contract_address,
                        "value": 0,
                        "data": HexBytes(allowance_a_data.hex()),
                    }
                )

            # Remove allowance for token B (always non-native)
            contract_api_msg = yield from self.get_contract_api_response(
                performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                contract_address=strategy["pair"]["token_b"]["address"],
                contract_id=str(UniswapV2ERC20Contract.contract_id),
                contract_callable="get_method_data",
                method_name="approve",
                spender=self.period_state.router_contract_address,
                value=0,
            )
            allowance_b_data = cast(
                bytes, contract_api_msg.raw_transaction.body["data"]
            )
            multi_send_txs.append(
                {
                    "operation": MultiSendOperation.CALL,
                    "to": self.period_state.multisend_contract_address,
                    "value": 0,
                    "data": HexBytes(allowance_b_data.hex()),
                }
            )

            # Swap first token back (can be native or not)
            if strategy["pair"]["token_a"]["is_native"]:
                contract_api_msg = yield from self.get_contract_api_response(
                    performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                    contract_address=self.period_state.router_contract_address,
                    contract_id=str(UniswapV2Router02Contract.contract_id),
                    contract_callable="get_method_data",
                    method_name="swap_exact_ETH_for_tokens",
                    amount_out_min=int(strategy["pair"]["token_a"]["amount_out_min"]),
                    path=[
                        strategy["pair"]["token_a"]["address"],
                        strategy["base"]["address"],
                    ],
                    to=self.period_state.safe_contract_address,
                    deadline=strategy["deadline"],
                )
                swap_a_data = cast(bytes, contract_api_msg.raw_transaction.body["data"])
                multi_send_txs.append(
                    {
                        "operation": MultiSendOperation.CALL,
                        "to": self.period_state.multisend_contract_address,
                        "value": 0,
                        "data": HexBytes(swap_a_data.hex()),
                    }
                )

            else:
                contract_api_msg = yield from self.get_contract_api_response(
                    performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                    contract_address=self.period_state.router_contract_address,
                    contract_id=str(UniswapV2Router02Contract.contract_id),
                    contract_callable="get_method_data",
                    method_name="swap_exact_tokens_for_tokens",
                    amount_in=int(strategy["pair"]["token_a"]["amount_out_min"]),
                    amount_out_min=int(strategy["base"]["amount_in_a"]),
                    path=[
                        strategy["pair"]["token_a"]["address"],
                        strategy["base"]["address"],
                    ],
                    to=self.period_state.safe_contract_address,
                    deadline=strategy["deadline"],
                )
                swap_a_data = cast(bytes, contract_api_msg.raw_transaction.body["data"])
                multi_send_txs.append(
                    {
                        "operation": MultiSendOperation.CALL,
                        "to": self.period_state.multisend_contract_address,
                        "value": 0,
                        "data": HexBytes(swap_a_data.hex()),
                    }
                )

            # Swap second token back (always non-native)
            contract_api_msg = yield from self.get_contract_api_response(
                performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                contract_address=self.period_state.router_contract_address,
                contract_id=str(UniswapV2Router02Contract.contract_id),
                contract_callable="get_method_data",
                method_name="swap_exact_tokens_for_tokens",
                amount_in=int(strategy["pair"]["token_b"]["amount_out_min"]),
                amount_out_min=int(strategy["base"]["amount_in_b"]),
                path=[
                    strategy["pair"]["token_b"]["address"],
                    strategy["base"]["address"],
                ],
                to=self.period_state.safe_contract_address,
                deadline=strategy["deadline"],
            )
            swap_b_data = cast(bytes, contract_api_msg.raw_transaction.body["data"])
            multi_send_txs.append(
                {
                    "operation": MultiSendOperation.CALL,
                    "to": self.period_state.multisend_contract_address,
                    "value": 0,
                    "data": HexBytes(swap_b_data.hex()),
                }
            )

            # Get the tx list data from multisend contract
            contract_api_msg = yield from self.get_contract_api_response(
                performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                contract_address=self.period_state.safe_contract_address,
                contract_id=str(MultiSendContract.contract_id),
                contract_callable="get_tx_data",
                multi_send_txs=multi_send_txs,
            )
            multisend_data = cast(str, contract_api_msg.raw_transaction.body["data"])
            multisend_data = multisend_data[2:]
            self.context.logger.info(f"Multisend data: {multisend_data}")
            # Get the tx hash from Gnosis Safe contract
            contract_api_msg = yield from self.get_contract_api_response(
                performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                contract_address=self.period_state.safe_contract_address,
                contract_id=str(GnosisSafeContract.contract_id),
                contract_callable="get_raw_safe_transaction_hash",
                to_address=self.period_state.multisend_contract_address,
                value=ETHER_VALUE,
                data=bytes.fromhex(multisend_data),
                safe_tx_gas=strategy["safe_tx_gas"],
                safe_nonce=strategy["safe_nonce"],
            )
            safe_tx_hash = cast(str, contract_api_msg.raw_transaction.body["tx_hash"])
            safe_tx_hash = safe_tx_hash[2:]
            self.context.logger.info(f"Hash of the Safe transaction: {safe_tx_hash}")
            payload = TransactionHashPayload(
                sender=self.context.agent_address,
                tx_hash=json.dumps(
                    {"tx_hash": safe_tx_hash, "tx_data": multisend_data}
                ),  # TOFIX
            )

        with benchmark_tool.measure(
            self,
        ).consensus():
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()


class ExitPoolTransactionSignatureBehaviour(TransactionSignatureBaseBehaviour):
    """Prepare the 'exit pool' multisend tx."""

    state_id = "exit_pool_tx_signature"
    matching_round = ExitPoolTransactionSignatureRound


class ExitPoolTransactionSendBehaviour(TransactionSendBaseBehaviour):
    """Prepare the 'exit pool' multisend tx."""

    state_id = "exit_pool_tx_send"
    matching_round = ExitPoolTransactionSendRound


class ExitPoolTransactionValidationBehaviour(TransactionValidationBaseBehaviour):
    """Prepare the 'exit pool' multisend tx."""

    state_id = "exit_pool_tx_validation"
    matching_round = ExitPoolTransactionValidationRound


class ExitPoolRandomnessBehaviour(RandomnessBehaviourPriceEstimation):
    """Get randomness."""

    state_id = "exit_pool_randomness"
    matching_round = ExitPoolRandomnessRound


class ExitPoolSelectKeeperBehaviour(SelectKeeperBehaviour):
    """'exit pool' select keeper."""

    state_id = "exit_pool_select_keeper"
    matching_round = ExitPoolSelectKeeperRound


class LiquidityProvisionConsensusBehaviour(AbstractRoundBehaviour):
    """This behaviour manages the consensus stages for the liquidity provision."""

    initial_state_cls = StrategyEvaluationBehaviour
    abci_app_cls = LiquidityProvisionAbciApp  # type: ignore
    behaviour_states: Set[Type[LiquidityProvisionBaseBehaviour]] = {  # type: ignore
        StrategyEvaluationBehaviour,  # type: ignore
        EnterPoolTransactionHashBehaviour,  # type: ignore
        EnterPoolTransactionSignatureBehaviour,  # type: ignore
        EnterPoolTransactionSendBehaviour,  # type: ignore
        EnterPoolTransactionValidationBehaviour,  # type: ignore
        EnterPoolRandomnessBehaviour,  # type: ignore
        EnterPoolSelectKeeperBehaviour,  # type: ignore
        ExitPoolTransactionHashBehaviour,  # type: ignore
        ExitPoolTransactionSignatureBehaviour,  # type: ignore
        ExitPoolTransactionSendBehaviour,  # type: ignore
        ExitPoolTransactionValidationBehaviour,  # type: ignore
        ExitPoolRandomnessBehaviour,  # type: ignore
        ExitPoolSelectKeeperBehaviour,  # type: ignore
        ResetBehaviour,  # type: ignore
        ResetAndPauseBehaviour,  # type: ignore
    }

    def setup(self) -> None:
        """Set up the behaviour."""
        super().setup()
        benchmark_tool.logger = self.context.logger
