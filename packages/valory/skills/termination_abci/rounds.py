# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
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
from typing import Optional, Tuple, cast

from packages.valory.skills.abstract_round_abci.abci_app_chain import (
    AbciAppTransitionMapping,
    chain,
)
from packages.valory.skills.abstract_round_abci.base import (
    AbciApp,
    AbstractRound,
    BaseSynchronizedData,
    BaseTxPayload,
    CollectSameUntilThresholdRound,
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
    def safe_contract_address(self) -> Optional[str]:
        """Get the safe contract address."""
        return cast(Optional[str], self.db.get("safe_contract_address", None))

    @property
    def termination_majority_reached(self) -> bool:
        """Get termination_majority_reached."""
        return cast(bool, self.db.get("termination_majority_reached", False))


class BackgroundRound(CollectSameUntilThresholdRound):
    """Defines the background round, which runs concurrently with other rounds."""

    round_id: str = "background_round"
    allowed_tx_type = BackgroundPayload.transaction_type
    payload_attribute: str = "background_data"
    synchronized_data_class = SynchronizedData

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Event]]:
        """Process the end of the block."""
        if self.threshold_reached:
            state = self.synchronized_data.update(
                synchronized_data_class=self.synchronized_data_class,
                termination_majority_reached=True,
                most_voted_tx_hash=self.most_voted_payload,
            )
            return state, Event.TERMINATE

        return None


class TerminationRound(AbstractRound):
    """Round to act as the counterpart of the behaviour responsible for terminating the agent."""

    round_id = "termination_round"

    def check_payload(self, payload: BaseTxPayload) -> None:
        """No logic required here."""

    def process_payload(self, payload: BaseTxPayload) -> None:
        """No logic required here."""

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Enum]]:
        """No logic required here."""
        return None


class PostTerminationTxAbciApp(AbciApp):
    """The abci app running after the multisig transaction has been settled."""

    initial_round_cls = TerminationRound
    # the following is not needed, it is added to satisfy the round check
    # the TerminationRound when run it terminates the agent, so nothing can come after it
    transition_function = {TerminationRound: {Event.TERMINATE: TerminationRound}}


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
