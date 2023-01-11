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

    DUMMY_FINAL = "dummy_final"
    DUMMY_KEEPER_SELECTION = "dummy_keeper_selection"
    DUMMY_RANDOMNESS = "dummy_randomness"
    DUMMY_STARTING = "dummy_starting"

    def __str__(self) -> str:
        """Get the string value of the transaction type."""
        return self.value


class DummyStartingPayload(BaseTxPayload):
    """Represent a transaction payload for the DummyStartingRound."""

    content: str
    transaction_type = TransactionType.DUMMY_STARTING


class DummyRandomnessPayload(BaseTxPayload):
    """Represent a transaction payload for the DummyRandomnessRound."""

    round_id: int
    randomness: str
    transaction_type = TransactionType.DUMMY_RANDOMNESS


class DummyKeeperSelectionPayload(BaseTxPayload):
    """Represent a transaction payload for the DummyKeeperSelectionRound."""

    keepers: str
    transaction_type = TransactionType.DUMMY_KEEPER_SELECTION


class DummyFinalPayload(BaseTxPayload):
    """Represent a transaction payload for the DummyFinalRound."""

    content: str
    transaction_type = TransactionType.DUMMY_FINAL
