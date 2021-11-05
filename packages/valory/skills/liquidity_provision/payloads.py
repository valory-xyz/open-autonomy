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

"""This module contains the transaction payloads for the liquidity_provision skill."""
from abc import ABC
from enum import Enum
from typing import Dict, Optional

from packages.valory.skills.abstract_round_abci.base import BaseTxPayload


class TransactionType(Enum):
    """Enumeration of transaction types."""

    STRATEGY_EVALUATION = "strategy_evaluation"
    WAIT = "wait"

    SWAP_SELECT_KEEPER = "swap_select_keeper"
    SWAP_TRANSACTION_HASH = "swap_tx_hash"
    SWAP_SIGNATURE = "swap_signature"
    SWAP_SEND = "swap_send"
    SWAP_VALIDATION = "swap_validation"

    ALLOWANCE_CHECK = "allowance_check"

    ADD_ALLOWANCE_SELECT_KEEPER = "add_allowance_select_keeper"
    ADD_ALLOWANCE_TRANSACTION_HASH = "add_allowance_tx_hash"
    ADD_ALLOWANCE_SIGNATURE = "add_allowance_signature"
    ADD_ALLOWANCE_SEND = "add_allowance_send"
    ADD_ALLOWANCE_VALIDATION = "add_allowance_validation"

    ADD_LIQUIDITY_SELECT_KEEPER = "add_liquidity_select_keeper"
    ADD_LIQUIDITY_TRANSACTION_HASH = "add_liquidity_tx_hash"
    ADD_LIQUIDITY_SIGNATURE = "add_liquidity_signature"
    ADD_LIQUIDITY_SEND = "add_liquidity_send"
    ADD_LIQUIDITY_VALIDATION = "add_liquidity_validation"

    REMOVE_LIQUIDITY_SELECT_KEEPER = "remove_liquidity_select_keeper"
    REMOVE_LIQUIDITY_TRANSACTION_HASH = "remove_liquidity_tx_hash"
    REMOVE_LIQUIDITY_SIGNATURE = "remove_liquidity_signature"
    REMOVE_LIQUIDITY_SEND = "remove_liquidity_send"
    REMOVE_LIQUIDITY_VALIDATION = "remove_liquidity_validation"

    REMOVE_ALLOWANCE_SELECT_KEEPER = "remove_allowance_select_keeper"
    REMOVE_ALLOWANCE_TRANSACTION_HASH = "remove_allowance_tx_hash"
    REMOVE_ALLOWANCE_SIGNATURE = "remove_allowance_signature"
    REMOVE_ALLOWANCE_SEND = "remove_allowance_send"
    REMOVE_ALLOWANCE_VALIDATION = "remove_allowance_validation"

    SWAP_BACK_SELECT_KEEPER = "swap_back_select_keeper"
    SWAP_BACK_TRANSACTION_HASH = "swap_back_tx_hash"
    SWAP_BACK_SIGNATURE = "swap_back_signature"
    SWAP_BACK_SEND = "swap_back_send"
    SWAP_BACK_VALIDATION = "swap_back_validation"

    def __str__(self) -> str:
        """Get the string value of the transaction type."""
        return self.value


class BaseLiquidityProvisionPayload(BaseTxPayload, ABC):
    """Base class for the liquidity provision skill."""

    def __hash__(self) -> int:
        """Hash the payload."""
        return hash(tuple(sorted(self.data.items())))


class StrategyType(Enum):
    """Enumeration of strategy types."""

    WAIT = "wait"
    GO = "go"

    def __str__(self) -> str:
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


class AllowanceCheckPayload(BaseLiquidityProvisionPayload):
    """Represent a transaction payload of type 'allowance_check'."""

    transaction_type = TransactionType.STRATEGY_EVALUATION

    def __init__(self, sender: str, allowance: int, id_: Optional[str] = None) -> None:
        """Initialize a 'allowance_check' transaction payload.

        :param sender: the sender (Ethereum) address
        :param allowance: the current allowance
        :param id_: the id of the transaction
        """
        super().__init__(sender, id_)
        self._allowance = allowance

    @property
    def allowance(self) -> int:
        """Get the strategy."""
        return self._allowance

    @property
    def data(self) -> Dict:
        """Get the data."""
        return dict(strategy=self.allowance)
