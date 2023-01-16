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
"""This module contains the round classes for register reset recovery."""

from enum import Enum
from typing import Dict, List, Optional, Tuple, Type, cast

from packages.valory.skills.abstract_round_abci.base import (
    AbciApp,
    AbciAppTransitionFunction,
    AbstractRound,
    AppState,
    BaseSynchronizedData,
    CollectSameUntilThresholdRound,
)
from packages.valory.skills.register_reset_recovery_abci.payloads import (
    RoundCountPayload,
)


class Event(Enum):
    """Event enumeration for the Round Count round."""

    DONE = "done"
    ROUND_TIMEOUT = "round_timeout"


class RoundCountRound(CollectSameUntilThresholdRound):
    """A round in which the round count is stored as a list."""

    payload_class = RoundCountPayload
    payload_attribute = "current_round_count"
    synchronized_data_class = BaseSynchronizedData

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Event]]:
        """Process the end of the block."""
        if self.threshold_reached:
            # this simulates a state that is built across different rounds
            # we are using `round_count` here simply for convenience reasons,
            # it can be any data.
            all_round_counts: List[int] = cast(
                List[int], self.synchronized_data.db.get("round_counts", [])
            )
            all_round_counts.append(self.most_voted_payload)
            synchronized_data = self.synchronized_data.update(
                round_counts=all_round_counts,
            )
            return synchronized_data, Event.DONE
        return None


class RoundCountAbciApp(AbciApp[Event]):
    """RoundCountAbciApp

    Initial round: RoundCountRound

    Initial states: {RoundCountRound}

    Transition states:
        0. RoundCountRound
            - done: 0.

    Final states: {}

    Timeouts:
        round timeout: 30.0
    """

    initial_round_cls: Type[AbstractRound] = RoundCountRound
    initial_states = {RoundCountRound}
    transition_function: AbciAppTransitionFunction = {
        RoundCountRound: {
            Event.DONE: RoundCountRound,
        }
    }
    event_to_timeout: Dict[Event, float] = {
        Event.ROUND_TIMEOUT: 30.0,
    }
    db_pre_conditions: Dict[AppState, List[str]] = {RoundCountRound: []}
