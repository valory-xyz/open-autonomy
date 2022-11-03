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

"""Tests for abstract_round_abci/test_tools/base.py"""

from pathlib import Path
from typing import Any, Dict, Type, cast

import pytest
from aea.helpers.base import cd
from aea.test_tools.utils import copy_class

from packages.valory.skills.abstract_round_abci.base import AbciAppDB, _MetaPayload
from packages.valory.skills.abstract_round_abci.behaviours import BaseBehaviour
from packages.valory.skills.abstract_round_abci.test_tools.base import (
    FSMBehaviourBaseCase,
)
from packages.valory.skills.abstract_round_abci.tests.data.dummy_abci import (
    PATH_TO_SKILL,
)
from packages.valory.skills.abstract_round_abci.tests.data.dummy_abci.behaviours import (
    DummyRoundBehaviour,
)
from packages.valory.skills.abstract_round_abci.tests.data.dummy_abci.rounds import (
    SynchronizedData,
)


participants = frozenset("abcd")


class TestFSMBehaviourBaseCaseSetup:
    """test TestFSMBehaviourBaseCaseSetup setup"""

    test_cls = Type[FSMBehaviourBaseCase]

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
        self.test_cls = cast(
            Type[FSMBehaviourBaseCase], copy_class(FSMBehaviourBaseCase)
        )

    def setup_test_cls(self, **kwargs) -> FSMBehaviourBaseCase:
        """Helper method to setup test to be tested"""

        with cd(self.test_cls.path_to_skill):
            self.test_cls.setup_class(**kwargs)

        test_instance = self.test_cls()  # type: ignore
        test_instance.setup()
        return test_instance

    def set_path_to_skill(self, path_to_skill: Path = PATH_TO_SKILL) -> None:
        """Set path_to_skill"""
        self.test_cls.path_to_skill = path_to_skill

    @pytest.mark.parametrize("kwargs", [{}, {"param_overrides": {"new_p": None}}])
    def test_setup(self, kwargs: Dict[str, Dict[str, Any]]) -> None:
        """Test setup"""

        self.set_path_to_skill()
        test_instance = self.setup_test_cls(**kwargs)
        assert test_instance
        assert hasattr(test_instance.behaviour.context.params, "new_p") == bool(kwargs)

    @pytest.mark.parametrize("behaviour", DummyRoundBehaviour.behaviours)
    def test_fast_forward_to_behaviour(self, behaviour: BaseBehaviour) -> None:
        """Test fast_forward_to_behaviour"""
        self.set_path_to_skill()
        test_instance = self.setup_test_cls()

        round_behaviour = test_instance._skill.skill_context.behaviours.main
        behaviour_id = behaviour.behaviour_id
        synchronized_data = SynchronizedData(
            AbciAppDB(setup_data=dict(participants=[participants]))
        )

        test_instance.fast_forward_to_behaviour(
            behaviour=round_behaviour,
            behaviour_id=behaviour_id,
            synchronized_data=synchronized_data,
        )
