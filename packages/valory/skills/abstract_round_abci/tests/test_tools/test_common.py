# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022-2023 Valory AG
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

from typing import Type, Union, cast

import pytest

from packages.valory.skills.abstract_round_abci.test_tools.common import (
    BaseRandomnessBehaviourTest,
    BaseSelectKeeperBehaviourTest,
)
from packages.valory.skills.abstract_round_abci.tests.data.dummy_abci import (
    PATH_TO_SKILL,
)
from packages.valory.skills.abstract_round_abci.tests.data.dummy_abci.behaviours import (
    DummyFinalBehaviour,
    DummyKeeperSelectionBehaviour,
    DummyRandomnessBehaviour,
)
from packages.valory.skills.abstract_round_abci.tests.data.dummy_abci.rounds import (
    Event,
)
from packages.valory.skills.abstract_round_abci.tests.test_tools.base import (
    FSMBehaviourTestToolSetup,
)


class BaseCommonBaseCaseTestSetup(FSMBehaviourTestToolSetup):
    """BaseRandomnessBehaviourTestSetup"""

    test_cls: Type[Union[BaseRandomnessBehaviourTest, BaseSelectKeeperBehaviourTest]]

    def set_done_event(self) -> None:
        """Set done_event"""
        self.test_cls.done_event = Event.DONE

    def set_next_behaviour_class(self, next_behaviour_class: Type) -> None:
        """Set next_behaviour_class"""
        self.test_cls.next_behaviour_class = next_behaviour_class


class TestBaseRandomnessBehaviourTestSetup(BaseCommonBaseCaseTestSetup):
    """Test BaseRandomnessBehaviourTest setup."""

    test_cls: Type[BaseRandomnessBehaviourTest] = BaseRandomnessBehaviourTest

    def set_randomness_behaviour_class(self) -> None:
        """Set randomness_behaviour_class"""
        self.test_cls.randomness_behaviour_class = DummyRandomnessBehaviour  # type: ignore

    def test_setup_randomness_behaviour_class_not_set(self) -> None:
        """Test setup randomness_behaviour_class not set."""

        self.set_path_to_skill()
        test_instance = cast(BaseRandomnessBehaviourTest, self.setup_test_cls())
        expected = f"'{self.test_cls.__name__}' object has no attribute 'randomness_behaviour_class'"
        with pytest.raises(AttributeError, match=expected):
            test_instance.test_randomness_behaviour()

    def test_setup_done_event_not_set(self) -> None:
        """Test setup done_event = Event.DONE not set."""

        self.set_path_to_skill()
        self.set_randomness_behaviour_class()

        test_instance = cast(BaseRandomnessBehaviourTest, self.setup_test_cls())
        expected = f"'{self.test_cls.__name__}' object has no attribute 'done_event'"
        with pytest.raises(AttributeError, match=expected):
            test_instance.test_randomness_behaviour()

    def test_setup_next_behaviour_class_not_set(self) -> None:
        """Test setup next_behaviour_class not set."""

        self.set_path_to_skill()
        self.set_randomness_behaviour_class()
        self.set_done_event()

        test_instance = cast(BaseRandomnessBehaviourTest, self.setup_test_cls())
        expected = (
            f"'{self.test_cls.__name__}' object has no attribute 'next_behaviour_class'"
        )
        with pytest.raises(AttributeError, match=expected):
            test_instance.test_randomness_behaviour()

    def test_successful_setup_randomness_behaviour_test(self) -> None:
        """Test successful setup of the test class inheriting from BaseRandomnessBehaviourTest."""

        self.set_path_to_skill()
        self.set_randomness_behaviour_class()
        self.set_done_event()
        self.set_next_behaviour_class(DummyKeeperSelectionBehaviour)
        test_instance = cast(BaseRandomnessBehaviourTest, self.setup_test_cls())
        test_instance.test_randomness_behaviour()


class TestBaseRandomnessBehaviourTestRunning(BaseRandomnessBehaviourTest):
    """Test TestBaseRandomnessBehaviourTestRunning running."""

    path_to_skill = PATH_TO_SKILL
    randomness_behaviour_class = DummyRandomnessBehaviour
    next_behaviour_class = DummyKeeperSelectionBehaviour
    done_event = Event.DONE


class TestBaseSelectKeeperBehaviourTestSetup(BaseCommonBaseCaseTestSetup):
    """Test BaseRandomnessBehaviourTest setup."""

    test_cls: Type[BaseSelectKeeperBehaviourTest] = BaseSelectKeeperBehaviourTest

    def set_select_keeper_behaviour_class(self) -> None:
        """Set select_keeper_behaviour_class"""
        self.test_cls.select_keeper_behaviour_class = DummyKeeperSelectionBehaviour  # type: ignore

    def test_setup_select_keeper_behaviour_class_not_set(self) -> None:
        """Test setup select_keeper_behaviour_class not set."""

        self.set_path_to_skill()
        test_instance = cast(BaseSelectKeeperBehaviourTest, self.setup_test_cls())
        expected = f"'{self.test_cls.__name__}' object has no attribute 'select_keeper_behaviour_class'"
        with pytest.raises(AttributeError, match=expected):
            test_instance.test_select_keeper_preexisting_keeper()

    def test_setup_done_event_not_set(self) -> None:
        """Test setup done_event = Event.DONE not set."""

        self.set_path_to_skill()
        self.set_select_keeper_behaviour_class()

        test_instance = cast(BaseSelectKeeperBehaviourTest, self.setup_test_cls())
        expected = f"'{self.test_cls.__name__}' object has no attribute 'done_event'"
        with pytest.raises(AttributeError, match=expected):
            test_instance.test_select_keeper_preexisting_keeper()

    def test_setup_next_behaviour_class_not_set(self) -> None:
        """Test setup next_behaviour_class not set."""

        self.set_path_to_skill()
        self.set_select_keeper_behaviour_class()
        self.set_done_event()

        test_instance = cast(BaseSelectKeeperBehaviourTest, self.setup_test_cls())
        expected = (
            f"'{self.test_cls.__name__}' object has no attribute 'next_behaviour_class'"
        )
        with pytest.raises(AttributeError, match=expected):
            test_instance.test_select_keeper_preexisting_keeper()

    def test_successful_setup_select_keeper_behaviour_test(self) -> None:
        """Test successful setup of the test class inheriting from BaseSelectKeeperBehaviourTest."""

        self.set_path_to_skill()
        self.set_select_keeper_behaviour_class()
        self.set_done_event()
        self.set_next_behaviour_class(DummyFinalBehaviour)
        test_instance = cast(BaseSelectKeeperBehaviourTest, self.setup_test_cls())
        test_instance.test_select_keeper_preexisting_keeper()


class TestBaseSelectKeeperBehaviourTestRunning(BaseSelectKeeperBehaviourTest):
    """Test BaseSelectKeeperBehaviourTest running."""

    path_to_skill = PATH_TO_SKILL
    select_keeper_behaviour_class = DummyKeeperSelectionBehaviour
    next_behaviour_class = DummyFinalBehaviour
    done_event = Event.DONE
