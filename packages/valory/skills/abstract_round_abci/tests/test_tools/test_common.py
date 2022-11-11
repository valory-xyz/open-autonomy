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

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Type, cast

import pytest
from aea.helpers.base import cd

from packages.valory.skills.abstract_round_abci.base import _MetaPayload
from packages.valory.skills.abstract_round_abci.test_tools.common import (
    BaseRandomnessBehaviourTest,
    BaseSelectKeeperBehaviourTest,
    CommonBaseCase,
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


class BaseCommonBaseCaseTestSetup(ABC):
    """BaseRandomnessBehaviourTestSetup"""

    test_cls: Type[CommonBaseCase]
    _test_cls: Type[CommonBaseCase]

    @abstractmethod
    def run_test(self, test_instance: Any) -> None:
        """Tun a test"""

    @classmethod
    def setup_class(cls) -> None:
        """Setup class"""
        cls.old_value = _MetaPayload.transaction_type_to_payload_cls.copy()  # type: ignore
        _MetaPayload.transaction_type_to_payload_cls.clear()

    @classmethod
    def teardown_class(cls) -> None:
        """Teardown class"""
        _MetaPayload.transaction_type_to_payload_cls = cls.old_value  # type: ignore

    def setup(self) -> None:
        """Setup test"""

        # must `copy` the class to avoid test interference
        test_cls = type(
            self._test_cls.__name__,
            self._test_cls.__bases__,
            dict(self._test_cls.__dict__),
        )
        self.test_cls = cast(Type[CommonBaseCase], test_cls)

    def setup_test_cls(self) -> CommonBaseCase:
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

    def set_select_keeper_behaviour_class(self) -> None:
        """Set randomness_behaviour_class"""
        self.test_cls.select_keeper_behaviour_class = DummyKeeperSelectionBehaviour  # type: ignore

    def set_done_event(self) -> None:
        """Set done_event"""
        self.test_cls.done_event = Event.DONE  # type: ignore

    def set_next_behaviour_class(self, next_behaviour_class: Type) -> None:
        """Set next_behaviour_class"""
        self.test_cls.next_behaviour_class = next_behaviour_class  # type: ignore


class TestBaseRandomnessBehaviourTestSetup(BaseCommonBaseCaseTestSetup):
    """Test BaseRandomnessBehaviourTest setup."""

    _test_cls = BaseRandomnessBehaviourTest

    def run_test(self, test_instance: BaseRandomnessBehaviourTest) -> None:
        """Run test"""
        test_instance.test_randomness_behaviour()

    def test_setup_randomness_behaviour_class_not_set(self) -> None:
        """Test setup randomness_behaviour_class not set."""

        self.set_path_to_skill()
        test_instance = cast(BaseRandomnessBehaviourTest, self.setup_test_cls())
        expected = f"'{self.test_cls.__name__}' object has no attribute 'randomness_behaviour_class'"
        with pytest.raises(AttributeError, match=expected):
            self.run_test(test_instance)

    def test_setup_done_event_not_set(self) -> None:
        """Test setup done_event = Event.DONE not set."""

        self.set_path_to_skill()
        self.set_randomness_behaviour_class()

        test_instance = cast(BaseRandomnessBehaviourTest, self.setup_test_cls())
        expected = f"'{self.test_cls.__name__}' object has no attribute 'done_event'"
        with pytest.raises(AttributeError, match=expected):
            self.run_test(test_instance)

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
            self.run_test(test_instance)

    def test_successful_setup_randomness_behaviour_test(self) -> None:
        """Test successful setup of the test class inheriting from BaseRandomnessBehaviourTest."""

        self.set_path_to_skill()
        self.set_randomness_behaviour_class()
        self.set_done_event()
        self.set_next_behaviour_class(DummyKeeperSelectionBehaviour)
        test_instance = cast(BaseRandomnessBehaviourTest, self.setup_test_cls())
        self.run_test(test_instance)


class TestBaseRandomnessBehaviourTestRunning(BaseRandomnessBehaviourTest):
    """Test TestBaseRandomnessBehaviourTestRunning running."""

    path_to_skill = PATH_TO_SKILL
    randomness_behaviour_class = DummyRandomnessBehaviour  # type: ignore
    next_behaviour_class = DummyKeeperSelectionBehaviour  # type: ignore
    done_event = Event.DONE


class TestBaseSelectKeeperBehaviourTestSetup(BaseCommonBaseCaseTestSetup):
    """Test BaseRandomnessBehaviourTest setup."""

    _test_cls = BaseSelectKeeperBehaviourTest

    def run_test(self, test_instance: BaseSelectKeeperBehaviourTest) -> None:
        """Run test"""
        test_instance.test_select_keeper_preexisting_keeper()

    def test_setup_select_keeper_behaviour_class_not_set(self) -> None:
        """Test setup randomness_behaviour_class not set."""

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
    select_keeper_behaviour_class = DummyKeeperSelectionBehaviour  # type: ignore
    next_behaviour_class = DummyFinalBehaviour  # type: ignore
    done_event = Event.DONE
