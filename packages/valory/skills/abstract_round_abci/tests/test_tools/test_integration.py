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

"""Tests for abstract_round_abci/test_tools/integration.py"""

from typing import Type, cast

from aea.test_tools.utils import copy_class

from packages.valory.skills.abstract_round_abci.base import _MetaPayload
from packages.valory.skills.abstract_round_abci.test_tools.integration import (
    IntegrationBaseCase,
)


class TestIntegrationBaseCase:
    """TestIntegrationBaseCase"""

    test_cls: Type[IntegrationBaseCase]

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
        test_cls = copy_class(IntegrationBaseCase)
        self.test_cls = cast(Type[IntegrationBaseCase], test_cls)

    def teardown(self) -> None:
        """Teardown test"""
        self.test_cls.teardown_class()  # otherwise keeps hanging

    def setup_test_cls(self) -> IntegrationBaseCase:
        """Helper method to setup test to be tested"""

        self.test_cls.setup_class()

        test_instance = self.test_cls()  # type: ignore
        test_instance.setup()
        return test_instance
