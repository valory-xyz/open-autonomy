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

"""This module contains the behaviours for the 'abstract_round_abci' skill."""
from typing import Dict, Optional, Type

from aea.exceptions import enforce
from aea.skills.behaviours import FSMBehaviour

from packages.valory.skills.abstract_round_abci.behaviour_utils import BaseState


State = Type[BaseState]
Action = Optional[str]
TransitionFunction = Dict[State, Dict[Action, State]]


class AbstractRoundBehaviour(FSMBehaviour):
    """This behaviour implements an abstract round."""

    initial_state_cls: State
    transition_function: TransitionFunction = {}

    def setup(self) -> None:
        """Set up the behaviour."""
        self._register_states(self.transition_function)

    def teardown(self) -> None:
        """Tear down the behaviour"""

    def _register_states(self, transition_function: TransitionFunction) -> None:
        """Register a list of states."""
        enforce(
            len(transition_function) != 0,
            "empty list of state classes",
            exception_class=ValueError,
        )
        for state, outgoing_transitions in transition_function.items():
            self._register_state_if_not_registered(
                state, initial=state == self.initial_state_cls
            )
            for event, next_state in outgoing_transitions.items():
                self._register_state_if_not_registered(
                    next_state, initial=next_state == self.initial_state_cls
                )
                self.register_transition(state.state_id, next_state.state_id, event)

    def _register_state_if_not_registered(
        self, state_cls: Type[BaseState], initial: bool = False
    ) -> None:
        """Register state, if not already registered."""
        if state_cls.state_id not in self._name_to_state:
            self._register_state(state_cls, initial=initial)

    def _register_state(
        self, state_cls: Type[BaseState], initial: bool = False
    ) -> None:
        """Register state."""
        name = state_cls.state_id
        return super().register_state(
            name,
            state_cls(name=name, skill_context=self.context),
            initial=initial,
        )
