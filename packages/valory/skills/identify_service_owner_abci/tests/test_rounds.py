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

from typing import Dict, FrozenSet
from unittest.mock import MagicMock

import pytest

from packages.valory.skills.abstract_round_abci.test_tools.rounds import (
    BaseCollectSameUntilThresholdRoundTest,
)
from packages.valory.skills.identify_service_owner_abci.payloads import (
    IdentifyServiceOwnerPayload,
)
from packages.valory.skills.identify_service_owner_abci.rounds import (
    Event,
    FinishedIdentifyServiceOwnerErrorRound,
    FinishedIdentifyServiceOwnerRound,
    IdentifyServiceOwnerAbciApp,
    IdentifyServiceOwnerRound,
    SynchronizedData,
)


def _participant_to_payload(
    participants: FrozenSet[str], service_owner: str
) -> Dict[str, IdentifyServiceOwnerPayload]:
    """Build participant-to-payload mapping with the given resolved owner."""
    return {
        participant: IdentifyServiceOwnerPayload(
            sender=participant, service_owner=service_owner
        )
        for participant in participants
    }


def _participant_to_none_payload(
    participants: FrozenSet[str],
) -> Dict[str, IdentifyServiceOwnerPayload]:
    """Build participant-to-payload mapping with an unresolved owner."""
    return {
        participant: IdentifyServiceOwnerPayload(sender=participant, service_owner=None)
        for participant in participants
    }


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


class TestIdentifyServiceOwnerRound(BaseCollectSameUntilThresholdRoundTest):
    """Exercise IdentifyServiceOwnerRound through the framework base test."""

    _synchronized_data_class = SynchronizedData
    _event_class = Event

    def test_done_event(self) -> None:
        """A threshold of identical non-empty payloads yields ``Event.DONE`` and writes ``service_owner``."""
        owner = "0xResolvedServiceOwner"
        test_round = IdentifyServiceOwnerRound(
            synchronized_data=self.synchronized_data,
            context=MagicMock(),
        )
        self._complete_run(
            self._test_round(
                test_round=test_round,
                round_payloads=_participant_to_payload(self.participants, owner),
                synchronized_data_update_fn=(
                    lambda data, _round: data.update(
                        synchronized_data_class=SynchronizedData,
                        service_owner=owner,
                    )
                ),
                synchronized_data_attr_checks=[lambda data: data.service_owner],
                most_voted_payload=owner,
                exit_event=Event.DONE,
            )
        )

    def test_none_event(self) -> None:
        """A threshold of identical all-``None`` payloads yields ``Event.ERROR``."""
        test_round = IdentifyServiceOwnerRound(
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
                exit_event=Event.ERROR,
            )
        )

    def test_no_majority_event(self) -> None:
        """A round in which majority is impossible yields ``Event.NO_MAJORITY``."""
        test_round = IdentifyServiceOwnerRound(
            synchronized_data=self.synchronized_data,
            context=MagicMock(),
        )
        self._test_no_majority_event(test_round)
