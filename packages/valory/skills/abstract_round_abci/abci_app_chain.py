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
from typing import Any, Dict, Set, Tuple, Type

from aea.exceptions import enforce

from packages.valory.skills.abstract_round_abci.base import (
    AbciApp,
    AbciAppTransitionFunction,
    AppState,
    EventType,
)


AbciAppTransitionMapping = Dict[AppState, Dict[Any, AppState]]


def chain(  # pylint: disable=too-many-locals
    abci_apps: Tuple[Type[AbciApp], ...],
    abci_app_transition_mapping: AbciAppTransitionMapping,
) -> Type[AbciApp]:
    """Concatenate multiple AbciApp types."""

    # Get the apps rounds, events and initial rounds
    rounds = (app.get_all_rounds() for app in abci_apps)

    # Ensure there are no common rounds
    common_round_classes = set.intersection(*rounds)
    enforce(
        len(common_round_classes) == 0,
        f"rounds in common between operands are not allowed ({common_round_classes})",
    )

    # Merge the transition functions, final states and events
    new_initial_state = abci_apps[0].initial_round_cls
    new_final_states = set.union(*(app.final_states for app in abci_apps))
    new_events_to_timeout = {
        e: t for app in abci_apps for e, t in app.event_to_timeout.items()
    }
    new_transition_function: AbciAppTransitionFunction = {
        state: events_to_rounds
        for app in abci_apps
        for state, events_to_rounds in app.transition_function.items()
    }

    # Update transition function according to the transition mapping
    for state, event_to_states in abci_app_transition_mapping.items():
        for event, new_state in event_to_states.items():
            # Overwrite the old state or create a new one if it does not exist
            new_transition_function[state][event] = new_state

    # Remove no longer used states from transition function and final states
    destination_states: Set[AppState] = set()

    for event_to_states in new_transition_function.values():  # type: ignore
        destination_states.update(event_to_states.values())  # type: ignore

    new_transition_function = {
        state: events_to_rounds
        for state, events_to_rounds in new_transition_function.items()
        if state in destination_states or state is new_initial_state
    }

    new_final_states = {
        state for state in new_final_states if state in destination_states
    }

    # Remove no longer used events
    used_events: Set[str] = set()

    for events in new_transition_function.values():  # type: ignore
        used_events.update(events.keys())  # type: ignore

    new_events_to_timeout = {
        event: timeout
        for event, timeout in new_events_to_timeout.items()
        if event in used_events
    }

    # Return the composed result
    class ComposedAbciApp(AbciApp[EventType]):
        """Composed abci app class."""

        initial_round_cls: AppState = new_initial_state
        transition_function: AbciAppTransitionFunction = new_transition_function
        final_states: Set[AppState] = new_final_states
        event_to_timeout: Dict[EventType, float] = new_events_to_timeout

    return ComposedAbciApp
