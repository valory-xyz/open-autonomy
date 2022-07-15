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
from typing import Dict, Optional, Set, Tuple, Type, cast

from packages.valory.skills.abstract_round_abci.base import (
    AbciApp,
    AbciAppDB,
    AbciAppTransitionFunction,
    AbstractRound,
    AppState,
    BaseSynchronizedData,
    CollectSameUntilThresholdRound,
    DegenerateRound,
    TransactionType,
)
from packages.valory.skills.apy_estimation_abci.payloads import (
    BatchPreparationPayload,
    EstimatePayload,
    FetchingPayload,
    OptimizationPayload,
    PreprocessPayload,
    RandomnessPayload,
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
    FILE_ERROR = "file_error"
    NETWORK_ERROR = "network_error"


class SynchronizedData(BaseSynchronizedData):
    """Class to represent the synchronized data.

    This data is replicated by the tendermint application.
    """

    @property
    def history_hash(self) -> str:
        """Get the most voted history hash."""
        return cast(str, self.db.get_strict("most_voted_history"))

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
    def models_hash(self) -> str:
        """Get the most_voted_models."""
        return cast(str, self.db.get_strict("most_voted_models"))

    @property
    def estimates_hash(self) -> str:
        """Get the most_voted_estimate."""
        return cast(str, self.db.get_strict("most_voted_estimate"))

    @property
    def is_most_voted_estimate_set(self) -> bool:
        """Check if most_voted_estimate is set."""
        return self.db.get("most_voted_estimate", None) is not None

    @property
    def full_training(self) -> bool:
        """Get the full_training flag."""
        return cast(bool, self.db.get("full_training", False))

    @property
    def n_estimations(self) -> int:
        """Get the n_estimations."""
        return cast(int, self.db.get("n_estimations", 0))


class APYEstimationAbstractRound(AbstractRound[Event, TransactionType], ABC):
    """Abstract round for the APY estimation skill."""

    @property
    def synchronized_data(self) -> SynchronizedData:
        """Return the synchronized data data."""
        return cast(SynchronizedData, super().synchronized_data)

    def _return_no_majority_event(self) -> Tuple[SynchronizedData, Event]:
        """
        Trigger the NO_MAJORITY event.

        :return: a new synchronized data and a NO_MAJORITY event
        """
        return self.synchronized_data, Event.NO_MAJORITY

    def _return_file_error(self) -> Tuple[SynchronizedData, Event]:
        """
        Trigger the FILE_ERROR event.

        :return: a new synchronized data and a FILE_ERROR event
        """
        return self.synchronized_data, Event.FILE_ERROR


class CollectHistoryRound(CollectSameUntilThresholdRound, APYEstimationAbstractRound):
    """A round in which agents collect historical data"""

    round_id = "collect_history"
    allowed_tx_type = FetchingPayload.transaction_type
    payload_attribute = "history"
    collection_key = "participant_to_history"
    selection_key = "most_voted_history"

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Event]]:
        """Process the end of the block."""
        if self.threshold_reached:
            if self.most_voted_payload is None:
                return self._return_file_error()

            if self.most_voted_payload == "":
                return self.synchronized_data, Event.NETWORK_ERROR

            update_kwargs = {
                "synchronized_data_class": SynchronizedData,
                self.collection_key: self.collection,
                self.selection_key: self.most_voted_payload,
            }

            synchronized_data = self.synchronized_data.update(**update_kwargs)
            return synchronized_data, Event.DONE

        if not self.is_majority_possible(
            self.collection, self.synchronized_data.nb_participants
        ):
            return self._return_no_majority_event()

        return None


class CollectLatestHistoryBatchRound(CollectHistoryRound):
    """A round in which agents collect the latest data batch"""

    round_id = "collect_batch"
    collection_key = "participant_to_batch"
    selection_key = "most_voted_batch"


class TransformRound(CollectSameUntilThresholdRound, APYEstimationAbstractRound):
    """A round in which agents transform data"""

    round_id = "transform"
    allowed_tx_type = TransformationPayload.transaction_type
    payload_attribute = "transformed_history_hash"

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Event]]:
        """Process the end of the block."""
        if self.threshold_reached and self.most_voted_payload is None:
            return self._return_file_error()

        if self.threshold_reached:
            synchronized_data = self.synchronized_data.update(
                synchronized_data_class=SynchronizedData,
                participant_to_transform=self.collection,
                most_voted_transform=self.most_voted_payload,
                latest_observation_hist_hash=cast(
                    TransformationPayload, list(self.collection.values())[0]
                ).latest_observation_hist_hash,
            )
            return synchronized_data, Event.DONE

        if not self.is_majority_possible(
            self.collection, self.synchronized_data.nb_participants
        ):
            return self._return_no_majority_event()

        return None


class PreprocessRound(CollectSameUntilThresholdRound, APYEstimationAbstractRound):
    """A round in which the agents preprocess the data"""

    round_id = "preprocess"
    allowed_tx_type = PreprocessPayload.transaction_type
    payload_attribute = "train_test_hash"

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Event]]:
        """Process the end of the block."""
        if self.threshold_reached:
            if self.most_voted_payload is None:
                return self._return_file_error()

            synchronized_data = self.synchronized_data.update(
                synchronized_data_class=SynchronizedData,
                participant_to_preprocessing=self.collection,
                most_voted_split=self.most_voted_payload,
            )
            return synchronized_data, Event.DONE

        if not self.is_majority_possible(
            self.collection, self.synchronized_data.nb_participants
        ):
            return self._return_no_majority_event()

        return None


class PrepareBatchRound(CollectSameUntilThresholdRound):
    """A round in which agents prepare a batch of data"""

    round_id = "prepare_batch"
    allowed_tx_type = BatchPreparationPayload.transaction_type
    payload_attribute = "prepared_batch"
    synchronized_data_class = SynchronizedData
    done_event = Event.DONE
    no_majority_event = Event.NO_MAJORITY
    none_event = Event.FILE_ERROR
    collection_key = "participant_to_batch_preparation"
    selection_key = "latest_observation_hist_hash"


class RandomnessRound(CollectSameUntilThresholdRound, APYEstimationAbstractRound):
    """A round in which a random number is retrieved

    This number is obtained from a distributed randomness beacon. The agents
    need to reach consensus on this number and subsequently use it to seed
    any random number generators.
    """

    round_id = "randomness"
    allowed_tx_type = RandomnessPayload.transaction_type
    payload_attribute = "randomness"

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Event]]:
        """Process the end of the block."""
        if self.threshold_reached:
            filtered_randomness = filter_out_numbers(self.most_voted_payload)

            if filtered_randomness is None:
                return self.synchronized_data, Event.RANDOMNESS_INVALID

            synchronized_data = self.synchronized_data.update(
                synchronized_data_class=SynchronizedData,
                participants_to_randomness=self.collection,
                most_voted_randomness=filtered_randomness,
            )
            return synchronized_data, Event.DONE

        if not self.is_majority_possible(
            self.collection, self.synchronized_data.nb_participants
        ):
            return self._return_no_majority_event()

        return None


class OptimizeRound(CollectSameUntilThresholdRound):
    """A round in which agents agree on the optimal hyperparameters"""

    round_id = "optimize"
    allowed_tx_type = OptimizationPayload.transaction_type
    payload_attribute = "best_params"
    synchronized_data_class = SynchronizedData
    done_event = Event.DONE
    no_majority_event = Event.NO_MAJORITY
    none_event = Event.FILE_ERROR
    collection_key = "participant_to_params"
    selection_key = "most_voted_params"


class TrainRound(CollectSameUntilThresholdRound, APYEstimationAbstractRound):
    """A round in which agents train a model"""

    round_id = "train"
    allowed_tx_type = TrainingPayload.transaction_type
    payload_attribute = "models_hash"

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Event]]:
        """Process the end of the block."""
        if self.threshold_reached:
            if self.most_voted_payload is None:
                return self._return_file_error()

            update_params = dict(
                synchronized_data_class=SynchronizedData,
                participants_to_training=self.collection,
                most_voted_models=self.most_voted_payload,
            )

            if self.synchronized_data.full_training:
                synchronized_data = self.synchronized_data.update(
                    full_training=True,
                    **update_params,
                )
                return synchronized_data, Event.FULLY_TRAINED

            synchronized_data = self.synchronized_data.update(**update_params)
            return synchronized_data, Event.DONE

        if not self.is_majority_possible(
            self.collection, self.synchronized_data.nb_participants
        ):
            return self._return_no_majority_event()

        return None


class TestRound(CollectSameUntilThresholdRound):
    """A round in which agents test a model"""

    round_id = "test"
    allowed_tx_type = _TestingPayload.transaction_type
    payload_attribute = "report_hash"
    synchronized_data_class = SynchronizedData
    done_event = Event.DONE
    no_majority_event = Event.NO_MAJORITY
    none_event = Event.FILE_ERROR
    collection_key = "participant_to_full_training"
    selection_key = "full_training"


class UpdateForecasterRound(CollectSameUntilThresholdRound):
    """A round in which agents update the forecasting model"""

    round_id = "update_forecaster"
    allowed_tx_type = UpdatePayload.transaction_type
    payload_attribute = "updated_models_hash"
    synchronized_data_class = SynchronizedData
    done_event = Event.DONE
    no_majority_event = Event.NO_MAJORITY
    none_event = Event.FILE_ERROR
    collection_key = "participant_to_update"
    selection_key = "most_voted_models"


class EstimateRound(CollectSameUntilThresholdRound, APYEstimationAbstractRound):
    """A round in which agents make predictions using a model"""

    round_id = "estimate"
    allowed_tx_type = EstimatePayload.transaction_type
    payload_attribute = "estimations_hash"

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Event]]:
        """Process the end of the block."""
        if self.threshold_reached:
            if self.most_voted_payload is None:
                return self._return_file_error()

            synchronized_data = self.synchronized_data.update(
                synchronized_data_class=SynchronizedData,
                participants_to_estimate=self.collection,
                n_estimations=cast(
                    SynchronizedData, self.synchronized_data
                ).n_estimations
                + 1,
                most_voted_estimate=self.most_voted_payload,
            )

            if (
                cast(SynchronizedData, synchronized_data).n_estimations
                % N_ESTIMATIONS_BEFORE_RETRAIN
                == 0
            ):
                return synchronized_data, Event.DONE

            return synchronized_data, Event.ESTIMATION_CYCLE

        if not self.is_majority_possible(
            self.collection, self.synchronized_data.nb_participants
        ):
            return self._return_no_majority_event()

        return None


class BaseResetRound(CollectSameUntilThresholdRound, APYEstimationAbstractRound):
    """A round that represents the reset of a period"""

    allowed_tx_type = ResetPayload.transaction_type
    payload_attribute = "period_count"

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Event]]:
        """Process the end of the block."""
        if self.threshold_reached:
            kwargs = dict(
                participants=self.synchronized_data.participants,
                all_participants=self.synchronized_data.all_participants,
                full_training=False,
                n_estimations=self.synchronized_data.n_estimations,
                most_voted_models=self.synchronized_data.models_hash,
            )
            if self.round_id == "cycle_reset":
                kwargs[
                    "latest_observation_hist_hash"
                ] = self.synchronized_data.latest_observation_hist_hash

            synchronized_data = self.synchronized_data.create(
                synchronized_data_class=SynchronizedData,
                **AbciAppDB.data_to_lists(kwargs),
            )
            return synchronized_data, Event.DONE

        if not self.is_majority_possible(
            self.collection, self.synchronized_data.nb_participants
        ):
            return self._return_no_majority_event()

        return None


class FreshModelResetRound(BaseResetRound):
    """A round that represents that consensus is reached and `N_ESTIMATIONS_BEFORE_RETRAIN` has been reached."""

    round_id = "fresh_model_reset"


class CycleResetRound(BaseResetRound):
    """A round that represents that consensus is reached and `N_ESTIMATIONS_BEFORE_RETRAIN` is not yet reached."""

    round_id = "cycle_reset"


class FinishedAPYEstimationRound(DegenerateRound, ABC):
    """A round that represents APY estimation has finished"""

    round_id = "finished_apy_estimation"


class FailedAPYRound(DegenerateRound, ABC):
    """A round that represents that the period failed"""

    round_id = "failed_apy"


class APYEstimationAbciApp(AbciApp[Event]):  # pylint: disable=too-few-public-methods
    """APYEstimationAbciApp

    Initial round: CollectHistoryRound

    Initial states: {CollectHistoryRound}

    Transition states:
        0. CollectHistoryRound
            - done: 1.
            - no majority: 0.
            - round timeout: 0.
            - file error: 13.
            - network error: 13.
        1. TransformRound
            - done: 2.
            - no majority: 1.
            - round timeout: 1.
            - file error: 13.
        2. PreprocessRound
            - done: 3.
            - no majority: 2.
            - round timeout: 2.
            - file error: 13.
        3. RandomnessRound
            - done: 4.
            - randomness invalid: 3.
            - no majority: 3.
            - round timeout: 3.
        4. OptimizeRound
            - done: 5.
            - no majority: 4.
            - round timeout: 4.
            - file error: 13.
        5. TrainRound
            - fully trained: 7.
            - done: 6.
            - no majority: 5.
            - round timeout: 5.
            - file error: 13.
        6. TestRound
            - done: 5.
            - no majority: 6.
            - round timeout: 6.
            - file error: 13.
        7. EstimateRound
            - done: 8.
            - estimation cycle: 9.
            - round timeout: 7.
            - no majority: 7.
            - file error: 13.
        8. FreshModelResetRound
            - done: 0.
            - round timeout: 8.
            - no majority: 8.
        9. CycleResetRound
            - done: 10.
            - round timeout: 9.
            - no majority: 9.
        10. CollectLatestHistoryBatchRound
            - done: 11.
            - round timeout: 10.
            - no majority: 10.
            - file error: 13.
            - network error: 13.
        11. PrepareBatchRound
            - done: 12.
            - round timeout: 11.
            - no majority: 11.
            - file error: 13.
        12. UpdateForecasterRound
            - done: 7.
            - round timeout: 12.
            - no majority: 12.
            - file error: 13.
        13. FailedAPYRound

    Final states: {FailedAPYRound}

    Timeouts:
        round timeout: 30.0
        reset timeout: 30.0
    """

    initial_round_cls: Type[AbstractRound] = CollectHistoryRound
    transition_function: AbciAppTransitionFunction = {
        CollectHistoryRound: {
            Event.DONE: TransformRound,
            Event.NO_MAJORITY: CollectHistoryRound,
            Event.ROUND_TIMEOUT: CollectHistoryRound,
            Event.FILE_ERROR: FailedAPYRound,
            Event.NETWORK_ERROR: FailedAPYRound,
        },
        TransformRound: {
            Event.DONE: PreprocessRound,
            Event.NO_MAJORITY: TransformRound,
            Event.ROUND_TIMEOUT: TransformRound,
            Event.FILE_ERROR: FailedAPYRound,
        },
        PreprocessRound: {
            Event.DONE: RandomnessRound,
            Event.NO_MAJORITY: PreprocessRound,
            Event.ROUND_TIMEOUT: PreprocessRound,
            Event.FILE_ERROR: FailedAPYRound,
        },
        RandomnessRound: {
            Event.DONE: OptimizeRound,
            Event.RANDOMNESS_INVALID: RandomnessRound,
            Event.NO_MAJORITY: RandomnessRound,
            Event.ROUND_TIMEOUT: RandomnessRound,
        },
        OptimizeRound: {
            Event.DONE: TrainRound,
            Event.NO_MAJORITY: OptimizeRound,
            Event.ROUND_TIMEOUT: OptimizeRound,
            Event.FILE_ERROR: FailedAPYRound,
        },
        TrainRound: {
            Event.FULLY_TRAINED: EstimateRound,
            Event.DONE: TestRound,
            Event.NO_MAJORITY: TrainRound,
            Event.ROUND_TIMEOUT: TrainRound,
            Event.FILE_ERROR: FailedAPYRound,
        },
        TestRound: {
            Event.DONE: TrainRound,
            Event.NO_MAJORITY: TestRound,
            Event.ROUND_TIMEOUT: TestRound,
            Event.FILE_ERROR: FailedAPYRound,
        },
        EstimateRound: {
            Event.DONE: FreshModelResetRound,
            Event.ESTIMATION_CYCLE: CycleResetRound,
            Event.ROUND_TIMEOUT: EstimateRound,
            Event.NO_MAJORITY: EstimateRound,
            Event.FILE_ERROR: FailedAPYRound,
        },
        FreshModelResetRound: {
            Event.DONE: CollectHistoryRound,
            Event.ROUND_TIMEOUT: FreshModelResetRound,
            Event.NO_MAJORITY: FreshModelResetRound,
        },
        CycleResetRound: {
            Event.DONE: CollectLatestHistoryBatchRound,
            Event.ROUND_TIMEOUT: CycleResetRound,
            Event.NO_MAJORITY: CycleResetRound,
        },
        CollectLatestHistoryBatchRound: {
            Event.DONE: PrepareBatchRound,
            Event.ROUND_TIMEOUT: CollectLatestHistoryBatchRound,
            Event.NO_MAJORITY: CollectLatestHistoryBatchRound,
            Event.FILE_ERROR: FailedAPYRound,
            Event.NETWORK_ERROR: FailedAPYRound,
        },
        PrepareBatchRound: {
            Event.DONE: UpdateForecasterRound,
            Event.ROUND_TIMEOUT: PrepareBatchRound,
            Event.NO_MAJORITY: PrepareBatchRound,
            Event.FILE_ERROR: FailedAPYRound,
        },
        UpdateForecasterRound: {
            Event.DONE: EstimateRound,
            Event.ROUND_TIMEOUT: UpdateForecasterRound,
            Event.NO_MAJORITY: UpdateForecasterRound,
            Event.FILE_ERROR: FailedAPYRound,
        },
        FailedAPYRound: {},
    }
    final_states: Set[AppState] = {FailedAPYRound}
    event_to_timeout: Dict[Event, float] = {
        Event.ROUND_TIMEOUT: 30.0,
        Event.RESET_TIMEOUT: 30.0,
    }
