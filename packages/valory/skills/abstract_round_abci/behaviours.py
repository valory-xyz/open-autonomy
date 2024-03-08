# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2024 Valory AG
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
from dataclasses import asdict
from typing import (
    AbstractSet,
    Any,
    Dict,
    Generator,
    Generic,
    List,
    Optional,
    Set,
    Tuple,
    Type,
    cast,
)

from aea.skills.base import Behaviour

from packages.valory.skills.abstract_round_abci.base import (
    ABCIAppInternalError,
    AbciApp,
    AbstractRound,
    EventType,
    PendingOffencesPayload,
    PendingOffencesRound,
    PendingOffense,
    RoundSequence,
)
from packages.valory.skills.abstract_round_abci.behaviour_utils import (
    BaseBehaviour,
    TmManager,
    make_degenerate_behaviour,
)
from packages.valory.skills.abstract_round_abci.models import SharedState


SLASHING_BACKGROUND_BEHAVIOUR_ID = "slashing_check_behaviour"
TERMINATION_BACKGROUND_BEHAVIOUR_ID = "background_behaviour"


BehaviourType = Type[BaseBehaviour]
Action = Optional[str]
TransitionFunction = Dict[BehaviourType, Dict[Action, BehaviourType]]


class _MetaRoundBehaviour(ABCMeta):
    """A metaclass that validates AbstractRoundBehaviour's attributes."""

    are_background_behaviours_set: bool = False

    def __new__(mcs, name: str, bases: Tuple, namespace: Dict, **kwargs: Any) -> Type:  # type: ignore
        """Initialize the class."""
        new_cls = super().__new__(mcs, name, bases, namespace, **kwargs)

        if ABC in bases:
            # abstract class, return
            return new_cls
        if not issubclass(new_cls, AbstractRoundBehaviour):
            # the check only applies to AbstractRoundBehaviour subclasses
            return new_cls

        mcs.are_background_behaviours_set = bool(
            new_cls.background_behaviours_cls - {PendingOffencesBehaviour}
        )
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
            _ = behaviour_cls.abci_app_cls
            _ = behaviour_cls.behaviours
            _ = behaviour_cls.initial_behaviour_cls
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
        matching_bg_round_classes = {
            behaviour_cls.matching_round
            for behaviour_cls in behaviour_cls.background_behaviours_cls
        }
        round_to_behaviour: Dict[Type[AbstractRound], List[BehaviourType]] = {
            round_cls: []
            for round_cls in behaviour_cls.abci_app_cls.get_all_round_classes(
                matching_bg_round_classes,
                mcs.are_background_behaviours_set,
            )
        }

        # check uniqueness
        for b in behaviour_cls.behaviours:
            behaviours = round_to_behaviour.get(b.matching_round, None)
            if behaviours is None:
                raise ABCIAppInternalError(
                    f"Behaviour {b.behaviour_id!r} specifies unknown {b.matching_round!r} as a matching round. "
                    "Please make sure that the round is implemented and belongs to the FSM. "
                    f"If {b.behaviour_id!r} is a background behaviour, please make sure that it is set correctly, "
                    f"by overriding the corresponding attribute of the chained skill's behaviour."
                )
            behaviours.append(b)
            if len(behaviours) > 1:
                behaviour_cls_ids = [
                    behaviour_cls_.auto_behaviour_id() for behaviour_cls_ in behaviours
                ]
                raise ABCIAppInternalError(
                    f"behaviours {behaviour_cls_ids} have the same matching round '{b.matching_round.auto_round_id()}'"
                )

        # check covering
        for round_cls, behaviours in round_to_behaviour.items():
            if round_cls in behaviour_cls.abci_app_cls.final_states:
                if len(behaviours) != 0:
                    raise ABCIAppInternalError(
                        f"round {round_cls.auto_round_id()} is a final round it shouldn't have any matching behaviours."
                    )
            elif len(behaviours) == 0:
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


class PendingOffencesBehaviour(BaseBehaviour):
    """A behaviour responsible for checking whether there are any pending offences."""

    matching_round = PendingOffencesRound

    @property
    def round_sequence(self) -> RoundSequence:
        """Get the round sequence from the shared state."""
        return cast(SharedState, self.context.state).round_sequence

    @property
    def pending_offences(self) -> Set[PendingOffense]:
        """Get the pending offences from the round sequence."""
        return self.round_sequence.pending_offences

    def has_pending_offences(self) -> bool:
        """Check if there are any pending offences."""
        return bool(len(self.pending_offences))

    def async_act(self) -> Generator:
        """
        Checks the pending offences.

        This behaviour simply checks if the set of pending offences is not empty.
        When it’s not empty, it pops the offence from the set, and sends it to the rest of the agents via a payload

        :return: None
        :yield: None
        """
        yield from self.wait_for_condition(self.has_pending_offences)
        offence = self.pending_offences.pop()
        offence_detected_log = (
            f"An offence of type {offence.offense_type.name} has been detected "
            f"for agent with address {offence.accused_agent_address} during round {offence.round_count}. "
        )
        offence_expiration = offence.last_transition_timestamp + offence.time_to_live
        last_timestamp = self.round_sequence.last_round_transition_timestamp

        if offence_expiration < last_timestamp.timestamp():
            ignored_log = "Offence will be ignored as it has expired."
            self.context.logger.info(offence_detected_log + ignored_log)
            return

        sharing_log = "Sharing offence with the other agents."
        self.context.logger.info(offence_detected_log + sharing_log)

        payload = PendingOffencesPayload(
            self.context.agent_address, *asdict(offence).values()
        )
        yield from self.send_a2a_transaction(payload)
        yield from self.wait_until_round_end()
        self.set_done()


class AbstractRoundBehaviour(  # pylint: disable=too-many-instance-attributes
    Behaviour, ABC, Generic[EventType], metaclass=_MetaRoundBehaviour
):
    """This behaviour implements an abstract round behaviour."""

    abci_app_cls: Type[AbciApp[EventType]]
    behaviours: AbstractSet[BehaviourType]
    initial_behaviour_cls: BehaviourType
    background_behaviours_cls: Set[BehaviourType] = {PendingOffencesBehaviour}  # type: ignore

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
        self.background_behaviours: Set[BaseBehaviour] = set()
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

    def _setup_background(self) -> None:
        """Set up the background behaviours."""
        params = cast(BaseBehaviour, self.current_behaviour).params
        for background_cls in self.background_behaviours_cls:
            background_cls = cast(Type[BaseBehaviour], background_cls)

            if (
                not params.use_termination
                and background_cls.auto_behaviour_id()
                == TERMINATION_BACKGROUND_BEHAVIOUR_ID
            ) or (
                not params.use_slashing
                and background_cls.auto_behaviour_id()
                == SLASHING_BACKGROUND_BEHAVIOUR_ID
                or background_cls == PendingOffencesBehaviour
            ):
                # comparing with the behaviour id is not entirely safe, as there is a potential for conflicts
                # if a user creates a behaviour with the same name
                continue

            self.background_behaviours.add(
                self.instantiate_behaviour_cls(background_cls)
            )

    def setup(self) -> None:
        """Set up the behaviours."""
        self.current_behaviour = self.instantiate_behaviour_cls(
            self.initial_behaviour_cls
        )
        self.tm_manager = self.instantiate_behaviour_cls(TmManager)  # type: ignore
        self._setup_background()

    def teardown(self) -> None:
        """Tear down the behaviour"""

    def _background_act(self) -> None:
        """Call the act wrapper for the background behaviours."""
        for behaviour in self.background_behaviours:
            behaviour.act_wrapper()

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

        tm_manager.informed = False
        tm_manager.acn_communication_attempted = False
        self._process_current_round()
        if self.current_behaviour is None:
            return

        self.current_behaviour.act_wrapper()
        if self.current_behaviour.is_done():
            self.current_behaviour.clean_up()
            self.current_behaviour = None

        self._background_act()

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
