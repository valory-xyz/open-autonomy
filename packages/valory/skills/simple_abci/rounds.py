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

"""This module contains the data classes for the simple ABCI application."""
import struct
from abc import ABC
from enum import Enum
from types import MappingProxyType
from typing import Dict, List, Mapping, Optional, Sequence, Tuple, Type, cast

from packages.valory.skills.abstract_round_abci.base import (
    AbciApp,
    AbciAppTransitionFunction,
    AbstractRound,
    BasePeriodState,
    CollectDifferentUntilAllRound,
    CollectSameUntilThresholdRound,
)
from packages.valory.skills.simple_abci.payloads import (
    RandomnessPayload,
    RegistrationPayload,
    ResetPayload,
    SelectKeeperPayload,
    TransactionType,
)


class Event(Enum):
    """Event enumeration for the simple abci demo."""

    DONE = "done"
    ROUND_TIMEOUT = "round_timeout"
    NO_MAJORITY = "no_majority"
    RESET_TIMEOUT = "reset_timeout"


def encode_float(value: float) -> bytes:  # pragma: nocover
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

    @property
    def keeper_randomness(self) -> float:
        """Get the keeper's random number [0-1]."""
        res = int(self.most_voted_randomness, base=16) // 10 ** 0 % 10
        return cast(float, res / 10)

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

    @property
    def participant_to_randomness(self) -> Mapping[str, RandomnessPayload]:
        """Get the participant_to_randomness."""
        return cast(
            Mapping[str, RandomnessPayload],
            self.db.get_strict("participant_to_randomness"),
        )

    @property
    def most_voted_randomness(self) -> str:
        """Get the most_voted_randomness."""
        return cast(str, self.db.get_strict("most_voted_randomness"))

    @property
    def most_voted_keeper_address(self) -> str:
        """Get the most_voted_keeper_address."""
        return cast(str, self.db.get_strict("most_voted_keeper_address"))

    @property
    def participant_to_selection(self) -> Mapping[str, SelectKeeperPayload]:
        """Get the participant_to_selection."""
        return cast(
            Mapping[str, SelectKeeperPayload],
            self.db.get_strict("participant_to_selection"),
        )


class SimpleABCIAbstractRound(AbstractRound[Event, TransactionType], ABC):
    """Abstract round for the simple abci skill."""

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


class RegistrationRound(CollectDifferentUntilAllRound, SimpleABCIAbstractRound):
    """A round in which the agents get registered"""

    round_id = "registration"
    allowed_tx_type = RegistrationPayload.transaction_type
    payload_attribute = "sender"

    def end_block(self) -> Optional[Tuple[BasePeriodState, Event]]:
        """Process the end of the block."""
        if self.collection_threshold_reached:
            state = self.period_state.update(
                participants=self.collection,
                period_state_class=PeriodState,
            )
            return state, Event.DONE
        return None


class BaseRandomnessRound(CollectSameUntilThresholdRound, SimpleABCIAbstractRound):
    """A round for generating randomness"""

    allowed_tx_type = RandomnessPayload.transaction_type
    payload_attribute = "randomness"

    def end_block(self) -> Optional[Tuple[BasePeriodState, Event]]:
        """Process the end of the block."""
        if self.threshold_reached:
            state = self.period_state.update(
                participant_to_randomness=MappingProxyType(self.collection),
                most_voted_randomness=self.most_voted_payload,
            )
            return state, Event.DONE
        if not self.is_majority_possible(
            self.collection, self.period_state.nb_participants
        ):
            return self._return_no_majority_event()
        return None


class SelectKeeperRound(CollectSameUntilThresholdRound, SimpleABCIAbstractRound):
    """A round in which a keeper is selected"""

    allowed_tx_type = SelectKeeperPayload.transaction_type
    payload_attribute = "keeper"

    def end_block(self) -> Optional[Tuple[BasePeriodState, Event]]:
        """Process the end of the block."""
        if self.threshold_reached:
            state = self.period_state.update(
                participant_to_selection=MappingProxyType(self.collection),
                most_voted_keeper_address=self.most_voted_payload,
            )
            return state, Event.DONE
        if not self.is_majority_possible(
            self.collection, self.period_state.nb_participants
        ):
            return self._return_no_majority_event()
        return None


class RandomnessStartupRound(BaseRandomnessRound):
    """Randomness round for startup."""

    round_id = "randomness_startup"


class SelectKeeperAStartupRound(SelectKeeperRound):
    """SelectKeeperAStartupRound round for startup."""

    round_id = "select_keeper_a_startup"


class BaseResetRound(CollectSameUntilThresholdRound, SimpleABCIAbstractRound):
    """A base class for rounds that lead to a reset round"""

    allowed_tx_type = ResetPayload.transaction_type
    payload_attribute = "period_count"

    def end_block(self) -> Optional[Tuple[BasePeriodState, Event]]:
        """Process the end of the block."""
        if self.threshold_reached:
            state = self.period_state.update(
                period_count=self.most_voted_payload,
                participants=self.period_state.participants,
            )
            return state, Event.DONE
        if not self.is_majority_possible(
            self.collection, self.period_state.nb_participants
        ):
            return self._return_no_majority_event()
        return None


class ResetAndPauseRound(BaseResetRound):
    """A round that represents that consensus is reached (the final round)"""

    round_id = "reset_and_pause"


class SimpleAbciApp(AbciApp[Event]):
    """SimpleAbciApp

    Initial round: RegistrationRound

    Initial states: {RegistrationRound}

    Transition states:
    0. RegistrationRound
        - done: 1.
    1. RandomnessStartupRound
        - done: 2.
        - round timeout: 1.
        - no majority: 1.
    2. SelectKeeperAStartupRound
        - done: 3.
        - round timeout: 0.
        - no majority: 0.
    3. ResetAndPauseRound
        - done: 1.
        - reset timeout: 0.
        - no majority: 0.

    Final states: {}

    Timeouts:
        round timeout: 30.0
        reset timeout: 30.0
    """

    initial_round_cls: Type[AbstractRound] = RegistrationRound
    transition_function: AbciAppTransitionFunction = {
        RegistrationRound: {
            Event.DONE: RandomnessStartupRound,
        },
        RandomnessStartupRound: {
            Event.DONE: SelectKeeperAStartupRound,
            Event.ROUND_TIMEOUT: RandomnessStartupRound,
            Event.NO_MAJORITY: RandomnessStartupRound,
        },
        SelectKeeperAStartupRound: {
            Event.DONE: ResetAndPauseRound,
            Event.ROUND_TIMEOUT: RegistrationRound,
            Event.NO_MAJORITY: RegistrationRound,
        },
        ResetAndPauseRound: {
            Event.DONE: RandomnessStartupRound,
            Event.RESET_TIMEOUT: RegistrationRound,
            Event.NO_MAJORITY: RegistrationRound,
        },
    }
    event_to_timeout: Dict[Event, float] = {
        Event.ROUND_TIMEOUT: 30.0,
        Event.RESET_TIMEOUT: 30.0,
    }
