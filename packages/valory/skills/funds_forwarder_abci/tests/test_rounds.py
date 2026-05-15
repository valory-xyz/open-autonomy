# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2026 Valory AG
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

"""Tests for the FundsForwarderAbciApp FSM."""

# pylint: disable=redefined-outer-name,too-few-public-methods

from typing import Dict, FrozenSet
from unittest.mock import MagicMock

import pytest

from packages.valory.skills.abstract_round_abci.test_tools.rounds import (
    BaseCollectSameUntilThresholdRoundTest,
)
from packages.valory.skills.funds_forwarder_abci.payloads import FundsForwarderPayload
from packages.valory.skills.funds_forwarder_abci.rounds import (
    Event,
    FinishedFundsForwarderNoTxRound,
    FinishedFundsForwarderWithTxRound,
    FundsForwarderAbciApp,
    FundsForwarderRound,
    SynchronizedData,
)


def _participant_to_payload(
    participants: FrozenSet[str], tx_submitter: str, tx_hash: str
) -> Dict[str, FundsForwarderPayload]:
    """Build participant-to-payload mapping with a populated transaction."""
    return {
        participant: FundsForwarderPayload(
            sender=participant,
            tx_submitter=tx_submitter,
            tx_hash=tx_hash,
        )
        for participant in participants
    }


def _participant_to_none_payload(
    participants: FrozenSet[str],
) -> Dict[str, FundsForwarderPayload]:
    """Build participant-to-payload mapping with no transaction needed."""
    return {
        participant: FundsForwarderPayload(
            sender=participant, tx_submitter=None, tx_hash=None
        )
        for participant in participants
    }


@pytest.fixture
def abci_app() -> FundsForwarderAbciApp:
    """Create an AbciApp instance."""
    synchronized_data = MagicMock(spec=SynchronizedData)
    logger = MagicMock()
    context = MagicMock()
    return FundsForwarderAbciApp(synchronized_data, logger, context)


class TestAbciAppInitialization:
    """Test AbciApp initialization."""

    def test_initial_round_cls(self, abci_app: FundsForwarderAbciApp) -> None:
        """Test initial round class."""
        assert abci_app.initial_round_cls is FundsForwarderRound

    def test_initial_states(self, abci_app: FundsForwarderAbciApp) -> None:
        """Test initial states."""
        assert abci_app.initial_states == {FundsForwarderRound}

    def test_final_states(self, abci_app: FundsForwarderAbciApp) -> None:
        """Test final states."""
        assert abci_app.final_states == {
            FinishedFundsForwarderWithTxRound,
            FinishedFundsForwarderNoTxRound,
        }


class TestFundsForwarderTransitions:
    """Test FundsForwarderRound transitions."""

    @pytest.mark.parametrize(
        "event,expected_next",
        [
            (Event.DONE, FinishedFundsForwarderWithTxRound),
            (Event.NONE, FinishedFundsForwarderNoTxRound),
            (Event.NO_MAJORITY, FundsForwarderRound),
            (Event.ROUND_TIMEOUT, FundsForwarderRound),
        ],
    )
    def test_transitions(
        self,
        abci_app: FundsForwarderAbciApp,
        event: Event,
        expected_next: type,
    ) -> None:
        """Test all transitions."""
        tf = abci_app.transition_function[FundsForwarderRound]
        assert tf[event] == expected_next


class TestFinalStateTransitions:
    """Test final states have empty transitions."""

    @pytest.mark.parametrize(
        "final_round",
        [
            FinishedFundsForwarderWithTxRound,
            FinishedFundsForwarderNoTxRound,
        ],
    )
    def test_empty_transitions(
        self,
        abci_app: FundsForwarderAbciApp,
        final_round: type,
    ) -> None:
        """Test final states have empty transition functions."""
        assert abci_app.transition_function[final_round] == {}


class TestDbConditions:
    """Test db pre/post conditions."""

    def test_pre_conditions(self, abci_app: FundsForwarderAbciApp) -> None:
        """Test pre conditions require service_owner."""
        assert abci_app.db_pre_conditions[FundsForwarderRound] == {"service_owner"}

    def test_post_conditions_with_tx(self, abci_app: FundsForwarderAbciApp) -> None:
        """Test post conditions for success with tx."""
        assert abci_app.db_post_conditions[FinishedFundsForwarderWithTxRound] == {
            "most_voted_tx_hash",
            "tx_submitter",
        }

    def test_post_conditions_no_tx(self, abci_app: FundsForwarderAbciApp) -> None:
        """Test post conditions for no tx."""
        assert abci_app.db_post_conditions[FinishedFundsForwarderNoTxRound] == set()


class TestSynchronizedData:
    """Test SynchronizedData properties."""

    @pytest.mark.parametrize(
        "prop,expected",
        [
            ("service_owner", "0xOwner"),
            ("most_voted_tx_hash", "0xHash"),
            ("tx_submitter", "funds_forwarder_round"),
        ],
    )
    def test_property(self, prop: str, expected: str) -> None:
        """Test SynchronizedData property delegates to db.get_strict."""
        mock_db = MagicMock()
        mock_db.get_strict.return_value = expected
        data = SynchronizedData(db=mock_db)
        assert getattr(data, prop) == expected


class TestFundsForwarderRound(BaseCollectSameUntilThresholdRoundTest):
    """Exercise FundsForwarderRound through the framework base test."""

    _synchronized_data_class = SynchronizedData
    _event_class = Event

    def test_done_event(self) -> None:
        """A threshold of identical populated payloads yields ``Event.DONE`` and writes the tx fields."""
        tx_submitter = "funds_forwarder_round"
        tx_hash = "0xDeadBeef"
        test_round = FundsForwarderRound(
            synchronized_data=self.synchronized_data,
            context=MagicMock(),
        )
        self._complete_run(
            self._test_round(
                test_round=test_round,
                round_payloads=_participant_to_payload(
                    self.participants, tx_submitter, tx_hash
                ),
                synchronized_data_update_fn=(
                    lambda data, _round: data.update(
                        synchronized_data_class=SynchronizedData,
                        tx_submitter=tx_submitter,
                        most_voted_tx_hash=tx_hash,
                    )
                ),
                synchronized_data_attr_checks=[
                    lambda data: data.tx_submitter,
                    lambda data: data.most_voted_tx_hash,
                ],
                most_voted_payload=tx_submitter,
                exit_event=Event.DONE,
            )
        )

    def test_none_event(self) -> None:
        """A threshold of identical all-``None`` payloads yields ``Event.NONE``."""
        test_round = FundsForwarderRound(
            synchronized_data=self.synchronized_data,
            context=MagicMock(),
        )
        self._complete_run(
            self._test_round(
                test_round=test_round,
                round_payloads=_participant_to_none_payload(self.participants),
                synchronized_data_update_fn=lambda data, _round: data,
                synchronized_data_attr_checks=[],
                most_voted_payload=None,
                exit_event=Event.NONE,
            )
        )

    def test_no_majority_event(self) -> None:
        """A round in which majority is impossible yields ``Event.NO_MAJORITY``."""
        test_round = FundsForwarderRound(
            synchronized_data=self.synchronized_data,
            context=MagicMock(),
        )
        self._test_no_majority_event(test_round)
