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

"""Test the base.py module of the skill."""
import logging  # noqa: F401
import re
from typing import Dict, FrozenSet, Optional, cast
from unittest import mock

import pytest

from packages.valory.skills.abstract_round_abci.base import (
    ABCIAppInternalError,
    AbstractRound,
    ConsensusParams,
    TransactionNotValidError,
)
from packages.valory.skills.apy_estimation.payloads import (
    FetchingPayload,
    RegistrationPayload,
)
from packages.valory.skills.apy_estimation.rounds import (
    CollectHistoryRound,
    Event,
    PeriodState,
    RegistrationRound,
)


MAX_PARTICIPANTS: int = 4


def get_participants() -> FrozenSet[str]:
    """Participants"""
    return frozenset([f"agent_{i}" for i in range(MAX_PARTICIPANTS)])


def get_participant_to_fetching(
    participants: FrozenSet[str],
) -> Dict[str, FetchingPayload]:
    """participant_to_fetching"""
    return {
        participant: FetchingPayload(sender=participant, history_hash="x0")
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
        cls.period_state = PeriodState(participants=cls.participants)
        cls.consensus_params = ConsensusParams(max_participants=MAX_PARTICIPANTS)

    @staticmethod
    def _test_no_majority_event(round_obj: AbstractRound) -> None:
        """Test the NO_MAJORITY event."""
        with mock.patch.object(round_obj, "is_majority_possible", return_value=False):
            result = round_obj.end_block()
            assert result is not None
            state, event = result
            assert event == Event.NO_MAJORITY


class TestRegistrationRound(BaseRoundTestClass):
    """Test RegistrationRound."""

    def test_run_default(
        self,
    ) -> None:
        """Run test."""

        test_round = RegistrationRound(
            state=self.period_state, consensus_params=self.consensus_params
        )
        self._run_with_round(test_round, Event.DONE, 1)

    def _run_with_round(
        self,
        test_round: RegistrationRound,
        expected_event: Optional[Event] = None,
        confirmations: Optional[int] = None,
    ) -> None:
        """Run with given round."""
        registration_payloads = [
            RegistrationPayload(sender=participant) for participant in self.participants
        ]

        first_participant = registration_payloads.pop(0)
        test_round.process_payload(first_participant)
        assert test_round.collection == {
            first_participant.sender,
        }
        assert test_round.end_block() is None

        with pytest.raises(
            TransactionNotValidError,
            match=f"payload attribute sender with value {first_participant.sender} "
            "has already been added for round: registration",
        ):
            test_round.check_payload(first_participant)

        with pytest.raises(
            ABCIAppInternalError,
            match=f"payload attribute sender with value {first_participant.sender} "
            "has already been added for round: registration",
        ):
            test_round.process_payload(first_participant)

        for participant_payload in registration_payloads:
            test_round.process_payload(participant_payload)
        assert test_round.collection_threshold_reached

        if confirmations is not None:
            test_round.block_confirmations = confirmations

        actual_next_state = PeriodState(participants=test_round.collection)

        res = test_round.end_block()

        if expected_event is None:
            assert res is expected_event
        else:
            assert res is not None
            state, event = res
            assert (
                cast(PeriodState, state).participants
                == cast(PeriodState, actual_next_state).participants
            )
            assert event == expected_event


class TestCollectHistoryRound(BaseRoundTestClass):
    """Test `CollectHistoryRound`."""

    def test_run(
        self,
    ) -> None:
        """Runs test."""

        test_round = CollectHistoryRound(
            state=self.period_state, consensus_params=self.consensus_params
        )

        with pytest.raises(
            ABCIAppInternalError,
            match=re.escape(
                "internal error: sender not in list of participants: ['agent_0', 'agent_1', 'agent_2', 'agent_3']"
            ),
        ):
            test_round.process_payload(
                FetchingPayload(sender="sender", history_hash="x0")
            )

        with pytest.raises(
            TransactionNotValidError,
            match=re.escape(
                "sender not in list of participants: ['agent_0', 'agent_1', 'agent_2', 'agent_3']"
            ),
        ):
            test_round.check_payload(
                FetchingPayload(sender="sender", history_hash="x0")
            )

        participant_to_fetching_payloads = get_participant_to_fetching(
            self.participants
        )

        first_payload = participant_to_fetching_payloads.pop(
            sorted(list(participant_to_fetching_payloads.keys()))[0]
        )
        test_round.process_payload(first_payload)

        assert test_round.collection[first_payload.sender] == first_payload
        assert test_round.end_block() is None
        assert not test_round.threshold_reached

        with pytest.raises(
            ABCIAppInternalError, match="internal error: not enough votes"
        ):
            _ = test_round.most_voted_payload

        with pytest.raises(
            ABCIAppInternalError,
            match="internal error: sender agent_0 has already sent value for round: collect_history",
        ):
            test_round.process_payload(first_payload)

        with pytest.raises(
            TransactionNotValidError,
            match="sender agent_0 has already sent value for round: collect_history",
        ):
            test_round.check_payload(
                FetchingPayload(
                    sender=sorted(list(self.participants))[0], history_hash="x0"
                )
            )

        for payload in participant_to_fetching_payloads.values():
            test_round.process_payload(payload)

        assert test_round.threshold_reached
        assert test_round.most_voted_payload == "x0"

        actual_next_state = self.period_state
        res = test_round.end_block()
        assert res is not None
        state, event = res
        assert state == actual_next_state
        assert event == Event.DONE

    def test_no_majority_event(self) -> None:
        """Test the no-majority event."""
        test_round = CollectHistoryRound(self.period_state, self.consensus_params)
        self._test_no_majority_event(test_round)


class TestTransformRound(BaseRoundTestClass):
    """Test `TransformRound`."""

    def test_run(self) -> None:
        """Runs test."""
        # TODO
        assert True


class TestPreprocessRound(BaseRoundTestClass):
    """Test `PreprocessRound`."""

    def test_run(self) -> None:
        """Runs test."""
        # TODO
        assert True


class TestOptimizeRound(BaseRoundTestClass):
    """Test `OptimizeRound`."""

    def test_run(self) -> None:
        """Runs test."""
        # TODO
        assert True


class TestTrainRound(BaseRoundTestClass):
    """Test `TrainRound`."""

    def test_run(self) -> None:
        """Runs test."""
        # TODO
        assert True


class TestTestRound(BaseRoundTestClass):
    """Test `TestRound`."""

    def test_run(self) -> None:
        """Runs test."""
        # TODO
        assert True


class TestEstimateRound(BaseRoundTestClass):
    """Test `EstimateRound`."""

    def test_run(self) -> None:
        """Runs test."""
        # TODO
        assert True
