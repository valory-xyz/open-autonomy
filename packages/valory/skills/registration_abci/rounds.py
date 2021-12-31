# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021 Valory AG
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
    """This class represents the finished round during operation."""

    round_id = "finished_registration"


class FinishedRegistrationFFWRound(DegenerateRound):
    """This class represents the finished round during operation."""

    round_id = "finished_registration_ffw"


class RegistrationStartupRound(CollectDifferentUntilAllRound):
    """
    This class represents the registration round.

    Input: None
    Output: a period state with the set of participants.

    It schedules the SelectKeeperTransactionSubmissionRoundA.
    """

    round_id = "registration_startup"
    allowed_tx_type = RegistrationPayload.transaction_type
    payload_attribute = "sender"
    required_block_confirmations = 1

    def end_block(self) -> Optional[Tuple[BasePeriodState, Event]]:
        """Process the end of the block."""
        if self.collection_threshold_reached:
            self.block_confirmations += 1
        if (  # fast forward at setup
            self.collection_threshold_reached
            and self.block_confirmations > self.required_block_confirmations
            and self.period_state.db.get("safe_contract_address", None) is not None
            and self.period_state.db.get("oracle_contract_address", None) is not None
        ):
            state = self.period_state.update(
                participants=self.collection,
                safe_contract_address=self.period_state.db.get_strict(
                    "safe_contract_address"
                ),
                oracle_contract_address=self.period_state.db.get_strict(
                    "oracle_contract_address"
                ),
                period_state_class=BasePeriodState,
            )
            return state, Event.FAST_FORWARD
        if (
            self.collection_threshold_reached
            and self.block_confirmations > self.required_block_confirmations
        ):  # initial deployment round
            state = self.period_state.update(
                participants=self.collection,
                period_state_class=BasePeriodState,
            )
            return state, Event.DONE
        return None


class RegistrationRound(CollectDifferentUntilThresholdRound):
    """
    This class represents the registration round during operation.

    Input: a period state with the contracts from previous rounds
    Output: a period state with the set of participants.

    It schedules the SelectKeeperTransactionSubmissionRoundA.
    """

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
                participants=frozenset(list(self.collection.keys())),
                period_state_class=BasePeriodState,
            )
            return state, Event.DONE
        return None


class AgentRegistrationAbciApp(AbciApp[Event]):
    """Registration ABCI application."""

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
