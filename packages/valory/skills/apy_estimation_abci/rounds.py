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

"""This module contains the rounds for the APY estimation ABCI application."""
from abc import ABC
from enum import Enum
from typing import Dict, Optional, Tuple, Type, cast

from packages.valory.skills.abstract_round_abci.base import (
    AbciApp,
    AbciAppTransitionFunction,
    AbstractRound,
    BasePeriodState,
    CollectDifferentUntilAllRound,
    CollectSameUntilThresholdRound,
    TransactionType,
)
from packages.valory.skills.apy_estimation_abci.payloads import (
    EstimatePayload,
    FetchingPayload,
    OptimizationPayload,
    PreprocessPayload,
    RandomnessPayload,
    RegistrationPayload,
    ResetPayload,
)
from packages.valory.skills.apy_estimation_abci.payloads import (
    TestingPayload as _TestingPayload,
)
from packages.valory.skills.apy_estimation_abci.payloads import (
    TrainingPayload,
    TransformationPayload,
)
from packages.valory.skills.apy_estimation_abci.tools.general import filter_out_numbers


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
    """Class to represent a period state.

    This state is replicated by the tendermint application.
    """

    @property
    def history_hash(self) -> str:
        """Get the most voted history hash."""
        return cast(str, self.db.get_strict("most_voted_history"))

    @property
    def transformed_history_hash(self) -> str:
        """Get the most voted transformed history hash."""
        return cast(str, self.db.get_strict("most_voted_transform"))

    @property
    def train_hash(self) -> str:
        """Get the most voted train hash."""
        split = cast(str, self.db.get_strict("most_voted_split"))
        return split[0 : len(split) // 2]

    @property
    def test_hash(self) -> str:
        """Get the most voted test hash."""
        split = cast(str, self.db.get_strict("most_voted_split"))
        return split[len(split) // 2 :]

    @property
    def params_hash(self) -> str:
        """Get the most_voted_params."""
        return cast(str, self.db.get_strict("most_voted_params"))

    @property
    def model_hash(self) -> str:
        """Get the most_voted_model."""
        return cast(str, self.db.get_strict("most_voted_model"))

    @property
    def most_voted_estimate(self) -> float:
        """Get the most_voted_estimate."""
        return cast(float, self.db.get_strict("most_voted_estimate"))

    @property
    def is_most_voted_estimate_set(self) -> bool:
        """Check if most_voted_estimate is set."""
        return self.db.get("most_voted_estimate", None) is not None

    @property
    def full_training(self) -> bool:
        """Get the full_training flag."""
        return cast(bool, self.db.get_strict("full_training"))

    @property
    def pair_name(self) -> str:
        """Get the pair_name."""
        return cast(str, self.db.get_strict("pair_name"))

    @property
    def n_estimations(self) -> int:
        """Get the n_estimations."""
        return cast(int, self.db.get_strict("n_estimations"))


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


class RegistrationRound(CollectDifferentUntilAllRound):
    """A round in which the agents get registered"""

    round_id = "registration"
    allowed_tx_type = RegistrationPayload.transaction_type
    payload_attribute = "sender"

    def end_block(self) -> Optional[Tuple[BasePeriodState, Event]]:
        """Process the end of the block."""
        if self.collection_threshold_reached:
            updated_state = self.period_state.update(
                participants=self.collection,
                period_state_class=PeriodState,
                full_training=False,
                n_estimations=0,
            )
            return updated_state, Event.DONE

        return None


class CollectHistoryRound(CollectSameUntilThresholdRound):
    """A round in which agents collect historical data"""

    round_id = "collect_history"
    allowed_tx_type = FetchingPayload.transaction_type
    payload_attribute = "history"
    period_state_class = PeriodState
    done_event = Event.DONE
    no_majority_event = Event.NO_MAJORITY
    collection_key = "participant_to_history"
    selection_key = "most_voted_history"


class TransformRound(CollectSameUntilThresholdRound):
    """A round in which agents transform data"""

    round_id = "transform"
    allowed_tx_type = TransformationPayload.transaction_type
    payload_attribute = "transformation"
    period_state_class = PeriodState
    done_event = Event.DONE
    no_majority_event = Event.NO_MAJORITY
    collection_key = "participant_to_transform"
    selection_key = "most_voted_transform"


class PreprocessRound(CollectSameUntilThresholdRound, APYEstimationAbstractRound):
    """A round in which the agents preprocess the data"""

    round_id = "preprocess"
    allowed_tx_type = PreprocessPayload.transaction_type
    payload_attribute = "train_test_hash"

    def end_block(self) -> Optional[Tuple[BasePeriodState, Event]]:
        """Process the end of the block."""
        if self.threshold_reached:
            updated_state = cast(
                PeriodState,
                self.period_state.update(
                    participant_to_preprocessing=self.collection,
                    most_voted_split=self.most_voted_payload,
                    pair_name=cast(
                        PreprocessPayload, list(self.collection.values())[0]
                    ).pair_name,
                ),
            )
            return updated_state, Event.DONE

        if not self.is_majority_possible(
            self.collection, self.period_state.nb_participants
        ):
            return self._return_no_majority_event()

        return None


class RandomnessRound(CollectSameUntilThresholdRound, APYEstimationAbstractRound):
    """A round in which a random number is retrieved

    This number is obtained from a distributed randomness beacon. The agents
    need to reach consensus on this number and subsequently use it to seed
    any random number generators.
    """

    round_id = "randomness"
    allowed_tx_type = RandomnessPayload.transaction_type
    payload_attribute = "randomness"

    def end_block(self) -> Optional[Tuple[BasePeriodState, Event]]:
        """Process the end of the block."""
        if self.threshold_reached:
            filtered_randomness = filter_out_numbers(self.most_voted_payload)

            if filtered_randomness is None:
                return self.period_state, Event.RANDOMNESS_INVALID

            updated_state = cast(
                PeriodState,
                self.period_state.update(
                    participants_to_randomness=self.collection,
                    most_voted_randomness=filtered_randomness,
                ),
            )
            return updated_state, Event.DONE

        if not self.is_majority_possible(
            self.collection, self.period_state.nb_participants
        ):
            return self._return_no_majority_event()

        return None


class OptimizeRound(CollectSameUntilThresholdRound):
    """A round in which agents select model hyperparameters"""

    round_id = "optimize"
    allowed_tx_type = OptimizationPayload.transaction_type
    payload_attribute = "best_params"
    period_state_class = PeriodState
    done_event = Event.DONE
    no_majority_event = Event.NO_MAJORITY
    collection_key = "participant_to_params"
    selection_key = "most_voted_params"


class TrainRound(CollectSameUntilThresholdRound, APYEstimationAbstractRound):
    """A round in which agents train a model"""

    round_id = "train"
    allowed_tx_type = TrainingPayload.transaction_type
    payload_attribute = "model"

    def end_block(self) -> Optional[Tuple[BasePeriodState, Event]]:
        """Process the end of the block."""
        if self.threshold_reached:
            if self.period_state.full_training:
                updated_state = self.period_state.update(
                    participants_to_training=self.collection,
                    full_training=True,
                    most_voted_model=self.most_voted_payload,
                )
                return updated_state, Event.FULLY_TRAINED

            updated_state = self.period_state.update(
                participants_to_training=self.collection,
                most_voted_model=self.most_voted_payload,
            )
            return updated_state, Event.DONE

        if not self.is_majority_possible(
            self.collection, self.period_state.nb_participants
        ):
            return self._return_no_majority_event()

        return None


class TestRound(CollectSameUntilThresholdRound):
    """A round in which agents test a model"""

    round_id = "test"
    allowed_tx_type = _TestingPayload.transaction_type
    payload_attribute = "report_hash"
    period_state_class = PeriodState
    done_event = Event.DONE
    no_majority_event = Event.NO_MAJORITY
    collection_key = "participant_to_full_training"
    selection_key = "full_training"


class EstimateRound(CollectSameUntilThresholdRound, APYEstimationAbstractRound):
    """A round in which agents perform model prediction"""

    round_id = "estimate"
    allowed_tx_type = EstimatePayload.transaction_type
    payload_attribute = "estimation"

    def end_block(self) -> Optional[Tuple[BasePeriodState, Event]]:
        """Process the end of the block."""
        if self.threshold_reached:
            updated_state = self.period_state.update(
                participants_to_estimate=self.collection,
                n_estimations=cast(PeriodState, self.period_state).n_estimations + 1,
                most_voted_estimate=self.most_voted_payload,
            )

            if (
                cast(PeriodState, updated_state).n_estimations
                % N_ESTIMATIONS_BEFORE_RETRAIN
                == 0
            ):
                return updated_state, Event.DONE

            return updated_state, Event.ESTIMATION_CYCLE

        if not self.is_majority_possible(
            self.collection, self.period_state.nb_participants
        ):
            return self._return_no_majority_event()

        return None


class ResetRound(CollectSameUntilThresholdRound, APYEstimationAbstractRound):
    """This class represents the base reset round."""

    round_id = "reset"
    allowed_tx_type = ResetPayload.transaction_type
    payload_attribute = "period_count"

    def end_block(self) -> Optional[Tuple[BasePeriodState, Event]]:
        """Process the end of the block."""
        if self.threshold_reached:
            kwargs = dict(
                period_count=self.most_voted_payload,
                participants=self.period_state.participants,
                full_training=False,
                n_estimations=self.period_state.n_estimations,
            )
            if self.round_id == "cycle_reset":
                kwargs["pair_name"] = self.period_state.pair_name
                kwargs["most_voted_model"] = self.period_state.model_hash
            updated_state = self.period_state.update(**kwargs)
            return updated_state, Event.DONE

        if not self.is_majority_possible(
            self.collection, self.period_state.nb_participants
        ):
            return self._return_no_majority_event()

        return None


class CycleResetRound(ResetRound):
    """This class represents the 'consensus-reached' round (the final round)."""

    round_id = "cycle_reset"


class APYEstimationAbciApp(AbciApp[Event]):  # pylint: disable=too-few-public-methods
    """APYEstimationAbciApp

    Initial round: RegistrationRound

    Initial states:

    Transition states:
    0. RegistrationRound
        - done: 1.
    1. CollectHistoryRound
        - done: 2.
        - no majority: 9.
        - round timeout: 9.
    2. TransformRound
        - done: 3.
        - no majority: 9.
        - round timeout: 9.
    3. PreprocessRound
        - done: 4.
        - no majority: 9.
        - round timeout: 9.
    4. RandomnessRound
        - done: 5.
        - randomness invalid: 4.
        - no majority: 4.
        - round timeout: 9.
    5. OptimizeRound
        - done: 6.
        - no majority: 9.
        - round timeout: 9.
    6. TrainRound
        - fully trained: 8.
        - done: 7.
        - no majority: 9.
        - round timeout: 9.
    7. TestRound
        - done: 6.
        - no majority: 9.
        - round timeout: 9.
    8. EstimateRound
        - done: 9.
        - estimation cycle: 10.
        - round timeout: 9.
        - no majority: 9.
    9. ResetRound
        - done: 1.
        - reset timeout: 0.
        - no majority: 0.
    10. CycleResetRound
        - done: 8.
        - reset timeout: 9.
        - no majority: 9.

    Final states:

    Timeouts:
        round timeout: 30.0
        reset timeout: 30.0
    """

    initial_round_cls: Type[AbstractRound] = RegistrationRound
    transition_function: AbciAppTransitionFunction = {
        RegistrationRound: {
            Event.DONE: CollectHistoryRound,
        },
        CollectHistoryRound: {
            Event.DONE: TransformRound,
            Event.NO_MAJORITY: ResetRound,
            Event.ROUND_TIMEOUT: ResetRound,
        },
        TransformRound: {
            Event.DONE: PreprocessRound,
            Event.NO_MAJORITY: ResetRound,
            Event.ROUND_TIMEOUT: ResetRound,
        },
        PreprocessRound: {
            Event.DONE: RandomnessRound,
            Event.NO_MAJORITY: ResetRound,
            Event.ROUND_TIMEOUT: ResetRound,
        },
        RandomnessRound: {
            Event.DONE: OptimizeRound,
            Event.RANDOMNESS_INVALID: RandomnessRound,
            Event.NO_MAJORITY: RandomnessRound,
            Event.ROUND_TIMEOUT: ResetRound,
        },
        OptimizeRound: {
            Event.DONE: TrainRound,
            Event.NO_MAJORITY: ResetRound,
            Event.ROUND_TIMEOUT: ResetRound,
        },
        TrainRound: {
            Event.FULLY_TRAINED: EstimateRound,
            Event.DONE: TestRound,
            Event.NO_MAJORITY: ResetRound,
            Event.ROUND_TIMEOUT: ResetRound,
        },
        TestRound: {
            Event.DONE: TrainRound,
            Event.NO_MAJORITY: ResetRound,
            Event.ROUND_TIMEOUT: ResetRound,
        },
        EstimateRound: {
            Event.DONE: ResetRound,
            Event.ESTIMATION_CYCLE: CycleResetRound,
            Event.ROUND_TIMEOUT: ResetRound,
            Event.NO_MAJORITY: ResetRound,
        },
        ResetRound: {
            Event.DONE: CollectHistoryRound,
            Event.RESET_TIMEOUT: RegistrationRound,
            Event.NO_MAJORITY: RegistrationRound,
        },
        CycleResetRound: {
            Event.DONE: EstimateRound,
            Event.RESET_TIMEOUT: ResetRound,
            Event.NO_MAJORITY: ResetRound,
        },
    }
    event_to_timeout: Dict[Event, float] = {
        Event.ROUND_TIMEOUT: 30.0,
        Event.RESET_TIMEOUT: 30.0,
    }
