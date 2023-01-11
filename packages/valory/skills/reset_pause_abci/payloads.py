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

"""This module contains the transaction payloads for the reset_pause_abci app."""
from enum import Enum
from typing import Any, Dict
from dataclasses import dataclass
from packages.valory.skills.abstract_round_abci.base import BaseTxPayload


class TransactionType(Enum):
    """Enumeration of transaction types."""

    RESETPAUSE = "reset_pause"

    def __str__(self) -> str:
        """Get the string value of the transaction type."""
        return self.value

@dataclass(frozen=True)
class ResetPausePayload(BaseTxPayload):
    """Represent a transaction payload of type 'reset'."""

    period_count: int
    transaction_type = TransactionType.RESETPAUSE
