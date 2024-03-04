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

"""This module contains the data classes for the `transaction settlement` ABCI application."""

import textwrap
from abc import ABC
from collections import deque
from enum import Enum
from typing import Any, Deque, Dict, List, Optional, Set, Tuple, cast

from packages.valory.skills.abstract_round_abci.base import (
    AbciApp,
    AbciAppTransitionFunction,
    AppState,
    BaseSynchronizedData,
    CollectSameUntilThresholdRound,
    DegenerateRound,
    OnlyKeeperSendsRound,
    get_name,
)
from packages.valory.skills.squads_transaction_settlement_abci.payloads import (
    ApproveTxPayload,
    CreateTxPayload,
    ExecuteTxPayload,
    RandomnessPayload,
    SelectKeeperPayload,
    VerifyTxPayload,
)


ADDRESS_LENGTH = 42
TX_HASH_LENGTH = 66
RETRIES_LENGTH = 64


class Event(Enum):
    """Event enumeration for the price estimation demo."""

    DONE = "done"
    ROUND_TIMEOUT = "round_timeout"
    NO_MAJORITY = "no_majority"


class SynchronizedData(BaseSynchronizedData):
    """
    Class to represent the synchronized data.

    This data is replicated by the tendermint application.
    """

    @property
    def is_keeper_set(self) -> bool:
        """Check whether keeper is set."""
        return bool(self.db.get("keepers", False))

    @property
    def keepers(self) -> Deque[str]:
        """Get the current cycle's keepers who have tried to submit a transaction."""
        if self.is_keeper_set:
            keepers_unparsed = cast(str, self.db.get_strict("keepers"))
            keepers_parsed = textwrap.wrap(
                keepers_unparsed[RETRIES_LENGTH:], ADDRESS_LENGTH
            )
            return deque(keepers_parsed)
        return deque()

    @property
    def most_voted_instruction_set(self) -> List[Dict[str, Any]]:
        """Return the list of instructions selected for execution on the multisig."""
        return cast(
            List[Dict[str, Any]], self.db.get_strict("most_voted_instruction_set")
        )

    @property
    def tx_pda(self) -> str:
        """Get the verified tx hash."""
        return cast(str, self.db.get_strict("tx_pda"))

    @property
    def most_voted_randomness_round(self) -> int:  # pragma: no cover
        """Get the first in priority keeper to try to re-submit a transaction."""
        round_ = self.db.get_strict("most_voted_randomness_round")
        return cast(int, round_)

    @property
    def most_voted_keeper_address(self) -> str:
        """Get the first in priority keeper to try to re-submit a transaction."""
        return self.keepers[0]


class CreateTxRandomnessRound(CollectSameUntilThresholdRound):
    """A round for generating randomness"""

    payload_class = RandomnessPayload
    synchronized_data_class = SynchronizedData
    done_event = Event.DONE
    no_majority_event = Event.NO_MAJORITY
    collection_key = get_name(SynchronizedData.participant_to_randomness)
    selection_key = (
        get_name(SynchronizedData.most_voted_randomness_round),
        get_name(SynchronizedData.most_voted_randomness),
    )


class CreateTxSelectKeeperRound(CollectSameUntilThresholdRound):
    """A round in which a keeper is selected for transaction submission"""

    payload_class = SelectKeeperPayload
    synchronized_data_class = SynchronizedData
    done_event = Event.DONE
    no_majority_event = Event.NO_MAJORITY
    collection_key = get_name(SynchronizedData.participant_to_selection)
    selection_key = get_name(SynchronizedData.keepers)


class CreateTxRound(OnlyKeeperSendsRound):
    """A round in which a keeper is selected for transaction submission"""

    keeper_payload: Optional[CreateTxPayload] = None
    payload_class = CreateTxPayload
    synchronized_data_class = SynchronizedData

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Enum]]:
        """Process the end of the block."""
        if self.keeper_payload is None:
            return None
        synchronized_data = cast(
            SynchronizedData,
            self.synchronized_data.update(
                synchronized_data_class=self.synchronized_data_class,
                **{
                    get_name(SynchronizedData.tx_pda): self.keeper_payload.tx_pda,
                },
            ),
        )
        return synchronized_data, Event.DONE


class ApproveTxRound(CollectSameUntilThresholdRound):
    """Approve transaction round."""

    payload_class = ApproveTxPayload
    synchronized_data_class = SynchronizedData
    collection_key = get_name(SynchronizedData.tx_pda)

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Enum]]:
        """End block."""
        if self.threshold_reached:
            return self.synchronized_data, Event.DONE
        return None


class ExecuteTxRandomnessRound(CollectSameUntilThresholdRound):
    """A round for generating randomness"""

    payload_class = RandomnessPayload
    synchronized_data_class = SynchronizedData
    done_event = Event.DONE
    no_majority_event = Event.NO_MAJORITY
    collection_key = get_name(SynchronizedData.participant_to_randomness)
    selection_key = (
        get_name(SynchronizedData.most_voted_randomness_round),
        get_name(SynchronizedData.most_voted_randomness),
    )


class ExecuteTxSelectKeeperRound(CollectSameUntilThresholdRound):
    """A round in which a keeper is selected for transaction submission"""

    payload_class = SelectKeeperPayload
    synchronized_data_class = SynchronizedData
    done_event = Event.DONE
    no_majority_event = Event.NO_MAJORITY
    collection_key = get_name(SynchronizedData.participant_to_selection)
    selection_key = get_name(SynchronizedData.keepers)


class ExecuteTxRound(OnlyKeeperSendsRound):
    """Execute tx round."""

    keeper_payload: Optional[ExecuteTxPayload] = None
    payload_class = CreateTxPayload
    synchronized_data_class = SynchronizedData

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Enum]]:
        """End block."""
        if self.keeper_payload is None:
            return None
        synchronized_data = cast(
            SynchronizedData,
            self.synchronized_data.update(
                synchronized_data_class=self.synchronized_data_class,
                **{
                    get_name(SynchronizedData.tx_pda): self.keeper_payload.tx_pda,
                },
            ),
        )
        return synchronized_data, Event.DONE


class VerifyTxRound(CollectSameUntilThresholdRound):
    """Verify transaction round."""

    payload_class = VerifyTxPayload
    synchronized_data_class = SynchronizedData

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Enum]]:
        """End block."""
        # TODO: Fix implementation
        # This round makes an assumption that the transactio was executed
        # succesfuly and value for VerifyTxPayload.verified is `True`
        # This is to keep things simple for now, We'll continue with
        # A proper round implementation in the next iteration
        if self.threshold_reached:
            return self.synchronized_data, Event.DONE
        return None


class FailedRound(DegenerateRound, ABC):
    """A round that represents that the period failed"""


class FinishedTransactionSubmissionRound(DegenerateRound, ABC):
    """A round that represents the transition to the ResetAndPauseRound"""


class SolanaTransactionSubmissionAbciApp(AbciApp[Event]):
    """SolanaTransactionSubmissionAbciApp

    Initial round: CreateTxRandomnessRound

    Initial states: {CreateTxRandomnessRound}

    Transition states:
        0. CreateTxRandomnessRound
            - done: 1.
            - no majority: 0.
            - round timeout: 0.
        1. CreateTxSelectKeeperRound
            - done: 2.
            - no majority: 0.
            - round timeout: 1.
        2. CreateTxRound
            - done: 3.
            - round timeout: 0.
        3. ApproveTxRound
            - done: 4.
            - no majority: 3.
            - round timeout: 3.
        4. ExecuteTxRandomnessRound
            - done: 5.
            - no majority: 4.
            - round timeout: 4.
        5. ExecuteTxSelectKeeperRound
            - done: 6.
            - no majority: 0.
            - round timeout: 5.
        6. ExecuteTxRound
            - done: 7.
            - round timeout: 4.
        7. VerifyTxRound
            - done: 8.
            - no majority: 7.
            - round timeout: 7.
        8. FinishedTransactionSubmissionRound
        9. FailedRound

    Final states: {FailedRound, FinishedTransactionSubmissionRound}

    Timeouts:
        round timeout: 30.0
    """

    initial_round_cls: AppState = CreateTxRandomnessRound
    initial_states: Set[AppState] = {CreateTxRandomnessRound}
    transition_function: AbciAppTransitionFunction = {
        CreateTxRandomnessRound: {
            Event.DONE: CreateTxSelectKeeperRound,
            Event.NO_MAJORITY: CreateTxRandomnessRound,
            Event.ROUND_TIMEOUT: CreateTxRandomnessRound,
        },
        CreateTxSelectKeeperRound: {
            Event.DONE: CreateTxRound,
            Event.NO_MAJORITY: CreateTxRandomnessRound,
            Event.ROUND_TIMEOUT: CreateTxSelectKeeperRound,
        },
        CreateTxRound: {
            Event.DONE: ApproveTxRound,
            Event.ROUND_TIMEOUT: CreateTxRandomnessRound,
        },
        ApproveTxRound: {
            Event.DONE: ExecuteTxRandomnessRound,
            Event.NO_MAJORITY: ApproveTxRound,
            Event.ROUND_TIMEOUT: ApproveTxRound,
        },
        ExecuteTxRandomnessRound: {
            Event.DONE: ExecuteTxSelectKeeperRound,
            Event.NO_MAJORITY: ExecuteTxRandomnessRound,
            Event.ROUND_TIMEOUT: ExecuteTxRandomnessRound,
        },
        ExecuteTxSelectKeeperRound: {
            Event.DONE: ExecuteTxRound,
            Event.NO_MAJORITY: CreateTxRandomnessRound,
            Event.ROUND_TIMEOUT: ExecuteTxSelectKeeperRound,
        },
        ExecuteTxRound: {
            Event.DONE: VerifyTxRound,
            Event.ROUND_TIMEOUT: ExecuteTxRandomnessRound,
        },
        VerifyTxRound: {
            Event.DONE: FinishedTransactionSubmissionRound,
            Event.NO_MAJORITY: VerifyTxRound,
            Event.ROUND_TIMEOUT: VerifyTxRound,
        },
        FinishedTransactionSubmissionRound: {},
        FailedRound: {},
    }
    final_states: Set[AppState] = {
        FinishedTransactionSubmissionRound,
        FailedRound,
    }
    event_to_timeout: Dict[Event, float] = {
        Event.ROUND_TIMEOUT: 30.0,
    }
    db_pre_conditions: Dict[AppState, Set[str]] = {
        CreateTxRandomnessRound: {
            get_name(SynchronizedData.most_voted_instruction_set),
            get_name(SynchronizedData.participants),
        }
    }
    db_post_conditions: Dict[AppState, Set[str]] = {
        FinishedTransactionSubmissionRound: {
            get_name(SynchronizedData.tx_pda),
        },
        FailedRound: set(),
    }
