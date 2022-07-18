# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2022 Valory AG
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
import logging
from typing import Any, Dict, List, Optional, Set, Tuple, Type

from aea.exceptions import enforce

from packages.valory.skills.abstract_round_abci.base import (
    AbciApp,
    AbciAppTransitionFunction,
    AppState,
    EventToTimeout,
    EventType,
)


_default_logger = logging.getLogger(
    "aea.packages.valory.skills.abstract_round_abci.abci_app_chain"
)

AbciAppTransitionMapping = Dict[AppState, AppState]


def check_set_uniqueness(sets: Tuple) -> Optional[Any]:
    """Checks that all elements in the set list are unique and not repeated among different sets"""
    all_elements = set.union(*sets)
    for element in all_elements:
        # Count the number of sets that include this element
        sets_in = [set_ for set_ in sets if element in set_]
        if len(sets_in) > 1:
            return element
    return None


def chain(  # pylint: disable=too-many-locals
    abci_apps: Tuple[Type[AbciApp], ...],
    abci_app_transition_mapping: AbciAppTransitionMapping,
) -> Type[AbciApp]:
    """Concatenate multiple AbciApp types."""
    enforce(
        len(abci_apps) > 1,
        f"there must be a minimum of two AbciApps to chain, found ({len(abci_apps)})",
    )
    enforce(
        len(set(abci_apps)) == len(abci_apps),
        "Found multiple occurences of same Abci App",
    )
    non_abstract_abci_apps = [
        abci_app.__name__
        for abci_app in abci_apps
        if not abci_app._is_abstract  # pylint: disable=protected-access
    ]
    enforce(
        len(non_abstract_abci_apps) == 0,
        f"found non-abstract AbciApp during chaining: {non_abstract_abci_apps}",
    )

    # Get the apps rounds
    rounds = tuple(app.get_all_rounds() for app in abci_apps)
    round_ids = tuple(
        {round_.round_id for round_ in app.get_all_rounds()} for app in abci_apps
    )

    # Ensure there are no common rounds
    common_round_classes = check_set_uniqueness(rounds)
    enforce(
        not common_round_classes,
        f"rounds in common between abci apps are not allowed ({common_round_classes})",
    )

    # Ensure there are no common round_ids
    common_round_ids = check_set_uniqueness(round_ids)
    enforce(
        not common_round_ids,
        f"round ids in common between abci apps are not allowed ({common_round_ids})",
    )

    # Ensure all states in app transition mapping (keys and values) are final states or initial states, respectively.
    all_final_states = {
        final_state for app in abci_apps for final_state in app.final_states
    }
    all_initial_states = {
        initial_state for app in abci_apps for initial_state in app.initial_states
    }.union({app.initial_round_cls for app in abci_apps})
    for key, value in abci_app_transition_mapping.items():
        if key not in all_final_states:
            raise ValueError(
                f"Found non-final state {key} specified in abci_app_transition_mapping."
            )
        if value not in all_initial_states:
            raise ValueError(
                f"Found non-initial state {value} specified in abci_app_transition_mapping."
            )

    # Warn about events duplicated in multiple apps
    app_to_events = {app: app.get_all_events() for app in abci_apps}
    all_events = set.union(*app_to_events.values())
    for event in all_events:
        apps = [str(app) for app, events in app_to_events.items() if event in events]
        if len(apps) > 1:
            apps_str = "\n".join(apps)
            _default_logger.warning(
                f"The same event '{event}' has been found in several apps:\n{apps_str}\nIt will be interpreted as the same event."
                " If this is not the intented behaviour, please rename it to enforce its uniqueness."
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
            if state in abci_app_transition_mapping:
                # we remove these final states
                continue
            # Update transition function according to the transition mapping
            new_events_to_rounds = {}
            for event, round_ in events_to_rounds.items():
                destination_round = abci_app_transition_mapping.get(round_, round_)
                new_events_to_rounds[event] = destination_round
            potential_transition_function[state] = new_events_to_rounds

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

    # Collect keys to persist across periods from all abcis
    new_cross_period_persisted_keys = []
    for app in abci_apps:
        new_cross_period_persisted_keys.extend(app.cross_period_persisted_keys)

    # Return the composed result
    class ComposedAbciApp(AbciApp[EventType]):
        """Composed abci app class."""

        initial_round_cls: AppState = new_initial_round_cls
        transition_function: AbciAppTransitionFunction = new_transition_function
        final_states: Set[AppState] = new_final_states
        event_to_timeout: EventToTimeout = new_events_to_timeout
        cross_period_persisted_keys: List[str] = new_cross_period_persisted_keys

    return ComposedAbciApp
