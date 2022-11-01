# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
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

"""Tests for abstract_round_abci/test_tools/common.py"""

from pathlib import Path
from typing import Type, cast

import pytest
from aea.helpers.base import cd

from packages.valory.skills.abstract_round_abci.test_tools.common import (
    BaseRandomnessBehaviourTest,
)
from packages.valory.skills.abstract_round_abci.tests.data import dummy_abci
from packages.valory.skills.abstract_round_abci.tests.data.dummy_abci.behaviours import (
    DummyKeeperSelectionBehaviour,
    DummyRandomnessBehaviour,
)
from packages.valory.skills.abstract_round_abci.tests.data.dummy_abci.rounds import (
    Event,
)


PATH_TO_SKILL = Path(dummy_abci.__file__).parent


class TestBaseRandomnessBehaviourTestSetup:
    """Test BaseRandomnessBehaviourTest setup."""

    test_cls: Type[BaseRandomnessBehaviourTest]

    def setup(self) -> None:
        """Setup test"""

        # must `copy` the class to avoid test interference
        test_cls = type(
            "BaseRandomnessBehaviourTest",
            BaseRandomnessBehaviourTest.__bases__,
            dict(BaseRandomnessBehaviourTest.__dict__),
        )
        self.test_cls = cast(Type[BaseRandomnessBehaviourTest], test_cls)

    def setup_test_cls(self) -> BaseRandomnessBehaviourTest:
        """Helper method to setup test to be tested"""

        with cd(self.test_cls.path_to_skill):
            self.test_cls.setup_class()

        test_instance = self.test_cls()  # type: ignore
        test_instance.setup()
        return test_instance

    def set_path_to_skill(self, path_to_skill: Path = PATH_TO_SKILL) -> None:
        """Set path_to_skill"""
        self.test_cls.path_to_skill = path_to_skill

    def set_randomness_behaviour_class(self) -> None:
        """Set randomness_behaviour_class"""
        self.test_cls.randomness_behaviour_class = DummyRandomnessBehaviour  # type: ignore

    def set_done_event(self) -> None:
        """Set done_event"""
        self.test_cls.done_event = Event.DONE

    def set_next_behaviour_class(self) -> None:
        """Set next_behaviour_class"""
        self.test_cls.next_behaviour_class = DummyKeeperSelectionBehaviour  # type: ignore

    def test_setup_randomness_behaviour_class_not_set(self) -> None:
        """Test setup randomness_behaviour_class not set."""

        self.set_path_to_skill()
        test_instance = self.setup_test_cls()
        expected = f"'{self.test_cls.__name__}' object has no attribute 'randomness_behaviour_class'"
        with pytest.raises(AttributeError, match=expected):
            test_instance.test_randomness_behaviour()  # pylint: disable=no-member

    def test_setup_done_event_not_set(self) -> None:
        """Test setup done_event = Event.DONE not set."""

        self.set_path_to_skill()
        self.set_randomness_behaviour_class()

        test_instance = self.setup_test_cls()
        expected = f"'{self.test_cls.__name__}' object has no attribute 'done_event'"
        with pytest.raises(AttributeError, match=expected):
            test_instance.test_randomness_behaviour()  # pylint: disable=no-member

    def test_setup_next_behaviour_class_not_set(self) -> None:
        """Test setup next_behaviour_class not set."""

        self.set_path_to_skill()
        self.set_randomness_behaviour_class()
        self.set_done_event()

        test_instance = self.setup_test_cls()
        expected = (
            f"'{self.test_cls.__name__}' object has no attribute 'next_behaviour_class'"
        )
        with pytest.raises(AttributeError, match=expected):
            test_instance.test_randomness_behaviour()  # pylint: disable=no-member

    def test_successful_setup_randomness_behaviour_test(self) -> None:
        """Test successful setup of the test class inheriting from BaseRandomnessBehaviourTest."""

        self.set_path_to_skill()
        self.set_randomness_behaviour_class()
        self.set_done_event()
        self.set_next_behaviour_class()
        test_instance = self.setup_test_cls()
        test_instance.test_randomness_behaviour()  # pylint: disable=no-member


class TestBaseRandomnessBehaviourTestRunning(BaseRandomnessBehaviourTest):
    """Test TestBaseRandomnessBehaviourTestRunning running."""

    path_to_skill = PATH_TO_SKILL
    randomness_behaviour_class = DummyRandomnessBehaviour  # type: ignore
    next_behaviour_class = DummyKeeperSelectionBehaviour  # type: ignore
    done_event = Event.DONE
