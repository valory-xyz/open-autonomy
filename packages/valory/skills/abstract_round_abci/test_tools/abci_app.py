# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
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


from typing import Dict, Tuple, Type
from unittest.mock import MagicMock

from packages.valory.skills.abstract_round_abci.base import (
    AbciApp,
    AbstractRound,
    BaseTxPayload,
)


class ConcreteRoundA(AbstractRound):
    """Dummy instantiation of the AbstractRound class."""

    round_id = "concrete_a"
    allowed_tx_type = "payload_a"

    def end_block(self) -> Tuple[MagicMock, MagicMock]:
        """End block."""
        return MagicMock(), MagicMock()

    def check_payload(self, payload: BaseTxPayload) -> None:
        """Check payloads of type 'payload_a'."""

    def process_payload(self, payload: BaseTxPayload) -> None:
        """Process payloads of type 'payload_a'."""


class ConcreteRoundB(AbstractRound):
    """Dummy instantiation of the AbstractRound class."""

    round_id = "concrete_b"
    allowed_tx_type = "payload_b"

    def end_block(self) -> None:
        """End block."""

    def check_payload(self, payload: BaseTxPayload) -> None:
        """Check payloads of type 'payload_b'."""

    def process_payload(self, payload: BaseTxPayload) -> None:
        """Process payloads of type 'payload_b'."""


class ConcreteRoundC(AbstractRound):
    """Dummy instantiation of the AbstractRound class."""

    round_id = "concrete_c"
    allowed_tx_type = "payload_c"

    def end_block(self) -> None:
        """End block."""

    def check_payload(self, payload: BaseTxPayload) -> None:
        """Check payloads of type 'payload_c'."""

    def process_payload(self, payload: BaseTxPayload) -> None:
        """Process payloads of type 'payload_c'."""


class AbciAppTest(AbciApp[str]):
    """A dummy AbciApp for testing purposes."""

    TIMEOUT: float = 1.0

    initial_round_cls: Type[AbstractRound] = ConcreteRoundA
    transition_function: Dict[Type[AbstractRound], Dict[str, Type[AbstractRound]]] = {
        ConcreteRoundA: {"a": ConcreteRoundA, "b": ConcreteRoundB, "c": ConcreteRoundC},
        ConcreteRoundB: {"b": ConcreteRoundB, "timeout": ConcreteRoundA},
        ConcreteRoundC: {"c": ConcreteRoundA, "timeout": ConcreteRoundC},
    }
    event_to_timeout: Dict[str, float] = {
        "timeout": TIMEOUT,
    }
