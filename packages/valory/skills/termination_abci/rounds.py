# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022-2023 Valory AG
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

"""This module contains the termination round classes."""

from enum import Enum
from typing import Dict, List, Optional, Tuple, cast

from packages.valory.skills.abstract_round_abci.abci_app_chain import (
    AbciAppTransitionMapping,
    chain,
)
from packages.valory.skills.abstract_round_abci.base import (
    ABCIAppInternalError,
    AbciApp,
    AbstractRound,
    AppState,
    BaseSynchronizedData,
    BaseTxPayload,
    CollectSameUntilThresholdRound,
    TransactionNotValidError,
    get_name,
)
from packages.valory.skills.termination_abci.payloads import BackgroundPayload
from packages.valory.skills.transaction_settlement_abci.rounds import (
    FailedRound,
    FinishedTransactionSubmissionRound,
    TransactionSubmissionAbciApp,
)


class Event(Enum):
    """Defines the (background) round events."""

    TERMINATE = "terminate"


class SynchronizedData(BaseSynchronizedData):
    """
    Class to represent the synchronized data.

    This data is replicated by the tendermint application.
    """

    @property
    def termination_majority_reached(self) -> bool:
        """Get termination_majority_reached."""
        return cast(bool, self.db.get("termination_majority_reached", False))

    @property
    def most_voted_tx_hash(self) -> str:
        """Get the most_voted_tx_hash."""
        return cast(str, self.db.get_strict("most_voted_tx_hash"))  # pragma: no cover


class BackgroundRound(CollectSameUntilThresholdRound):
    """Defines the background round, which runs concurrently with other rounds."""

    payload_class = BackgroundPayload
    payload_attribute: str = "background_data"
    synchronized_data_class = SynchronizedData

    def process_payload(self, payload: BaseTxPayload) -> None:
        """Process payload."""
        # for background round payloads, we don't need to check the round_count, as round_count is irrelevant for the
        # background since it's running concurrently in the background.
        sender = payload.sender
        if sender not in self.accepting_payloads_from:
            raise ABCIAppInternalError(
                f"{sender} not in list of participants: {sorted(self.accepting_payloads_from)}"
            )

        if sender in self.collection:
            raise ABCIAppInternalError(
                f"sender {sender} has already sent value for round: {self.round_id}"
            )

        if self._hash_length:
            content = payload.data.get(self.payload_attribute)
            if not content or len(content) % self._hash_length:
                msg = f"Expecting serialized data of chunk size {self._hash_length}"
                raise ABCIAppInternalError(f"{msg}, got: {content} in {self.round_id}")

        self.collection[sender] = payload

    def check_payload(self, payload: BaseTxPayload) -> None:
        """Check Payload"""
        # NOTE: the TransactionNotValidError is intercepted in ABCIRoundHandler.deliver_tx
        #  which means it will be logged instead of raised
        # for background round payloads, we don't need to check the round_count, as round_count is irrelevant for the
        # background since it's running concurrently in the background.
        sender_in_participant_set = payload.sender in self.accepting_payloads_from
        if not sender_in_participant_set:
            raise TransactionNotValidError(
                f"{payload.sender} not in list of participants: {sorted(self.accepting_payloads_from)}"
            )

        if payload.sender in self.collection:
            raise TransactionNotValidError(
                f"sender {payload.sender} has already sent value for round: {self.round_id}"
            )

        if self._hash_length:
            content = payload.data.get(self.payload_attribute)
            if not content or len(content) % self._hash_length:
                msg = f"Expecting serialized data of chunk size {self._hash_length}"
                raise TransactionNotValidError(
                    f"{msg}, got: {content} in {self.round_id}"
                )

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Event]]:
        """Process the end of the block."""
        if self.threshold_reached:
            state = self.synchronized_data.update(
                synchronized_data_class=self.synchronized_data_class,
                **{
                    get_name(SynchronizedData.termination_majority_reached): True,
                    get_name(
                        SynchronizedData.most_voted_tx_hash
                    ): self.most_voted_payload,
                },
            )
            return state, Event.TERMINATE

        return None


class TerminationRound(AbstractRound):
    """Round to act as the counterpart of the behaviour responsible for terminating the agent."""

    payload_class = None
    synchronized_data_class = SynchronizedData
    payload_attribute = ""

    def check_payload(self, payload: BaseTxPayload) -> None:
        """No logic required here."""

    def process_payload(self, payload: BaseTxPayload) -> None:
        """No logic required here."""

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Enum]]:
        """No logic required here."""
        return None


class PostTerminationTxAbciApp(AbciApp[Event]):
    """PostTerminationTxAbciApp

    Initial round: TerminationRound

    Initial states: {TerminationRound}

    Transition states:
        0. TerminationRound
            - terminate: 0.

    Final states: {}

    Timeouts:

    """

    initial_round_cls = TerminationRound
    # the following is not needed, it is added to satisfy the round check
    # the TerminationRound when run it terminates the agent, so nothing can come after it
    transition_function = {TerminationRound: {Event.TERMINATE: TerminationRound}}
    db_pre_conditions: Dict[AppState, List[str]] = {TerminationRound: []}


termination_transition_function: AbciAppTransitionMapping = {
    FinishedTransactionSubmissionRound: PostTerminationTxAbciApp.initial_round_cls,
    FailedRound: TransactionSubmissionAbciApp.initial_round_cls,
}
TerminationAbciApp = chain(
    (
        TransactionSubmissionAbciApp,
        PostTerminationTxAbciApp,
    ),
    termination_transition_function,
)

TerminationAbciApp.transition_function[BackgroundRound] = {
    Event.TERMINATE: TransactionSubmissionAbciApp.initial_round_cls,
}
