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
from typing import FrozenSet, Mapping, cast  # noqa : F401
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
    StrategyEvaluationRound,
    TransactionHashBaseRound,
    TransactionSendBaseRound,
    TransactionSignatureBaseRound,
    TransactionValidationBaseRound,
)
from packages.valory.skills.price_estimation_abci.payloads import FinalizationTxPayload

from tests.test_skills.test_price_estimation_abci.test_rounds import (
    get_participant_to_signature,
    get_participant_to_tx_hash,
    get_participant_to_votes,
)


MAX_PARTICIPANTS: int = 4


def get_participants() -> FrozenSet[str]:
    """Returns test value for participants"""
    return frozenset([f"agent_{i}" for i in range(MAX_PARTICIPANTS)])


def get_participant_to_strategy(
    participants: FrozenSet[str],
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
        self._test_no_majority_event(test_round)
        assert test_round.end_block() is None

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
        self._test_no_majority_event(test_round)
        assert test_round.end_block() is None

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


class TestTransactionSendBaseRound(BaseRoundTestClass):
    """Test TransactionSendBaseRound."""

    def test_run(
        self,
    ) -> None:
        """Run tests."""

        test_round = TransactionSendBaseRound(
            self.period_state.update(
                most_voted_keeper_address="agent_0",
            ),
            self.consensus_params,
        )

        assert test_round.end_block() is None
        test_round.process_payload(
            FinalizationTxPayload(sender="agent_0", tx_hash="tx_hash")
        )

        actual_next_state = self.period_state.update(
            final_tx_hash=test_round.keeper_payload
        )

        res = test_round.end_block()
        assert res is not None
        state, event = res
        assert (
            cast(PeriodState, state).final_tx_hash
            == cast(PeriodState, actual_next_state).final_tx_hash
        )
        assert event == Event.DONE


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
        self._test_no_majority_event(test_round)
        assert test_round.end_block() is None

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

    def test_negative_votes(
        self,
    ) -> None:
        """Run tests."""
        test_round = TransactionValidationBaseRound(
            self.period_state, self.consensus_params
        )
        (sender, first_payload), *payloads = get_participant_to_votes(
            self.participants, False
        ).items()

        test_round.process_payload(first_payload)
        assert not test_round.negative_vote_threshold_reached
        self._test_no_majority_event(test_round)
        assert test_round.end_block() is None

        for _, payload in payloads:
            test_round.process_payload(payload)

        assert test_round.negative_vote_threshold_reached

        res = test_round.end_block()
        assert res is not None

        _, event = res
        assert event == Event.EXIT


class TestStrategyEvaluationRound(BaseRoundTestClass):
    """Test StrategyEvaluationRound"""

    def test_run(
        self,
    ) -> None:
        """Run tests."""
        test_round = StrategyEvaluationRound(self.period_state, self.consensus_params)

        (sender, first_payload), *payloads = get_participant_to_strategy(
            self.participants
        ).items()

        test_round.process_payload(first_payload)
        mock_obj = mock.patch.object(
            StrategyEvaluationPayload, "strategy", return_value="strategy"
        )

        with mock_obj:
            assert not test_round.threshold_reached
            self._test_no_majority_event(test_round)
            assert test_round.end_block() is None

        for _, payload in payloads:
            test_round.process_payload(payload)

        with mock_obj:
            assert test_round.threshold_reached
            actual_next_state = self.period_state.update(
                participant_to_strategy=get_participant_to_strategy(self.participants),
                most_voted_strategy=test_round.most_voted_payload,
            )

        with mock_obj:
            res = test_round.end_block()

        assert res is not None
        state, event = res
        assert (
            cast(PeriodState, state).participant_to_strategy.keys()
            == cast(PeriodState, actual_next_state).participant_to_strategy.keys()
        )
        assert event == Event.RESET_TIMEOUT
