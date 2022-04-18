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
import json
from enum import Enum
from typing import Dict, Optional, Set, Tuple, Type

from packages.valory.skills.abstract_round_abci.base import (
    AbciApp,
    AbciAppTransitionFunction,
    AbstractRound,
    AppState,
    BasePeriodState,
    CollectDifferentUntilAllRound,
    CollectDifferentUntilThresholdRound,
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


class RegistrationStartupRound(CollectDifferentUntilAllRound):
    """A round in which the agents get registered"""

    round_id = "registration_startup"
    allowed_tx_type = RegistrationPayload.transaction_type
    payload_attribute = "initialisation"
    required_block_confirmations = 1

    def end_block(self) -> Optional[Tuple[BasePeriodState, Event]]:
        """Process the end of the block."""
        if self.collection_threshold_reached:
            self.block_confirmations += 1
        if (  # fast forward at setup
            self.collection_threshold_reached
            and self.block_confirmations > self.required_block_confirmations
            and self.most_voted_payload is not None
        ):
            initialisation = json.loads(self.most_voted_payload)
            state = self.period_state.update(
                participants=frozenset(self.collection),
                all_participants=frozenset(self.collection),
                period_state_class=BasePeriodState,
                **initialisation,
            )
            return state, Event.FAST_FORWARD
        if (
            self.collection_threshold_reached
            and self.block_confirmations > self.required_block_confirmations
        ):
            state = self.period_state.update(
                participants=frozenset(self.collection),
                all_participants=frozenset(self.collection),
                period_state_class=BasePeriodState,
            )
            return state, Event.DONE
        return None


class RegistrationRound(CollectDifferentUntilThresholdRound):
    """A round in which the agents get registered"""

    round_id = "registration"
    allowed_tx_type = RegistrationPayload.transaction_type
    payload_attribute = "sender"
    required_block_confirmations = 10
    done_event = Event.DONE

    def end_block(self) -> Optional[Tuple[BasePeriodState, Event]]:
        """Process the end of the block."""
        if self.collection_threshold_reached:
            self.block_confirmations += 1
        if (  # contracts are set from previous rounds
            self.collection_threshold_reached
            and self.block_confirmations
            > self.required_block_confirmations  # we also wait here as it gives more (available) agents time to join
        ):
            state = self.period_state.update(
                participants=frozenset(self.collection),
                period_state_class=BasePeriodState,
            )
            return state, Event.DONE
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
