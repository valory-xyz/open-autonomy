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
from queue import Queue
from typing import Dict, Optional, Type, Any

from aea.exceptions import enforce
from aea.skills.behaviours import FSMBehaviour

from packages.valory.skills.abstract_round_abci.base import BehaviourMessage
from packages.valory.skills.abstract_round_abci.behaviour_utils import BaseState


State = Type[BaseState]
Action = Optional[str]
TransitionFunction = Dict[State, Dict[Action, State]]


class AbstractRoundBehaviour(FSMBehaviour):
    """This behaviour implements an abstract round."""

    initial_state_cls: State
    transition_function: TransitionFunction = {}

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the behaviour."""
        super().__init__(**kwargs)
        self.input_queue: Queue = Queue()

        self._round_to_state: Dict[str, str] = {}
        self._last_round_id: str = ""

    def setup(self) -> None:
        """Set up the behaviour."""
        self.input_queue = Queue()
        self._register_states(self.transition_function)

    def teardown(self) -> None:
        """Tear down the behaviour"""
        self.input_queue = Queue()

    def act(self) -> None:
        """Implement the behaviour."""
        if self.current is None:
            return

        while not self.input_queue.empty():
            message: BehaviourMessage = self.input_queue.get_nowait()
            self._process_behaviour_message(message)

        current_state = self.get_state(self.current)
        if current_state is None:
            return

        current_state.act_wrapper()

        if current_state.is_done():
            if current_state in self._final_states:
                # we reached a final state - return.
                self.current = None
                return
            event = current_state.event
            next_state = self.transitions.get(self.current, {}).get(event, None)
            self.current = next_state

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
        if state_cls.matching_round is not None:
            enforce(
                state_cls.matching_round.round_id not in self._round_to_state,
                "round id already used",
            )
            self._round_to_state[state_cls.matching_round.round_id] = name
        return super().register_state(
            name,
            state_cls(name=name, skill_context=self.context),
            initial=initial,
        )

    def _process_behaviour_message(self, _message: BehaviourMessage) -> None:
        """Process a behaviour message."""
        # if message == BehaviourMessage.COMMITTED_BLOCK
        new_round_id = self.context.state.period.current_round_id
        if self._last_round_id == new_round_id:
            # round has not changed - do nothing
            return
        self._last_round_id = new_round_id
        # before changing state, send an exception
        # to the 'BaseState' behaviour (using 'generator.throw())
        self.current = self._round_to_state[self._last_round_id]
