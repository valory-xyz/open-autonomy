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

"""Test the behaviours.py module of the skill."""
from typing import Generator
from unittest.mock import MagicMock

import pytest

from packages.valory.skills.abstract_round_abci.behaviour_utils import BaseState
from packages.valory.skills.abstract_round_abci.behaviours import AbstractRoundBehaviour


class StateA(BaseState):
    """Dummy state behaviour."""

    state_id = "state_a"

    def async_act(self) -> Generator:
        """Dummy act method."""


class ConcreteRoundBehaviour(AbstractRoundBehaviour):
    """Concrete round behaviour."""

    initial_state_cls = StateA
    transition_function = {StateA: {"loop": StateA}}


class TestAbstractRoundBehaviour:
    """Test 'AbstractRoundBehaviour' class."""

    def setup(self) -> None:
        """Set up the tests."""
        self.behaviour = ConcreteRoundBehaviour(name="", skill_context=MagicMock())

    def test_setup(self) -> None:
        """Test 'setup' method."""
        self.behaviour.setup()

    def test_teardown(self) -> None:
        """Test 'teardown' method."""
        self.behaviour.teardown()

    def test_current_state_return_none(self) -> None:
        """Test 'current_state' property return None."""
        assert self.behaviour.current_state is None

    def test_register_state_matching_round_is_not_none_and_already_registered(
        self,
    ) -> None:
        """Test when '_register_state' called with state behaviour with matching round already used."""
        matching_round = MagicMock(round_id="round_1")
        state1 = MagicMock(matching_round=matching_round)
        state2 = MagicMock(matching_round=matching_round)
        self.behaviour._register_state(state1)
        with pytest.raises(ValueError, match="round id already used"):
            self.behaviour._register_state(state2)

    def test_act_current_state_name_is_none(self) -> None:
        """Test 'act' with current state None."""
        self.behaviour.current = None
        self.behaviour.act()

    def test_act_current_state_name_is_not_none_state_none(self) -> None:
        """Test 'act' with current state is not None, but associated state is None."""
        self.behaviour.current = MagicMock()
        self.behaviour.act()

    def test_act_current_state_final_state(self) -> None:
        """Test 'act' when ending up in a final state."""
        current_state_name = MagicMock()
        current_state_mock = MagicMock()
        current_state_mock.name = current_state_name
        current_state_mock.is_done = MagicMock(return_value=True)
        self.behaviour.current = current_state_name
        self.behaviour.register_final_state(current_state_name, current_state_mock)
        self.behaviour.act()

        assert self.behaviour.current is None

    def test_act_next_state_set(self) -> None:
        """Test 'act' when next state is set."""
        current_state_name = MagicMock()
        current_state_mock = MagicMock(name=current_state_name)
        current_state_mock.is_done = MagicMock(return_value=True)
        next_state_mock = MagicMock()
        self.behaviour.register_state(current_state_name, current_state_mock)
        self.behaviour.current = current_state_name
        self.behaviour._next_state = next_state_mock
        self.behaviour.act()

        assert self.behaviour.current == next_state_mock
        assert self.behaviour._next_state is None

    def test_act_make_transition(self) -> None:
        """Test 'act' when next state is set."""
        current_state_name = MagicMock()
        current_state_mock = MagicMock(name=current_state_name)
        current_state_mock.is_done = MagicMock(return_value=True)
        self.behaviour.register_state(current_state_name, current_state_mock)
        self.behaviour.current = current_state_name
        self.behaviour.act()

        assert self.behaviour.current is None

    def test_act_with_current_and_last_same(self) -> None:
        """Test 'act' with current_round==last_round."""
        round_name = "round"
        self.behaviour.context.state.period.current_round_id = round_name
        self.behaviour._last_round_id = round_name
        self.behaviour.current = MagicMock()
        self.behaviour.act()

    def test_act_with_current_and_last_different(self) -> None:
        """Test 'act' with current_round!=last_round."""
        round_name_1 = "round_1"
        round_name_2 = "round_2"
        self.behaviour.context.state.period.current_round_id = round_name_1
        self.behaviour._last_round_id = round_name_2
        self.behaviour.current = MagicMock()
        self.behaviour.act()

    def test_act_with_current_and_last_different_matching_round(
        self,
    ) -> None:
        """
        Test the 'act' method.

        Test 'act' with::
        - current_round!=last_round
        - current state has a matching round
        """
        round_name_1 = "round_1"
        round_name_2 = "round_2"
        self.behaviour.context.state.period.current_round_id = round_name_1
        self.behaviour._last_round_id = round_name_2

        # register current_state so we can stop it
        current_state_name = MagicMock()
        current_state_mock = MagicMock(
            name=current_state_name, matching_round=MagicMock(), state_id=MagicMock()
        )
        current_state_mock.is_done = MagicMock(return_value=True)
        self.behaviour.register_state(current_state_name, current_state_mock)
        self.behaviour.current = current_state_name

        self.behaviour.act()

        current_state_mock.stop.assert_called()
