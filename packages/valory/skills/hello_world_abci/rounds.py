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
"""This module contains the data classes for the Hello World ABCI application."""

from abc import ABC
from enum import Enum
from types import MappingProxyType
from typing import Dict, Mapping, Optional, Tuple, Type, cast

from packages.valory.skills.abstract_round_abci.base import (
    AbciApp,
    AbciAppTransitionFunction,
    AbstractRound,
    BaseSynchronizedData,
    CollectDifferentUntilAllRound,
    CollectSameUntilThresholdRound,
)
from packages.valory.skills.hello_world_abci.payloads import (
    PrintMessagePayload,
    RegistrationPayload,
    ResetPayload,
    SelectKeeperPayload,
    TransactionType,
)


class Event(Enum):
    """Event enumeration for the Hello World ABCI demo."""

    DONE = "done"
    ROUND_TIMEOUT = "round_timeout"
    NO_MAJORITY = "no_majority"
    RESET_TIMEOUT = "reset_timeout"


class SynchronizedData(
    BaseSynchronizedData
):  # pylint: disable=too-many-instance-attributes
    """
    Class to represent the synchronized data.

    This state is replicated by the tendermint application.
    """

    @property
    def participant_to_selection(self) -> Mapping[str, SelectKeeperPayload]:
        """Get the participant_to_selection."""
        return cast(
            Mapping[str, SelectKeeperPayload],
            self.db.get_strict("participant_to_selection"),
        )


class HelloWorldABCIAbstractRound(AbstractRound[Event, TransactionType], ABC):
    """Abstract round for the Hello World ABCI skill."""

    @property
    def synchronized_data(self) -> SynchronizedData:
        """Return the synchronized data."""
        return cast(SynchronizedData, self._synchronized_data)


class RegistrationRound(CollectDifferentUntilAllRound, HelloWorldABCIAbstractRound):
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


class SelectKeeperRound(CollectSameUntilThresholdRound, HelloWorldABCIAbstractRound):
    """A round in a which keeper is selected"""

    round_id = "select_keeper"
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
            return self.synchronized_data, Event.NO_MAJORITY
        return None


class PrintMessageRound(CollectDifferentUntilAllRound, HelloWorldABCIAbstractRound):
    """A round in which the agents get registered"""

    round_id = "print_message"
    allowed_tx_type = PrintMessagePayload.transaction_type
    payload_attribute = "message"

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


class ResetAndPauseRound(CollectSameUntilThresholdRound, HelloWorldABCIAbstractRound):
    """This class represents the base reset round."""

    round_id = "reset_and_pause"
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
            return self.synchronized_data, Event.NO_MAJORITY
        return None


class HelloWorldAbciApp(AbciApp[Event]):
    """HelloWorldAbciApp

    Initial round: RegistrationRound

    Initial states: {RegistrationRound}

    Transition states:
        0. RegistrationRound
            - done: 1.
        1. SelectKeeperRound
            - done: 2.
            - round timeout: 0.
            - no majority: 0.
        2. PrintMessageRound
            - done: 3.
            - round timeout: 0.
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
            Event.DONE: SelectKeeperRound,
        },
        SelectKeeperRound: {
            Event.DONE: PrintMessageRound,
            Event.ROUND_TIMEOUT: RegistrationRound,
            Event.NO_MAJORITY: RegistrationRound,
        },
        PrintMessageRound: {
            Event.DONE: ResetAndPauseRound,
            Event.ROUND_TIMEOUT: RegistrationRound,
        },
        ResetAndPauseRound: {
            Event.DONE: SelectKeeperRound,
            Event.RESET_TIMEOUT: RegistrationRound,
            Event.NO_MAJORITY: RegistrationRound,
        },
    }
    event_to_timeout: Dict[Event, float] = {
        Event.ROUND_TIMEOUT: 30.0,
        Event.RESET_TIMEOUT: 30.0,
    }
