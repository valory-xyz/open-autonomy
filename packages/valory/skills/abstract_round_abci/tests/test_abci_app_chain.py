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

"""Test the abci_app_chain.py module of the skill."""

# pylint: skip-file

from typing import Tuple, Type

import pytest
from aea.exceptions import AEAEnforceError

from packages.valory.skills.abstract_round_abci.abci_app_chain import (
    AbciAppTransitionMapping,
    chain,
)
from packages.valory.skills.abstract_round_abci.base import (
    AbciApp,
    AbstractRound,
    DegenerateRound,
)


def make_round_class(name: str, bases: Tuple = (AbstractRound,)) -> Type[AbstractRound]:
    """Make a round class."""
    new_round_cls = type(name, bases, {})
    setattr(new_round_cls, "round_id", name)  # noqa: B010
    assert issubclass(new_round_cls, AbstractRound)  # nosec
    return new_round_cls


class TestAbciAppChaining:
    """Test chaning of AbciApps."""

    def setup(self) -> None:
        """Setup test."""
        self.round_1a = make_round_class("round_1a")
        self.round_1b = make_round_class("round_1b")
        self.round_1b_dupe = make_round_class("round_1b")  # duplicated round id
        self.round_1c = make_round_class("round_1c", (DegenerateRound,))

        self.round_2a = make_round_class("round_2a")
        self.round_2b = make_round_class("round_2b")
        self.round_2c = make_round_class("round_2c", (DegenerateRound,))
        self.round_2d = make_round_class("round_2d")

        self.round_3a = make_round_class("round_3a")
        self.round_3b = make_round_class("round_3b")
        self.round_3c = make_round_class("round_3c", (DegenerateRound,))

        self.event_1a = "event_1a"
        self.event_1b = "event_1b"
        self.event_1c = "event_1c"
        self.event_timeout1 = "timeout_1"

        self.event_2a = "event_2a"
        self.event_2b = "event_2b"
        self.event_2c = "event_2c"
        self.event_timeout2 = "timeout_2"

        self.event_3a = "event_3a"
        self.event_3b = "event_3b"
        self.event_3c = "event_3c"
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
                self.round_1b: {
                    self.event_1a: self.round_1a,
                    self.event_1c: self.round_1c,
                },
                self.round_1c: {},
            }
            final_states = {self.round_1c}
            event_to_timeout = {self.event_timeout1: self.timeout1}

        self.app1_class = AbciApp1

        class AbciApp2(AbciApp):
            initial_round_cls = self.round_2a
            transition_function = {
                self.round_2a: {
                    self.event_timeout2: self.round_2a,
                    self.event_2b: self.round_2b,
                },
                self.round_2b: {
                    self.event_2a: self.round_2a,
                    self.event_2c: self.round_2c,
                },
                self.round_2c: {},
            }
            final_states = {self.round_2c}
            event_to_timeout = {self.event_timeout2: self.timeout2}

        self.app2_class = AbciApp2

        class AbciApp3(AbciApp):
            initial_round_cls = self.round_3a
            transition_function = {
                self.round_3a: {
                    self.event_timeout3: self.round_3a,
                    self.event_3b: self.round_3b,
                },
                self.round_3b: {
                    self.event_3a: self.round_3a,
                    self.event_3c: self.round_3c,
                    self.event_1a: self.round_3a,  # duplicated event
                },
                self.round_3c: {},
            }
            final_states = {self.round_3c}
            event_to_timeout = {self.event_timeout3: self.timeout3}

        self.app3_class = AbciApp3

        class AbciApp3Dupe(AbciApp):
            initial_round_cls = self.round_3a
            transition_function = {
                self.round_3a: {
                    self.event_timeout3: self.round_3a,
                    self.event_3b: self.round_3b,
                },
                self.round_1b_dupe: {  # duplucated round id
                    self.event_3a: self.round_3a,
                    self.event_3c: self.round_3c,
                    self.event_1a: self.round_3a,  # duplicated event
                },
                self.round_3c: {},
            }
            final_states = {self.round_3c}
            event_to_timeout = {self.event_timeout3: self.timeout3}

        self.app3_class_dupe = AbciApp3Dupe

        class AbciApp2Faulty1(AbciApp):
            initial_round_cls = self.round_2a
            transition_function = {
                self.round_2a: {
                    self.event_timeout2: self.round_2a,
                    self.event_2b: self.round_2b,
                },
                self.round_2b: {
                    self.event_2a: self.round_2a,
                    self.event_2c: self.round_2c,
                },
                self.round_2c: {},
            }
            final_states = {self.round_2c}
            event_to_timeout = {self.event_timeout1: self.timeout2}

        self.app2_class_faulty1 = AbciApp2Faulty1

    def test_chain_two(self) -> None:
        """Test the AbciApp chain function."""

        abci_app_transition_mapping: AbciAppTransitionMapping = {
            self.round_1c: self.round_2a,
            self.round_2c: self.round_1a,
        }

        ComposedAbciApp = chain((self.app1_class, self.app2_class), abci_app_transition_mapping)  # type: ignore

        assert ComposedAbciApp.initial_round_cls == self.round_1a
        assert ComposedAbciApp.transition_function == {
            self.round_1a: {
                self.event_timeout1: self.round_1a,
                self.event_1b: self.round_1b,
            },
            self.round_1b: {
                self.event_1a: self.round_1a,
                self.event_1c: self.round_2a,
            },
            self.round_2a: {
                self.event_timeout2: self.round_2a,
                self.event_2b: self.round_2b,
            },
            self.round_2b: {
                self.event_2a: self.round_2a,
                self.event_2c: self.round_1a,
            },
        }
        assert ComposedAbciApp.final_states == set()
        assert ComposedAbciApp.event_to_timeout == {
            self.event_timeout1: self.timeout1,
            self.event_timeout2: self.timeout2,
        }

    def test_chain_three(self) -> None:
        """Test the AbciApp chain function."""

        abci_app_transition_mapping: AbciAppTransitionMapping = {
            self.round_1c: self.round_2a,
            self.round_2c: self.round_3a,
        }

        ComposedAbciApp = chain((self.app1_class, self.app2_class, self.app3_class), abci_app_transition_mapping)  # type: ignore

        assert ComposedAbciApp.initial_round_cls == self.round_1a
        assert ComposedAbciApp.transition_function == {
            self.round_1a: {
                self.event_timeout1: self.round_1a,
                self.event_1b: self.round_1b,
            },
            self.round_1b: {
                self.event_1a: self.round_1a,
                self.event_1c: self.round_2a,
            },
            self.round_2a: {
                self.event_timeout2: self.round_2a,
                self.event_2b: self.round_2b,
            },
            self.round_2b: {
                self.event_2a: self.round_2a,
                self.event_2c: self.round_3a,
            },
            self.round_3a: {
                self.event_timeout3: self.round_3a,
                self.event_3b: self.round_3b,
            },
            self.round_3b: {
                self.event_3a: self.round_3a,
                self.event_3c: self.round_3c,
                self.event_1a: self.round_3a,
            },
            self.round_3c: {},
        }
        assert ComposedAbciApp.final_states == {self.round_3c}
        assert ComposedAbciApp.event_to_timeout == {
            self.event_timeout1: self.timeout1,
            self.event_timeout2: self.timeout2,
            self.event_timeout3: self.timeout3,
        }

    def test_chain_two_negative_timeouts(self) -> None:
        """Test the AbciApp chain function."""

        abci_app_transition_mapping: AbciAppTransitionMapping = {
            self.round_1c: self.round_2a,
            self.round_2c: self.round_1a,
        }

        with pytest.raises(
            ValueError, match="but it is already defined in a prior app with timeout"
        ):
            _ = chain((self.app1_class, self.app2_class_faulty1), abci_app_transition_mapping)  # type: ignore

    def test_chain_two_negative_mapping_initial_states(self) -> None:
        """Test the AbciApp chain function."""

        abci_app_transition_mapping: AbciAppTransitionMapping = {
            self.round_1c: self.round_2b,
            self.round_2c: self.round_1a,
        }

        with pytest.raises(ValueError, match="Found non-initial state"):
            _ = chain((self.app1_class, self.app2_class), abci_app_transition_mapping)  # type: ignore

    def test_chain_two_negative_mapping_final_states(self) -> None:
        """Test the AbciApp chain function."""

        abci_app_transition_mapping: AbciAppTransitionMapping = {
            self.round_1c: self.round_2a,
            self.round_2b: self.round_1a,
        }

        with pytest.raises(ValueError, match="Found non-final state"):
            _ = chain((self.app1_class, self.app2_class), abci_app_transition_mapping)  # type: ignore

    def test_chain_two_dupe(self) -> None:
        """Test the AbciApp chain function."""

        abci_app_transition_mapping: AbciAppTransitionMapping = {
            self.round_1c: self.round_2a,
            self.round_2c: self.round_1a,
        }
        with pytest.raises(
            AEAEnforceError,
            match=r"round ids in common between abci apps are not allowed.*",
        ):
            chain((self.app1_class, self.app3_class_dupe), abci_app_transition_mapping)  # type: ignore

    def test_chain_with_abstract_abci_app_fails(self) -> None:
        """Test chaining with an abstract AbciApp fails."""
        self.app2_class._is_abstract = False
        self.app3_class._is_abstract = False
        with pytest.raises(
            AEAEnforceError,
            match=r"found non-abstract AbciApp during chaining: \['AbciApp2', 'AbciApp3'\]",
        ):
            abci_app_transition_mapping: AbciAppTransitionMapping = {
                self.round_1c: self.round_2a,
                self.round_2c: self.round_3a,
            }
            chain((self.app1_class, self.app2_class, self.app3_class), abci_app_transition_mapping)  # type: ignore
