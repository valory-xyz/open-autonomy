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
from dataclasses import dataclass
from enum import Enum

from packages.valory.skills.abstract_round_abci.base import BaseTxPayload


class TransactionType(Enum):
    """Enumeration of transaction types."""

    REGISTRATION = "registration"
    RANDOMNESS = "collect_randomness"
    SELECT_KEEPER = "select_keeper"
    PRINT_MESSAGE = "print_message"
    RESET = "reset"

    def __str__(self) -> str:
        """Get the string value of the transaction type."""
        return self.value


@dataclass(frozen=True)
class BaseHelloWorldAbciPayload(BaseTxPayload, ABC):
    """Base class for the Hello World abci demo."""


@dataclass(frozen=True)
class RegistrationPayload(BaseHelloWorldAbciPayload):
    """Represent a transaction payload of type 'registration'."""

    transaction_type = TransactionType.REGISTRATION


@dataclass(frozen=True)
class CollectRandomnessPayload(BaseHelloWorldAbciPayload):
    """Represent a transaction payload of type 'randomness'."""

    round_id: int
    randomness: str
    transaction_type = TransactionType.RANDOMNESS


@dataclass(frozen=True)
class PrintMessagePayload(BaseHelloWorldAbciPayload):
    """Represent a transaction payload of type 'randomness'."""

    message: str
    transaction_type = TransactionType.PRINT_MESSAGE


@dataclass(frozen=True)
class SelectKeeperPayload(BaseHelloWorldAbciPayload):
    """Represent a transaction payload of type 'select_keeper'."""

    keeper: str
    transaction_type = TransactionType.SELECT_KEEPER


@dataclass(frozen=True)
class ResetPayload(BaseHelloWorldAbciPayload):
    """Represent a transaction payload of type 'reset'."""

    period_count: int
    transaction_type = TransactionType.RESET
