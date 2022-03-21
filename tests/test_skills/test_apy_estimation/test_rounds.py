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

"""Test the base.py module of the skill."""
from typing import Dict, FrozenSet, Optional, Tuple
from unittest import mock

import pytest

from packages.valory.skills.abstract_round_abci.base import (
    AbstractRound,
    ConsensusParams,
    StateDB,
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
    PeriodState,
    PreprocessRound,
    RandomnessRound,
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
        participant: FetchingPayload(
            sender=participant, history=history, latest_observation_timestamp=0
        )
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
    model_hash: Optional[str],
) -> Dict[str, TrainingPayload]:
    """Get training payload."""
    return {
        participant: TrainingPayload(participant, model_hash)
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

    period_state: PeriodState
    consensus_params: ConsensusParams
    participants: FrozenSet[str]

    @classmethod
    def setup(
        cls,
    ) -> None:
        """Setup the test class."""

        cls.participants = get_participants()
        cls.period_state = PeriodState(
            db=StateDB(
                initial_period=0,
                initial_data=dict(
                    participants=cls.participants, all_participants=cls.participants
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
            state, event = result
            assert event == Event.NO_MAJORITY


class TestCollectHistoryRound(BaseCollectSameUntilThresholdRoundTest):
    """Test `CollectHistoryRound`."""

    _period_state_class = PeriodState
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
        test_round = CollectHistoryRound(self.period_state, self.consensus_params)
        self._complete_run(
            self._test_round(
                test_round=test_round,
                round_payloads=get_participant_to_fetching(
                    self.participants, most_voted_payload
                ),
                state_update_fn=lambda _period_state, _: _period_state,
                state_attr_checks=[],
                most_voted_payload=most_voted_payload,
                exit_event=expected_event,
            )
        )

    def test_no_majority_event(self) -> None:
        """Test the no-majority event."""
        test_round = CollectHistoryRound(self.period_state, self.consensus_params)
        self._test_no_majority_event(test_round)


class TestTransformRound(BaseCollectSameUntilThresholdRoundTest):
    """Test `TransformRound`."""

    _period_state_class = PeriodState
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

        test_round = TransformRound(self.period_state, self.consensus_params)
        self._complete_run(
            self._test_round(
                test_round=test_round,
                round_payloads=get_transformation_payload(
                    self.participants, most_voted_payload
                ),
                state_update_fn=lambda _period_state, _: _period_state,
                state_attr_checks=[],
                most_voted_payload=most_voted_payload,
                exit_event=expected_event,
            )
        )

    def test_no_majority_event(self) -> None:
        """Test the no-majority event."""
        test_round = TransformRound(self.period_state, self.consensus_params)
        self._test_no_majority_event(test_round)


class TestPreprocessRound(BaseCollectSameUntilThresholdRoundTest):
    """Test `PreprocessRound`."""

    _period_state_class = PeriodState
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

        test_round = PreprocessRound(self.period_state, self.consensus_params)
        self._complete_run(
            self._test_round(
                test_round=test_round,
                round_payloads=get_participant_to_preprocess_payload(  # type: ignore
                    self.participants, *most_voted_payloads
                ),
                state_update_fn=lambda _period_state, _: _period_state,
                state_attr_checks=[],
                most_voted_payload="train_hashtest_hash"
                if not any(payload is None for payload in most_voted_payloads)
                else None,
                exit_event=expected_event,
            )
        )

    def test_no_majority_event(self) -> None:
        """Test the no-majority event."""
        test_round = PreprocessRound(self.period_state, self.consensus_params)
        self._test_no_majority_event(test_round)


class TestRandomnessRound(BaseCollectSameUntilThresholdRoundTest):
    """Test RandomnessRound."""

    _period_state_class = PeriodState
    _event_class = Event

    def test_run(
        self,
    ) -> None:
        """Run tests."""

        test_round = RandomnessRound(self.period_state, self.consensus_params)
        self._complete_run(
            self._test_round(
                test_round=test_round,
                round_payloads=get_participant_to_randomness(self.participants, 1),
                state_update_fn=lambda period_state, _: period_state,
                state_attr_checks=[],
                most_voted_payload=RANDOMNESS,
                exit_event=Event.DONE,
            )
        )

    def test_invalid_randomness(self) -> None:
        """Test the no-majority event."""
        test_round = RandomnessRound(self.period_state, self.consensus_params)
        self._complete_run(
            self._test_round(
                test_round=test_round,
                round_payloads=get_participant_to_invalid_randomness(
                    self.participants, 1
                ),
                state_update_fn=lambda period_state, _: period_state,
                state_attr_checks=[],
                most_voted_payload=INVALID_RANDOMNESS,
                exit_event=Event.RANDOMNESS_INVALID,
            )
        )

    def test_no_majority_event(self) -> None:
        """Test the no-majority event."""
        test_round = RandomnessRound(self.period_state, self.consensus_params)
        self._test_no_majority_event(test_round)


class TestOptimizeRound(BaseCollectSameUntilThresholdRoundTest):
    """Test `OptimizeRound`."""

    _period_state_class = PeriodState
    _event_class = Event

    def test_run(self) -> None:
        """Runs test."""

        test_round = OptimizeRound(self.period_state, self.consensus_params)
        self._complete_run(
            self._test_round(
                test_round=test_round,
                round_payloads=get_participant_to_optimize_payload(self.participants),
                state_update_fn=lambda _period_state, _: _period_state,
                state_attr_checks=[],
                most_voted_payload="best_params_hash",
                exit_event=Event.DONE,
            )
        )

    def test_no_majority_event(self) -> None:
        """Test the no-majority event."""
        test_round = OptimizeRound(self.period_state, self.consensus_params)
        self._test_no_majority_event(test_round)


class TestTrainRound(BaseCollectSameUntilThresholdRoundTest):
    """Test `TrainRound`."""

    _period_state_class = PeriodState
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
            self.period_state.update(full_training=full_training), self.consensus_params
        )
        self._complete_run(
            self._test_round(
                test_round=test_round,
                round_payloads=get_participant_to_train_payload(
                    self.participants, most_voted_payload
                ),
                state_update_fn=lambda _period_state, _: _period_state,
                state_attr_checks=[],
                most_voted_payload=most_voted_payload,
                exit_event=expected_event,
            )
        )

    def test_no_majority_event(self) -> None:
        """Test the no-majority event."""
        test_round = TrainRound(self.period_state, self.consensus_params)
        self._test_no_majority_event(test_round)


class TestTestRound(BaseCollectSameUntilThresholdRoundTest):
    """Test `TestRound`."""

    _period_state_class = PeriodState
    _event_class = Event

    def test_run(self) -> None:
        """Runs test."""

        test_round = _TestRound(
            self.period_state.update(full_training=True), self.consensus_params
        )
        self._complete_run(
            self._test_round(
                test_round=test_round,
                round_payloads=get_participant_to_test_payload(self.participants),
                state_update_fn=lambda _period_state, _: _period_state.update(
                    full_training=True
                ),
                state_attr_checks=[lambda state: state.full_training],
                most_voted_payload="report_hash",
                exit_event=Event.DONE,
            )
        )

    def test_no_majority_event(self) -> None:
        """Test the no-majority event."""
        test_round = _TestRound(self.period_state, self.consensus_params)
        self._test_no_majority_event(test_round)


class TestEstimateRound(BaseCollectSameUntilThresholdRoundTest):
    """Test `EstimateRound`."""

    _period_state_class = PeriodState
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

        test_round = EstimateRound(self.period_state, self.consensus_params)
        self._complete_run(
            self._test_round(
                test_round=test_round,
                round_payloads=get_participant_to_estimate_payload(
                    self.participants, most_voted_payload
                ),
                state_update_fn=lambda _period_state, _: _period_state.update(
                    n_estimations=n_estimations,
                ),
                state_attr_checks=[lambda _: n_estimations + 1],
                most_voted_payload=most_voted_payload,
                exit_event=expected_event,
            )
        )

    def test_no_majority_event(self) -> None:
        """Test the no-majority event."""
        test_round = EstimateRound(self.period_state, self.consensus_params)
        self._test_no_majority_event(test_round)


class TestCycleResetRound(BaseCollectSameUntilThresholdRoundTest):
    """Test `CycleResetRound`."""

    _period_state_class = PeriodState
    _event_class = Event

    def test_run(
        self,
    ) -> None:
        """Run tests"""

        test_round = CycleResetRound(self.period_state, self.consensus_params)
        self._complete_run(
            self._test_round(
                test_round=test_round,
                round_payloads=get_participant_to_reset_payload(self.participants),
                state_update_fn=lambda _period_state, _test_round: _period_state.update(
                    period_count=_test_round.most_voted_payload,
                    most_voted_model="",
                    full_training=False,
                    n_estimations=1,
                    latest_observation_hist_hash="x0",
                    participants=get_participants(),
                    all_participants=get_participants(),
                ),
                state_attr_checks=[],
                most_voted_payload=1,
                exit_event=Event.DONE,
            )
        )

    def test_no_majority_event(self) -> None:
        """Test the no-majority event."""
        test_round = CycleResetRound(self.period_state, self.consensus_params)
        self._test_no_majority_event(test_round)


class TestFreshModelResetRound(BaseCollectSameUntilThresholdRoundTest):
    """Test `FreshModelResetRound`."""

    _period_state_class = PeriodState
    _event_class = Event

    def test_run(
        self,
    ) -> None:
        """Run tests"""

        test_round = FreshModelResetRound(self.period_state, self.consensus_params)
        self._complete_run(
            self._test_round(
                test_round=test_round,
                round_payloads=get_participant_to_reset_payload(self.participants),
                state_update_fn=lambda _period_state, _test_round: _period_state.update(
                    period_count=_test_round.most_voted_payload,
                    most_voted_model="",
                    full_training=False,
                    n_estimations=1,
                    participants=get_participants(),
                    all_participants=get_participants(),
                ),
                state_attr_checks=[],
                most_voted_payload=1,
                exit_event=Event.DONE,
            )
        )

    def test_no_majority_event(self) -> None:
        """Test the no-majority event."""
        test_round = FreshModelResetRound(self.period_state, self.consensus_params)
        self._test_no_majority_event(test_round)


def test_period() -> None:
    """Test PeriodState."""

    participants = get_participants()
    period_count = 1
    period_setup_params: Dict = {}
    most_voted_randomness = 1
    estimates_hash = "test_hash"
    full_training = False
    n_estimations = 1

    period_state = PeriodState(
        db=StateDB(
            initial_period=period_count,
            initial_data=dict(
                participants=participants,
                period_setup_params=period_setup_params,
                most_voted_randomness=most_voted_randomness,
                most_voted_estimate=estimates_hash,
                full_training=full_training,
                n_estimations=n_estimations,
            ),
        )
    )

    assert period_state.participants == participants
    assert period_state.period_count == period_count
    assert period_state.most_voted_randomness == most_voted_randomness
    assert period_state.estimates_hash == estimates_hash
    assert period_state.full_training == full_training
    assert period_state.n_estimations == n_estimations
    assert period_state.is_most_voted_estimate_set is not None
