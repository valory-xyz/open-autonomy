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

"""ABCI App test tools."""


from abc import ABC
from enum import Enum
from typing import Dict, Tuple, Type, Union
from unittest.mock import MagicMock

from packages.valory.skills.abstract_round_abci.base import (
    AbciApp,
    AbstractRound,
    BaseSynchronizedData,
    BaseTxPayload,
    DegenerateRound,
)


class _ConcreteRound(AbstractRound, ABC):
    """ConcreteRound"""

    synchronized_data_class = BaseSynchronizedData
    payload_attribute = ""

    def end_block(self) -> Union[None, Tuple[MagicMock, MagicMock]]:
        """End block."""

    def check_payload(self, payload: BaseTxPayload) -> None:
        """Check payload."""

    def process_payload(self, payload: BaseTxPayload) -> None:
        """Process payload."""


class ConcreteRoundA(_ConcreteRound):
    """Dummy instantiation of the AbstractRound class."""

    payload_class = BaseTxPayload

    def end_block(self) -> Tuple[MagicMock, MagicMock]:
        """End block."""
        return MagicMock(), MagicMock()


class ConcreteRoundB(_ConcreteRound):
    """Dummy instantiation of the AbstractRound class."""

    payload_class = BaseTxPayload


class ConcreteRoundC(_ConcreteRound):
    """Dummy instantiation of the AbstractRound class."""

    payload_class = BaseTxPayload


class ConcreteBackgroundRound(_ConcreteRound):
    """Dummy instantiation of the AbstractRound class."""

    payload_class = BaseTxPayload


class ConcreteBackgroundSlashingRound(_ConcreteRound):
    """Dummy instantiation of the AbstractRound class."""

    payload_class = BaseTxPayload


class ConcreteTerminationRoundA(_ConcreteRound):
    """Dummy instantiation of the AbstractRound class."""

    payload_class = BaseTxPayload


class ConcreteTerminationRoundB(_ConcreteRound):
    """Dummy instantiation of the AbstractRound class."""

    payload_class = BaseTxPayload


class ConcreteTerminationRoundC(_ConcreteRound):
    """Dummy instantiation of the AbstractRound class."""

    payload_class = BaseTxPayload


class ConcreteSlashingRoundA(_ConcreteRound):
    """Dummy instantiation of the AbstractRound class."""

    payload_class = BaseTxPayload


class ConcreteSlashingRoundB(_ConcreteRound):
    """Dummy instantiation of the AbstractRound class."""

    payload_class = BaseTxPayload


class ConcreteEvents(Enum):
    """Defines dummy events to be used for testing purposes."""

    TERMINATE = "terminate"
    PENDING_OFFENCE = "pending_offence"
    SLASH_START = "slash_start"
    SLASH_END = "slash_end"
    A = "a"
    B = "b"
    C = "c"
    D = "c"
    TIMEOUT = "timeout"

    def __str__(self) -> str:
        """Get the string representation of the event."""
        return self.value


class TerminationAppTest(AbciApp[ConcreteEvents]):
    """A dummy Termination abci for testing purposes."""

    initial_round_cls: Type[AbstractRound] = ConcreteBackgroundRound
    transition_function: Dict[
        Type[AbstractRound], Dict[ConcreteEvents, Type[AbstractRound]]
    ] = {
        ConcreteBackgroundRound: {
            ConcreteEvents.TERMINATE: ConcreteTerminationRoundA,
        },
        ConcreteTerminationRoundA: {
            ConcreteEvents.A: ConcreteTerminationRoundA,
            ConcreteEvents.B: ConcreteTerminationRoundB,
            ConcreteEvents.C: ConcreteTerminationRoundC,
        },
        ConcreteTerminationRoundB: {
            ConcreteEvents.B: ConcreteTerminationRoundB,
            ConcreteEvents.TIMEOUT: ConcreteTerminationRoundA,
        },
        ConcreteTerminationRoundC: {
            ConcreteEvents.C: ConcreteTerminationRoundA,
            ConcreteEvents.TIMEOUT: ConcreteTerminationRoundC,
        },
    }


class SlashingAppTest(AbciApp[ConcreteEvents]):
    """A dummy Slashing abci for testing purposes."""

    initial_round_cls: Type[AbstractRound] = ConcreteBackgroundSlashingRound
    transition_function: Dict[
        Type[AbstractRound], Dict[ConcreteEvents, Type[AbstractRound]]
    ] = {
        ConcreteBackgroundSlashingRound: {
            ConcreteEvents.SLASH_START: ConcreteSlashingRoundA,
        },
        ConcreteSlashingRoundA: {ConcreteEvents.D: ConcreteSlashingRoundB},
        ConcreteSlashingRoundB: {
            ConcreteEvents.SLASH_END: DegenerateRound,
        },
    }


class AbciAppTest(AbciApp[ConcreteEvents]):
    """A dummy AbciApp for testing purposes."""

    TIMEOUT: float = 1.0

    initial_round_cls: Type[AbstractRound] = ConcreteRoundA
    transition_function: Dict[
        Type[AbstractRound], Dict[ConcreteEvents, Type[AbstractRound]]
    ] = {
        ConcreteRoundA: {
            ConcreteEvents.A: ConcreteRoundA,
            ConcreteEvents.B: ConcreteRoundB,
            ConcreteEvents.C: ConcreteRoundC,
        },
        ConcreteRoundB: {
            ConcreteEvents.B: ConcreteRoundB,
            ConcreteEvents.TIMEOUT: ConcreteRoundA,
        },
        ConcreteRoundC: {
            ConcreteEvents.C: ConcreteRoundA,
            ConcreteEvents.TIMEOUT: ConcreteRoundC,
        },
    }
    event_to_timeout: Dict[ConcreteEvents, float] = {
        ConcreteEvents.TIMEOUT: TIMEOUT,
    }
