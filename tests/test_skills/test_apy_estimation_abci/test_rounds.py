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

"""Test the rounds of the skill."""
from typing import Dict, FrozenSet, Optional, Tuple
from unittest import mock

import pytest

from packages.valory.skills.abstract_round_abci.base import (
    AbciAppDB,
    AbstractRound,
    ConsensusParams,
)
from packages.valory.skills.apy_estimation_abci.payloads import (
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
)
from packages.valory.skills.apy_estimation_abci.rounds import (
    CollectHistoryRound,
    CycleResetRound,
    EstimateRound,
    Event,
    FreshModelResetRound,
    OptimizeRound,
    PreprocessRound,
    RandomnessRound,
    SynchronizedData,
)
from packages.valory.skills.apy_estimation_abci.rounds import TestRound as _TestRound
from packages.valory.skills.apy_estimation_abci.rounds import TrainRound, TransformRound

from tests.test_skills.test_abstract_round_abci.test_base_rounds import (
    BaseCollectSameUntilThresholdRoundTest,
)


MAX_PARTICIPANTS: int = 4
RANDOMNESS: str = "d1c29dce46f979f9748210d24bce4eae8be91272f5ca1a6aea2832d3dd676f51"
INVALID_RANDOMNESS: str = "invalid_randomness"


def get_participants() -> FrozenSet[str]:
    """Participants"""
    return frozenset([f"agent_{i}" for i in range(MAX_PARTICIPANTS)])


def get_participant_to_fetching(
    participants: FrozenSet[str], history: Optional[str]
) -> Dict[str, FetchingPayload]:
    """participant_to_fetching"""
    return {
        participant: FetchingPayload(sender=participant, history=history)
        for participant in participants
    }


def get_participant_to_randomness(
    participants: FrozenSet[str], round_id: int
) -> Dict[str, RandomnessPayload]:
    """participant_to_randomness"""
    return {
        participant: RandomnessPayload(
            sender=participant,
            round_id=round_id,
            randomness=RANDOMNESS,
        )
        for participant in participants
    }


def get_participant_to_invalid_randomness(
    participants: FrozenSet[str], round_id: int
) -> Dict[str, RandomnessPayload]:
    """Invalid participant_to_randomness"""
    return {
        participant: RandomnessPayload(
            sender=participant,
            round_id=round_id,
            randomness=INVALID_RANDOMNESS,
        )
        for participant in participants
    }


def get_transformation_payload(
    participants: FrozenSet[str],
    transformation_hash: Optional[str],
) -> Dict[str, TransformationPayload]:
    """Get transformation payloads."""
    return {
        participant: TransformationPayload(participant, transformation_hash, "x1")
        for participant in participants
    }


def get_participant_to_preprocess_payload(
    participants: FrozenSet[str],
    train_hash: Optional[str],
    test_hash: Optional[str],
) -> Dict[str, PreprocessPayload]:
    """Get preprocess payload."""
    return {
        participant: PreprocessPayload(
            participant,
            train_hash,
            test_hash,
        )
        for participant in participants
    }


def get_participant_to_optimize_payload(
    participants: FrozenSet[str],
) -> Dict[str, OptimizationPayload]:
    """Get optimization payload."""
    return {
        participant: OptimizationPayload(participant, "best_params_hash")  # type: ignore
        for participant in participants
    }


def get_participant_to_train_payload(
    participants: FrozenSet[str],
    models_hash: Optional[str],
) -> Dict[str, TrainingPayload]:
    """Get training payload."""
    return {
        participant: TrainingPayload(participant, models_hash)
        for participant in participants
    }


def get_participant_to_test_payload(
    participants: FrozenSet[str],
) -> Dict[str, _TestingPayload]:
    """Get testing payload."""
    return {
        participant: _TestingPayload(participant, "report_hash")
        for participant in participants
    }


def get_participant_to_estimate_payload(
    participants: FrozenSet[str],
    estimations_hash: Optional[str],
) -> Dict[str, EstimatePayload]:
    """Get estimate payload."""
    return {
        participant: EstimatePayload(participant, estimations_hash)
        for participant in participants
    }


def get_participant_to_reset_payload(
    participants: FrozenSet[str],
) -> Dict[str, ResetPayload]:
    """Get reset payload."""
    return {
        participant: ResetPayload(participant, period_count=1)
        for participant in participants
    }


class BaseRoundTestClass:
    """Base test class for Rounds."""

    synchronized_data: SynchronizedData
    consensus_params: ConsensusParams
    participants: FrozenSet[str]

    @classmethod
    def setup(
        cls,
    ) -> None:
        """Setup the test class."""

        cls.participants = get_participants()
        cls.synchronized_data = SynchronizedData(
            db=AbciAppDB(
                setup_data=dict(
                    participants=[cls.participants], all_participants=[cls.participants]
                ),
            )
        )
        cls.consensus_params = ConsensusParams(max_participants=MAX_PARTICIPANTS)

    @staticmethod
    def _test_no_majority_event(round_obj: AbstractRound) -> None:
        """Test the NO_MAJORITY event."""
        with mock.patch.object(round_obj, "is_majority_possible", return_value=False):
            result = round_obj.end_block()
            assert result is not None
            synchronized_data, event = result
            assert event == Event.NO_MAJORITY


class TestCollectHistoryRound(BaseCollectSameUntilThresholdRoundTest):
    """Test `CollectHistoryRound`."""

    _synchronized_data_class = SynchronizedData
    _event_class = Event

    @pytest.mark.parametrize(
        "most_voted_payload, expected_event",
        (("x0", Event.DONE), (None, Event.FILE_ERROR), ("", Event.NETWORK_ERROR)),
    )
    def test_run(
        self,
        most_voted_payload: Optional[str],
        expected_event: Event,
    ) -> None:
        """Runs test."""
        test_round = CollectHistoryRound(self.synchronized_data, self.consensus_params)
        self._complete_run(
            self._test_round(
                test_round=test_round,
                round_payloads=get_participant_to_fetching(
                    self.participants, most_voted_payload
                ),
                synchronized_data_update_fn=lambda _synchronized_data, _: _synchronized_data,
                synchronized_data_attr_checks=[],
                most_voted_payload=most_voted_payload,
                exit_event=expected_event,
            )
        )

    def test_no_majority_event(self) -> None:
        """Test the no-majority event."""
        test_round = CollectHistoryRound(self.synchronized_data, self.consensus_params)
        self._test_no_majority_event(test_round)


class TestTransformRound(BaseCollectSameUntilThresholdRoundTest):
    """Test `TransformRound`."""

    _synchronized_data_class = SynchronizedData
    _event_class = Event

    @pytest.mark.parametrize(
        "most_voted_payload, expected_event",
        (("x0", Event.DONE), (None, Event.FILE_ERROR)),
    )
    def test_run(
        self,
        most_voted_payload: Optional[str],
        expected_event: Event,
    ) -> None:
        """Runs test."""

        test_round = TransformRound(self.synchronized_data, self.consensus_params)
        self._complete_run(
            self._test_round(
                test_round=test_round,
                round_payloads=get_transformation_payload(
                    self.participants, most_voted_payload
                ),
                synchronized_data_update_fn=lambda _synchronized_data, _: _synchronized_data,
                synchronized_data_attr_checks=[],
                most_voted_payload=most_voted_payload,
                exit_event=expected_event,
            )
        )

    def test_no_majority_event(self) -> None:
        """Test the no-majority event."""
        test_round = TransformRound(self.synchronized_data, self.consensus_params)
        self._test_no_majority_event(test_round)


class TestPreprocessRound(BaseCollectSameUntilThresholdRoundTest):
    """Test `PreprocessRound`."""

    _synchronized_data_class = SynchronizedData
    _event_class = Event

    @pytest.mark.parametrize(
        "most_voted_payloads, expected_event",
        ((("train_hash", "test_hash"), Event.DONE), ((None, None), Event.FILE_ERROR)),
    )
    def test_run(
        self,
        most_voted_payloads: Tuple[Optional[str]],
        expected_event: Event,
    ) -> None:
        """Runs test."""

        test_round = PreprocessRound(self.synchronized_data, self.consensus_params)
        self._complete_run(
            self._test_round(
                test_round=test_round,
                round_payloads=get_participant_to_preprocess_payload(  # type: ignore
                    self.participants, *most_voted_payloads
                ),
                synchronized_data_update_fn=lambda _synchronized_data, _: _synchronized_data,
                synchronized_data_attr_checks=[],
                most_voted_payload="train_hashtest_hash"
                if not any(payload is None for payload in most_voted_payloads)
                else None,
                exit_event=expected_event,
            )
        )

    def test_no_majority_event(self) -> None:
        """Test the no-majority event."""
        test_round = PreprocessRound(self.synchronized_data, self.consensus_params)
        self._test_no_majority_event(test_round)


class TestRandomnessRound(BaseCollectSameUntilThresholdRoundTest):
    """Test RandomnessRound."""

    _synchronized_data_class = SynchronizedData
    _event_class = Event

    def test_run(
        self,
    ) -> None:
        """Run tests."""

        test_round = RandomnessRound(self.synchronized_data, self.consensus_params)
        self._complete_run(
            self._test_round(
                test_round=test_round,
                round_payloads=get_participant_to_randomness(self.participants, 1),
                synchronized_data_update_fn=lambda synchronized_data, _: synchronized_data,
                synchronized_data_attr_checks=[],
                most_voted_payload=RANDOMNESS,
                exit_event=Event.DONE,
            )
        )

    def test_invalid_randomness(self) -> None:
        """Test the no-majority event."""
        test_round = RandomnessRound(self.synchronized_data, self.consensus_params)
        self._complete_run(
            self._test_round(
                test_round=test_round,
                round_payloads=get_participant_to_invalid_randomness(
                    self.participants, 1
                ),
                synchronized_data_update_fn=lambda synchronized_data, _: synchronized_data,
                synchronized_data_attr_checks=[],
                most_voted_payload=INVALID_RANDOMNESS,
                exit_event=Event.RANDOMNESS_INVALID,
            )
        )

    def test_no_majority_event(self) -> None:
        """Test the no-majority event."""
        test_round = RandomnessRound(self.synchronized_data, self.consensus_params)
        self._test_no_majority_event(test_round)


class TestOptimizeRound(BaseCollectSameUntilThresholdRoundTest):
    """Test `OptimizeRound`."""

    _synchronized_data_class = SynchronizedData
    _event_class = Event

    def test_run(self) -> None:
        """Runs test."""

        test_round = OptimizeRound(self.synchronized_data, self.consensus_params)
        self._complete_run(
            self._test_round(
                test_round=test_round,
                round_payloads=get_participant_to_optimize_payload(self.participants),
                synchronized_data_update_fn=lambda _synchronized_data, _: _synchronized_data,
                synchronized_data_attr_checks=[],
                most_voted_payload="best_params_hash",
                exit_event=Event.DONE,
            )
        )

    def test_no_majority_event(self) -> None:
        """Test the no-majority event."""
        test_round = OptimizeRound(self.synchronized_data, self.consensus_params)
        self._test_no_majority_event(test_round)


class TestTrainRound(BaseCollectSameUntilThresholdRoundTest):
    """Test `TrainRound`."""

    _synchronized_data_class = SynchronizedData
    _event_class = Event

    @pytest.mark.parametrize(
        "full_training, most_voted_payload, expected_event",
        (
            (True, "x0", Event.FULLY_TRAINED),
            (False, "x0", Event.DONE),
            (True, None, Event.FILE_ERROR),
        ),
    )
    def test_run(
        self,
        full_training: bool,
        most_voted_payload: Optional[str],
        expected_event: Event,
    ) -> None:
        """Runs test."""

        test_round = TrainRound(
            self.synchronized_data.update(full_training=full_training),
            self.consensus_params,
        )
        self._complete_run(
            self._test_round(
                test_round=test_round,
                round_payloads=get_participant_to_train_payload(
                    self.participants, most_voted_payload
                ),
                synchronized_data_update_fn=lambda _synchronized_data, _: _synchronized_data,
                synchronized_data_attr_checks=[],
                most_voted_payload=most_voted_payload,
                exit_event=expected_event,
            )
        )

    def test_no_majority_event(self) -> None:
        """Test the no-majority event."""
        test_round = TrainRound(self.synchronized_data, self.consensus_params)
        self._test_no_majority_event(test_round)


class TestTestRound(BaseCollectSameUntilThresholdRoundTest):
    """Test `TestRound`."""

    _synchronized_data_class = SynchronizedData
    _event_class = Event

    def test_run(self) -> None:
        """Runs test."""

        test_round = _TestRound(
            self.synchronized_data.update(full_training=False),
            self.consensus_params,
        )
        self._complete_run(
            self._test_round(
                test_round=test_round,
                round_payloads=get_participant_to_test_payload(self.participants),
                synchronized_data_update_fn=lambda _synchronized_data, _: _synchronized_data.update(
                    full_training=True
                ),
                synchronized_data_attr_checks=[
                    lambda _synchronized_data: bool(_synchronized_data.full_training)
                ],
                most_voted_payload="report_hash",
                exit_event=Event.DONE,
            )
        )

    def test_no_majority_event(self) -> None:
        """Test the no-majority event."""
        test_round = _TestRound(self.synchronized_data, self.consensus_params)
        self._test_no_majority_event(test_round)


class TestEstimateRound(BaseCollectSameUntilThresholdRoundTest):
    """Test `EstimateRound`."""

    _synchronized_data_class = SynchronizedData
    _event_class = Event

    @pytest.mark.parametrize(
        "n_estimations, most_voted_payload, expected_event",
        (
            (0, "test_hash", Event.ESTIMATION_CYCLE),
            (59, "test_hash", Event.DONE),
            (0, None, Event.FILE_ERROR),
        ),
    )
    def test_estimation_cycle_run(
        self,
        n_estimations: int,
        most_voted_payload: Optional[str],
        expected_event: Event,
    ) -> None:
        """Runs test."""

        test_round = EstimateRound(
            self.synchronized_data.update(n_estimations=n_estimations),
            self.consensus_params,
        )
        self._complete_run(
            self._test_round(
                test_round=test_round,
                round_payloads=get_participant_to_estimate_payload(
                    self.participants, most_voted_payload
                ),
                synchronized_data_update_fn=lambda _synchronized_data, _: _synchronized_data.update(
                    n_estimations=n_estimations,
                ),
                synchronized_data_attr_checks=[lambda _: n_estimations + 1],
                most_voted_payload=most_voted_payload,
                exit_event=expected_event,
            )
        )

    def test_no_majority_event(self) -> None:
        """Test the no-majority event."""
        test_round = EstimateRound(self.synchronized_data, self.consensus_params)
        self._test_no_majority_event(test_round)


class TestCycleResetRound(BaseCollectSameUntilThresholdRoundTest):
    """Test `CycleResetRound`."""

    _synchronized_data_class = SynchronizedData
    _event_class = Event

    def test_run(
        self,
    ) -> None:
        """Run tests"""

        test_round = CycleResetRound(
            self.synchronized_data.update(
                latest_observation_hist_hash="x0",
                most_voted_models="",
                full_training=True,
            ),
            self.consensus_params,
        )
        self._complete_run(
            self._test_round(
                test_round=test_round,
                round_payloads=get_participant_to_reset_payload(self.participants),
                synchronized_data_update_fn=lambda _synchronized_data, _test_round: _synchronized_data.update(
                    full_training=False,
                ),
                synchronized_data_attr_checks=[
                    lambda _synchronized_data: _synchronized_data.full_training
                ],
                most_voted_payload=1,
                exit_event=Event.DONE,
            )
        )

    def test_no_majority_event(self) -> None:
        """Test the no-majority event."""
        test_round = CycleResetRound(self.synchronized_data, self.consensus_params)
        self._test_no_majority_event(test_round)


class TestFreshModelResetRound(BaseCollectSameUntilThresholdRoundTest):
    """Test `FreshModelResetRound`."""

    _synchronized_data_class = SynchronizedData
    _event_class = Event

    def test_run(
        self,
    ) -> None:
        """Run tests"""

        test_round = FreshModelResetRound(
            self.synchronized_data.update(
                n_estimations=1, full_training=True, most_voted_models=""
            ),
            self.consensus_params,
        )
        self._complete_run(
            self._test_round(
                test_round=test_round,
                round_payloads=get_participant_to_reset_payload(self.participants),
                synchronized_data_update_fn=lambda _synchronized_data, _test_round: _synchronized_data.update(
                    full_training=False,
                ),
                synchronized_data_attr_checks=[
                    lambda _synchronized_data: _synchronized_data.full_training
                ],
                most_voted_payload=1,
                exit_event=Event.DONE,
            )
        )

    def test_no_majority_event(self) -> None:
        """Test the no-majority event."""
        test_round = FreshModelResetRound(self.synchronized_data, self.consensus_params)
        self._test_no_majority_event(test_round)


def test_period() -> None:
    """Test SynchronizedData."""

    participants = get_participants()
    setup_params: Dict = {}
    most_voted_randomness = 1
    estimates_hash = "test_hash"
    full_training = False
    n_estimations = 1

    synchronized_data = SynchronizedData(
        db=AbciAppDB(
            setup_data=AbciAppDB.data_to_lists(
                dict(
                    participants=participants,
                    setup_params=setup_params,
                    most_voted_randomness=most_voted_randomness,
                    most_voted_estimate=estimates_hash,
                    full_training=full_training,
                    n_estimations=n_estimations,
                )
            ),
        )
    )

    assert synchronized_data.participants == participants
    assert synchronized_data.period_count == 0
    assert synchronized_data.most_voted_randomness == most_voted_randomness
    assert synchronized_data.estimates_hash == estimates_hash
    assert synchronized_data.full_training == full_training
    assert synchronized_data.n_estimations == n_estimations
    assert synchronized_data.is_most_voted_estimate_set is not None
