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
from copy import copy
from typing import Dict, Set, Type

from aea.exceptions import enforce

from packages.valory.skills.abstract_round_abci.base import (
    AbciApp,
    AbciAppTransitionFunction,
    AppState,
    EventType,
)


def chain(  # pylint: disable=too-many-locals
    abci_app_1: Type[AbciApp], abci_app_2: Type[AbciApp], *abci_apps: Type[AbciApp]
) -> Type[AbciApp]:
    """Concatenate multiple AbciApp types."""

    # Get the apps rounds, events and initial rounds
    rounds_1 = abci_app_1.get_all_rounds()
    rounds_2 = abci_app_2.get_all_rounds()

    events_1 = abci_app_1.get_all_events()
    events_2 = abci_app_2.get_all_events()

    initial_1 = abci_app_1.initial_round_cls
    initial_2 = abci_app_2.initial_round_cls

    # Ensure there are no common rounds or events
    common_round_classes = rounds_1.intersection(rounds_2)
    enforce(
        len(common_round_classes) == 0,
        "rounds in common between operands are not allowed",
    )
    common_events = events_1.intersection(events_2)
    enforce(
        len(common_events) == 0, "events in common between operands are not allowed"
    )

    # Build the new final states and events
    new_final_states = copy(abci_app_2.final_states)
    new_event_to_timeout = {
        **abci_app_1.event_to_timeout,
        **abci_app_2.event_to_timeout,
    }
    if initial_1 not in abci_app_1.final_states:
        new_initial_state = initial_1
        new_transition_function: AbciAppTransitionFunction = copy(
            abci_app_2.transition_function
        )
        for start_1, out_transitions_1 in abci_app_1.transition_function.items():
            if start_1 in abci_app_1.final_states:
                continue
            new_transition_function[start_1] = {}
            for event_1, end_1 in out_transitions_1.items():
                if end_1 in abci_app_1.final_states:
                    end_1 = initial_2
                new_transition_function[start_1][event_1] = end_1
    else:
        new_initial_state = initial_2
        new_transition_function = copy(abci_app_2.transition_function)

    # Return the composed result
    class ComposedAbciApp(AbciApp[EventType]):
        """Composed abci app class."""

        initial_round_cls: AppState = new_initial_state
        transition_function: AbciAppTransitionFunction = new_transition_function
        final_states: Set[AppState] = new_final_states
        event_to_timeout: Dict[EventType, float] = new_event_to_timeout

    if len(abci_apps) > 0:
        return chain(ComposedAbciApp, abci_apps[0], *abci_apps)
    return ComposedAbciApp
