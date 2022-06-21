# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2022 Valory AG
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

"""This module contains the data classes for the reset_pause_abci application."""
from enum import Enum
from typing import Dict, Optional, Set, Tuple, Type

from packages.valory.skills.abstract_round_abci.base import (
    AbciApp,
    AbciAppDB,
    AbciAppTransitionFunction,
    AbstractRound,
    AppState,
    BaseSynchronizedData,
    CollectSameUntilThresholdRound,
    DegenerateRound,
)
from packages.valory.skills.reset_pause_abci.payloads import ResetPausePayload


class Event(Enum):
    """Event enumeration for the reset_pause_abci app."""

    DONE = "done"
    ROUND_TIMEOUT = "round_timeout"
    NO_MAJORITY = "no_majority"
    RESET_AND_PAUSE_TIMEOUT = "reset_and_pause_timeout"


class ResetAndPauseRound(CollectSameUntilThresholdRound):
    """A round that represents that consensus is reached (the final round)"""

    round_id = "reset_and_pause"
    allowed_tx_type = ResetPausePayload.transaction_type
    payload_attribute = "period_count"
    _allow_rejoin_payloads = True

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Event]]:
        """Process the end of the block."""
        if self.threshold_reached:
            extra_kwargs = {}
            for key in self.synchronized_data.db.cross_period_persisted_keys:
                extra_kwargs[key] = self.synchronized_data.db.get_strict(key)
            synchronized_data = self.synchronized_data.create(
                synchronized_data_class=self.synchronized_data_class,
                **AbciAppDB.data_to_lists(
                    dict(
                        participants=self.synchronized_data.participants,
                        all_participants=self.synchronized_data.all_participants,
                        **extra_kwargs,
                    )
                ),
            )
            return synchronized_data, Event.DONE
        if not self.is_majority_possible(
            self.collection, self.synchronized_data.nb_participants
        ):
            return self.synchronized_data, Event.NO_MAJORITY
        return None


class FinishedResetAndPauseRound(DegenerateRound):
    """A round that represents reset and pause has finished"""

    round_id = "finished_reset_pause"


class FinishedResetAndPauseErrorRound(DegenerateRound):
    """A round that represents reset and pause has finished with errors"""

    round_id = "finished_reset_pause_error"


class ResetPauseABCIApp(AbciApp[Event]):
    """ResetPauseABCIApp

    Initial round: RegistrationRound

    Initial states: {RegistrationRound}

    Transition states:

    0. ResetAndPauseRound
        - done: 1.
        - reset timeout: 0.
        - no majority: 0.
    1. FinishedResetAndPauseRound
    2. FinishedResetAndPauseErrorRound

    Initial states: {
        ResetAndPauseRound,
    }

    Final states: {
        FinishedResetAndPauseRound,
        FinishedResetAndPauseErrorRound,
    }

    Timeouts:
        round timeout: 30.0
        reset timeout: 30.0
    """

    initial_round_cls: Type[AbstractRound] = ResetAndPauseRound
    transition_function: AbciAppTransitionFunction = {
        ResetAndPauseRound: {
            Event.DONE: FinishedResetAndPauseRound,
            Event.RESET_AND_PAUSE_TIMEOUT: FinishedResetAndPauseErrorRound,
            Event.NO_MAJORITY: FinishedResetAndPauseErrorRound,
        },
        FinishedResetAndPauseRound: {},
        FinishedResetAndPauseErrorRound: {},
    }
    final_states: Set[AppState] = {
        FinishedResetAndPauseRound,
        FinishedResetAndPauseErrorRound,
    }
    event_to_timeout: Dict[Event, float] = {
        Event.ROUND_TIMEOUT: 30.0,
        Event.RESET_AND_PAUSE_TIMEOUT: 30.0,
    }
