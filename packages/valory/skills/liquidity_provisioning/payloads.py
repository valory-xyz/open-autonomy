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

"""This module contains the transaction payloads for the price_estimation app."""
from abc import ABC
from enum import Enum
from typing import Dict, Optional

from packages.valory.skills.abstract_round_abci.base import BaseTxPayload

from packages.valory.skills.price_estimation_abci.payloads import (
    RegistrationPayload,
    RandomnessPayload,
    SelectKeeperPayload,
    ValidatePayload,
    SignaturePayload,

)

class TransactionType(Enum):
    """Enumeration of transaction types."""

    SWAP = "swap"
    ALLOWANCE_CHECK = "allowance_check"
    APPROVE = "approve"
    ADD_LIQUIDITY = "add_liquidity"
    REMOVE_LIQUIDITY = "remove_liquidity"


    def __str__(self) -> str:
        """Get the string value of the transaction type."""
        return self.value