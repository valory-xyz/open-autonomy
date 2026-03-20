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

from unittest.mock import MagicMock

import pytest

from packages.valory.skills.funds_forwarder_abci.rounds import (
    Event,
    FinishedFundsForwarderNoTxRound,
    FinishedFundsForwarderWithTxRound,
    FundsForwarderAbciApp,
    FundsForwarderRound,
    SynchronizedData,
)


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

    def test_service_owner(self) -> None:
        """Test service_owner property."""
        mock_db = MagicMock()
        mock_db.get_strict.return_value = "0xOwner"
        data = SynchronizedData(db=mock_db)
        assert data.service_owner == "0xOwner"

    def test_most_voted_tx_hash(self) -> None:
        """Test most_voted_tx_hash property."""
        mock_db = MagicMock()
        mock_db.get_strict.return_value = "0xHash"
        data = SynchronizedData(db=mock_db)
        assert data.most_voted_tx_hash == "0xHash"

    def test_tx_submitter(self) -> None:
        """Test tx_submitter property."""
        mock_db = MagicMock()
        mock_db.get_strict.return_value = "funds_forwarder_round"
        data = SynchronizedData(db=mock_db)
        assert data.tx_submitter == "funds_forwarder_round"
