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

"""This module contains the data classes for the liquidity provision ABCI application."""
import json
from abc import ABC
from enum import Enum
from types import MappingProxyType
from typing import Dict, Mapping, Optional, Tuple, Type, cast

from packages.valory.skills.abstract_round_abci.base import (
    AbciApp,
    AbciAppTransitionFunction,
    AbstractRound,
    BasePeriodState,
    CollectDifferentUntilThresholdRound,
    CollectSameUntilThresholdRound,
    OnlyKeeperSendsRound,
    VotingRound,
)
from packages.valory.skills.liquidity_provision.payloads import (
    StrategyEvaluationPayload,
    StrategyType,
)
from packages.valory.skills.oracle_deployment_abci.rounds import (
    RandomnessOracleRound as RandomnessRound,
)
from packages.valory.skills.price_estimation_abci.payloads import TransactionHashPayload
from packages.valory.skills.transaction_settlement_abci.payloads import (
    FinalizationTxPayload,
    SignaturePayload,
    TransactionType,
    ValidatePayload,
)
from packages.valory.skills.transaction_settlement_abci.rounds import (
    ResetAndPauseRound,
    ResetRound,
)


class Event(Enum):
    """Event enumeration for the liquidity provision demo."""

    DONE = "done"
    EXIT = "exit"
    ROUND_TIMEOUT = "round_timeout"
    NO_MAJORITY = "no_majority"
    RESET_TIMEOUT = "reset_timeout"
    WAIT = "wait"


class PeriodState(
    BasePeriodState
):  # pylint: disable=too-many-instance-attributes,too-many-statements,too-many-public-methods
    """
    Class to represent a period state.

    This state is replicated by the tendermint application.
    """

    @property
    def most_voted_strategy(self) -> dict:
        """Get the most_voted_strategy."""
        return cast(dict, self.db.get_strict("most_voted_strategy"))

    @property
    def participant_to_votes(self) -> Mapping[str, ValidatePayload]:
        """Get the participant_to_votes."""
        return cast(
            Mapping[str, ValidatePayload], self.db.get_strict("participant_to_votes")
        )

    @property
    def participant_to_strategy(self) -> Mapping[str, StrategyEvaluationPayload]:
        """Get the participant_to_votes."""
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
    def most_voted_tx_data(self) -> str:
        """Get the most_voted_enter_pool_tx_data."""
        return cast(str, self.db.get_strict("most_voted_tx_data"))

    @property
    def final_tx_hash(self) -> str:
        """Get the final_enter_pool_tx_hash."""
        return cast(str, self.db.get_strict("final_tx_hash"))


class LiquidityProvisionAbstractRound(AbstractRound[Event, TransactionType], ABC):
    """Abstract round for the liquidity provision skill."""

    @property
    def period_state(self) -> PeriodState:
        """Return the period state."""
        return cast(PeriodState, self._state)

    def _return_no_majority_event(self) -> Tuple[PeriodState, Event]:
        """
        Trigger the NO_MAJORITY event.

        :return: a new period state and a NO_MAJORITY event
        """
        return self.period_state, Event.NO_MAJORITY


class TransactionHashBaseRound(
    CollectSameUntilThresholdRound, LiquidityProvisionAbstractRound
):
    """A base class for rounds in which agents compute the transaction hash"""

    round_id = "tx_hash"
    allowed_tx_type = TransactionHashPayload.transaction_type
    payload_attribute = "tx_hash"

    def end_block(self) -> Optional[Tuple[BasePeriodState, Event]]:
        """Process the end of the block."""
        if self.threshold_reached:
            dict_ = json.loads(self.most_voted_payload)
            state = self.period_state.update(
                participant_to_tx_hash=MappingProxyType(self.collection),
                most_voted_tx_hash=dict_["tx_hash"],
                most_voted_tx_data=dict_["tx_data"],
            )
            return state, Event.DONE
        if not self.is_majority_possible(
            self.collection, self.period_state.nb_participants
        ):
            return self._return_no_majority_event()
        return None


class TransactionSignatureBaseRound(
    CollectDifferentUntilThresholdRound, LiquidityProvisionAbstractRound
):
    """A base class for rounds in which agents sign the transaction"""

    round_id = "abstract_signature"
    allowed_tx_type = SignaturePayload.transaction_type
    payload_attribute = "signature"

    def end_block(self) -> Optional[Tuple[BasePeriodState, Event]]:
        """Process the end of the block."""
        if self.collection_threshold_reached:
            state = self.period_state.update(
                participant_to_signature=MappingProxyType(self.collection),
            )
            return state, Event.DONE
        if not self.is_majority_possible(
            self.collection, self.period_state.nb_participants
        ):
            return self._return_no_majority_event()
        return None


class TransactionSendBaseRound(OnlyKeeperSendsRound, LiquidityProvisionAbstractRound):
    """A base class for rounds in which agents send the transaction"""

    round_id = "finalization"
    allowed_tx_type = FinalizationTxPayload.transaction_type
    payload_attribute = "tx_hash"

    def end_block(self) -> Optional[Tuple[BasePeriodState, Event]]:
        """Process the end of the block."""
        # if reached participant threshold, set the result
        if self.has_keeper_sent_payload:
            state = self.period_state.update(final_tx_hash=self.keeper_payload)
            return state, Event.DONE
        return None


class TransactionValidationBaseRound(VotingRound, LiquidityProvisionAbstractRound):
    """A base class for rounds in which agents validate the transaction"""

    round_id = "transaction_valid_round"
    allowed_tx_type = ValidatePayload.transaction_type
    exit_event: Event = Event.EXIT
    payload_attribute = "vote"

    def end_block(self) -> Optional[Tuple[BasePeriodState, Event]]:
        """Process the end of the block."""
        # if reached participant threshold, set the result
        if self.positive_vote_threshold_reached:
            state = self.period_state.update(
                participant_to_votes=MappingProxyType(self.collection)
            )
            return state, Event.DONE
        if self.negative_vote_threshold_reached:
            state = self.period_state.update()
            return state, self.exit_event
        if not self.is_majority_possible(
            self.collection, self.period_state.nb_participants
        ):
            return self._return_no_majority_event()
        return None


class StrategyEvaluationRound(
    CollectSameUntilThresholdRound, LiquidityProvisionAbstractRound
):
    """A round in which agents evaluate the financial strategy"""

    round_id = "strategy_evaluation"
    allowed_tx_type = StrategyEvaluationPayload.transaction_type
    payload_attribute = "strategy"

    def end_block(self) -> Optional[Tuple[BasePeriodState, Event]]:
        """Process the end of the block."""
        if self.threshold_reached:
            state = self.period_state.update(
                participant_to_strategy=MappingProxyType(self.collection),
                most_voted_strategy=self.most_voted_payload,
            )
            event = (
                Event.DONE
                if state.most_voted_strategy["action"] == StrategyType.GO  # type: ignore
                else Event.RESET_TIMEOUT
            )
            return state, event
        if not self.is_majority_possible(
            self.collection, self.period_state.nb_participants
        ):
            return self._return_no_majority_event()
        return None


class EnterPoolTransactionHashRound(TransactionHashBaseRound):
    """A round in which agents compute the transaction hash for pool entry"""

    round_id = "enter_pool_tx_hash"


class EnterPoolTransactionSignatureRound(TransactionSignatureBaseRound):
    """A round in which agents sign the transaction for pool entry"""

    round_id = "enter_pool_tx_signature"


class EnterPoolTransactionSendRound(TransactionSendBaseRound):
    """A round in which agents send the transaction for pool entry"""

    round_id = "enter_pool_tx_send"


class EnterPoolTransactionValidationRound(TransactionValidationBaseRound):
    """A round in which agents validate the transaction for pool entry"""

    round_id = "enter_pool_tx_validation"


class EnterPoolRandomnessRound(RandomnessRound):
    """A round for generating randomness"""

    round_id = "enter_pool_randomness"


class EnterPoolSelectKeeperRound(
    CollectSameUntilThresholdRound, LiquidityProvisionAbstractRound
):
    """A round in which a keeper is selected"""

    round_id = "enter_pool_select_keeper"


class ExitPoolTransactionHashRound(TransactionHashBaseRound):
    """A round in which agents compute the transaction hash for pool exit"""

    round_id = "exit_pool_tx_hash"


class ExitPoolTransactionSignatureRound(TransactionSignatureBaseRound):
    """A round in which agents sign the transaction for pool exit"""

    round_id = "exit_pool_tx_signature"


class ExitPoolTransactionSendRound(TransactionSendBaseRound):
    """A round in which agents send the transaction for pool exit"""

    round_id = "exit_pool_tx_send"


class ExitPoolTransactionValidationRound(TransactionValidationBaseRound):
    """A round in which agents validate the transaction for pool exit"""

    round_id = "exit_pool_tx_validation"


class ExitPoolRandomnessRound(RandomnessRound):
    """A round for generating randomness"""

    round_id = "exit_pool_randomness"


class ExitPoolSelectKeeperRound(
    CollectSameUntilThresholdRound, LiquidityProvisionAbstractRound
):
    """A round in a which keeper is selected"""

    round_id = "exit_pool_select_keeper"


class SwapBackTransactionHashRound(TransactionHashBaseRound):
    """A round in which agents compute the transaction hash for a swap back"""

    round_id = "swap_back_tx_hash"


class SwapBackTransactionSignatureRound(TransactionSignatureBaseRound):
    """A round in which agents sign the transaction for a swap back"""

    round_id = "swap_back_tx_signature"


class SwapBackTransactionSendRound(TransactionSendBaseRound):
    """A round in which agents send the transaction for a swap back"""

    round_id = "swap_back_tx_send"


class SwapBackTransactionValidationRound(TransactionValidationBaseRound):
    """A round in which agents validate the transaction for a swap back"""

    round_id = "swap_back_tx_validation"


class SwapBackRandomnessRound(RandomnessRound):
    """A round for generating randomness"""

    round_id = "swap_back_randomness"


class SwapBackSelectKeeperRound(
    CollectSameUntilThresholdRound, LiquidityProvisionAbstractRound
):
    """A round in a which keeper is selected"""

    round_id = "swap_back_select_keeper"


class LiquidityProvisionAbciApp(AbciApp[Event]):
    """LiquidityProvisionAbciApp

    Initial round: ResetRound

    Initial states: {ResetRound}

    Transition states:
    0. ResetRound
        - done: 1.
    1. StrategyEvaluationRound
        - done: 2.
        - wait: 20.
        - round timeout: 0.
        - no majority: 0.
    2. EnterPoolTransactionHashRound
        - done: 3.
        - round timeout: 0.
        - no majority: 0.
    3. EnterPoolTransactionSignatureRound
        - done: 4.
        - round timeout: 0.
        - no majority: 0.
    4. EnterPoolTransactionSendRound
        - done: 5.
        - round timeout: 0.
        - no majority: 0.
    5. EnterPoolTransactionValidationRound
        - done: 20.
        - round timeout: 6.
        - no majority: 0.
    6. EnterPoolRandomnessRound
        - done: 7.
        - round timeout: 0.
        - no majority: 0.
    7. EnterPoolSelectKeeperRound
        - done: 8.
        - round timeout: 0.
        - no majority: 0.
    8. ExitPoolTransactionHashRound
        - done: 9.
        - round timeout: 0.
        - no majority: 0.
    9. ExitPoolTransactionSignatureRound
        - done: 10.
        - round timeout: 0.
        - no majority: 0.
    10. ExitPoolTransactionSendRound
        - done: 11.
        - round timeout: 0.
        - no majority: 0.
    11. ExitPoolTransactionValidationRound
        - done: 14.
        - round timeout: 12.
        - no majority: 0.
    12. ExitPoolRandomnessRound
        - done: 13.
        - round timeout: 0.
        - no majority: 0.
    13. ExitPoolSelectKeeperRound
        - done: 8.
        - round timeout: 0.
        - no majority: 0.
    14. SwapBackTransactionHashRound
        - done: 15.
        - round timeout: 0.
        - no majority: 0.
    15. SwapBackTransactionSignatureRound
        - done: 16.
        - round timeout: 0.
        - no majority: 0.
    16. SwapBackTransactionSendRound
        - done: 17.
        - round timeout: 0.
        - no majority: 0.
    17. SwapBackTransactionValidationRound
        - done: 20.
        - round timeout: 18.
        - no majority: 0.
    18. SwapBackRandomnessRound
        - done: 19.
        - round timeout: 0.
        - no majority: 0.
    19. SwapBackSelectKeeperRound
        - done: 14.
        - round timeout: 0.
        - no majority: 0.
    20. ResetAndPauseRound
        - done: 1.
        - reset timeout: 0.
        - no majority: 0.

    Final states: {}

    Timeouts:
        exit: 5.0
        round timeout: 30.0
    """

    initial_round_cls: Type[AbstractRound] = ResetRound
    transition_function: AbciAppTransitionFunction = {
        ResetRound: {
            Event.DONE: StrategyEvaluationRound,
        },
        StrategyEvaluationRound: {
            Event.DONE: EnterPoolTransactionHashRound,
            Event.WAIT: ResetAndPauseRound,
            Event.ROUND_TIMEOUT: ResetRound,
            Event.NO_MAJORITY: ResetRound,
        },
        EnterPoolTransactionHashRound: {
            Event.DONE: EnterPoolTransactionSignatureRound,
            Event.ROUND_TIMEOUT: ResetRound,
            Event.NO_MAJORITY: ResetRound,
        },
        EnterPoolTransactionSignatureRound: {
            Event.DONE: EnterPoolTransactionSendRound,
            Event.ROUND_TIMEOUT: ResetRound,
            Event.NO_MAJORITY: ResetRound,
        },
        EnterPoolTransactionSendRound: {
            Event.DONE: EnterPoolTransactionValidationRound,
            Event.ROUND_TIMEOUT: ResetRound,
            Event.NO_MAJORITY: ResetRound,
        },
        EnterPoolTransactionValidationRound: {
            Event.DONE: ResetAndPauseRound,
            Event.ROUND_TIMEOUT: ResetRound,
            Event.NO_MAJORITY: ResetRound,
            Event.ROUND_TIMEOUT: EnterPoolRandomnessRound,
        },
        EnterPoolRandomnessRound: {
            Event.DONE: EnterPoolSelectKeeperRound,
            Event.ROUND_TIMEOUT: ResetRound,
            Event.NO_MAJORITY: ResetRound,
        },
        EnterPoolSelectKeeperRound: {
            Event.DONE: ExitPoolTransactionHashRound,
            Event.ROUND_TIMEOUT: ResetRound,
            Event.NO_MAJORITY: ResetRound,
        },
        ExitPoolTransactionHashRound: {
            Event.DONE: ExitPoolTransactionSignatureRound,
            Event.ROUND_TIMEOUT: ResetRound,
            Event.NO_MAJORITY: ResetRound,
        },
        ExitPoolTransactionSignatureRound: {
            Event.DONE: ExitPoolTransactionSendRound,
            Event.ROUND_TIMEOUT: ResetRound,
            Event.NO_MAJORITY: ResetRound,
        },
        ExitPoolTransactionSendRound: {
            Event.DONE: ExitPoolTransactionValidationRound,
            Event.ROUND_TIMEOUT: ResetRound,
            Event.NO_MAJORITY: ResetRound,
        },
        ExitPoolTransactionValidationRound: {
            Event.DONE: SwapBackTransactionHashRound,
            Event.ROUND_TIMEOUT: ResetRound,
            Event.NO_MAJORITY: ResetRound,
            Event.ROUND_TIMEOUT: ExitPoolRandomnessRound,
        },
        ExitPoolRandomnessRound: {
            Event.DONE: ExitPoolSelectKeeperRound,
            Event.ROUND_TIMEOUT: ResetRound,
            Event.NO_MAJORITY: ResetRound,
        },
        ExitPoolSelectKeeperRound: {
            Event.DONE: ExitPoolTransactionHashRound,
            Event.ROUND_TIMEOUT: ResetRound,
            Event.NO_MAJORITY: ResetRound,
        },
        SwapBackTransactionHashRound: {
            Event.DONE: SwapBackTransactionSignatureRound,
            Event.ROUND_TIMEOUT: ResetRound,
            Event.NO_MAJORITY: ResetRound,
        },
        SwapBackTransactionSignatureRound: {
            Event.DONE: SwapBackTransactionSendRound,
            Event.ROUND_TIMEOUT: ResetRound,
            Event.NO_MAJORITY: ResetRound,
        },
        SwapBackTransactionSendRound: {
            Event.DONE: SwapBackTransactionValidationRound,
            Event.ROUND_TIMEOUT: ResetRound,
            Event.NO_MAJORITY: ResetRound,
        },
        SwapBackTransactionValidationRound: {
            Event.DONE: ResetAndPauseRound,
            Event.ROUND_TIMEOUT: ResetRound,
            Event.NO_MAJORITY: ResetRound,
            Event.ROUND_TIMEOUT: SwapBackRandomnessRound,
        },
        SwapBackRandomnessRound: {
            Event.DONE: SwapBackSelectKeeperRound,
            Event.ROUND_TIMEOUT: ResetRound,
            Event.NO_MAJORITY: ResetRound,
        },
        SwapBackSelectKeeperRound: {
            Event.DONE: SwapBackTransactionHashRound,
            Event.ROUND_TIMEOUT: ResetRound,
            Event.NO_MAJORITY: ResetRound,
        },
        ResetAndPauseRound: {
            Event.DONE: StrategyEvaluationRound,
            Event.RESET_TIMEOUT: ResetRound,
            Event.NO_MAJORITY: ResetRound,
        },
    }
    event_to_timeout: Dict[Event, float] = {
        Event.EXIT: 5.0,
        Event.ROUND_TIMEOUT: 30.0,
    }
