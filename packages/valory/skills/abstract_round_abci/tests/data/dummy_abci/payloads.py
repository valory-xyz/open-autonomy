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

"""This module contains the transaction payloads of the DummyAbciApp."""

from abc import ABC
from enum import Enum
from typing import Any, Dict, Hashable

from packages.valory.skills.abstract_round_abci.base import BaseTxPayload


class TransactionType(Enum):
    """Enumeration of transaction types."""

    # TODO: define transaction types: e.g. TX_HASH: "tx_hash"
    DUMMY_FINAL = "dummy_final"
    DUMMY_KEEPER_SELECTION = "dummy_keeper_selection"
    DUMMY_RANDOMNESS = "dummy_randomness"
    DUMMY_STARTING = "dummy_starting"

    def __str__(self) -> str:
        """Get the string value of the transaction type."""
        return self.value


class BaseDummyPayload(BaseTxPayload, ABC):
    """Base payload for DummyAbciApp."""

    def __init__(self, sender: str, content: Hashable, **kwargs: Any) -> None:
        """Initialize a transaction payload."""

        super().__init__(sender, **kwargs)
        setattr(self, f"_{self.transaction_type}", content)
        p = property(lambda s: getattr(self, f"_{self.transaction_type}"))
        setattr(self.__class__, f"{self.transaction_type}", p)

    @property
    def data(self) -> Dict[str, Hashable]:
        """Get the data."""
        return dict(content=getattr(self, str(self.transaction_type)))


class DummyStartingPayload(BaseDummyPayload):
    """Represent a transaction payload for the DummyStartingRound."""

    transaction_type = TransactionType.DUMMY_STARTING


class DummyRandomnessPayload(BaseTxPayload):
    """Represent a transaction payload for the DummyRandomnessRound."""

    transaction_type = TransactionType.DUMMY_RANDOMNESS

    def __init__(
        self, sender: str, round_id: int, randomness: str, **kwargs: Any
    ) -> None:
        """Initialize DummyRandomnessPayload"""
        super().__init__(sender, **kwargs)
        self._round_id = round_id
        self._randomness = randomness

    @property
    def round_id(self) -> int:
        """Get the round id."""
        return self._round_id  # pragma: nocover

    @property
    def randomness(self) -> str:
        """Get the randomness."""
        return self._randomness  # pragma: nocover

    @property
    def data(self) -> Dict:
        """Get the data."""
        return dict(round_id=self._round_id, randomness=self._randomness)


class DummyKeeperSelectionPayload(BaseDummyPayload):
    """Represent a transaction payload for the DummyKeeperSelectionRound."""

    transaction_type = TransactionType.DUMMY_KEEPER_SELECTION


class DummyFinalPayload(BaseDummyPayload):
    """Represent a transaction payload for the DummyFinalRound."""

    transaction_type = TransactionType.DUMMY_FINAL
