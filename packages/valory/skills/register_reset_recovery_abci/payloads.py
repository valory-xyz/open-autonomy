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

"""This module contains the transaction payloads for this skill."""
from enum import Enum
from typing import Any, Dict

from packages.valory.skills.abstract_round_abci.base import BaseTxPayload


class TransactionType(Enum):
    """Enumeration of transaction types."""

    ROUND_COUNT = "round_count"


class RoundCountPayload(BaseTxPayload):
    """Defines the RoundCount payload."""

    transaction_type = TransactionType.ROUND_COUNT

    def __init__(self, sender: str, current_round_count: int, **kwargs: Any) -> None:
        """Initialize a 'ROUND_COUNT' transaction payload.

        :param sender: the sender (Ethereum) address
        :param current_round_count: the round count.
        :param kwargs: the keyword arguments
        """
        super().__init__(sender, **kwargs)
        self._current_round_count = current_round_count

    @property
    def current_round_count(self) -> int:
        """Get the round count."""
        return self._current_round_count

    @property
    def data(self) -> Dict:
        """Get the data."""
        return dict(current_round_count=self.current_round_count)

