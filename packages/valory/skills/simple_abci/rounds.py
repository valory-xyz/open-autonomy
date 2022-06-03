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
from typing import Dict, List, Mapping, Optional, Tuple, Type, cast

from packages.valory.skills.abstract_round_abci.base import (
    AbciApp,
    AbciAppTransitionFunction,
    AbstractRound,
    BaseSynchronizedData,
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


class SynchronizedData(
    BaseSynchronizedData
):  # pylint: disable=too-many-instance-attributes
    """
    Class to represent the synchronized data.

    This data is replicated by the tendermint application.
    """

    @property
    def participant_to_randomness(self) -> Mapping[str, RandomnessPayload]:
        """Get the participant_to_randomness."""
        return cast(
            Mapping[str, RandomnessPayload],
            self.db.get_strict("participant_to_randomness"),
        )

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
    def synchronized_data(self) -> SynchronizedData:
        """Return the synchronized data."""
        return cast(SynchronizedData, self._synchronized_data)

    def _return_no_majority_event(self) -> Tuple[SynchronizedData, Event]:
        """
        Trigger the NO_MAJORITY event.

        :return: a new synchronized data synchronized data and a NO_MAJORITY event
        """
        return self.synchronized_data, Event.NO_MAJORITY


class RegistrationRound(CollectDifferentUntilAllRound, SimpleABCIAbstractRound):
    """A round in which the agents get registered"""

    round_id = "registration"
    allowed_tx_type = RegistrationPayload.transaction_type
    payload_attribute = "sender"

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Event]]:
        """Process the end of the block."""
        if self.collection_threshold_reached:
            synchronized_data = self.synchronized_data.update(
                participants=self.collection,
                all_participants=self.collection,
                synchronized_data_class=SynchronizedData,
            )
            return synchronized_data, Event.DONE
        return None


class BaseRandomnessRound(CollectSameUntilThresholdRound, SimpleABCIAbstractRound):
    """A round for generating randomness"""

    allowed_tx_type = RandomnessPayload.transaction_type
    payload_attribute = "randomness"

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Event]]:
        """Process the end of the block."""
        if self.threshold_reached:
            synchronized_data = self.synchronized_data.update(
                participant_to_randomness=MappingProxyType(self.collection),
                most_voted_randomness=self.most_voted_payload,
            )
            return synchronized_data, Event.DONE
        if not self.is_majority_possible(
            self.collection, self.synchronized_data.nb_participants
        ):
            return self._return_no_majority_event()
        return None


class SelectKeeperRound(CollectSameUntilThresholdRound, SimpleABCIAbstractRound):
    """A round in a which keeper is selected"""

    allowed_tx_type = SelectKeeperPayload.transaction_type
    payload_attribute = "keeper"

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Event]]:
        """Process the end of the block."""
        if self.threshold_reached:
            synchronized_data = self.synchronized_data.update(
                participant_to_selection=MappingProxyType(self.collection),
                most_voted_keeper_address=self.most_voted_payload,
            )
            return synchronized_data, Event.DONE
        if not self.is_majority_possible(
            self.collection, self.synchronized_data.nb_participants
        ):
            return self._return_no_majority_event()
        return None


class RandomnessStartupRound(BaseRandomnessRound):
    """A round for generating randomness"""

    round_id = "randomness_startup"


class SelectKeeperAtStartupRound(SelectKeeperRound):
    """A round in a which keeper is selected"""

    round_id = "select_keeper_at_startup"


class BaseResetRound(CollectSameUntilThresholdRound, SimpleABCIAbstractRound):
    """This class represents the base reset round."""

    allowed_tx_type = ResetPayload.transaction_type
    payload_attribute = "period_count"

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Event]]:
        """Process the end of the block."""
        if self.threshold_reached:
            synchronized_data = self.synchronized_data.create(
                participants=[self.synchronized_data.participants],
                all_participants=[self.synchronized_data.all_participants],
            )
            return synchronized_data, Event.DONE
        if not self.is_majority_possible(
            self.collection, self.synchronized_data.nb_participants
        ):
            return self._return_no_majority_event()
        return None


class ResetAndPauseRound(BaseResetRound):
    """A round representing that consensus was reached (the final round)."""

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
        2. SelectKeeperAtStartupRound
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
            Event.DONE: SelectKeeperAtStartupRound,
            Event.ROUND_TIMEOUT: RandomnessStartupRound,
            Event.NO_MAJORITY: RandomnessStartupRound,
        },
        SelectKeeperAtStartupRound: {
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
