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
from unittest import mock
from unittest.mock import MagicMock

import pytest

from packages.valory.skills.abstract_round_abci.base import AbstractRound
from packages.valory.skills.abstract_round_abci.models import (
    BaseParams,
    Requests,
    SharedState,
)


class TestSharedState:
    """Test SharedState(Model) class."""

    @mock.patch.object(SharedState, "_process_initial_round_cls")
    def test_initialization(self, *_):
        """Test the initialization of the shared state."""
        SharedState(name="", skill_context=MagicMock())

    @mock.patch.object(SharedState, "_process_initial_round_cls")
    def test_setup(self, *_):
        """Test setup method."""
        shared_state = SharedState(name="", skill_context=MagicMock())
        with mock.patch.object(shared_state.context, "params"):
            shared_state.setup()

    @mock.patch.object(SharedState, "_process_initial_round_cls")
    def test_period_state_negative_not_available(self, *_):
        """Test 'period_state' property getter, negative case (not available)."""
        shared_state = SharedState(name="", skill_context=MagicMock())
        with mock.patch.object(shared_state.context, "params"):
            shared_state.setup()
            with pytest.raises(ValueError, match="period_state not available"):
                shared_state.period_state

    @mock.patch.object(SharedState, "_process_initial_round_cls")
    def test_period_state_positive(self, *_):
        """Test 'period_state' property getter, negative case (not available)."""
        shared_state = SharedState(name="", skill_context=MagicMock())
        with mock.patch.object(shared_state.context, "params"):
            shared_state.setup()
            shared_state.period._round_results = [MagicMock()]
            shared_state.period_state

    def test_process_initial_round_cls_negative_field_not_set(self):
        """Test '_process_initial_round_cls', negative case (field not set)."""
        with pytest.raises(ValueError, match="'initial_round_cls' must be set"):
            SharedState._process_initial_round_cls(None)

    def test_process_initial_round_cls_negative_cannot_locate(self):
        """Test '_process_initial_round_cls', negative case (cannot locate class)."""
        with pytest.raises(ValueError, match="'initial_round_cls' not found"):
            SharedState._process_initial_round_cls("cannot.find.cls")

    def test_process_initial_round_cls_negative_not_a_class(self):
        """Test '_process_initial_round_cls', negative case (not a class)."""
        mock_obj = MagicMock()
        with mock.patch(
            "packages.valory.skills.abstract_round_abci.models.locate",
            return_value=mock_obj,
        ):
            with pytest.raises(
                ValueError, match=f"The object {mock_obj} is not a class"
            ):
                SharedState._process_initial_round_cls("any.dotted.path")

    def test_process_initial_round_cls_negative_not_subclass_of_abstract_round(self):
        """Test '_process_initial_round_cls', negative case (not subclass of AbstractRound)."""
        with mock.patch(
            "packages.valory.skills.abstract_round_abci.models.locate",
            return_value=MagicMock,
        ):
            with pytest.raises(
                ValueError,
                match=f"The class {MagicMock} is not an instance of {AbstractRound.__module__}.{AbstractRound.__name__}",
            ):
                SharedState._process_initial_round_cls("any.dotted.path")

    def test_process_initial_round_cls_positive(self):
        """Test '_process_initial_round_cls', positive case."""

        class ConcreteRound(AbstractRound):
            pass

        with mock.patch(
            "packages.valory.skills.abstract_round_abci.models.locate",
            return_value=ConcreteRound,
        ):
            SharedState._process_initial_round_cls("any.dotted.path")


def test_requests_model_initialization():
    """Test initialization of the 'Requests(Model)' class."""
    Requests(name="", skill_context=MagicMock())


def test_base_params_model_initialization():
    """Test initialization of the 'BaseParams(Model)' class."""
    BaseParams(
        name="",
        skill_context=MagicMock(),
        tendermint_url="",
        consensus=dict(max_participants=1),
    )
