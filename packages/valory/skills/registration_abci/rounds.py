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

"""This module contains the data classes for common apps ABCI application."""
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple

from packages.valory.skills.abstract_round_abci.base import (
    AbciApp,
    AbciAppTransitionFunction,
    AppState,
    BaseSynchronizedData,
    CollectSameUntilAllRound,
    CollectSameUntilThresholdRound,
    DegenerateRound,
    get_name,
)
from packages.valory.skills.registration_abci.payloads import RegistrationPayload


class Event(Enum):
    """Event enumeration for the price estimation demo."""

    DONE = "done"
    ROUND_TIMEOUT = "round_timeout"
    NO_MAJORITY = "no_majority"


class FinishedRegistrationRound(DegenerateRound):
    """A round representing that agent registration has finished"""


class RegistrationStartupRound(CollectSameUntilAllRound):
    """
    A round in which the agents get registered.

    This round waits until all agents have registered.
    """

    payload_class = RegistrationPayload
    payload_attribute = "initialisation"
    synchronized_data_class = BaseSynchronizedData

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Event]]:
        """Process the end of the block."""
        if not self.collection_threshold_reached:
            return None

        synchronized_data = self.synchronized_data.update(
            participants=frozenset(self.collection),
            synchronized_data_class=self.synchronized_data_class,
        )

        return synchronized_data, Event.DONE


class RegistrationRound(CollectSameUntilThresholdRound):
    """
    A round in which the agents get registered.

    This rounds waits until the threshold of agents has been reached
    and then a further x block confirmations.
    """

    payload_class = RegistrationPayload
    payload_attribute = "initialisation"
    required_block_confirmations = 10
    done_event = Event.DONE
    synchronized_data_class = BaseSynchronizedData

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Event]]:
        """Process the end of the block."""
        if self.threshold_reached:
            self.block_confirmations += 1
        if (
            self.threshold_reached
            and self.block_confirmations
            > self.required_block_confirmations  # we also wait here as it gives more (available) agents time to join
        ):
            synchronized_data = self.synchronized_data.update(
                participants=frozenset(self.collection),
                synchronized_data_class=self.synchronized_data_class,
            )
            return synchronized_data, Event.DONE
        if (
            not self.is_majority_possible(
                self.collection, self.synchronized_data.nb_participants
            )
            and self.block_confirmations > self.required_block_confirmations
        ):
            return self.synchronized_data, Event.NO_MAJORITY
        return None


class AgentRegistrationAbciApp(AbciApp[Event]):
    """AgentRegistrationAbciApp

    Initial round: RegistrationStartupRound

    Initial states: {RegistrationRound, RegistrationStartupRound}

    Transition states:
        0. RegistrationStartupRound
            - done: 2.
        1. RegistrationRound
            - done: 2.
            - no majority: 1.
        2. FinishedRegistrationRound

    Final states: {FinishedRegistrationRound}

    Timeouts:
        round timeout: 30.0
    """

    initial_round_cls: AppState = RegistrationStartupRound
    initial_states: Set[AppState] = {RegistrationStartupRound, RegistrationRound}
    transition_function: AbciAppTransitionFunction = {
        RegistrationStartupRound: {
            Event.DONE: FinishedRegistrationRound,
        },
        RegistrationRound: {
            Event.DONE: FinishedRegistrationRound,
            Event.NO_MAJORITY: RegistrationRound,
        },
        FinishedRegistrationRound: {},
    }
    final_states: Set[AppState] = {
        FinishedRegistrationRound,
    }
    event_to_timeout: Dict[Event, float] = {
        Event.ROUND_TIMEOUT: 30.0,
    }
    db_pre_conditions: Dict[AppState, List[str]] = {
        RegistrationStartupRound: [],
        RegistrationRound: [],
    }
    db_post_conditions: Dict[AppState, List[str]] = {
        FinishedRegistrationRound: [
            get_name(BaseSynchronizedData.participants),
            get_name(BaseSynchronizedData.all_participants),
        ],
    }
