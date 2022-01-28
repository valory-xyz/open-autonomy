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

"""This module contains the transaction payloads for the liquidity_provision skill."""
from abc import ABC
from enum import Enum
from typing import Dict, Optional

from packages.valory.skills.abstract_round_abci.base import BaseTxPayload


class TransactionType(Enum):
    """Enumeration of transaction types."""

    STRATEGY_EVALUATION = "strategy_evaluation"
    WAIT = "wait"
    ALLOWANCE_CHECK = "allowance_check"
    TRANSACTION_HASH = "tx_hash"
    LP_RESULT = "lp_result"

    def __str__(self) -> str:
        """Get the string value of the transaction type."""
        return self.value


class BaseLiquidityProvisionPayload(BaseTxPayload, ABC):
    """Base class for the liquidity provision skill."""

    def __hash__(self) -> int:  # pragma: nocover
        """Hash the payload."""
        return hash(tuple(sorted(self.data.items())))


class StrategyType(Enum):
    """Enumeration of strategy types."""

    WAIT = "wait"
    ENTER = "enter"
    EXIT = "exit"
    SWAP_BACK = "swap_back"

    def __str__(self) -> str:  # pragma: nocover
        """Get the string value of the strategy type."""
        return self.value


class StrategyEvaluationPayload(BaseLiquidityProvisionPayload):
    """Represent a transaction payload of type 'strategy_evaluation'."""

    transaction_type = TransactionType.STRATEGY_EVALUATION

    def __init__(self, sender: str, strategy: dict, id_: Optional[str] = None) -> None:
        """Initialize a 'strategy_evaluation' transaction payload.

        :param sender: the sender (Ethereum) address
        :param strategy: the new strategy to follow
        :param id_: the id of the transaction
        """
        super().__init__(sender, id_)
        self._strategy = strategy

    @property
    def strategy(self) -> dict:
        """Get the strategy."""
        return self._strategy

    @property
    def data(self) -> Dict:
        """Get the data."""
        return dict(strategy=self.strategy)
