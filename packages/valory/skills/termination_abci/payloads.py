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

"""This module contains the termination payload classes."""
from enum import Enum
from typing import Any, Dict

from packages.valory.skills.abstract_round_abci.base import BaseTxPayload


class TransactionType(Enum):
    """Defines the possible transaction types."""

    BACKGROUND = "background"


class BackgroundPayload(BaseTxPayload):
    """Defines the background round payload."""

    transaction_type = TransactionType.BACKGROUND

    def __init__(self, sender: str, background_data: str, **kwargs: Any) -> None:
        """Initialize a 'Termination' transaction payload.

        :param sender: the sender (Ethereum) address
        :param background_data: serialized tx.
        :param kwargs: the keyword arguments
        """
        super().__init__(sender, **kwargs)
        self._background_data = background_data

    @property
    def background_data(self) -> str:
        """Get the termination data."""
        return self._background_data

    @property
    def data(self) -> Dict:
        """Get the data."""
        return dict(background_data=self.background_data)
