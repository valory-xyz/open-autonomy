# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2023 Valory AG
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
from packages.valory.skills.abstract_round_abci.behaviour_utils import (
    BaseBehaviour,
    TmManager,
    make_degenerate_behaviour,
)


BehaviourType = Type[BaseBehaviour]
Action = Optional[str]
TransitionFunction = Dict[BehaviourType, Dict[Action, BehaviourType]]


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
        mcs._check_behaviour_id_uniqueness(behaviour_cls)
        mcs._check_initial_behaviour_in_set_of_behaviours(behaviour_cls)
        mcs._check_matching_round_consistency(behaviour_cls)

    @classmethod
    def _check_all_required_classattributes_are_set(
        mcs, behaviour_cls: "AbstractRoundBehaviour"
    ) -> None:
        """Check that all the required class attributes are set."""
        try:
            behaviour_cls.abci_app_cls  # pylint: disable=pointless-statement
            behaviour_cls.behaviours  # pylint: disable=pointless-statement
            behaviour_cls.initial_behaviour_cls  # pylint: disable=pointless-statement
        except AttributeError as e:
            raise ABCIAppInternalError(*e.args) from None

    @classmethod
    def _check_behaviour_id_uniqueness(
        mcs, behaviour_cls: "AbstractRoundBehaviour"
    ) -> None:
        """Check that behaviour ids are unique across behaviours."""
        behaviour_id_to_behaviour = defaultdict(lambda: [])
        for behaviour_class in behaviour_cls.behaviours:
            behaviour_id_to_behaviour[behaviour_class.auto_behaviour_id()].append(
                behaviour_class
            )
            if len(behaviour_id_to_behaviour[behaviour_class.auto_behaviour_id()]) > 1:
                behaviour_classes_names = [
                    _behaviour_cls.__name__
                    for _behaviour_cls in behaviour_id_to_behaviour[
                        behaviour_class.auto_behaviour_id()
                    ]
                ]
                raise ABCIAppInternalError(
                    f"behaviours {behaviour_classes_names} have the same behaviour id '{behaviour_class.auto_behaviour_id()}'"
                )

    @classmethod
    def _check_matching_round_consistency(
        mcs, behaviour_cls: "AbstractRoundBehaviour"
    ) -> None:
        """Check that matching rounds are: (1) unique across behaviour, and (2) covering."""
        round_to_behaviour: Dict[Type[AbstractRound], List[BehaviourType]] = {
            round_cls: []
            for round_cls in behaviour_cls.abci_app_cls.get_all_round_classes(
                behaviour_cls.is_background_behaviour_set
            )
        }

        # check uniqueness
        for b in behaviour_cls.behaviours:
            round_to_behaviour[b.matching_round].append(b)
            if len(round_to_behaviour[b.matching_round]) > 1:
                behaviour_class_ids = [
                    _behaviour_cls.auto_behaviour_id()
                    for _behaviour_cls in round_to_behaviour[b.matching_round]
                ]
                raise ABCIAppInternalError(
                    f"behaviours {behaviour_class_ids} have the same matching round '{b.matching_round.auto_round_id()}'"
                )

        # check covering
        for round_cls, behaviours in round_to_behaviour.items():
            if round_cls in behaviour_cls.abci_app_cls.final_states:
                if len(behaviours) != 0:
                    raise ABCIAppInternalError(
                        f"round {round_cls.auto_round_id()} is a final round it shouldn't have any matching behaviours."
                    )
                continue  # pragma: nocover
            if len(behaviours) == 0:
                raise ABCIAppInternalError(
                    f"round {round_cls.auto_round_id()} is not a matching round of any behaviour"
                )

    @classmethod
    def _check_initial_behaviour_in_set_of_behaviours(
        mcs, behaviour_cls: "AbstractRoundBehaviour"
    ) -> None:
        """Check the initial behaviour is in the set of behaviours."""
        if behaviour_cls.initial_behaviour_cls not in behaviour_cls.behaviours:
            raise ABCIAppInternalError(
                f"initial behaviour {behaviour_cls.initial_behaviour_cls.auto_behaviour_id()} is not in the set of behaviours"
            )


class AbstractRoundBehaviour(
    Behaviour, ABC, Generic[EventType], metaclass=_MetaRoundBehaviour
):
    """This behaviour implements an abstract round behaviour."""

    abci_app_cls: Type[AbciApp[EventType]]
    behaviours: AbstractSet[BehaviourType]
    initial_behaviour_cls: BehaviourType
    background_behaviour_cls: Optional[BehaviourType] = None

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the behaviour."""
        super().__init__(**kwargs)
        self._behaviour_id_to_behaviours: Dict[
            str, BehaviourType
        ] = self._get_behaviour_id_to_behaviour_mapping(self.behaviours)
        self._round_to_behaviour: Dict[
            Type[AbstractRound], BehaviourType
        ] = self._get_round_to_behaviour_mapping(self.behaviours)

        self.current_behaviour: Optional[BaseBehaviour] = None
        self.background_behaviour: Optional[BaseBehaviour] = None
        self.tm_manager: Optional[TmManager] = None
        # keep track of last round height so to detect changes
        self._last_round_height = 0

        # this variable remembers the actual next transition
        # when we cannot preemptively interrupt the current behaviour
        # because it has not a matching round.
        self._next_behaviour_cls: Optional[BehaviourType] = None

    @classmethod
    def _get_behaviour_id_to_behaviour_mapping(
        cls, behaviours: AbstractSet[BehaviourType]
    ) -> Dict[str, BehaviourType]:
        """Get behaviour id to behaviour mapping."""
        result: Dict[str, BehaviourType] = {}
        for behaviour_cls in behaviours:
            behaviour_id = behaviour_cls.auto_behaviour_id()
            if behaviour_id in result:
                raise ValueError(
                    f"cannot have two behaviours with the same id; got {behaviour_cls} and {result[behaviour_id]} both with id '{behaviour_id}'"
                )
            result[behaviour_id] = behaviour_cls
        return result

    @classmethod
    def _get_round_to_behaviour_mapping(
        cls, behaviours: AbstractSet[BehaviourType]
    ) -> Dict[Type[AbstractRound], BehaviourType]:
        """Get round-to-behaviour mapping."""
        result: Dict[Type[AbstractRound], BehaviourType] = {}
        for behaviour_cls in behaviours:
            round_cls = behaviour_cls.matching_round
            if round_cls in result:
                raise ValueError(
                    f"the behaviours '{behaviour_cls.auto_behaviour_id()}' and '{result[round_cls].auto_behaviour_id()}' point to the same matching round '{round_cls.auto_round_id()}'"
                )
            result[round_cls] = behaviour_cls

        # iterate over rounds and map final (i.e. degenerate) rounds
        #  to the degenerate behaviour class
        for final_round_cls in cls.abci_app_cls.final_states:
            new_degenerate_behaviour = make_degenerate_behaviour(final_round_cls)
            new_degenerate_behaviour.matching_round = final_round_cls
            result[final_round_cls] = new_degenerate_behaviour

        return result

    def instantiate_behaviour_cls(self, behaviour_cls: BehaviourType) -> BaseBehaviour:
        """Instantiate the behaviours class."""
        return behaviour_cls(
            name=behaviour_cls.auto_behaviour_id(), skill_context=self.context
        )

    @property
    def is_background_behaviour_set(self) -> bool:
        """Returns whether the background behaviour is set."""
        return self.background_behaviour_cls is not None

    def setup(self) -> None:
        """Set up the behaviours."""
        self.current_behaviour = self.instantiate_behaviour_cls(
            self.initial_behaviour_cls
        )
        self.tm_manager = self.instantiate_behaviour_cls(TmManager)  # type: ignore
        if self.is_background_behaviour_set:
            self.background_behaviour_cls = cast(
                Type[BaseBehaviour], self.background_behaviour_cls
            )
            self.background_behaviour = self.instantiate_behaviour_cls(
                self.background_behaviour_cls
            )

    def teardown(self) -> None:
        """Tear down the behaviour"""

    def act(self) -> None:
        """Implement the behaviour."""
        tm_manager = cast(TmManager, self.tm_manager)
        if tm_manager.tm_communication_unhealthy or tm_manager.is_acting:
            # tendermint is not healthy, or we are already applying a fix.
            # try_fix() internally uses generators, that's why it's relevant
            # to know whether a fix is already being applied.
            # It might happen that tendermint is healthy, but the fix is not yet finished.
            tm_manager.try_fix()
            return

        self._process_current_round()
        if self.current_behaviour is None:
            return

        self.current_behaviour.act_wrapper()
        if self.current_behaviour.is_done():
            self.current_behaviour.clean_up()
            self.current_behaviour = None

        if self.background_behaviour is not None:
            self.background_behaviour.act_wrapper()

    def _process_current_round(self) -> None:
        """Process current ABCIApp round."""
        current_round_height = self.context.state.round_sequence.current_round_height
        if (
            self.current_behaviour is not None
            and self._last_round_height == current_round_height
        ):
            # round has not changed - do nothing
            return
        self._last_round_height = current_round_height
        current_round_cls = type(self.context.state.round_sequence.current_round)

        # each round has a behaviour associated to it
        next_behaviour_cls = self._round_to_behaviour[current_round_cls]

        # stop the current behaviour and replace it with the new behaviour
        if self.current_behaviour is not None:
            current_behaviour = cast(BaseBehaviour, self.current_behaviour)
            current_behaviour.clean_up()
            current_behaviour.stop()
            self.context.logger.debug(
                "overriding transition: current behaviour: '%s', next behaviour: '%s'",
                self.current_behaviour.behaviour_id if self.current_behaviour else None,
                next_behaviour_cls.auto_behaviour_id(),
            )

        self.current_behaviour = self.instantiate_behaviour_cls(next_behaviour_cls)
