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
    BatchPreparationPayload,
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
    UpdatePayload,
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
    """Class to represent a period state. This state is replicated by the tendermint application."""

    @property
    def history_hash(self) -> str:
        """Get the most voted history hash."""
        return cast(str, self.db.get_strict("most_voted_history"))

    @property
    def latest_observation_timestamp(self) -> str:
        """Get the latest observation's timestamp."""
        return cast(str, self.db.get_strict("latest_observation_timestamp"))

    @property
    def batch_hash(self) -> str:
        """Get the most voted batch hash."""
        return cast(str, self.db.get_strict("most_voted_batch"))

    @property
    def transformed_history_hash(self) -> str:
        """Get the most voted transformed history hash."""
        return cast(str, self.db.get_strict("most_voted_transform"))

    @property
    def latest_observation_hist_hash(self) -> str:
        """Get the latest observation's history hash."""
        return cast(str, self.db.get_strict("latest_observation_hist_hash"))

    @property
    def train_hash(self) -> str:
        """Get the most voted train hash."""
        split = cast(str, self.db.get_strict("most_voted_split"))
        return split[0 : int(len(split) / 2)]

    @property
    def test_hash(self) -> str:
        """Get the most voted test hash."""
        split = cast(str, self.db.get_strict("most_voted_split"))
        return split[int(len(split) / 2) :]

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
        if self.collection_threshold_reached:
            updated_state = self.period_state.update(
                participants=self.collection,
                period_state_class=PeriodState,
                full_training=False,
                n_estimations=0,
            )
            return updated_state, Event.DONE

        return None


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
    collection_key = "participant_to_history"
    selection_key = "most_voted_history"

    def end_block(self) -> Optional[Tuple[BasePeriodState, Event]]:
        """Process the end of the block."""
        if self.threshold_reached:
            update_kwargs = {
                self.collection_key: self.collection,
                self.selection_key: self.most_voted_payload,
                "latest_observation_timestamp": cast(
                    FetchingPayload, list(self.collection.values())[0]
                ).latest_observation_timestamp,
            }

            updated_state = cast(
                PeriodState,
                self.period_state.update(**update_kwargs),
            )
            return updated_state, Event.DONE

        if not self.is_majority_possible(
            self.collection, self.period_state.nb_participants
        ):
            return self._return_no_majority_event()

        return None


class CollectLatestHistoryBatchRound(CollectHistoryRound):
    """
    This class represents the 'CollectLatestHistoryBatchRound' round.

    Input: a period state with the prior round data.
    Output: a new period state with the prior round data and the votes for the historical batch data.

    It schedules the `PrepareBatchRound`.
    """

    round_id = "collect_batch"
    collection_key = "participant_to_batch"
    selection_key = "most_voted_batch"


class TransformRound(CollectSameUntilThresholdRound, APYEstimationAbstractRound):
    """
    This class represents the 'Transform' round.

    Input: a period state with the prior round data.
    Output: a new period state with the prior round data and the votes for the transformed data.

    It schedules the PreprocessRound.
    """

    round_id = "transform"
    allowed_tx_type = TransformationPayload.transaction_type
    payload_attribute = "transformed_history_hash"

    def end_block(self) -> Optional[Tuple[BasePeriodState, Event]]:
        """Process the end of the block."""
        if self.threshold_reached:
            updated_state = cast(
                PeriodState,
                self.period_state.update(
                    participant_to_transform=self.collection,
                    most_voted_transform=self.most_voted_payload,
                    latest_observation_hist_hash=cast(
                        TransformationPayload, list(self.collection.values())[0]
                    ).latest_observation_hist_hash,
                ),
            )
            return updated_state, Event.DONE

        if not self.is_majority_possible(
            self.collection, self.period_state.nb_participants
        ):
            return self._return_no_majority_event()

        return None


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


class PrepareBatchRound(CollectSameUntilThresholdRound):
    """
    This class represents the 'PrepareBatchRound'.

    Input: a period state with the prior round data.
    Output: a new period state with the prior round data and the votes for the transformed data.

    It schedules the `UpdateForecasterRound`.
    """

    round_id = "prepare_batch"
    allowed_tx_type = BatchPreparationPayload.transaction_type
    payload_attribute = "prepared_batch"
    period_state_class = PeriodState
    done_event = Event.DONE
    no_majority_event = Event.NO_MAJORITY
    collection_key = "participant_to_batch_preparation"
    selection_key = "latest_observation_hist_hash"


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
    """
    This class represents the 'Optimize' round.

    Input: a period state with the prior round data.
    Output: a new period state with the prior round data and the votes for the hyperparameters.

    It schedules the TrainRound.
    """

    round_id = "optimize"
    allowed_tx_type = OptimizationPayload.transaction_type
    payload_attribute = "best_params"
    period_state_class = PeriodState
    done_event = Event.DONE
    no_majority_event = Event.NO_MAJORITY
    collection_key = "participant_to_params"
    selection_key = "most_voted_params"


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
    """
    This class represents the 'Test' round.

    Input: a period state with the prior round data.
    Output: a new period state with the prior round data and the votes for the results.

    It schedules the EstimateConsensusRound.
    """

    round_id = "test"
    allowed_tx_type = _TestingPayload.transaction_type
    payload_attribute = "report_hash"
    period_state_class = PeriodState
    done_event = Event.DONE
    no_majority_event = Event.NO_MAJORITY
    collection_key = "participant_to_full_training"
    selection_key = "full_training"


class UpdateForecasterRound(CollectSameUntilThresholdRound):
    """
    This class represents the 'UpdateForecasterRound' round.

    Input: a period state with the prior round data.
    Output: a new period state with the prior round data and the votes for the historical batch data.

    It schedules the `EstimateRound`.
    """

    round_id = "update_forecaster"
    allowed_tx_type = UpdatePayload.transaction_type
    payload_attribute = "updated_model_hash"
    period_state_class = PeriodState
    done_event = Event.DONE
    no_majority_event = Event.NO_MAJORITY
    collection_key = "participant_to_update"
    selection_key = "most_voted_model"


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
            if self.round_id in ("cycle_reset", "fresh_model_reset"):
                kwargs["pair_name"] = self.period_state.pair_name
                kwargs["most_voted_model"] = self.period_state.model_hash
            if self.round_id == "cycle_reset":
                kwargs[
                    "latest_observation_hist_hash"
                ] = self.period_state.latest_observation_hist_hash

            updated_state = self.period_state.update(**kwargs)
            return updated_state, Event.DONE

        if not self.is_majority_possible(
            self.collection, self.period_state.nb_participants
        ):
            return self._return_no_majority_event()

        return None


class FreshModelResetRound(ResetRound):
    """This class represents round that gets activated if `N_ESTIMATIONS_BEFORE_RETRAIN` get reached."""

    round_id = "fresh_model_reset"


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
            Event.DONE: FreshModelResetRound,
            Event.ESTIMATION_CYCLE: CycleResetRound,
            Event.ROUND_TIMEOUT: ResetRound,  # if the round times out we reset the period
            Event.NO_MAJORITY: ResetRound,  # if there is no majority we reset the period
        },
        FreshModelResetRound: {
            Event.DONE: CollectHistoryRound,
            Event.ROUND_TIMEOUT: ResetRound,  # if the round times out we reset the period
            Event.NO_MAJORITY: ResetRound,  # if there is no majority we reset the period
        },
        CycleResetRound: {
            Event.DONE: CollectLatestHistoryBatchRound,
            Event.ROUND_TIMEOUT: ResetRound,  # if the round times out we try to assemble a new group of agents
            Event.NO_MAJORITY: ResetRound,  # if we cannot agree we try to assemble a new group of agents
        },
        CollectLatestHistoryBatchRound: {
            Event.DONE: PrepareBatchRound,
            Event.ROUND_TIMEOUT: ResetRound,  # if the round times out we reset the period
            Event.NO_MAJORITY: ResetRound,  # if there is no majority we reset the period
        },
        PrepareBatchRound: {
            Event.DONE: UpdateForecasterRound,
            Event.ROUND_TIMEOUT: ResetRound,  # if the round times out we reset the period
            Event.NO_MAJORITY: ResetRound,  # if there is no majority we reset the period
        },
        UpdateForecasterRound: {
            Event.DONE: EstimateRound,
            Event.ROUND_TIMEOUT: ResetRound,  # if the round times out we reset the period
            Event.NO_MAJORITY: ResetRound,  # if there is no majority we reset the period
        },
        ResetRound: {
            Event.DONE: RegistrationRound,
            Event.RESET_TIMEOUT: RegistrationRound,  # if the round times out we try to assemble a new group of agents
            Event.NO_MAJORITY: RegistrationRound,  # if we cannot agree we try to assemble a new group of agents
        },
    }
    event_to_timeout: Dict[Event, float] = {
        Event.ROUND_TIMEOUT: 30.0,
        Event.RESET_TIMEOUT: 30.0,
    }
