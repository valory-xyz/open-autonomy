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
from abc import ABC, ABCMeta
from collections import defaultdict
from typing import AbstractSet, Any, Dict, Generic, List, Optional, Tuple, Type, cast

from aea.skills.base import Behaviour

from packages.valory.skills.abstract_round_abci.base import (
    ABCIAppInternalError,
    AbciApp,
    AbstractRound,
    EventType,
)
from packages.valory.skills.abstract_round_abci.behaviour_utils import BaseState


StateType = Type[BaseState]
Action = Optional[str]
TransitionFunction = Dict[StateType, Dict[Action, StateType]]


class _MetaRoundBehaviour(ABCMeta):
    """A metaclass that validates AbstractRoundBehaviour's attributes."""

    def __new__(mcs, name: str, bases: Tuple, namespace: Dict, **kwargs: Any) -> Type:  # type: ignore
        """Initialize the class."""
        new_cls = super().__new__(mcs, name, bases, namespace, **kwargs)

        if ABC in bases:
            # abstract class, return
            return new_cls
        if not issubclass(new_cls, AbstractRoundBehaviour):
            # the check only applies to AbstractRoundBehaviour subclasses
            return new_cls

        mcs._check_consistency(cast(AbstractRoundBehaviour, new_cls))
        return new_cls

    @classmethod
    def _check_consistency(mcs, behaviour_cls: "AbstractRoundBehaviour") -> None:
        """Check consistency of class attributes."""
        mcs._check_all_required_classattributes_are_set(behaviour_cls)
        mcs._check_state_id_uniqueness(behaviour_cls)
        mcs._check_initial_state_in_set_of_states(behaviour_cls)
        mcs._check_matching_round_consistency(behaviour_cls)

    @staticmethod
    def _check_all_required_classattributes_are_set(
        behaviour_cls: "AbstractRoundBehaviour",
    ) -> None:
        """Check that all the required class attributes are set."""
        try:
            behaviour_cls.abci_app_cls  # pylint: disable=pointless-statement
            behaviour_cls.behaviour_states  # pylint: disable=pointless-statement
            behaviour_cls.initial_state_cls  # pylint: disable=pointless-statement
        except AttributeError as e:
            raise ABCIAppInternalError(*e.args) from None

    @staticmethod
    def _check_state_id_uniqueness(behaviour_cls: "AbstractRoundBehaviour") -> None:
        """Check that state behaviour ids are unique across behaviour states."""
        state_id_to_state = defaultdict(lambda: [])
        for state_class in behaviour_cls.behaviour_states:
            state_id_to_state[state_class.state_id].append(state_class)
            if len(state_id_to_state[state_class.state_id]) > 1:
                state_classes_names = [
                    _state_cls.__name__
                    for _state_cls in state_id_to_state[state_class.state_id]
                ]
                raise ABCIAppInternalError(
                    f"states {state_classes_names} have the same state id '{state_class.state_id}'"
                )

    @staticmethod
    def _check_matching_round_consistency(
        behaviour_cls: "AbstractRoundBehaviour",
    ) -> None:
        """Check that matching rounds are: (1) unique across behaviour states, and (2) covering."""
        round_to_state: Dict[Type[AbstractRound], List[StateType]] = {
            round_cls: []
            for round_cls in behaviour_cls.abci_app_cls.get_all_round_classes()
        }

        # check uniqueness
        for b in behaviour_cls.behaviour_states:
            if b.matching_round is None:
                continue
            round_to_state[b.matching_round].append(b)
            if len(round_to_state[b.matching_round]) > 1:
                state_class_ids = [
                    _state_cls.state_id
                    for _state_cls in round_to_state[b.matching_round]
                ]
                raise ABCIAppInternalError(
                    f"states {state_class_ids} have the same matching round '{b.matching_round.round_id}'"
                )

        # check covering
        for round_cls, states in round_to_state.items():
            if len(states) == 0:
                raise ABCIAppInternalError(
                    f"round {round_cls.round_id} is not a matching round of any state behaviour"
                )

    @staticmethod
    def _check_initial_state_in_set_of_states(
        behaviour_cls: "AbstractRoundBehaviour",
    ) -> None:
        """Check the initial state is in the set of states."""
        if behaviour_cls.initial_state_cls not in behaviour_cls.behaviour_states:
            raise ABCIAppInternalError(
                f"initial state {behaviour_cls.initial_state_cls.state_id} is not in the set of states"
            )


class AbstractRoundBehaviour(
    Behaviour, ABC, Generic[EventType], metaclass=_MetaRoundBehaviour
):
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

        self.current_state: Optional[BaseState] = None

        # keep track of last round height so to detect changes
        self._last_round_height = 0

        # this variable remembers the actual next transition
        # when we cannot preemptively interrupt the current state
        # because it has not a matching round.
        self._next_state_cls: Optional[StateType] = None

    @staticmethod
    def _get_state_id_to_state_mapping(
        behaviour_states: AbstractSet[StateType],
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

    @staticmethod
    def _get_round_to_state_mapping(
        behaviour_states: AbstractSet[StateType],
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

    def instantiate_state_cls(self, state_cls: StateType) -> BaseState:
        """Instantiate the state class."""
        return state_cls(name=state_cls.state_id, skill_context=self.context)

    def setup(self) -> None:
        """Set up the behaviour."""
        self.current_state = self.instantiate_state_cls(self.initial_state_cls)

    def teardown(self) -> None:
        """Tear down the behaviour"""

    def act(self) -> None:
        """Implement the behaviour."""
        self._process_current_round()

        current_state = self.current_state
        if current_state is None:
            return

        current_state.act_wrapper()

        if current_state.is_done():
            current_state.clean_up()
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
        current_round_height = self.context.state.period.current_round_height
        if (
            self.current_state is not None
            and self._last_round_height == current_round_height
        ) and self.current_state.matching_round is not None:
            # round has not changed - do nothing
            return
        self._last_round_height = current_round_height
        current_round_cls = type(self.context.state.period.current_round)
        # each round has a state behaviour associated to it
        self._next_state_cls = self._round_to_state[current_round_cls]

        # checking if current state behaviour has a matching round.
        #  if so, stop it and replace it with the new state behaviour
        #  if not, then leave it running; the next state will be scheduled
        #  when current state is done
        if self.current_state is None:
            self.current_state = self.instantiate_state_cls(self._next_state_cls)
            return

        current_state = cast(BaseState, self.current_state)
        # current state cannot be replaced if matching_round is None
        if current_state.matching_round is not None:
            current_state.stop()
            self.current_state = self.instantiate_state_cls(self._next_state_cls)
            return
