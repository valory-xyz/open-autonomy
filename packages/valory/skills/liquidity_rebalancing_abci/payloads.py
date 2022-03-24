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

"""This module contains the transaction payloads for the liquidity_rebalancing_abci skill."""
from abc import ABC
from enum import Enum
from typing import Any, Dict, Optional

from packages.valory.skills.abstract_round_abci.base import BaseTxPayload


class TransactionType(Enum):
    """Enumeration of transaction types."""

    STRATEGY_EVALUATION = "strategy_evaluation"
    WAIT = "wait"
    ALLOWANCE_CHECK = "allowance_check"
    TRANSACTION_HASH = "tx_hash"
    LP_RESULT = "lp_result"
    TX_HASH = "tx_hash"
    SLEEP = "sleep"

    def __str__(self) -> str:
        """Get the string value of the transaction type."""
        return self.value


class BaseLiquidityRebalancingPayload(BaseTxPayload, ABC):
    """Base class for the liquidity rebalancing skill."""

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


class StrategyEvaluationPayload(BaseLiquidityRebalancingPayload):
    """Represent a transaction payload of type 'strategy_evaluation'."""

    transaction_type = TransactionType.STRATEGY_EVALUATION

    def __init__(self, sender: str, strategy: str, **kwargs: Any) -> None:
        """Initialize a 'strategy_evaluation' transaction payload.

        :param sender: the sender (Ethereum) address
        :param strategy: the new strategy to follow
        :param kwargs: the keyword arguments
        """
        super().__init__(sender, **kwargs)
        self._strategy = strategy

    @property
    def strategy(self) -> str:
        """Get the strategy."""
        return self._strategy

    @property
    def data(self) -> Dict:
        """Get the data."""
        return dict(strategy=self.strategy)


class TransactionHashPayload(BaseTxPayload):
    """Represent a transaction payload of type 'tx_hash'."""

    transaction_type = TransactionType.TX_HASH

    def __init__(
        self, sender: str, tx_hash: Optional[str] = None, **kwargs: Any
    ) -> None:
        """Initialize an 'tx_hash' transaction payload.

        :param sender: the sender (Ethereum) address
        :param tx_hash: the tx_hash
        :param kwargs: the keyword arguments
        """
        super().__init__(sender, **kwargs)
        self._tx_hash = tx_hash

    @property
    def tx_hash(self) -> Optional[str]:
        """Get the tx_hash."""
        return self._tx_hash

    @property
    def data(self) -> Dict:
        """Get the data."""
        return dict(tx_hash=self.tx_hash) if self.tx_hash is not None else {}


class SleepPayload(BaseTxPayload):
    """Represent a transaction payload of type 'sleep'."""

    transaction_type = TransactionType.SLEEP

    @property
    def sleep(self) -> str:
        """Get the sleep dummy property."""
        return "sleep"

    @property
    def data(self) -> Dict:
        """Get the data."""
        return dict(sleep=self.sleep)
