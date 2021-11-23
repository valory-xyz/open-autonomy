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
from typing import Dict, FrozenSet, cast
from unittest import mock

import pytest

from packages.valory.skills.abstract_round_abci.base import (
    ABCIAppInternalError,
    AbstractRound,
    ConsensusParams,
    TransactionNotValidError,
)
from packages.valory.skills.apy_estimation.payloads import FetchingPayload
from packages.valory.skills.apy_estimation.rounds import (
    Event,
    PeriodState, CollectHistoryRound,
)

MAX_PARTICIPANTS: int = 4


def get_participants() -> FrozenSet[str]:
    """Participants"""
    return frozenset([f"agent_{i}" for i in range(MAX_PARTICIPANTS)])


def get_participant_to_fetching(
        participants: FrozenSet[str],
) -> Dict[str, FetchingPayload]:
    """participant_to_observations"""
    return {
        participant: FetchingPayload(sender=participant, history_hash='x0')
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
            test_round.process_payload(FetchingPayload(sender="sender", history_hash='x0'))

        with pytest.raises(
                TransactionNotValidError,
                match=re.escape(
                    "sender not in list of participants: ['agent_0', 'agent_1', 'agent_2', 'agent_3']"
                ),
        ):
            test_round.check_payload(FetchingPayload(sender="sender", history_hash='x0'))

        participant_to_fetching_payloads = get_participant_to_fetching(
            self.participants
        )

        first_payload = participant_to_fetching_payloads.pop(
            sorted(list(participant_to_fetching_payloads.keys()))[0]
        )
        test_round.process_payload(first_payload)

        assert test_round.collection[first_payload.sender] == first_payload
        assert test_round.end_block() == (None, None)
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
                FetchingPayload(sender=sorted(list(self.participants))[0], history_hash='x0')
            )

        for payload in participant_to_fetching_payloads.values():
            test_round.process_payload(payload)

        assert test_round.threshold_reached
        assert test_round.most_voted_payload == 'x0'

        actual_next_state = self.period_state.update(
            participant_to_observations=dict(
                get_participant_to_fetching(self.participants)
            ),
            most_voted_observation=test_round.most_voted_payload,
        )
        res = test_round.end_block()
        assert res is not None
        state, event = res
        assert (
                cast(PeriodState, state).participant_to_observations.keys()
                == cast(PeriodState, actual_next_state).participant_to_observations.keys()
        )
        assert event == Event.DONE

    def test_no_majority_event(self) -> None:
        """Test the no-majority event."""
        test_round = CollectHistoryRound(self.period_state, self.consensus_params)
        self._test_no_majority_event(test_round)
