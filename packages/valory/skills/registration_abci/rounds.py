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

"""This module contains the data classes for common apps ABCI application."""
from enum import Enum
from typing import Dict, Optional, Set, Tuple, Type

from packages.valory.skills.abstract_round_abci.base import (
    AbciApp,
    AbciAppTransitionFunction,
    AbstractRound,
    AppState,
    BaseSynchronizedData,
    CollectSameUntilAllRound,
    CollectSameUntilThresholdRound,
    DegenerateRound,
)
from packages.valory.skills.registration_abci.payloads import RegistrationPayload


class Event(Enum):
    """Event enumeration for the price estimation demo."""

    DONE = "done"
    ROUND_TIMEOUT = "round_timeout"
    NO_MAJORITY = "no_majority"
    FAST_FORWARD = "fast_forward"


class FinishedRegistrationRound(DegenerateRound):
    """A round representing that agent registration has finished"""

    round_id = "finished_registration"


class FinishedRegistrationFFWRound(DegenerateRound):
    """A fast-forward round representing that agent registration has finished"""

    round_id = "finished_registration_ffw"


class RegistrationStartupRound(CollectSameUntilAllRound):
    """A round in which the agents get registered"""

    round_id = "registration_startup"
    allowed_tx_type = RegistrationPayload.transaction_type
    payload_attribute = "initialisation"

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Event]]:
        """Process the end of the block."""
        if (  # fast forward at setup
            self.collection_threshold_reached and self.common_payload is not None
        ):
            synchronized_data = self.synchronized_data.update(
                participants=frozenset(self.collection),
                all_participants=frozenset(self.collection),
                synchronized_data_class=BaseSynchronizedData,
            )
            return synchronized_data, Event.FAST_FORWARD
        if self.collection_threshold_reached:
            synchronized_data = self.synchronized_data.update(
                participants=frozenset(self.collection),
                all_participants=frozenset(self.collection),
                synchronized_data_class=BaseSynchronizedData,
            )
            return synchronized_data, Event.DONE
        return None


class RegistrationRound(CollectSameUntilThresholdRound):
    """A round in which the agents get registered"""

    round_id = "registration"
    allowed_tx_type = RegistrationPayload.transaction_type
    payload_attribute = "initialisation"
    required_block_confirmations = 10
    done_event = Event.DONE

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Event]]:
        """Process the end of the block."""
        if self.threshold_reached:
            self.block_confirmations += 1
        if (  # contracts are set from previous rounds
            self.threshold_reached
            and self.block_confirmations
            > self.required_block_confirmations  # we also wait here as it gives more (available) agents time to join
        ):
            synchronized_data = self.synchronized_data.update(
                participants=frozenset(self.collection),
                synchronized_data_class=BaseSynchronizedData,
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
            - fast forward: 3.
        1. RegistrationRound
            - done: 3.
            - no majority: 1.
        2. FinishedRegistrationRound
        3. FinishedRegistrationFFWRound

    Final states: {FinishedRegistrationFFWRound, FinishedRegistrationRound}

    Timeouts:
        round timeout: 30.0
    """

    initial_round_cls: Type[AbstractRound] = RegistrationStartupRound
    initial_states: Set[AppState] = {RegistrationStartupRound, RegistrationRound}
    transition_function: AbciAppTransitionFunction = {
        RegistrationStartupRound: {
            Event.DONE: FinishedRegistrationRound,
            Event.FAST_FORWARD: FinishedRegistrationFFWRound,
        },
        RegistrationRound: {
            Event.DONE: FinishedRegistrationFFWRound,
            Event.NO_MAJORITY: RegistrationRound,
        },
        FinishedRegistrationRound: {},
        FinishedRegistrationFFWRound: {},
    }
    final_states: Set[AppState] = {
        FinishedRegistrationRound,
        FinishedRegistrationFFWRound,
    }
    event_to_timeout: Dict[Event, float] = {
        Event.ROUND_TIMEOUT: 30.0,
    }
