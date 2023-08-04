# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2023 Valory AG
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

"""This module contains the rounds for the offend_abci skill."""

import json
from enum import Enum
from typing import Dict, Optional, Set, Tuple

from packages.valory.skills.abstract_round_abci.base import (
    AbciApp,
    AbciAppTransitionFunction,
    AppState,
    BaseSynchronizedData,
    CollectSameUntilThresholdRound,
    DegenerateRound,
    OffenseStatusDecoder,
)
from packages.valory.skills.offend_abci.payloads import OffencesPayload


class Event(Enum):
    """Event enumeration for the Offend ABCI demo."""

    DONE = "done"
    ROUND_TIMEOUT = "round_timeout"
    NO_MAJORITY = "no_majority"


class OffendRound(CollectSameUntilThresholdRound):
    """A round in which the agents simulate an offence"""

    synchronized_data_class = BaseSynchronizedData
    payload_class = OffencesPayload

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Event]]:
        """Process the end of the block."""

        if self.threshold_reached:
            self.context.state.round_sequence.offence_status = json.loads(
                self.most_voted_payload,
                cls=OffenseStatusDecoder,
            )
            return self.synchronized_data, Event.DONE
        if not self.is_majority_possible(
            self.collection, self.synchronized_data.nb_participants
        ):
            return self.synchronized_data, Event.NO_MAJORITY
        return None


class FinishedOffendRound(DegenerateRound):
    """Indicates the completion of `OffendRound`."""


class OffendAbciApp(AbciApp[Event]):
    """OffendAbciApp

    Initial round: OffendRound

    Initial states: {OffendRound}

    Transition states:
        0. OffendRound
            - done: 1.
            - no majority: 0.
            - round timeout: 0.
        1. FinishedOffendRound

    Final states: {FinishedOffendRound}

    Timeouts:
        round timeout: 30.0
    """

    initial_round_cls: AppState = OffendRound
    transition_function: AbciAppTransitionFunction = {
        OffendRound: {
            Event.DONE: FinishedOffendRound,
            Event.NO_MAJORITY: OffendRound,
            Event.ROUND_TIMEOUT: OffendRound,
        },
        FinishedOffendRound: {},
    }
    final_states: Set[AppState] = {FinishedOffendRound}
    event_to_timeout: Dict[Event, float] = {
        Event.ROUND_TIMEOUT: 30.0,
    }
    db_pre_conditions: Dict[AppState, Set[str]] = {OffendRound: set()}
    db_post_conditions: Dict[AppState, Set[str]] = {FinishedOffendRound: set()}
