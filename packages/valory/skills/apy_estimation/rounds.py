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

"""This module contains the rounds for the APY estimation ABCI application."""
from abc import ABC
from enum import Enum
from typing import AbstractSet, Any, Dict, Optional, Tuple, Type, cast

from aea.exceptions import enforce

from packages.valory.skills.abstract_round_abci.base import (
    AbciApp,
    AbciAppTransitionFunction,
    AbstractRound,
    BasePeriodState,
    CollectDifferentUntilAllRound,
    CollectSameUntilThresholdRound,
    TransactionType,
)
from packages.valory.skills.apy_estimation.payloads import (
    EstimatePayload,
    FetchingPayload,
    OptimizationPayload,
    PreprocessPayload,
    RandomnessPayload,
    RegistrationPayload,
    ResetPayload,
)
from packages.valory.skills.apy_estimation.payloads import (
    TestingPayload as _TestingPayload,
)
from packages.valory.skills.apy_estimation.payloads import (
    TrainingPayload,
    TransformationPayload,
)
from packages.valory.skills.apy_estimation.tools.general import filter_out_numbers


N_ESTIMATIONS_BEFORE_RETRAIN = 60


class Event(Enum):
    """Event enumeration for the APY estimation demo."""

    DONE = "done"
    ROUND_TIMEOUT = "round_timeout"
    NO_MAJORITY = "no_majority"
    RESET_TIMEOUT = "reset_timeout"
    FULLY_TRAINED = "fully_trained"
    ESTIMATION_CYCLE = "estimation_cycle"
    RANDOMNESS_INVALID = "randomness_invalid"


class PeriodState(BasePeriodState):
    """Class to represent a period state. This state is replicated by the tendermint application."""

    def __init__(  # pylint: disable=too-many-arguments,too-many-locals
        self,
        participants: Optional[AbstractSet[str]] = None,
        period_count: Optional[int] = None,
        period_setup_params: Optional[Dict] = None,
        most_voted_randomness: Optional[int] = None,
        most_voted_estimate: Optional[float] = None,
        full_training: bool = False,
        pair_name: Optional[str] = None,
        n_estimations: int = 0,
    ) -> None:
        """Initialize the state."""
        super().__init__(participants, period_count, period_setup_params)
        self._most_voted_randomness = most_voted_randomness
        self._most_voted_estimate = most_voted_estimate
        self._full_training = full_training
        self._pair_name = pair_name
        self._n_estimations = n_estimations

    @property
    def most_voted_randomness(self) -> int:
        """Get the most_voted_randomness."""
        enforce(
            self._most_voted_randomness is not None,
            "'most_voted_randomness' field is None",
        )
        return cast(int, self._most_voted_randomness)

    @property
    def most_voted_estimate(self) -> Optional[float]:
        """Get the most_voted_estimate."""
        enforce(
            self._most_voted_estimate is not None,
            "'most_voted_estimate' field is None",
        )
        return self._most_voted_estimate

    @property
    def is_most_voted_estimate_set(self) -> bool:
        """Check if most_voted_estimate is set."""
        return self._most_voted_estimate is not None

    @property
    def full_training(self) -> bool:
        """Get the full_training flag."""
        return self._full_training

    @property
    def pair_name(self) -> str:
        """Get the pair_name."""
        enforce(
            self._pair_name is not None,
            "'pair_name' field is None",
        )
        return cast(str, self._pair_name)

    @property
    def n_estimations(self) -> int:
        """Get the n_estimations."""
        enforce(
            self._n_estimations is not None,
            "'n_estimations' field is None",
        )
        return cast(int, self._n_estimations)


class APYEstimationAbstractRound(AbstractRound[Event, TransactionType], ABC):
    """Abstract round for the APY estimation skill."""

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


class RegistrationRound(CollectDifferentUntilAllRound, APYEstimationAbstractRound):
    """
    This class represents the registration round.

    Input: None
    Output: a period state with the set of participants.

    It schedules the SelectKeeperARound.
    """

    round_id = "registration"
    allowed_tx_type = RegistrationPayload.transaction_type
    payload_attribute = "sender"

    def end_block(self) -> Optional[Tuple[BasePeriodState, Event]]:
        """Process the end of the block."""
        state_event = None

        if self.collection_threshold_reached:
            updated_state = PeriodState(
                participants=self.collection,
                period_count=self.period_state.period_count,
            )
            state_event = updated_state, Event.DONE

        return state_event


class CollectHistoryRound(CollectSameUntilThresholdRound, APYEstimationAbstractRound):
    """
    This class represents the 'collect-history' round.

    Input: a period state with the prior round data.
    Output: a new period state with the prior round data and the votes for the historical data.

    It schedules the TransformRound.
    """

    round_id = "collect_history"
    allowed_tx_type = FetchingPayload.transaction_type
    payload_attribute = "history"

    def end_block(self) -> Optional[Tuple[BasePeriodState, Event]]:
        """Process the end of the block."""
        state_event = None

        if self.threshold_reached:
            state_event = self.period_state, Event.DONE

        elif not self.is_majority_possible(
            self.collection, self.period_state.nb_participants
        ):
            state_event = self._return_no_majority_event()

        return state_event


class TransformRound(CollectSameUntilThresholdRound, APYEstimationAbstractRound):
    """
    This class represents the 'Transform' round.

    Input: a period state with the prior round data.
    Output: a new period state with the prior round data and the votes for the transformed data.

    It schedules the PreprocessRound.
    """

    round_id = "transform"
    allowed_tx_type = TransformationPayload.transaction_type
    payload_attribute = "transformation"

    def end_block(self) -> Optional[Tuple[BasePeriodState, Event]]:
        """Process the end of the block."""
        state_event = None

        if self.threshold_reached:
            state_event = self.period_state, Event.DONE

        elif not self.is_majority_possible(
            self.collection, self.period_state.nb_participants
        ):
            state_event = self._return_no_majority_event()

        return state_event


class PreprocessRound(CollectSameUntilThresholdRound, APYEstimationAbstractRound):
    """
    This class represents the 'Preprocess' round.

    Input: a period state with the prior round data.
    Output: a new period state with the prior round data and the votes for the preprocessed data.

    It schedules the RandomnessRound.
    """

    round_id = "preprocess"
    allowed_tx_type = PreprocessPayload.transaction_type
    payload_attribute = "train_test_hash"

    def end_block(self) -> Optional[Tuple[BasePeriodState, Event]]:
        """Process the end of the block."""
        state_event = None

        if self.threshold_reached:
            state_event = self.period_state, Event.DONE

        elif not self.is_majority_possible(
            self.collection, self.period_state.nb_participants
        ):
            state_event = self._return_no_majority_event()

        return state_event


class RandomnessRound(CollectSameUntilThresholdRound, APYEstimationAbstractRound):
    """
    This class represents the randomness round.

    Input: a set of participants (addresses).
    Output: a set of participants (addresses) and randomness.

    It schedules the OptimizeRound.
    """

    round_id = "randomness"
    allowed_tx_type = RandomnessPayload.transaction_type
    payload_attribute = "randomness"

    def end_block(self) -> Optional[Tuple[BasePeriodState, Event]]:
        """Process the end of the block."""
        state_event = None

        if self.threshold_reached:
            filtered_randomness = filter_out_numbers(self.most_voted_payload)

            if filtered_randomness is None:
                state_event = self.period_state, Event.RANDOMNESS_INVALID

            else:
                updated_state = cast(
                    PeriodState,
                    self.period_state.update(most_voted_randomness=filtered_randomness),
                )
                state_event = updated_state, Event.DONE

        elif not self.is_majority_possible(
            self.collection, self.period_state.nb_participants
        ):
            state_event = self._return_no_majority_event()

        return state_event


class OptimizeRound(CollectSameUntilThresholdRound, APYEstimationAbstractRound):
    """
    This class represents the 'Optimize' round.

    Input: a period state with the prior round data.
    Output: a new period state with the prior round data and the votes for the hyperparameters.

    It schedules the TrainRound.
    """

    round_id = "optimize"
    allowed_tx_type = OptimizationPayload.transaction_type
    payload_attribute = "best_params"

    def end_block(self) -> Optional[Tuple[BasePeriodState, Event]]:
        """Process the end of the block."""
        state_event = None

        if self.threshold_reached:
            state_event = self.period_state, Event.DONE

        elif not self.is_majority_possible(
            self.collection, self.period_state.nb_participants
        ):
            state_event = self._return_no_majority_event()

        return state_event


class TrainRound(CollectSameUntilThresholdRound, APYEstimationAbstractRound):
    """
    This class represents the 'Train' round.

    Input: a period state with the prior round data.
    Output: a new period state with the prior round data and the votes for the model.

    It schedules the TestRound.
    """

    round_id = "train"
    allowed_tx_type = TrainingPayload.transaction_type
    payload_attribute = "model"

    def end_block(self) -> Optional[Tuple[BasePeriodState, Event]]:
        """Process the end of the block."""
        state_event = None

        if self.threshold_reached:
            if self.period_state.full_training:
                event = Event.FULLY_TRAINED
            else:
                event = Event.DONE

            state_event = self.period_state, event

        elif not self.is_majority_possible(
            self.collection, self.period_state.nb_participants
        ):
            state_event = self._return_no_majority_event()

        return state_event


class TestRound(CollectSameUntilThresholdRound, APYEstimationAbstractRound):
    """
    This class represents the 'Test' round.

    Input: a period state with the prior round data.
    Output: a new period state with the prior round data and the votes for the results.

    It schedules the EstimateConsensusRound.
    """

    round_id = "test"
    allowed_tx_type = _TestingPayload.transaction_type
    payload_attribute = "report_hash"

    def end_block(self) -> Optional[Tuple[BasePeriodState, Event]]:
        """Process the end of the block."""
        state_event = None

        if self.threshold_reached:
            updated_state = self.period_state.update(
                full_training=True,
            )
            state_event = updated_state, Event.DONE

        elif not self.is_majority_possible(
            self.collection, self.period_state.nb_participants
        ):
            state_event = self._return_no_majority_event()

        return state_event


class EstimateRound(CollectSameUntilThresholdRound, APYEstimationAbstractRound):
    """
    This class represents the 'estimate' round.

    Input: a period state with the prior round data.
    Output: a new period state with the prior round data and the votes for each estimate.

    It schedules the `ResetRound` or the `CycleResetRound`.
    """

    round_id = "estimate"
    allowed_tx_type = EstimatePayload.transaction_type
    payload_attribute = "estimation"

    def end_block(self) -> Optional[Tuple[BasePeriodState, Event]]:
        """Process the end of the block."""
        state_event = None

        if self.threshold_reached:
            updated_state = self.period_state.update(
                n_estimations=cast(PeriodState, self.period_state).n_estimations + 1
            )

            if (
                cast(PeriodState, updated_state).n_estimations
                % N_ESTIMATIONS_BEFORE_RETRAIN
                == 0
            ):
                event = Event.DONE
            else:
                event = Event.ESTIMATION_CYCLE

            state_event = updated_state, event

        elif not self.is_majority_possible(
            self.collection, self.period_state.nb_participants
        ):
            state_event = self._return_no_majority_event()

        return state_event


class ResetRound(CollectSameUntilThresholdRound, APYEstimationAbstractRound):
    """This class represents the base reset round."""

    round_id = "reset"
    allowed_tx_type = ResetPayload.transaction_type
    payload_attribute = "period_count"

    def end_block(self) -> Optional[Tuple[BasePeriodState, Event]]:
        """Process the end of the block."""
        state_event = None

        if self.threshold_reached:
            updated_state = self.period_state.update(
                period_count=self.most_voted_payload,
                period_setup_params=None,
                most_voted_estimate=None,
            )

            if self.round_id == "reset":
                updated_state = updated_state.update(
                    full_training=False,
                    pair_name=None,
                )

            state_event = updated_state, Event.DONE

        elif not self.is_majority_possible(
            self.collection, self.period_state.nb_participants
        ):
            state_event = self._return_no_majority_event()

        return state_event


class CycleResetRound(ResetRound):
    """This class represents the 'consensus-reached' round (the final round)."""

    round_id = "cycle_reset"


class APYEstimationAbciApp(AbciApp[Event]):  # pylint: disable=too-few-public-methods
    """APY estimation ABCI application."""

    initial_round_cls: Type[AbstractRound] = RegistrationRound
    transition_function: AbciAppTransitionFunction = {
        RegistrationRound: {
            Event.DONE: CollectHistoryRound,
        },
        CollectHistoryRound: {
            Event.DONE: TransformRound,
            Event.NO_MAJORITY: ResetRound,  # if there is no majority we reset the period
            Event.ROUND_TIMEOUT: ResetRound,  # if the round times out we reset the period
        },
        TransformRound: {
            Event.DONE: PreprocessRound,
            Event.NO_MAJORITY: ResetRound,  # if there is no majority we reset the period
            Event.ROUND_TIMEOUT: ResetRound,  # if the round times out we reset the period
        },
        PreprocessRound: {
            Event.DONE: RandomnessRound,
            Event.NO_MAJORITY: ResetRound,  # if there is no majority we reset the period
            Event.ROUND_TIMEOUT: ResetRound,  # if the round times out we reset the period
        },
        RandomnessRound: {
            Event.DONE: OptimizeRound,
            Event.RANDOMNESS_INVALID: RandomnessRound,
            Event.NO_MAJORITY: RandomnessRound,  # if there is no majority we reset the period
            Event.ROUND_TIMEOUT: ResetRound,  # if the round times out we reset the period
        },
        OptimizeRound: {
            Event.DONE: TrainRound,
            Event.NO_MAJORITY: ResetRound,  # if there is no majority we reset the period
            Event.ROUND_TIMEOUT: ResetRound,  # if the round times out we reset the period
        },
        TrainRound: {
            Event.FULLY_TRAINED: EstimateRound,
            Event.DONE: TestRound,
            Event.NO_MAJORITY: ResetRound,  # if there is no majority we reset the period
            Event.ROUND_TIMEOUT: ResetRound,  # if the round times out we reset the period
        },
        TestRound: {
            Event.DONE: TrainRound,
            Event.NO_MAJORITY: ResetRound,  # if there is no majority we reset the period
            Event.ROUND_TIMEOUT: ResetRound,  # if the round times out we reset the period
        },
        EstimateRound: {
            Event.DONE: ResetRound,
            Event.ESTIMATION_CYCLE: CycleResetRound,
            Event.ROUND_TIMEOUT: ResetRound,  # if the round times out we reset the period
            Event.NO_MAJORITY: ResetRound,  # if there is no majority we reset the period
        },
        ResetRound: {
            Event.DONE: CollectHistoryRound,
            Event.RESET_TIMEOUT: RegistrationRound,  # if the round times out we try to assemble a new group of agents
            Event.NO_MAJORITY: RegistrationRound,  # if we cannot agree we try to assemble a new group of agents
        },
        CycleResetRound: {
            Event.DONE: EstimateRound,
            Event.RESET_TIMEOUT: ResetRound,  # if the round times out we try to assemble a new group of agents
            Event.NO_MAJORITY: ResetRound,  # if we cannot agree we try to assemble a new group of agents
        },
    }
    event_to_timeout: Dict[Event, float] = {
        Event.ROUND_TIMEOUT: 30.0,
        Event.RESET_TIMEOUT: 30.0,
    }
