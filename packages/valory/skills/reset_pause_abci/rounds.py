# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2023 Valory AG
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
from typing import Dict, Optional, Set, Tuple

from packages.valory.skills.abstract_round_abci.base import (
    AbciApp,
    AbciAppTransitionFunction,
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

    payload_class = ResetPausePayload
    _allow_rejoin_payloads = True
    synchronized_data_class = BaseSynchronizedData

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Event]]:
        """Process the end of the block."""
        if self.threshold_reached:
            return self.synchronized_data.create(), Event.DONE
        if not self.is_majority_possible(
            self.collection, self.synchronized_data.nb_participants
        ):
            return self.synchronized_data, Event.NO_MAJORITY
        return None


class FinishedResetAndPauseRound(DegenerateRound):
    """A round that represents reset and pause has finished"""


class FinishedResetAndPauseErrorRound(DegenerateRound):
    """A round that represents reset and pause has finished with errors"""


class ResetPauseAbciApp(AbciApp[Event]):
    """ResetPauseAbciApp

    Initial round: ResetAndPauseRound

    Initial states: {ResetAndPauseRound}

    Transition states:
        0. ResetAndPauseRound
            - done: 1.
            - reset and pause timeout: 2.
            - no majority: 2.
        1. FinishedResetAndPauseRound
        2. FinishedResetAndPauseErrorRound

    Final states: {FinishedResetAndPauseErrorRound, FinishedResetAndPauseRound}

    Timeouts:
        round timeout: 30.0
        reset and pause timeout: 30.0
    """

    initial_round_cls: AppState = ResetAndPauseRound
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
    db_pre_conditions: Dict[AppState, Set[str]] = {ResetAndPauseRound: set()}
    db_post_conditions: Dict[AppState, Set[str]] = {
        FinishedResetAndPauseRound: set(),
        FinishedResetAndPauseErrorRound: set(),
    }
