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
