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
from typing import List
from unittest.mock import MagicMock

import pytest

from packages.valory.skills.abstract_round_abci.abci_app_chain import (
    AbciAppTransitionMapping,
    abci_app_chain,
    period_state_chain,
)
from packages.valory.skills.abstract_round_abci.base import AbciApp, BasePeriodState


class TestAbciAppChaining:
    """Test chaning of AbciApps."""

    def setup(self) -> None:
        """Setup test."""
        self.round_1a = MagicMock()
        self.round_1b = MagicMock()

        self.round_2a = MagicMock()
        self.round_2b = MagicMock()

        self.round_3a = MagicMock()
        self.round_3b = MagicMock()

        self.event_1a = "event_1a"
        self.event_1b = "event_1b"
        self.event_timeout1 = "timeout_1"

        self.event_2a = "event_2a"
        self.event_2b = "event_2b"
        self.event_timeout2 = "timeout_2"

        self.event_3a = "3a"
        self.event_3b = "3b"
        self.event_timeout3 = "timeout_3"

        self.timeout1 = 10.0
        self.timeout2 = 15.0
        self.timeout3 = 20.0

        class AbciApp1(AbciApp):
            initial_round_cls = self.round_1a
            transition_function = {
                self.round_1a: {
                    self.event_timeout1: self.round_1a,
                    self.event_1b: self.round_1b,
                },
                self.round_1b: {self.event_1a: self.round_1a},
            }
            final_states = {self.round_1b}
            event_to_timeout = {self.event_timeout1: self.timeout1}

        self.app1_class = AbciApp1

        class AbciApp2(AbciApp):
            initial_round_cls = self.round_2a
            transition_function = {
                self.round_2a: {
                    self.event_timeout2: self.round_2a,
                    self.event_2b: self.round_2b,
                },
                self.round_2b: {self.event_2a: self.round_2a},
            }
            final_states = {self.round_2b}
            event_to_timeout = {self.event_timeout2: self.timeout2}

        self.app2_class = AbciApp2

        class AbciApp3(AbciApp):
            initial_round_cls = self.round_3a
            transition_function = {
                self.round_3a: {
                    self.event_timeout3: self.round_3a,
                    self.event_3b: self.round_3b,
                },
                self.round_3b: {self.event_3a: self.round_3a},
            }
            final_states = {self.round_3b}
            event_to_timeout = {self.event_timeout3: self.timeout3}

        self.app3_class = AbciApp3

        class AbciApp2Faulty1(AbciApp):
            initial_round_cls = self.round_2a
            transition_function = {
                self.round_2a: {
                    self.event_timeout2: self.round_2a,
                    self.event_2b: self.round_2b,
                },
                self.round_2b: {self.event_2a: self.round_2a},
            }
            final_states = {self.round_2b}
            event_to_timeout = {self.event_timeout1: self.timeout2}

        self.app2_class_faulty1 = AbciApp2Faulty1

    def test_chain_two(self) -> None:
        """Test the AbciApp chain function."""

        abci_app_transition_mapping: AbciAppTransitionMapping = {
            self.round_1a: {self.event_1b: self.round_2a}
        }

        ComposedAbciApp = abci_app_chain((self.app1_class, self.app2_class), abci_app_transition_mapping)  # type: ignore

        assert ComposedAbciApp.initial_round_cls == self.round_1a
        assert ComposedAbciApp.transition_function == {
            self.round_1a: {
                self.event_timeout1: self.round_1a,
                self.event_1b: self.round_2a,
            },
            self.round_2a: {
                self.event_timeout2: self.round_2a,
                self.event_2b: self.round_2b,
            },
            self.round_2b: {self.event_2a: self.round_2a},
        }
        assert ComposedAbciApp.final_states == {self.round_2b}
        assert ComposedAbciApp.event_to_timeout == {
            self.event_timeout1: self.timeout1,
            self.event_timeout2: self.timeout2,
        }

    def test_chain_three(self) -> None:
        """Test the AbciApp chain function."""

        abci_app_transition_mapping: AbciAppTransitionMapping = {
            self.round_1a: {self.event_1b: self.round_2a},
            self.round_2a: {self.event_2b: self.round_3a},
        }

        ComposedAbciApp = abci_app_chain((self.app1_class, self.app2_class, self.app3_class), abci_app_transition_mapping)  # type: ignore

        assert ComposedAbciApp.initial_round_cls == self.round_1a
        assert ComposedAbciApp.transition_function == {
            self.round_1a: {
                self.event_timeout1: self.round_1a,
                self.event_1b: self.round_2a,
            },
            self.round_2a: {
                self.event_timeout2: self.round_2a,
                self.event_2b: self.round_3a,
            },
            self.round_3a: {
                self.event_timeout3: self.round_3a,
                self.event_3b: self.round_3b,
            },
            self.round_3b: {self.event_3a: self.round_3a},
        }
        assert ComposedAbciApp.final_states == {self.round_3b}
        assert ComposedAbciApp.event_to_timeout == {
            self.event_timeout1: self.timeout1,
            self.event_timeout2: self.timeout2,
            self.event_timeout3: self.timeout3,
        }

    def test_chain_two_negative_timeouts(self) -> None:
        """Test the AbciApp chain function."""

        abci_app_transition_mapping: AbciAppTransitionMapping = {
            self.round_1a: {self.event_1b: self.round_2a}
        }

        with pytest.raises(
            ValueError, match="but it is already defined in a prior app with timeout"
        ):
            _ = abci_app_chain((self.app1_class, self.app2_class_faulty1), abci_app_transition_mapping)  # type: ignore


def test_chain_period() -> None:
    """Test the period state chain function."""

    class period_state_A(BasePeriodState):
        """Period state A class"""

        def __init__(self, participants: List[str]):
            self._participants_a = participants

        @property
        def participants_a(self) -> List[str]:
            """Get the participants"""
            return self._participants_a

    class period_state_B(BasePeriodState):
        """Period state B class"""

        def __init__(self, participants: List[str]):
            self._participants_b = participants

        @property
        def participants_b(self) -> List[str]:
            """Get the participants"""
            return self._participants_b

    chained_period_state = period_state_chain((period_state_A, period_state_B))

    assert hasattr(chained_period_state, "participants_a")
    assert hasattr(chained_period_state, "participants_b")
