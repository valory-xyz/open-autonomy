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

"""This module contains the transaction payloads for the APY estimation app."""
from enum import Enum
from typing import Dict, Optional

import pandas as pd

from packages.valory.skills.simple_abci.payloads import BaseSimpleAbciPayload


class TransactionType(Enum):
    """Enumeration of transaction types."""

    REGISTRATION = "registration"
    RANDOMNESS = "randomness"
    SELECT_KEEPER = "select_keeper"
    RESET = "reset"
    TRANSFORMATION = "transformation"
    FETCHING = "fetching"

    def __str__(self) -> str:
        """Get the string value of the transaction type."""
        return self.value


class FetchingPayload(BaseSimpleAbciPayload):
    """Represent a transaction payload of type 'fetching'."""

    transaction_type = TransactionType.FETCHING

    def __init__(self, sender: str, history_hash: str, id_: Optional[str] = None) -> None:
        """Initialize a 'fetching' transaction payload.

        :param sender: the sender (Ethereum) address
        :param history_hash: the fetched history's hash.
        :param id_: the id of the transaction
        """
        super().__init__(sender, id_)
        self._history = history_hash

    @property
    def history(self) -> str:
        """Get the fetched history."""
        return self._history

    @property
    def data(self) -> Dict:
        """Get the data."""
        return {"history": self._history}


class TransformationPayload(BaseSimpleAbciPayload):
    """Represent a transaction payload of type 'transformation'."""

    transaction_type = TransactionType.TRANSFORMATION

    def __init__(
        self, sender: str, transformation: pd.DataFrame, id_: Optional[str] = None
    ) -> None:
        """Initialize an 'transformation' transaction payload.

        :param sender: the sender (Ethereum) address
        :param transformation: the transformation of the history.
        :param id_: the id of the transaction
        """
        super().__init__(sender, id_)
        self._transformation = transformation

    @property
    def transformation(self) -> pd.DataFrame:
        """Get the transformation."""
        return self._transformation

    @property
    def data(self) -> Dict:
        """Get the data."""
        return {"transformation": self.transformation}


class ResetPayload(BaseSimpleAbciPayload):
    """Represent a transaction payload of type 'reset'."""

    transaction_type = TransactionType.RESET

    def __init__(
        self, sender: str, period_count: int, id_: Optional[str] = None
    ) -> None:
        """Initialize an 'reset' transaction payload.

        :param sender: the sender (Ethereum) address
        :param period_count: the period count id
        :param id_: the id of the transaction
        """
        super().__init__(sender, id_)
        self._period_count = period_count

    @property
    def period_count(self) -> int:
        """Get the period_count."""
        return self._period_count

    @property
    def data(self) -> Dict:
        """Get the data."""
        return dict(period_count=self.period_count)
