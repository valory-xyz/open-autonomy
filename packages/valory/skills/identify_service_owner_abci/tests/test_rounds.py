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

"""Tests for the IdentifyServiceOwnerAbciApp FSM."""

# pylint: disable=redefined-outer-name,too-few-public-methods

from unittest.mock import MagicMock

import pytest

from packages.valory.skills.identify_service_owner_abci.rounds import (
    Event,
    FinishedIdentifyServiceOwnerErrorRound,
    FinishedIdentifyServiceOwnerRound,
    IdentifyServiceOwnerAbciApp,
    IdentifyServiceOwnerRound,
    SynchronizedData,
)


@pytest.fixture
def abci_app() -> IdentifyServiceOwnerAbciApp:
    """Create an AbciApp instance."""
    synchronized_data = MagicMock(spec=SynchronizedData)
    logger = MagicMock()
    context = MagicMock()
    return IdentifyServiceOwnerAbciApp(synchronized_data, logger, context)


class TestAbciAppInitialization:
    """Test AbciApp initialization."""

    def test_initial_round_cls(self, abci_app: IdentifyServiceOwnerAbciApp) -> None:
        """Test initial round class."""
        assert abci_app.initial_round_cls is IdentifyServiceOwnerRound

    def test_initial_states(self, abci_app: IdentifyServiceOwnerAbciApp) -> None:
        """Test initial states."""
        assert abci_app.initial_states == {IdentifyServiceOwnerRound}

    def test_final_states(self, abci_app: IdentifyServiceOwnerAbciApp) -> None:
        """Test final states."""
        assert abci_app.final_states == {
            FinishedIdentifyServiceOwnerRound,
            FinishedIdentifyServiceOwnerErrorRound,
        }


class TestIdentifyServiceOwnerTransitions:
    """Test IdentifyServiceOwnerRound transitions."""

    @pytest.mark.parametrize(
        "event,expected_next",
        [
            (Event.DONE, FinishedIdentifyServiceOwnerRound),
            (Event.ERROR, FinishedIdentifyServiceOwnerErrorRound),
            (Event.NO_MAJORITY, IdentifyServiceOwnerRound),
            (Event.ROUND_TIMEOUT, IdentifyServiceOwnerRound),
        ],
    )
    def test_transitions(
        self,
        abci_app: IdentifyServiceOwnerAbciApp,
        event: Event,
        expected_next: type,
    ) -> None:
        """Test all transitions."""
        tf = abci_app.transition_function[IdentifyServiceOwnerRound]
        assert tf[event] == expected_next


class TestFinalStateTransitions:
    """Test final states have empty transitions."""

    @pytest.mark.parametrize(
        "final_round",
        [
            FinishedIdentifyServiceOwnerRound,
            FinishedIdentifyServiceOwnerErrorRound,
        ],
    )
    def test_empty_transitions(
        self,
        abci_app: IdentifyServiceOwnerAbciApp,
        final_round: type,
    ) -> None:
        """Test final states have empty transition functions."""
        assert abci_app.transition_function[final_round] == {}


class TestCrossPeriodPersistedKeys:
    """Test cross period persisted keys."""

    def test_keys(self, abci_app: IdentifyServiceOwnerAbciApp) -> None:
        """Test cross period persisted keys contain service_owner."""
        assert "service_owner" in abci_app.cross_period_persisted_keys


class TestDbConditions:
    """Test db pre/post conditions."""

    def test_pre_conditions(self, abci_app: IdentifyServiceOwnerAbciApp) -> None:
        """Test pre conditions are empty."""
        assert abci_app.db_pre_conditions[IdentifyServiceOwnerRound] == set()

    def test_post_conditions_success(
        self, abci_app: IdentifyServiceOwnerAbciApp
    ) -> None:
        """Test post conditions for success."""
        assert abci_app.db_post_conditions[FinishedIdentifyServiceOwnerRound] == {
            "service_owner"
        }

    def test_post_conditions_error(self, abci_app: IdentifyServiceOwnerAbciApp) -> None:
        """Test post conditions for error."""
        assert (
            abci_app.db_post_conditions[FinishedIdentifyServiceOwnerErrorRound] == set()
        )


class TestSynchronizedData:
    """Test SynchronizedData properties."""

    def test_service_owner(self) -> None:
        """Test service_owner property."""
        mock_db = MagicMock()
        mock_db.get_strict.return_value = "0xOwner"
        data = SynchronizedData(db=mock_db)
        assert data.service_owner == "0xOwner"
        mock_db.get_strict.assert_called_with("service_owner")
