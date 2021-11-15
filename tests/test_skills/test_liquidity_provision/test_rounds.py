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

"""Tests for rounds.py file in valory/liquidity_provision."""

from types import MappingProxyType
from typing import AbstractSet, FrozenSet, List, Mapping, cast  # noqa : F401
from unittest import mock

import pytest

from packages.valory.skills.abstract_round_abci.base import (
    ABCIAppInternalError,
    AbstractRound,
    ConsensusParams,
)
from packages.valory.skills.liquidity_provision.payloads import (
    StrategyEvaluationPayload,
)
from packages.valory.skills.liquidity_provision.rounds import (  # noqa: F401
    Event,
    PeriodState,
    TransactionHashBaseRound,
    TransactionSignatureBaseRound,
    TransactionValidationBaseRound,
)

from tests.test_skills.test_price_estimation_abci.test_rounds import (
    get_participant_to_signature,
    get_participant_to_tx_hash,
    get_participant_to_votes,
)


MAX_PARTICIPANTS: int = 4


def get_participants() -> AbstractSet[str]:
    """Returns test value for participants"""
    return set([f"agent_{i}" for i in range(MAX_PARTICIPANTS)])


def get_participant_to_strategy(
    participants: List[str],
) -> Mapping[str, StrategyEvaluationPayload]:
    """Returns test value for participant_to_strategy"""
    return dict(
        [
            (participant, StrategyEvaluationPayload(sender=participant, strategy={}))
            for participant in participants
        ]
    )


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

        cls.participants = get_participants()  # type: ignore
        cls.period_state = PeriodState(participants=cls.participants)
        cls.consensus_params = ConsensusParams(max_participants=MAX_PARTICIPANTS)

    def _test_no_majority_event(self, round_obj: AbstractRound) -> None:
        """Test the NO_MAJORITY event."""
        with mock.patch.object(round_obj, "is_majority_possible", return_value=False):
            result = round_obj.end_block()
            assert result is not None
            _, event = result
            assert event == Event.NO_MAJORITY


class TestTransactionHashBaseRound(BaseRoundTestClass):
    """Test TransactionHashBaseRound"""

    def test_run(
        self,
    ) -> None:
        """Run tests."""

        test_round = TransactionHashBaseRound(self.period_state, self.consensus_params)
        (sender, first_payload), *payloads = get_participant_to_tx_hash(
            self.participants
        ).items()

        test_round.process_payload(first_payload)
        assert not test_round.threshold_reached
        with pytest.raises(ABCIAppInternalError, match="not enough votes"):
            _ = test_round.most_voted_payload

        for _, payload in payloads:
            test_round.process_payload(payload)

        assert test_round.threshold_reached
        assert test_round.most_voted_payload == "tx_hash"

        actual_next_state = self.period_state.update(
            participant_to_tx_hash=MappingProxyType(
                get_participant_to_tx_hash(self.participants)
            ),
            most_voted_tx_hash=test_round.most_voted_payload,
        )

        res = test_round.end_block()
        assert res is not None
        state, event = res
        assert (
            cast(PeriodState, state).participant_to_tx_hash.keys()
            == cast(PeriodState, actual_next_state).participant_to_tx_hash.keys()
        )
        assert event == Event.DONE


class TestTransactionSignatureBaseRound(BaseRoundTestClass):
    """Test TransactionSignatureBaseRound."""

    def test_run(
        self,
    ) -> None:
        """Run tests."""
        test_round = TransactionSignatureBaseRound(
            self.period_state, self.consensus_params
        )
        (sender, first_payload), *payloads = get_participant_to_signature(
            self.participants
        ).items()

        test_round.process_payload(first_payload)
        assert not test_round.collection_threshold_reached

        for _, payload in payloads:
            test_round.process_payload(payload)

        assert test_round.collection_threshold_reached
        actual_next_state = self.period_state.update(
            participant_to_signature=MappingProxyType(
                get_participant_to_signature(self.participants)
            ),
        )

        res = test_round.end_block()
        assert res is not None
        state, event = res
        assert (
            cast(PeriodState, state).participant_to_signature.keys()
            == cast(PeriodState, actual_next_state).participant_to_signature.keys()
        )
        assert event == Event.DONE


@pytest.mark.skip
class TestTransactionSendBaseRound(BaseRoundTestClass):
    """Test TransactionSendBaseRound."""

    def test_run(
        self,
    ) -> None:
        """Run tests."""


class TestTransactionValidationBaseRound(BaseRoundTestClass):
    """Test TransactionValidationBaseRound"""

    def test_run(
        self,
    ) -> None:
        """Run tests."""
        test_round = TransactionValidationBaseRound(
            self.period_state, self.consensus_params
        )
        (sender, first_payload), *payloads = get_participant_to_votes(
            self.participants
        ).items()

        test_round.process_payload(first_payload)
        assert not test_round.positive_vote_threshold_reached

        for _, payload in payloads:
            test_round.process_payload(payload)

        assert test_round.positive_vote_threshold_reached
        actual_next_state = self.period_state.update(
            participant_to_votes=MappingProxyType(
                get_participant_to_votes(self.participants)
            ),
        )

        res = test_round.end_block()
        assert res is not None
        state, event = res
        assert (
            cast(PeriodState, state).participant_to_votes.keys()
            == cast(PeriodState, actual_next_state).participant_to_votes.keys()
        )
        assert event == Event.DONE
