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

from typing import AbstractSet, Any, Dict, Generic, Optional, Type, cast

from aea.skills.base import Behaviour

from packages.valory.skills.abstract_round_abci.base import (
    AbciApp,
    AbstractRound,
    EventType,
)
from packages.valory.skills.abstract_round_abci.behaviour_utils import BaseState


StateType = Type[BaseState]
Action = Optional[str]
TransitionFunction = Dict[StateType, Dict[Action, StateType]]


class AbstractRoundBehaviour(Behaviour, Generic[EventType]):
    """This behaviour implements an abstract round behaviour."""

    abci_app_cls: Type[AbciApp[EventType]]
    behaviour_states: AbstractSet[StateType]
    initial_state_cls: StateType

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the behaviour."""
        super().__init__(**kwargs)
        self._state_id_to_states: Dict[
            str, StateType
        ] = self._get_state_id_to_state_mapping(self.behaviour_states)
        self._round_to_state: Dict[
            Type[AbstractRound], StateType
        ] = self._get_round_to_state_mapping(self.behaviour_states)
        self._check_initial_state_in_set_of_states(
            self.initial_state_cls, self.behaviour_states
        )

        self.current_state: Optional[BaseState] = None

        # keep track of last round id so to detect changes
        self._last_round_id: Optional[str] = None

        # this variable remembers the actual next transition
        # when we cannot preemptively interrupt the current state
        # because it has not a matching round.
        self._next_state_cls: Optional[StateType] = None

    @classmethod
    def _get_state_id_to_state_mapping(
        cls, behaviour_states: AbstractSet[StateType]
    ) -> Dict[str, StateType]:
        """Get state id to state mapping."""
        result: Dict[str, StateType] = {}
        for state_behaviour_cls in behaviour_states:
            state_id = state_behaviour_cls.state_id
            if state_id in result:
                raise ValueError(
                    f"cannot have two states with the same id; got {state_behaviour_cls} and {result[state_id]} both with id '{state_id}'"
                )
            result[state_id] = state_behaviour_cls
        return result

    @classmethod
    def _get_round_to_state_mapping(
        cls, behaviour_states: AbstractSet[StateType]
    ) -> Dict[Type[AbstractRound], StateType]:
        """Get round-to-state mapping."""
        result: Dict[Type[AbstractRound], StateType] = {}
        for state_behaviour_cls in behaviour_states:
            if state_behaviour_cls.matching_round is None:
                continue
            round_cls = state_behaviour_cls.matching_round
            if round_cls in result:
                raise ValueError(
                    f"the states '{state_behaviour_cls.state_id}' and '{result[round_cls].state_id}' point to the same matching round '{round_cls.round_id}'"
                )
            result[round_cls] = state_behaviour_cls
        return result

    @classmethod
    def _check_initial_state_in_set_of_states(
        cls, initial_state: StateType, states: AbstractSet[StateType]
    ) -> None:
        """Check the initial state is in the set of states."""
        if initial_state not in states:
            raise ValueError(
                f"initial state {initial_state.state_id} is not in the set of states"
            )

    def instantiate_state_cls(self, state_cls: StateType) -> BaseState:
        """Instantiate the state class."""
        return state_cls(name=state_cls.state_id, skill_context=self.context)

    def setup(self) -> None:
        """Set up the behaviour."""
        self.current_state = self.instantiate_state_cls(self.initial_state_cls)

    def teardown(self) -> None:
        """Tear down the behaviour"""

    def _initialize_last_round_id_if_none(self) -> None:
        """Initialize last round id field if it is not initialized yet."""
        if self._last_round_id is None:
            self._last_round_id = self.context.state.period.current_round_id

    def act(self) -> None:
        """Implement the behaviour."""
        # initialize last round id to current round id if not initialized yet
        # we cannot do this in the setup because the behaviour may load
        # before the state model
        self._initialize_last_round_id_if_none()

        self._process_current_round()

        current_state = self.current_state
        if current_state is None:
            return

        current_state.act_wrapper()

        if current_state.is_done():
            # if next state is set, take the FSM behaviour transition
            # this branch also handle the case when matching round of current state is not set
            if self._next_state_cls is not None:
                self.context.logger.debug(
                    "overriding transition: current state: '%s', next state: '%s'",
                    self.current_state.state_id if self.current_state else None,
                    self._next_state_cls.state_id,
                )
                self.current_state = self.instantiate_state_cls(self._next_state_cls)
                self._next_state_cls = None
            else:
                # otherwise, set it to None
                self.current_state = None

    def _process_current_round(self) -> None:
        """Process current ABCIApp round."""
        current_round_id = self.context.state.period.current_round_id
        if (
            self.current_state is not None and self._last_round_id == current_round_id
        ) and self.current_state.matching_round is not None:
            # round has not changed - do nothing
            return
        self._last_round_id = current_round_id
        current_round_cls = type(self.context.state.period.current_round)
        # each round has a state behaviour associated to it
        self._next_state_cls = self._round_to_state[current_round_cls]

        # checking if current state behaviour has a matching round.
        #  if so, stop it and replace it with the new state behaviour
        #  if not, then leave it running; the next state will be scheduled
        #  when current state is done
        current_state = self.current_state
        if current_state is None:
            self.current_state = self.instantiate_state_cls(self._next_state_cls)
            return

        current_state = cast(BaseState, current_state)
        # current state cannot be replaced if matching_round is None
        if (
            current_state.matching_round is not None
            and current_state.state_id != self._next_state_cls.state_id
        ):
            current_state.stop()
            self.current_state = self.instantiate_state_cls(self._next_state_cls)
            return
