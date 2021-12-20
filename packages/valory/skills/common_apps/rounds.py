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

"""This module contains the data classes for the price estimation ABCI application."""
import struct
from abc import ABC
from enum import Enum
from typing import AbstractSet, Dict, List, Optional, Sequence, Set, Tuple, Type, cast

from packages.valory.skills.abstract_round_abci.base import (
    AbciApp,
    AbciAppTransitionFunction,
    AbstractRound,
    AppState,
    BasePeriodState,
    CollectDifferentUntilAllRound,
    CollectDifferentUntilThresholdRound,
)
from packages.valory.skills.price_estimation_abci.payloads import (
    RegistrationPayload,
    TransactionType,
)


class Event(Enum):
    """Event enumeration for the price estimation demo."""

    DONE = "done"
    ROUND_TIMEOUT = "round_timeout"
    NO_MAJORITY = "no_majority"
    FAST_FORWARD = "fast_forward"
    NEGATIVE = "negative"
    NONE = "none"
    VALIDATE_TIMEOUT = "validate_timeout"
    DEPLOY_TIMEOUT = "deploy_timeout"
    RESET_TIMEOUT = "reset_timeout"
    RESET_AND_PAUSE_TIMEOUT = "reset_and_pause_timeout"
    FAILED = "failed"


def encode_float(value: float) -> bytes:
    """Encode a float value."""
    return struct.pack("d", value)


def rotate_list(my_list: list, positions: int) -> List[str]:
    """Rotate a list n positions."""
    return my_list[positions:] + my_list[:positions]


class PeriodState(BasePeriodState):  # pylint: disable=too-many-instance-attributes
    """
    Class to represent a period state.

    This state is replicated by the tendermint application.
    """

    def __init__(  # pylint: disable=too-many-arguments,too-many-locals
        self,
        participants: Optional[AbstractSet[str]] = None,
        period_count: Optional[int] = None,
        period_setup_params: Optional[Dict] = None,
    ) -> None:
        """Initialize a period state."""
        super().__init__(
            participants=participants,
            period_count=period_count,
            period_setup_params=period_setup_params,
        )

    @property
    def sorted_participants(self) -> Sequence[str]:
        """
        Get the sorted participants' addresses.

        The addresses are sorted according to their hexadecimal value;
        this is the reason we use key=str.lower as comparator.

        This property is useful when interacting with the Safe contract.

        :return: the sorted participants' addresses
        """
        return sorted(self.participants, key=str.lower)


class AgentRegistrationAbstractRound(AbstractRound[Event, TransactionType], ABC):
    """Abstract round for the agent registration skill."""

    @property
    def period_state(self) -> PeriodState:
        """Return the period state."""
        return cast(PeriodState, self._state)

    def _return_no_majority_event(self) -> Tuple[PeriodState, Event]:
        """
        Trigger the NO_MAJORITY event.

        :return: a new period state and a NO_MAJORITY event
        """
        return self.period_state, Event.NO_MAJORITY


class FinishedRound(
    CollectDifferentUntilThresholdRound, AgentRegistrationAbstractRound
):
    """
    This class represents the finished round during operation.

    Input: a period state with the contracts from previous rounds
    Output: a period state with the set of participants.

    It is a sink round.
    """

    round_id = "finished"
    allowed_tx_type = None
    payload_attribute = ""

    def end_block(self) -> Optional[Tuple[BasePeriodState, Event]]:
        """End block."""


class FinishedERound(FinishedRound):
    """This class represents the finished round during operation."""

    round_id = "finished_e"


class FinishedFRound(FinishedRound):
    """This class represents the finished round during operation."""

    round_id = "finished_f"


class RegistrationStartupRound(
    CollectDifferentUntilAllRound, AgentRegistrationAbstractRound
):
    """
    This class represents the registration round.

    Input: None
    Output: a period state with the set of participants.

    It schedules the SelectKeeperARound.
    """

    round_id = "registration_at_startup"
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
            and self.period_state.period_setup_params != {}
            and self.period_state.period_setup_params.get("safe_contract_address", None)
            is not None
            and self.period_state.period_setup_params.get(
                "oracle_contract_address", None
            )
            is not None
        ):
            state = PeriodState(
                participants=self.collection,
                period_count=self.period_state.period_count,
            )
            return state, Event.FAST_FORWARD
        if (
            self.collection_threshold_reached
            and self.block_confirmations > self.required_block_confirmations
        ):  # initial deployment round
            state = PeriodState(
                participants=self.collection,
                period_count=self.period_state.period_count,
            )
            return state, Event.DONE
        return None


class RegistrationRound(
    CollectDifferentUntilThresholdRound, AgentRegistrationAbstractRound
):
    """
    This class represents the registration round during operation.

    Input: a period state with the contracts from previous rounds
    Output: a period state with the set of participants.

    It schedules the SelectKeeperARound.
    """

    round_id = "registration"
    allowed_tx_type = RegistrationPayload.transaction_type
    payload_attribute = "sender"
    required_block_confirmations = 10

    def end_block(self) -> Optional[Tuple[BasePeriodState, Event]]:
        """Process the end of the block."""
        if self.collection_threshold_reached:
            self.block_confirmations += 1
        if (  # contracts are set from previous rounds
            self.collection_threshold_reached
            and self.block_confirmations
            > self.required_block_confirmations  # we also wait here as it gives more (available) agents time to join
        ):
            state = PeriodState(
                participants=frozenset(list(self.collection.keys())),
                period_count=self.period_state.period_count,
            )
            return state, Event.DONE
        return None


class AgentRegistrationAbciApp(AbciApp[Event]):
    """Registration ABCI application."""

    initial_round_cls: Type[AbstractRound] = RegistrationStartupRound
    initial_states: Set[AppState] = {RegistrationStartupRound, RegistrationRound}
    transition_function: AbciAppTransitionFunction = {
        RegistrationStartupRound: {
            Event.DONE: FinishedERound,
            Event.FAST_FORWARD: FinishedFRound,
        },
        RegistrationRound: {
            Event.DONE: FinishedFRound,
        },
        FinishedERound: {},
        FinishedFRound: {},
    }
    final_states: Set[AppState] = {FinishedERound, FinishedFRound}
    event_to_timeout: Dict[Event, float] = {
        Event.ROUND_TIMEOUT: 30.0,
    }
