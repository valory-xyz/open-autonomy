# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2024 Valory AG
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

"""This module contains the behaviours for the 'abci' skill."""

from abc import ABC
from collections import deque
from typing import Deque, Generator, Optional, Set, Type, cast

from packages.valory.contracts.squads_multisig.contract import (
    MultisigAccountType,
    SquadsMultisig,
    SquadsMultisigAuthorityIndex,
    TransactionStatus,
)
from packages.valory.protocols.contract_api.message import ContractApiMessage
from packages.valory.skills.abstract_round_abci.behaviours import (
    AbstractRoundBehaviour,
    BaseBehaviour,
)
from packages.valory.skills.abstract_round_abci.common import (
    RandomnessBehaviour,
    SelectKeeperBehaviour,
)
from packages.valory.skills.squads_transaction_settlement_abci.models import (
    SolanaTransactionSettlementParams,
)
from packages.valory.skills.squads_transaction_settlement_abci.payloads import (
    ApproveTxPayload,
    CreateTxPayload,
    ExecuteTxPayload,
    RandomnessPayload,
    SelectKeeperPayload,
    VerifyTxPayload,
)
from packages.valory.skills.squads_transaction_settlement_abci.rounds import (
    ApproveTxRound,
    CreateTxRandomnessRound,
    CreateTxRound,
    CreateTxSelectKeeperRound,
    ExecuteTxRandomnessRound,
    ExecuteTxRound,
    ExecuteTxSelectKeeperRound,
    SolanaTransactionSubmissionAbciApp,
    SynchronizedData,
    VerifyTxRound,
)


SOLANA = "solana"


class SolanaTransactionSettlementBaseBehaviour(BaseBehaviour, ABC):
    """Base behaviour for the common apps' skill."""

    @property
    def synchronized_data(self) -> SynchronizedData:
        """Return the synchronized data."""
        return cast(SynchronizedData, super().synchronized_data)

    @property
    def params(self) -> SolanaTransactionSettlementParams:
        """Return the params."""
        return cast(SolanaTransactionSettlementParams, super().params)

    def next_tx_index(self) -> Generator[None, None, Optional[int]]:
        """Get current tx index."""
        response = yield from self.get_contract_api_response(
            performative=ContractApiMessage.Performative.GET_STATE,  # type: ignore
            contract_address=self.synchronized_data.safe_contract_address,
            contract_id=str(SquadsMultisig.contract_id),
            contract_callable="next_tx_index",
            chain_id=SOLANA,
            ledger_id=SOLANA,
        )
        if response.performative != ContractApiMessage.Performative.STATE:
            return None
        return cast(int, response.state.body.pop("data"))

    def get_tx_pda(self, tx_index: int) -> Generator[None, None, Optional[str]]:
        """Create a new PDA for ms transaction."""
        response = yield from self.get_contract_api_response(
            performative=ContractApiMessage.Performative.GET_STATE,  # type: ignore
            contract_address=self.synchronized_data.safe_contract_address,
            contract_id=str(SquadsMultisig.contract_id),
            contract_callable="get_tx_pda",
            tx_index=tx_index,
            chain_id=SOLANA,
            ledger_id=SOLANA,
        )
        if response.performative != ContractApiMessage.Performative.STATE:
            return None
        return cast(str, response.state.body.pop("data"))

    @staticmethod
    def serialized_keepers(keepers: Deque[str], keeper_retries: int) -> str:
        """Get the keepers serialized."""
        if len(keepers) == 0:
            return ""
        keepers_ = "".join(keepers)
        keeper_retries_ = keeper_retries.to_bytes(32, "big").hex()
        concatenated = keeper_retries_ + keepers_

        return concatenated


class CreateTxRandomnessRoundRandomnessBehaviour(RandomnessBehaviour):
    """Retrieve randomness."""

    matching_round = CreateTxRandomnessRound
    payload_class = RandomnessPayload


class CreateTxSelectKeeperBehaviour(  # pylint: disable=too-many-ancestors
    SelectKeeperBehaviour, SolanaTransactionSettlementBaseBehaviour
):
    """Retrieve randomness."""

    matching_round = CreateTxSelectKeeperRound
    payload_class = SelectKeeperPayload

    def async_act(self) -> Generator:
        """Do the action."""

        with self.context.benchmark_tool.measure(self.behaviour_id).local():
            keepers = deque((self._select_keeper(),))
            payload = self.payload_class(
                self.context.agent_address, self.serialized_keepers(keepers, 1)
            )

        with self.context.benchmark_tool.measure(self.behaviour_id).consensus():
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()


class CreateTxBehaviour(SolanaTransactionSettlementBaseBehaviour):
    """Create a transaction with with given set of instructions."""

    matching_round = CreateTxRound

    def async_act(self) -> Generator:  # pylint: disable=inconsistent-return-statements
        """Create transaction."""
        with self.context.benchmark_tool.measure(self.behaviour_id).local():
            next_tx_index = yield from self.next_tx_index()
            if next_tx_index is None:
                return None
            tx_pda = yield from self.get_tx_pda(tx_index=next_tx_index)
            if tx_pda is None:
                return None
            response = yield from self.get_contract_api_response(
                performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                contract_address=self.synchronized_data.safe_contract_address,
                contract_id=str(SquadsMultisig.contract_id),
                contract_callable="create_new_transaction_ix",
                authority_index=SquadsMultisigAuthorityIndex.VAULT.value,
                creator=self.context.agent_addresses["solana"],
                ixs=self.synchronized_data.most_voted_instruction_set,
                tx_pda=tx_pda,
                chain_id=SOLANA,
                ledger_id=SOLANA,
            )
            if response.performative != ContractApiMessage.Performative.RAW_TRANSACTION:
                return None
            tx_digest, _ = yield from self.send_raw_transaction(
                transaction=response.raw_transaction,
                chain_id=SOLANA,
            )
            yield from self.sleep(5)

            self.context.logger.info(
                f"Created transaction with PDA {tx_pda} and hash={tx_digest}"
            )
            payload = CreateTxPayload(
                sender=self.context.agent_address,
                tx_pda=tx_pda,
                tx_digest=cast(str, tx_digest),
            )
        with self.context.benchmark_tool.measure(self.behaviour_id).consensus():
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()
        self.set_done()


class ApproveTxBehaviour(SolanaTransactionSettlementBaseBehaviour):
    """Approve the transaction with given PDA."""

    matching_round = ApproveTxRound

    def async_act(self) -> Generator:  # pylint: disable=inconsistent-return-statements
        """Create transaction."""
        # TODO: Extend implementation
        # It might happen that the ApproveTxRound might not get an majority and
        # we will enter the approve tx round again. This means an agent can try to approve the
        # tx even if they already have done so. To prevent this, add a check which makes sure
        # if an agent has already approved/rejected the tx they don't make the transaction again
        with self.context.benchmark_tool.measure(self.behaviour_id).local():
            response = yield from self.get_contract_api_response(
                performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                contract_address=self.synchronized_data.safe_contract_address,
                contract_id=str(SquadsMultisig.contract_id),
                contract_callable="approve_transaction_ix",
                tx_pda=self.synchronized_data.tx_pda,
                member=self.context.agent_addresses["solana"],
                chain_id=SOLANA,
                ledger_id=SOLANA,
            )
            if response.performative != ContractApiMessage.Performative.RAW_TRANSACTION:
                return None
            yield from self.sleep(5)
            tx_digest, _ = yield from self.send_raw_transaction(
                transaction=response.raw_transaction,
                chain_id=SOLANA,
            )
            self.context.logger.info(
                f"Approved transaction with PDA {self.synchronized_data.tx_pda} and hash={tx_digest}"
            )
            payload = ApproveTxPayload(
                sender=self.context.agent_address,
                tx_pda=self.synchronized_data.tx_pda,
                tx_digest=cast(str, tx_digest),
            )
        with self.context.benchmark_tool.measure(self.behaviour_id).consensus():
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()
        self.set_done()


class ExecuteTxRandomnessRoundRandomnessBehaviour(RandomnessBehaviour):
    """Retrieve randomness."""

    matching_round = ExecuteTxRandomnessRound
    payload_class = RandomnessPayload


class ExecuteTxSelectKeeperBehaviour(  # pylint: disable=too-many-ancestors
    SelectKeeperBehaviour, SolanaTransactionSettlementBaseBehaviour
):
    """Retrieve randomness."""

    matching_round = ExecuteTxSelectKeeperRound
    payload_class = SelectKeeperPayload

    def async_act(self) -> Generator:
        """Do the action."""

        with self.context.benchmark_tool.measure(self.behaviour_id).local():
            keepers = deque((self._select_keeper(),))
            payload = self.payload_class(
                self.context.agent_address, self.serialized_keepers(keepers, 1)
            )

        with self.context.benchmark_tool.measure(self.behaviour_id).consensus():
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()


class ExecuteTxBehaviour(SolanaTransactionSettlementBaseBehaviour):
    """Execute the transaction with given PDA."""

    matching_round = ExecuteTxRound

    def async_act(self) -> Generator:  # pylint: disable=inconsistent-return-statements
        """Create transaction."""
        with self.context.benchmark_tool.measure(self.behaviour_id).local():
            response = yield from self.get_contract_api_response(
                performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                contract_address=self.synchronized_data.safe_contract_address,
                contract_id=str(SquadsMultisig.contract_id),
                contract_callable="execute_transaction_ix",
                tx_pda=self.synchronized_data.tx_pda,
                member=self.context.agent_addresses["solana"],
                chain_id=SOLANA,
                ledger_id=SOLANA,
            )
            if response.performative != ContractApiMessage.Performative.RAW_TRANSACTION:
                return None
            yield from self.sleep(5)

            tx_digest, _ = yield from self.send_raw_transaction(
                transaction=response.raw_transaction,
                chain_id=SOLANA,
            )
            self.context.logger.info(
                f"Executed transaction with PDA {self.synchronized_data.tx_pda} and hash={tx_digest}"
            )
            payload = ExecuteTxPayload(
                sender=self.context.agent_address,
                tx_pda=self.synchronized_data.tx_pda,
                tx_digest=cast(str, tx_digest),
            )
        with self.context.benchmark_tool.measure(self.behaviour_id).consensus():
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()
        self.set_done()


class VerifyTxBehaviour(SolanaTransactionSettlementBaseBehaviour):
    """Execute the transaction with given PDA."""

    matching_round = VerifyTxRound
    _verification_retries: Optional[int] = None

    def async_act(self) -> Generator:  # pylint: disable=inconsistent-return-statements
        """Create transaction."""

        if self._verification_retries is None:
            self._verification_retries = 0

        if self._verification_retries > self.params.tx_verification_retries:
            payload = VerifyTxPayload(
                sender=self.context.agent_address,
                tx_pda=self.synchronized_data.tx_pda,
                verified=False,
            )
            with self.context.benchmark_tool.measure(self.behaviour_id).consensus():
                yield from self.send_a2a_transaction(payload)
                yield from self.wait_until_round_end()
            return self.set_done()

        with self.context.benchmark_tool.measure(self.behaviour_id).local():
            response = yield from self.get_contract_api_response(
                performative=ContractApiMessage.Performative.GET_STATE,  # type: ignore
                contract_address=self.synchronized_data.tx_pda,
                contract_id=str(SquadsMultisig.contract_id),
                contract_callable="get_account_state",
                account_type=MultisigAccountType.MS_TRANSACTION.value,
                chain_id=SOLANA,
                ledger_id=SOLANA,
            )
            if response.performative != ContractApiMessage.Performative.STATE:
                return None
            account_state = response.state.body
            if TransactionStatus(account_state["status"]) != TransactionStatus.Executed:
                yield from self.sleep(self.params.tx_verification_sleep)
                self._verification_retries += 1
                return None
            self._verification_retries = 0
            payload = VerifyTxPayload(
                sender=self.context.agent_address,
                tx_pda=self.synchronized_data.tx_pda,
                verified=True,
            )
        with self.context.benchmark_tool.measure(self.behaviour_id).consensus():
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()
        self.set_done()


class SolanaTransactionSettlementRoundBehaviour(AbstractRoundBehaviour):
    """This behaviour manages the consensus stages for the basic transaction settlement."""

    initial_behaviour_cls = CreateTxRandomnessRoundRandomnessBehaviour
    abci_app_cls = SolanaTransactionSubmissionAbciApp
    behaviours: Set[Type[BaseBehaviour]] = {
        CreateTxRandomnessRoundRandomnessBehaviour,  # type: ignore
        CreateTxSelectKeeperBehaviour,  # type: ignore
        CreateTxBehaviour,  # type: ignore
        ApproveTxBehaviour,  # type: ignore
        ExecuteTxRandomnessRoundRandomnessBehaviour,  # type: ignore
        ExecuteTxSelectKeeperBehaviour,  # type: ignore
        ExecuteTxBehaviour,  # type: ignore
        VerifyTxBehaviour,  # type: ignore
    }
