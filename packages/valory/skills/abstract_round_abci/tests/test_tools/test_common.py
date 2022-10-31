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

from typing import cast
from unittest import mock
from pathlib import Path

import pytest

from aea.helpers.base import cd
from aea.components.base import _CheckUsedDependencies  # for temporary patch


from packages.valory.skills.abstract_round_abci.common import RandomnessBehaviour, SelectKeeperBehaviour, BaseBehaviour
from packages.valory.skills.abstract_round_abci.test_tools.common import (
    BaseRandomnessBehaviourTest,
    BaseSelectKeeperBehaviourTest,
)

# need to change
from packages.valory.skills.transaction_settlement_abci.rounds import Event
from packages.valory.skills.transaction_settlement_abci.behaviours import (
    RandomnessTransactionSubmissionBehaviour,
    SelectKeeperTransactionSubmissionBehaviourA,
)


test_skill = "transaction_settlement_abci"
PATH_TO_SKILL = BaseRandomnessBehaviourTest.path_to_skill.parent / test_skill


# TODO:
#  the following doesn't work, because it cannot access the other concrete skill (e.g. simple_abci)
#  autonomy -s test --cov by-path ./packages/valory/skills/abstract_round_abci/
#  to run the test one can use the pytest directly
#  pytest -vv packages/valory/skills/abstract_round_abci/tests/test_tools/test_common.py --cov packages/valory/skills/abstract_round_abci/ --cov-report term-missing


class TestBaseRandomnessBehaviourTestSetup:
    """Test BaseRandomnessBehaviourTest setup."""

    def setup(self) -> None:
        """Setup test"""

        # must `copy` the class to avoid test interference
        test_cls = type(
            "BaseRandomnessBehaviourTest",
            BaseRandomnessBehaviourTest.__bases__,
            dict(BaseRandomnessBehaviourTest.__dict__)
        )
        self.test_cls = cast(BaseRandomnessBehaviourTest, test_cls)

    def setup_test_cls(self) -> BaseRandomnessBehaviourTest:
        """Helper method to setup test to be tested"""

        with cd(self.test_cls.path_to_skill):
            # another temporary patch, needed for imports from other modules
            with mock.patch.object(_CheckUsedDependencies, "run_check", return_value=lambda: None):
                self.test_cls.setup_class()

        test_instance = self.test_cls()  # type: ignore
        test_instance.setup()
        return test_instance

    def set_path_to_skill(self, path_to_skill: Path = PATH_TO_SKILL) -> None:
        """Set path_to_skill"""
        self.test_cls.path_to_skill = path_to_skill

    def set_randomness_behaviour_class(self) -> None:
        """Set randomness_behaviour_class"""
        self.test_cls.randomness_behaviour_class = RandomnessTransactionSubmissionBehaviour

    def set_done_event(self) -> None:
        """Set done_event"""
        self.test_cls.done_event = Event.DONE

    def set_next_behaviour_class(self) -> None:
        """Set next_behaviour_class"""
        self.test_cls.next_behaviour_class = SelectKeeperTransactionSubmissionBehaviourA

    def test_setup_fails_without_skill_path_overwrite(self):
        """Test setup fails without skill path overwrite."""

        # we must overwrite since it is accessed in _prepare_skill, else load will fail
        # -> skill_config.directory = cls.path_to_skill
        with pytest.raises(AttributeError, match="'AbstractRoundBehaviour' object has no attribute 'behaviours'"):
            self.setup_test_cls()

    def test_setup_randomness_behaviour_class_not_set(self):
        """Test setup randomness_behaviour_class not set."""

        self.set_path_to_skill()
        test_instance = self.setup_test_cls()
        expected = f"'{self.test_cls.__name__}' object has no attribute 'randomness_behaviour_class'"
        with pytest.raises(AttributeError, match=expected):
            test_instance.test_randomness_behaviour()

    def test_setup_done_event_not_set(self):
        """Test setup done_event = Event.DONE not set."""

        # NOTE: if moved to top first test fails!? -> reason: _CheckUsedDependencies
        self.set_path_to_skill()
        self.set_randomness_behaviour_class()

        test_instance = self.setup_test_cls()
        expected = f"'{self.test_cls.__name__}' object has no attribute 'done_event'"
        with pytest.raises(AttributeError, match=expected):
            test_instance.test_randomness_behaviour()

    def test_setup_next_behaviour_class_not_set(self):
        """Test setup next_behaviour_class not set."""

        self.set_path_to_skill()
        self.set_randomness_behaviour_class()
        self.set_done_event()

        test_instance = self.setup_test_cls()
        expected = f"'{self.test_cls.__name__}' object has no attribute 'next_behaviour_class'"
        with pytest.raises(AttributeError, match=expected):
            test_instance.test_randomness_behaviour()

    def test_successful_setup_randomness_behaviour_test(self):
        """Test successful setup of the test class inheriting from BaseRandomnessBehaviourTest."""

        self.set_path_to_skill()
        self.set_randomness_behaviour_class()
        self.set_done_event()
        self.set_next_behaviour_class()
        assert self.setup_test_cls()


class TestBaseRandomnessBehaviourTestRunning(BaseRandomnessBehaviourTest):
    """Test TestBaseRandomnessBehaviourTestRunning running."""

    path_to_skill = PATH_TO_SKILL
    randomness_behaviour_class = RandomnessTransactionSubmissionBehaviour
    next_behaviour_class = SelectKeeperTransactionSubmissionBehaviourA
    done_event = Event.DONE
