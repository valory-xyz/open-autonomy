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

"""Test the abci_app_chain.py module of the skill."""
from unittest.mock import MagicMock

from packages.valory.skills.abstract_round_abci.abci_app_chain import (
    AbciAppTransitionMapping,
    chain,
)
from packages.valory.skills.abstract_round_abci.base import AbciApp


def test_chain_two() -> None:
    """Test the AbciApp chain function."""

    round_1a = MagicMock()
    round_1b = MagicMock()
    print(round_1a, round_1b)

    round_2a = MagicMock()
    round_2b = MagicMock()
    print(round_2a, round_2b)
    print("-------")

    event_1a = "event_1a"
    event_1b = "event_1b"
    event_timeout1 = "timeout_1"

    event_2a = "event_2a"
    event_2b = "event_2b"
    event_timeout2 = "timeout_2"

    timeout1 = 10.0
    timeout2 = 10.0

    class AbciApp1(AbciApp):
        initial_round_cls = round_1a
        transition_function = {
            round_1a: {event_timeout1: round_1a, event_1b: round_1b},
            round_1b: {event_1a: round_1a},
        }
        final_states = {round_1b}
        event_to_timeout = {event_timeout1: timeout1}

    class AbciApp2(AbciApp):
        initial_round_cls = round_2a
        transition_function = {
            round_2a: {event_timeout2: round_2a, event_2b: round_2b},
            round_2b: {event_2a: round_2a},
        }
        final_states = {round_2b}
        event_to_timeout = {event_timeout2: timeout2}

    round_transition_mapping: AbciAppTransitionMapping = {event_1b: round_2a}

    ComposedAbciApp = chain((AbciApp1, AbciApp2), round_transition_mapping)  # type: ignore

    assert ComposedAbciApp.initial_round_cls == round_1a
    assert ComposedAbciApp.transition_function == {
        round_1a: {event_timeout1: round_1a, event_1b: round_2a},
        round_2a: {event_timeout2: round_2a, event_2b: round_2b},
        round_2b: {event_2a: round_2a},
    }
    assert ComposedAbciApp.final_states == {round_2b}
    assert ComposedAbciApp.event_to_timeout == {
        event_timeout1: timeout1,
        event_timeout2: timeout2,
    }


def test_chain_three() -> None:
    """Test the AbciApp chain function."""

    round_1a = MagicMock()
    round_1b = MagicMock()

    round_2a = MagicMock()
    round_2b = MagicMock()

    round_3a = MagicMock()
    round_3b = MagicMock()

    event_1a = "1a"
    event_1b = "1b"
    event_timeout1 = "timeout_1"

    event_2a = "2a"
    event_2b = "2b"
    event_timeout2 = "timeout_2"

    event_3a = "3a"
    event_3b = "3b"
    event_timeout3 = "timeout_3"

    timeout1 = 10.0
    timeout2 = 10.0
    timeout3 = 10.0

    class AbciApp1(AbciApp):
        initial_round_cls = round_1a
        transition_function = {
            round_1a: {event_timeout1: round_1a, event_1b: round_1b},
            round_1b: {event_1a: round_1a},
        }
        final_states = {round_1b}
        event_to_timeout = {event_timeout1: timeout1}

    class AbciApp2(AbciApp):
        initial_round_cls = round_2a
        transition_function = {
            round_2a: {event_timeout2: round_2a, event_2b: round_2b},
            round_2b: {event_2a: round_2a},
        }
        final_states = {round_2b}
        event_to_timeout = {event_timeout2: timeout2}

    class AbciApp3(AbciApp):
        initial_round_cls = round_3a
        transition_function = {
            round_3a: {event_timeout3: round_3a, event_3b: round_3b},
            round_3b: {event_3a: round_3a},
        }
        final_states = {round_3b}
        event_to_timeout = {event_timeout3: timeout3}

    round_transition_mapping: AbciAppTransitionMapping = {
        event_1b: round_2a,
        event_2b: round_3a,
    }

    ComposedAbciApp = chain((AbciApp1, AbciApp2, AbciApp3), round_transition_mapping)  # type: ignore

    assert ComposedAbciApp.initial_round_cls == round_1a
    assert ComposedAbciApp.transition_function == {
        round_1a: {event_timeout1: round_1a, event_1b: round_2a},
        round_2a: {event_timeout2: round_2a, event_2b: round_3a},
        round_3a: {event_timeout3: round_3a, event_3b: round_3b},
        round_3b: {event_3a: round_3a},
    }
    assert ComposedAbciApp.final_states == {round_3b}
    assert ComposedAbciApp.event_to_timeout == {
        event_timeout1: timeout1,
        event_timeout2: timeout2,
        event_timeout3: timeout3,
    }
