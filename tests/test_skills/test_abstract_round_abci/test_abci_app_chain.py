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

from packages.valory.skills.abstract_round_abci.abci_app_chain import chain
from packages.valory.skills.abstract_round_abci.base import AbciApp


def test_chain() -> None:
    """Test the AbciApp chain function."""

    round_1a = MagicMock()
    round_1b = MagicMock()
    round_2a = MagicMock()
    round_2b = MagicMock()

    event_1a = "1a"
    event_1b = "1b"
    event_timeout1 = "timeout_1"
    event_2a = "2a"
    event_2b = "2b"
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

    AbciApp3 = chain(AbciApp1, AbciApp2)

    assert AbciApp3.initial_round_cls == round_1a
    assert AbciApp3.transition_function == {
        round_1a: {event_timeout1: round_1a, event_1b: round_2a},
        round_2a: {event_timeout2: round_2a, event_2b: round_2b},
        round_2b: {event_2a: round_2a},
    }
    assert AbciApp3.final_states == {round_2b}
    assert AbciApp3.event_to_timeout == {
        event_timeout1: timeout1,
        event_timeout2: timeout2,
    }
