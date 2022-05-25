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

"""This module contains the data classes for the liquidity rebalancing ABCI application."""
import json
from abc import ABC
from enum import Enum
from types import MappingProxyType
from typing import Dict, Mapping, Optional, Set, Tuple, Type, cast

from packages.valory.skills.abstract_round_abci.base import (
    AbciApp,
    AbciAppTransitionFunction,
    AbstractRound,
    AppState,
    BaseSynchronizedData,
    CollectSameUntilThresholdRound,
    DegenerateRound,
)
from packages.valory.skills.liquidity_rebalancing_abci.payloads import (
    SleepPayload,
    StrategyEvaluationPayload,
    StrategyType,
    TransactionHashPayload,
)
from packages.valory.skills.transaction_settlement_abci.payloads import (
    SignaturePayload,
    TransactionType,
)


class Event(Enum):
    """Event enumeration for the liquidity rebalancing demo."""

    DONE = "done"
    DONE_ENTER = "done_enter"
    DONE_EXIT = "done_exit"
    DONE_SWAP_BACK = "done_swap_back"
    EXIT = "exit"
    ROUND_TIMEOUT = "round_timeout"
    NO_MAJORITY = "no_majority"
    RESET_TIMEOUT = "reset_timeout"


class SynchronizedData(
    BaseSynchronizedData
):  # pylint: disable=too-many-instance-attributes,too-many-statements,too-many-public-methods
    """
    Class to represent the synchronized data.

    This data is replicated by the tendermint application.
    """

    @property
    def most_voted_strategy(self) -> str:
        """Get the most_voted_strategy."""
        return cast(str, self.db.get_strict("most_voted_strategy"))

    @property
    def participant_to_strategy(self) -> Mapping[str, StrategyEvaluationPayload]:
        """Get the participant_to_strategy."""
        return cast(
            Mapping[str, StrategyEvaluationPayload],
            self.db.get_strict("participant_to_strategy"),
        )

    @property
    def participant_to_tx_hash(self) -> Mapping[str, TransactionHashPayload]:
        """Get the participant_to_tx_hash."""
        return cast(
            Mapping[str, TransactionHashPayload],
            self.db.get_strict("participant_to_tx_hash"),
        )

    @property
    def most_voted_keeper_address(self) -> str:
        """Get the most_voted_keeper_address."""
        return cast(str, self.db.get_strict("most_voted_keeper_address"))

    @property
    def safe_contract_address(self) -> str:
        """Get the safe contract address."""
        return cast(str, self.db.get_strict("safe_contract_address"))

    @property
    def multisend_contract_address(self) -> str:
        """Get the multisend contract address."""
        return cast(str, self.db.get_strict("multisend_contract_address"))

    @property
    def router_contract_address(self) -> str:
        """Get the router02 contract address."""
        return cast(str, self.db.get_strict("router_contract_address"))

    @property
    def participant_to_signature(self) -> Mapping[str, SignaturePayload]:
        """Get the participant_to_signature."""
        return cast(
            Mapping[str, SignaturePayload],
            self.db.get_strict("participant_to_signature"),
        )

    @property
    def most_voted_tx_hash(self) -> str:
        """Get the most_voted_enter_pool_tx_hash."""
        return cast(str, self.db.get_strict("most_voted_tx_hash"))

    @property
    def final_tx_hash(self) -> str:
        """Get the final_enter_pool_tx_hash."""
        return cast(str, self.db.get_strict("final_tx_hash"))


class LiquidityRebalancingAbstractRound(AbstractRound[Event, TransactionType], ABC):
    """Abstract round for the liquidity rebalancing skill."""

    @property
    def synchronized_data(self) -> SynchronizedData:
        """Return the synchronized data."""
        return cast(SynchronizedData, self._synchronized_data)

    def _return_no_majority_event(self) -> Tuple[SynchronizedData, Event]:
        """
        Trigger the NO_MAJORITY event.

        :return: a new synchronized data and a NO_MAJORITY event
        """
        return self.synchronized_data, Event.NO_MAJORITY


class TransactionHashBaseRound(
    CollectSameUntilThresholdRound, LiquidityRebalancingAbstractRound
):
    """A base class for rounds in which agents compute the transaction hash"""

    round_id = "tx_hash"
    allowed_tx_type = TransactionHashPayload.transaction_type
    payload_attribute = "tx_hash"

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Event]]:
        """Process the end of the block."""
        if self.threshold_reached:
            dict_ = json.loads(self.most_voted_payload)
            synchronized_data = self.synchronized_data.update(
                participant_to_tx_hash=MappingProxyType(self.collection),
                most_voted_tx_hash=dict_["tx_hash"],
            )
            return synchronized_data, Event.DONE
        if not self.is_majority_possible(
            self.collection, self.synchronized_data.nb_participants
        ):
            return self._return_no_majority_event()
        return None


class StrategyEvaluationRound(
    CollectSameUntilThresholdRound, LiquidityRebalancingAbstractRound
):
    """A round in which agents evaluate the financial strategy"""

    round_id = "strategy_evaluation"
    allowed_tx_type = StrategyEvaluationPayload.transaction_type
    payload_attribute = "strategy"

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Event]]:
        """Process the end of the block."""
        if self.threshold_reached:
            synchronized_data = self.synchronized_data.update(
                participant_to_strategy=MappingProxyType(self.collection),
                most_voted_strategy=self.most_voted_payload,
            )

            strategy = json.loads(self.most_voted_payload)

            event = Event.RESET_TIMEOUT
            if strategy["action"] == StrategyType.WAIT.value:
                event = Event.DONE
            elif strategy["action"] == StrategyType.ENTER.value:
                event = Event.DONE_ENTER
            elif strategy["action"] == StrategyType.EXIT.value:
                event = Event.DONE_EXIT
            elif strategy["action"] == StrategyType.SWAP_BACK.value:
                event = Event.DONE_SWAP_BACK
            return synchronized_data, event
        if not self.is_majority_possible(
            self.collection, self.synchronized_data.nb_participants
        ):
            return self._return_no_majority_event()
        return None


class SleepRound(CollectSameUntilThresholdRound, LiquidityRebalancingAbstractRound):
    """A round in which agents wait for a predefined amount of time"""

    round_id = "sleep"
    allowed_tx_type = SleepPayload.transaction_type
    payload_attribute = "sleep"

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Event]]:
        """Process the end of the block."""
        if self.threshold_reached:
            return self.synchronized_data, Event.DONE
        if not self.is_majority_possible(
            self.collection, self.synchronized_data.nb_participants
        ):
            return self._return_no_majority_event()
        return None


class EnterPoolTransactionHashRound(TransactionHashBaseRound):
    """A round in which agents compute the transaction hash for pool entry"""

    round_id = "enter_pool_tx_hash"


class FinishedEnterPoolTransactionHashRound(DegenerateRound):
    """A round that represents pool enter has finished"""

    round_id = "finished_enter_pool_hash"


class ExitPoolTransactionHashRound(TransactionHashBaseRound):
    """A round in which agents compute the transaction hash for pool exit"""

    round_id = "exit_pool_tx_hash"


class FinishedExitPoolTransactionHashRound(DegenerateRound):
    """A round that represents pool exit has finished"""

    round_id = "finished_exit_pool_hash"


class SwapBackTransactionHashRound(TransactionHashBaseRound):
    """A round in which agents compute the transaction hash for a swap back"""

    round_id = "swap_back_tx_hash"


class FinishedSwapBackTransactionHashRound(DegenerateRound):
    """A round that represents swap back has finished"""

    round_id = "finished_swap_back_hash"


class LiquidityRebalancingAbciApp(AbciApp[Event]):
    """LiquidityRebalancingAbciApp

    Initial round: StrategyEvaluationRound

    Initial states: {StrategyEvaluationRound}

    Transition states:
        0. StrategyEvaluationRound
            - done: 1.
            - done enter: 2.
            - done exit: 4.
            - done swap back: 6.
            - round timeout: 0.
            - no majority: 0.
        1. SleepRound
            - done: 0.
            - round timeout: 0.
            - no majority: 0.
        2. EnterPoolTransactionHashRound
            - done: 3.
            - round timeout: 0.
            - no majority: 0.
        3. FinishedEnterPoolTransactionHashRound
        4. ExitPoolTransactionHashRound
            - done: 5.
            - round timeout: 0.
            - no majority: 0.
        5. FinishedExitPoolTransactionHashRound
        6. SwapBackTransactionHashRound
            - done: 7.
            - round timeout: 0.
            - no majority: 0.
        7. FinishedSwapBackTransactionHashRound

    Final states: {FinishedEnterPoolTransactionHashRound, FinishedExitPoolTransactionHashRound, FinishedSwapBackTransactionHashRound}

    Timeouts:
        exit: 5.0
        round timeout: 30.0
    """

    initial_round_cls: Type[AbstractRound] = StrategyEvaluationRound
    transition_function: AbciAppTransitionFunction = {
        StrategyEvaluationRound: {
            Event.DONE: SleepRound,
            Event.DONE_ENTER: EnterPoolTransactionHashRound,
            Event.DONE_EXIT: ExitPoolTransactionHashRound,
            Event.DONE_SWAP_BACK: SwapBackTransactionHashRound,
            Event.ROUND_TIMEOUT: StrategyEvaluationRound,
            Event.NO_MAJORITY: StrategyEvaluationRound,
        },
        SleepRound: {
            Event.DONE: StrategyEvaluationRound,
            Event.ROUND_TIMEOUT: StrategyEvaluationRound,
            Event.NO_MAJORITY: StrategyEvaluationRound,
        },
        EnterPoolTransactionHashRound: {
            Event.DONE: FinishedEnterPoolTransactionHashRound,
            Event.ROUND_TIMEOUT: StrategyEvaluationRound,
            Event.NO_MAJORITY: StrategyEvaluationRound,
        },
        FinishedEnterPoolTransactionHashRound: {},
        ExitPoolTransactionHashRound: {
            Event.DONE: FinishedExitPoolTransactionHashRound,
            Event.ROUND_TIMEOUT: StrategyEvaluationRound,
            Event.NO_MAJORITY: StrategyEvaluationRound,
        },
        FinishedExitPoolTransactionHashRound: {},
        SwapBackTransactionHashRound: {
            Event.DONE: FinishedSwapBackTransactionHashRound,
            Event.ROUND_TIMEOUT: StrategyEvaluationRound,
            Event.NO_MAJORITY: StrategyEvaluationRound,
        },
        FinishedSwapBackTransactionHashRound: {},
    }
    final_states: Set[AppState] = {
        FinishedEnterPoolTransactionHashRound,
        FinishedExitPoolTransactionHashRound,
        FinishedSwapBackTransactionHashRound,
    }
    event_to_timeout: Dict[Event, float] = {
        Event.EXIT: 5.0,
        Event.ROUND_TIMEOUT: 30.0,
    }
