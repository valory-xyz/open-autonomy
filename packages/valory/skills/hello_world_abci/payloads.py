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

"""This module contains the transaction payloads for the Hello World skill."""
from abc import ABC
from enum import Enum
from typing import Any, Dict

from packages.valory.skills.abstract_round_abci.base import BaseTxPayload


class TransactionType(Enum):
    """Enumeration of transaction types."""

    REGISTRATION = "registration"
    SELECT_KEEPER = "select_keeper"
    PRINT_MESSAGE = "print_message"
    RESET = "reset"

    def __str__(self) -> str:
        """Get the string value of the transaction type."""
        return self.value


class BaseHelloWorldAbciPayload(BaseTxPayload, ABC):
    """Base class for the Hello World abci demo."""

    def __hash__(self) -> int:
        """Hash the payload."""
        return hash(tuple(sorted(self.data.items())))


class RegistrationPayload(BaseHelloWorldAbciPayload):
    """Represent a transaction payload of type 'registration'."""

    transaction_type = TransactionType.REGISTRATION


class PrintMessagePayload(BaseHelloWorldAbciPayload):
    """Represent a transaction payload of type 'randomness'."""

    transaction_type = TransactionType.PRINT_MESSAGE

    def __init__(self, sender: str, message: str, **kwargs: Any) -> None:
        """Initialize a 'select_keeper' transaction payload.

        :param sender: the sender (Ethereum) address
        :param message: the message printed by the agent
        :param kwargs: the keyword arguments
        """
        super().__init__(sender, **kwargs)
        self._message = message

    @property
    def message(self) -> str:
        """Get the message"""
        return self._message

    @property
    def data(self) -> Dict:
        """Get the data."""
        return dict(message=self._message)


class SelectKeeperPayload(BaseHelloWorldAbciPayload):
    """Represent a transaction payload of type 'select_keeper'."""

    transaction_type = TransactionType.SELECT_KEEPER

    def __init__(self, sender: str, keeper: str, **kwargs: Any) -> None:
        """Initialize an 'select_keeper' transaction payload.

        :param sender: the sender (Ethereum) address
        :param keeper: the keeper selection
        :param kwargs: the keyword arguments
        """
        super().__init__(sender, **kwargs)
        self._keeper = keeper

    @property
    def keeper(self) -> str:
        """Get the keeper."""
        return self._keeper

    @property
    def data(self) -> Dict:
        """Get the data."""
        return dict(keeper=self.keeper)


class ResetPayload(BaseHelloWorldAbciPayload):
    """Represent a transaction payload of type 'reset'."""

    transaction_type = TransactionType.RESET

    def __init__(self, sender: str, period_count: int, **kwargs: Any) -> None:
        """Initialize an 'rest' transaction payload.

        :param sender: the sender (Ethereum) address
        :param period_count: the period count id
        :param kwargs: the keyword arguments
        """
        super().__init__(sender, **kwargs)
        self._period_count = period_count

    @property
    def period_count(self) -> int:
        """Get the period_count."""
        return self._period_count

    @property
    def data(self) -> Dict:
        """Get the data."""
        return dict(period_count=self.period_count)
