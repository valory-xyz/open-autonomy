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

"""Test the models.py module of the skill."""
from typing import Any, Optional, Tuple
from unittest import mock
from unittest.mock import MagicMock

import pytest

from packages.valory.skills.abstract_round_abci.base import (
    AbciApp,
    AbstractRound,
    BasePeriodState,
)
from packages.valory.skills.abstract_round_abci.models import (
    BaseParams,
    Requests,
    SharedState,
)

from tests.test_skills.test_abstract_round_abci.test_base import AbciAppTest


class ConcreteRound(AbstractRound):
    """A ConcreteRound for testing purposes."""

    def end_block(self) -> Optional[Tuple[BasePeriodState, "AbstractRound"]]:
        """Handle the end of the block."""


class TestSharedState:
    """Test SharedState(Model) class."""

    @mock.patch.object(SharedState, "_process_abci_app_cls")
    def test_initialization(self, *_: Any) -> None:
        """Test the initialization of the shared state."""
        SharedState(abci_app_cls=MagicMock(), name="", skill_context=MagicMock())

    @mock.patch.object(SharedState, "_process_abci_app_cls")
    def test_setup(self, *_: Any) -> None:
        """Test setup method."""
        shared_state = SharedState(
            abci_app_cls=MagicMock, name="", skill_context=MagicMock()
        )
        with mock.patch.object(shared_state.context, "params"):
            shared_state.setup()

    @mock.patch.object(SharedState, "_process_abci_app_cls")
    def test_period_state_negative_not_available(self, *_: Any) -> None:
        """Test 'period_state' property getter, negative case (not available)."""
        shared_state = SharedState(
            abci_app_cls=AbciAppTest, name="", skill_context=MagicMock()
        )
        with mock.patch.object(shared_state.context, "params"):
            shared_state.setup()
            shared_state.period.abci_app.latest_result = None
            with pytest.raises(ValueError, match="period_state not available"):
                shared_state.period_state

    @mock.patch.object(SharedState, "_process_abci_app_cls")
    def test_period_state_positive(self, *_: Any) -> None:
        """Test 'period_state' property getter, negative case (not available)."""
        shared_state = SharedState(
            abci_app_cls=AbciAppTest, name="", skill_context=MagicMock()
        )
        with mock.patch.object(shared_state.context, "params"):
            shared_state.setup()
            shared_state.period._round_results = [MagicMock()]
            shared_state.period_state

    def test_process_abci_app_cls_negative_not_a_class(self) -> None:
        """Test '_process_abci_app_cls', negative case (not a class)."""
        mock_obj = MagicMock()
        with pytest.raises(ValueError, match=f"The object {mock_obj} is not a class"):
            SharedState._process_abci_app_cls(mock_obj)

    def test_process_abci_app_cls_negative_not_subclass_of_abstract_round(
        self,
    ) -> None:
        """Test '_process_abci_app_cls', negative case (not subclass of AbstractRound)."""
        with pytest.raises(
            ValueError,
            match=f"The class {MagicMock} is not an instance of {AbciApp.__module__}.{AbciApp.__name__}",
        ):
            SharedState._process_abci_app_cls(MagicMock)

    def test_process_abci_app_cls_positive(self) -> None:
        """Test '_process_abci_app_cls', positive case."""

        SharedState._process_abci_app_cls(AbciAppTest)


def test_requests_model_initialization() -> None:
    """Test initialization of the 'Requests(Model)' class."""
    Requests(name="", skill_context=MagicMock())


def test_base_params_model_initialization() -> None:
    """Test initialization of the 'BaseParams(Model)' class."""
    BaseParams(
        name="",
        skill_context=MagicMock(),
        tendermint_url="",
        consensus=dict(max_participants=1),
    )
