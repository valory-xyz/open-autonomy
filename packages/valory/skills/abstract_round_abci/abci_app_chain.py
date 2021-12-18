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

"""This module contains utilities for AbciApps."""
import inspect
from itertools import chain
from typing import Any, Dict, Set, Tuple, Type

from aea.exceptions import enforce

from packages.valory.skills.abstract_round_abci.base import (
    AbciApp,
    AbciAppTransitionFunction,
    AppState,
    BasePeriodState,
    EventToTimeout,
    EventType,
)


AbciAppTransitionMapping = Dict[AppState, Dict[Any, AppState]]


def abci_app_chain(  # pylint: disable=too-many-locals
    abci_apps: Tuple[Type[AbciApp], ...],
    abci_app_transition_mapping: AbciAppTransitionMapping,
) -> Type[AbciApp]:
    """Concatenate multiple AbciApp types."""
    enforce(
        len(abci_apps) > 1,
        f"there must be a minimum of two AbciApps to chain, found ({len(abci_apps)})",
    )

    # Get the apps rounds
    rounds = (app.get_all_rounds() for app in abci_apps)

    # Ensure there are no common rounds
    common_round_classes = set.intersection(*rounds)
    enforce(
        len(common_round_classes) == 0,
        f"rounds in common between operands are not allowed ({common_round_classes})",
    )

    # Merge the transition functions, final states and events
    new_initial_round_cls = abci_apps[0].initial_round_cls
    potential_final_states = set.union(*(app.final_states for app in abci_apps))
    potential_events_to_timeout: EventToTimeout = {}
    for app in abci_apps:
        for e, t in app.event_to_timeout.items():
            if e in potential_events_to_timeout and potential_events_to_timeout[e] != t:
                raise ValueError(
                    f"Event {e} defined in app {app} is defined with timeout {t} but it is already defined in a prior app with timeout {potential_events_to_timeout[e]}."
                )
            potential_events_to_timeout[e] = t
    potential_transition_function: AbciAppTransitionFunction = {}
    for app in abci_apps:
        for state, events_to_rounds in app.transition_function.items():
            potential_transition_function[state] = events_to_rounds

    # Update transition function according to the transition mapping
    for state, event_to_states in abci_app_transition_mapping.items():
        for event, new_state in event_to_states.items():
            # Overwrite the old state or create a new one if it does not exist
            if state not in potential_transition_function:
                potential_transition_function[state] = {event: new_state}
            else:
                potential_transition_function[state][event] = new_state

    # Remove no longer used states from transition function and final states
    destination_states: Set[AppState] = set()
    for event_to_states in potential_transition_function.values():
        destination_states.update(event_to_states.values())
    new_transition_function: AbciAppTransitionFunction = {
        state: events_to_rounds
        for state, events_to_rounds in potential_transition_function.items()
        if state in destination_states or state is new_initial_round_cls
    }
    new_final_states = {
        state for state in potential_final_states if state in destination_states
    }

    # Remove no longer used events
    used_events: Set[str] = set()
    for event_to_states in new_transition_function.values():
        used_events.update(event_to_states.keys())
    new_events_to_timeout = {
        event: timeout
        for event, timeout in potential_events_to_timeout.items()
        if event in used_events
    }

    # Return the composed result
    class ComposedAbciApp(AbciApp[EventType]):
        """Composed abci app class."""

        initial_round_cls: AppState = new_initial_round_cls
        transition_function: AbciAppTransitionFunction = new_transition_function
        final_states: Set[AppState] = new_final_states
        event_to_timeout: EventToTimeout = new_events_to_timeout

    return ComposedAbciApp


def period_state_chain(
    Base_Classes: Tuple[Type[BasePeriodState], ...]
) -> Type[BasePeriodState]:
    """Concatenate multiple period states using a class factory."""

    # Class constructor
    def __init__(self, **kwargs):

        all_params = set(
            chain.from_iterable(
                tuple(inspect.signature(Base_Class.__init__).parameters.keys())
                for Base_Class in Base_Classes
            )
        )

        # Set attributes
        for key, value in kwargs.items():
            if key not in all_params:
                message = f"period_state_chain: parameter {key}: {type(key)} = {value} does not belong to any of the base classes"
                raise TypeError(message)
            setattr(self, key, value)

        # Call base constructors
        for Base_Class in Base_Classes:
            params = inspect.signature(Base_Class.__init__).parameters
            init_params = {
                key: value for key, value in kwargs.items() if key in params.keys()
            }
            Base_Class.__init__(self, *init_params)

    # Create new class and return it
    ComposedPeriodState = type(
        "ComposedPeriodState", Base_Classes, {"__init__": __init__}
    )
    return ComposedPeriodState
