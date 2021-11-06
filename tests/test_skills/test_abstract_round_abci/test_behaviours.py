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
from typing import Dict, Generator, Optional, Tuple
from unittest import mock
from unittest.mock import MagicMock

import pytest

from packages.valory.skills.abstract_round_abci.base import (
    ABCIAppInternalError,
    AbciApp,
    AbstractRound,
    BasePeriodState,
    BaseTxPayload,
    EventType,
    Period,
)
from packages.valory.skills.abstract_round_abci.behaviour_utils import BaseState
from packages.valory.skills.abstract_round_abci.behaviours import (
    AbstractRoundBehaviour,
    _MetaRoundBehaviour,
)


STATE_A_ID = "state_a"
STATE_B_ID = "state_b"
STATE_C_ID = "state_c"
ROUND_A_ID = "round_a"
ROUND_B_ID = "round_b"


class RoundA(AbstractRound):
    """Round A."""

    round_id = ROUND_A_ID
    allowed_tx_type = "payload_a"

    def end_block(self) -> Optional[Tuple[BasePeriodState, EventType]]:
        """End block."""

    def check_payload(self, payload: BaseTxPayload) -> None:
        """Check payload."""

    def process_payload(self, payload: BaseTxPayload) -> None:
        """Process payload."""


class RoundB(AbstractRound):
    """Round B."""

    round_id = ROUND_B_ID
    allowed_tx_type = "payload_b"

    def end_block(self) -> Optional[Tuple[BasePeriodState, EventType]]:
        """End block."""

    def check_payload(self, payload: BaseTxPayload) -> None:
        """Check payload."""

    def process_payload(self, payload: BaseTxPayload) -> None:
        """Process payload."""


class StateA(BaseState):
    """Dummy state behaviour."""

    state_id = STATE_A_ID
    matching_round = RoundA

    def async_act(self) -> Generator:
        """Dummy act method."""
        yield


class StateB(BaseState):
    """Dummy state behaviour."""

    state_id = STATE_B_ID
    matching_round = RoundB

    def async_act(self) -> Generator:
        """Dummy act method."""
        yield


class StateC(BaseState):
    """Dummy state behaviour."""

    state_id = STATE_C_ID
    matching_round = None

    def async_act(self) -> Generator:
        """Dummy act method."""
        yield


class ConcreteAbciApp(AbciApp):
    """Concrete ABCI App."""

    initial_round_cls = RoundA
    transition_function = {RoundA: {MagicMock(): RoundB}}
    event_to_timeout: Dict = {}


class ConcreteRoundBehaviour(AbstractRoundBehaviour):
    """Concrete round behaviour."""

    abci_app_cls = ConcreteAbciApp
    behaviour_states = {StateA, StateB}  # type: ignore
    initial_state_cls = StateA


class TestAbstractRoundBehaviour:
    """Test 'AbstractRoundBehaviour' class."""

    def setup(self) -> None:
        """Set up the tests."""
        self.period_mock = MagicMock()
        context_mock = MagicMock()
        context_mock.state.period = self.period_mock
        self.behaviour = ConcreteRoundBehaviour(name="", skill_context=context_mock)

    def test_setup(self) -> None:
        """Test 'setup' method."""
        self.behaviour.setup()

    def test_teardown(self) -> None:
        """Test 'teardown' method."""
        self.behaviour.teardown()

    def test_current_state_return_none(self) -> None:
        """Test 'current_state' property return None."""
        assert self.behaviour.current_state is None

    def test_act_current_state_name_is_none(self) -> None:
        """Test 'act' with current state None."""
        self.behaviour.current_state = None
        with mock.patch.object(self.behaviour, "_process_current_round"):
            self.behaviour.act()

    def test_get_state_id_to_state_mapping_negative(self) -> None:
        """Test classmethod '_get_state_id_to_state_mapping', negative case."""
        state_id = "state_id"
        state_1 = MagicMock(state_id=state_id)
        state_2 = MagicMock(state_id=state_id)

        with pytest.raises(
            ValueError,
            match=f"cannot have two states with the same id; got {state_2} and {state_1} both with id '{state_id}'",
        ):
            with mock.patch(
                "packages.valory.skills.abstract_round_abci.behaviours._MetaRoundBehaviour._check_consistency"
            ):

                class MyRoundBehaviour(AbstractRoundBehaviour):
                    abci_app_cls = MagicMock
                    behaviour_states = [state_1, state_2]  # type: ignore
                    initial_state_cls = MagicMock()

                MyRoundBehaviour(name=MagicMock(), skill_context=MagicMock())

    def test_get_round_to_state_mapping_two_states_same_round(self) -> None:
        """Test classmethod '_get_round_to_state_mapping' when two different states point to the same round."""
        state_id_1 = "state_id_1"
        state_id_2 = "state_id_2"
        round_cls = RoundA
        round_id = round_cls.round_id
        state_1 = MagicMock(state_id=state_id_1, matching_round=round_cls)
        state_2 = MagicMock(state_id=state_id_2, matching_round=round_cls)

        with pytest.raises(
            ValueError,
            match=f"the states '{state_id_2}' and '{state_id_1}' point to the same matching round '{round_id}'",
        ):
            with mock.patch(
                "packages.valory.skills.abstract_round_abci.behaviours._MetaRoundBehaviour._check_consistency"
            ):

                class MyRoundBehaviour(AbstractRoundBehaviour):
                    abci_app_cls = ConcreteAbciApp
                    behaviour_states = [StateC, state_1, state_2]  # type: ignore
                    initial_state_cls = StateC

                MyRoundBehaviour(name=MagicMock(), skill_context=MagicMock())

    def test_check_state_id_uniqueness_negative(self) -> None:
        """Test metaclass method '_check_consistency', negative case."""
        state_id = "state_id"
        state_1_cls_name = "State1"
        state_2_cls_name = "State2"
        state_1 = MagicMock(state_id=state_id, __name__=state_1_cls_name)
        state_2 = MagicMock(state_id=state_id, __name__=state_2_cls_name)

        with pytest.raises(
            ABCIAppInternalError,
            match=fr"states \['{state_1_cls_name}', '{state_2_cls_name}'\] have the same state id '{state_id}'",
        ):

            class MyRoundBehaviour(AbstractRoundBehaviour):
                abci_app_cls = MagicMock
                behaviour_states = [state_1, state_2]  # type: ignore
                initial_state_cls = MagicMock()

    def test_check_consistency_two_states_same_round(self) -> None:
        """Test metaclass method '_check_consistency' when two different states point to the same round."""
        state_id_1 = "state_id_1"
        state_id_2 = "state_id_2"
        round_cls = RoundA
        round_id = round_cls.round_id
        state_1 = MagicMock(state_id=state_id_1, matching_round=round_cls)
        state_2 = MagicMock(state_id=state_id_2, matching_round=round_cls)

        with pytest.raises(
            ABCIAppInternalError,
            match=rf"internal error: states \['{state_id_1}', '{state_id_2}'\] have the same matching round '{round_id}'",
        ):

            class MyRoundBehaviour(AbstractRoundBehaviour):
                abci_app_cls = ConcreteAbciApp
                behaviour_states = [StateC, state_1, state_2]  # type: ignore
                initial_state_cls = StateC

    def test_get_round_to_state_mapping_matching_round_none(self) -> None:
        """Test classmethod '_get_round_to_state_mapping' when a state has matching round none."""

        class MyRoundBehaviour(AbstractRoundBehaviour):
            abci_app_cls = ConcreteAbciApp
            behaviour_states = [StateA, StateB, StateC]  # type: ignore
            initial_state_cls = StateA

    def test_check_initial_state_in_set_of_states_negative_case(self) -> None:
        """Test classmethod '_check_initial_state_in_set_of_states' when initial state is NOT in the set."""
        state_1 = MagicMock(state_id="state_id_1", matching_round=None)
        state_2 = MagicMock(state_id="state_id_2", matching_round=None)

        with pytest.raises(
            ABCIAppInternalError,
            match="initial state state_id_2 is not in the set of states",
        ):

            class MyRoundBehaviour(AbstractRoundBehaviour):
                abci_app_cls = ConcreteAbciApp
                behaviour_states = [state_1]  # type: ignore
                initial_state_cls = state_2

    def test_act_no_round_change(self) -> None:
        """Test the 'act' method of the behaviour, with no round change."""
        self.period_mock.current_round = RoundA(MagicMock(), MagicMock())
        self.period_mock.current_round_height = 0

        # check that after setup(), current state is initial state
        self.behaviour.setup()
        assert isinstance(self.behaviour.current_state, StateA)

        # check that after act(), current state is initial state
        self.behaviour.act()
        assert isinstance(self.behaviour.current_state, StateA)

        # check that once the flag done is set, tries to schedule
        # the next state behaviour, but without success
        self.behaviour.current_state.set_done()
        self.behaviour.act()
        assert self.behaviour.current_state is None

    def test_act_with_round_change(self) -> None:
        """Test the 'act' method of the behaviour, with round change."""
        self.period_mock.current_round = RoundA(MagicMock(), MagicMock())
        self.period_mock.current_round_height = 0

        # check that after setup(), current state is initial state
        self.behaviour.setup()
        assert isinstance(self.behaviour.current_state, StateA)

        # check that after act(), current state is initial state
        self.behaviour.act()
        assert isinstance(self.behaviour.current_state, StateA)

        # change the round
        self.period_mock.current_round = RoundB(MagicMock(), MagicMock())
        self.period_mock.current_round_height = (
            self.period_mock.current_round_height + 1
        )

        # check that if the round is changed, the behaviour transition is taken
        self.behaviour.act()
        assert isinstance(self.behaviour.current_state, StateB)

    def test_act_with_round_change_but_matching_round_current_state_is_none(
        self,
    ) -> None:
        """Test 'act', with round change but with matching round of current state equal to None."""
        self.period_mock.current_round = RoundA(MagicMock(), MagicMock())
        self.period_mock.current_round_height = 0

        # instantiate state with matching round = None
        self.behaviour.current_state = self.behaviour.instantiate_state_cls(StateC)  # type: ignore

        # check that after act(), current state is same state
        self.behaviour.act()
        assert isinstance(self.behaviour.current_state, StateC)

        # check that state does not change until done flag is set
        self.behaviour.act()
        assert isinstance(self.behaviour.current_state, StateC)

        # after behaviour is done, the transition can be taken
        self.behaviour.current_state.set_done()
        # the next act schedules the next state
        self.behaviour.act()
        assert isinstance(self.behaviour.current_state, StateA)

    def test_act_with_round_change_matching_round_current_state_is_none_and_round_change(
        self,
    ) -> None:
        """Test 'act', with round change but with matching round None and round change."""
        self.period_mock.current_round = RoundA(MagicMock(), MagicMock())
        self.period_mock.current_round_height = 0

        # instantiate state with matching round = None
        self.behaviour.current_state = self.behaviour.instantiate_state_cls(StateC)  # type: ignore

        # check that after act(), current state is same state
        self.behaviour.act()
        assert isinstance(self.behaviour.current_state, StateC)

        # check that round does not change until done flag is set
        self.behaviour.act()
        assert isinstance(self.behaviour.current_state, StateC)

        # change the round
        self.period_mock.current_round = RoundB(MagicMock(), MagicMock())
        self.period_mock.current_round_height = (
            self.period_mock.current_round_height + 1
        )

        # check that even if round changes behaviour stays in the same state
        self.behaviour.act()
        assert isinstance(self.behaviour.current_state, StateC)

        # after behaviour is done, the transition can be taken
        self.behaviour.current_state.set_done()
        # the next act schedules the next state
        self.behaviour.act()
        assert isinstance(self.behaviour.current_state, StateB)

    def test_act_with_round_change_after_current_state_is_none(self) -> None:
        """Test the 'act' method of the behaviour, with round change, after cur state is none."""
        self.period_mock.current_round = RoundA(MagicMock(), MagicMock())
        self.period_mock.current_round_height = 0

        # instantiate state
        self.behaviour.current_state = self.behaviour.instantiate_state_cls(StateA)  # type: ignore

        # check that after act(), current state is same state
        self.behaviour.act()
        assert isinstance(self.behaviour.current_state, StateA)

        # check that after the state is done, current state is None
        self.behaviour.current_state.set_done()
        self.behaviour.act()
        assert self.behaviour.current_state is None

        # change the round
        self.period_mock.current_round = RoundB(MagicMock(), MagicMock())
        self.period_mock.current_round_height = (
            self.period_mock.current_round_height + 1
        )

        # check that if the round is changed, the behaviour transition is taken
        self.behaviour.act()
        assert isinstance(self.behaviour.current_state, StateB)


def test_meta_round_behaviour_when_instance_not_subclass_of_abstract_round() -> None:
    """Test instantiation of meta class when instance not a subclass of abstract round."""

    class MyRoundBeahviour(metaclass=_MetaRoundBehaviour):
        pass


def test_abstract_round_behaviour_instantiation_without_attributes_raises_error() -> None:
    """Test that definition of concrete subclass of AbstractRoundBehavior without attributes raises error."""
    with pytest.raises(ABCIAppInternalError):

        class MyRoundBehaviour(AbstractRoundBehaviour):
            pass


def test_abstract_round_behaviour_matching_rounds_not_covered() -> None:
    """Test that definition of concrete subclass of AbstractRoundBehavior when matching round not covered."""
    with pytest.raises(ABCIAppInternalError):

        class MyRoundBehaviour(AbstractRoundBehaviour):
            abci_app_cls = ConcreteAbciApp
            behaviour_states = {StateA}  # type: ignore
            initial_state_cls = StateA


def test_self_loops_in_abci_app_reinstantiate_behaviour_state() -> None:
    """Test that a self-loop transition in the AbciApp will trigger a transition in the round behaviour."""
    event = MagicMock()

    class AbciAppTest(AbciApp):
        initial_round_cls = RoundA
        transition_function = {RoundA: {event: RoundA}}

    class RoundBehaviour(AbstractRoundBehaviour):
        abci_app_cls = AbciAppTest
        behaviour_states = {StateA}  # type: ignore
        initial_state_cls = StateA

    period = Period(AbciAppTest)
    period.setup(MagicMock(), MagicMock(), MagicMock())
    context_mock = MagicMock()
    context_mock.state.period = period
    behaviour = RoundBehaviour(name="", skill_context=context_mock)
    behaviour.setup()

    state_1 = behaviour.current_state
    assert isinstance(state_1, StateA)

    period.abci_app.process_event(event)

    behaviour.act()
    state_2 = behaviour.current_state
    assert isinstance(state_2, StateA)
    assert id(state_1) != id(state_2)
    assert state_1 != state_2
