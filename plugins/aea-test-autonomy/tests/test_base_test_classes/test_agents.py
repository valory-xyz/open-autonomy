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

"""Tests for aea-test-autonomy plugin base test classes for agent e2e tests."""

from typing import Type

from aea_test_autonomy.base_test_classes.agents import (
    BaseTestEnd2End,
)



class BaseTest:
    """BaseTest"""

    test_cls: Type[BaseTestEnd2End]

    def setup(self):
        """Setup test"""

        self.setup_class_called = False

    def teardown(self) -> None:
        """Teardown test"""

        if self.setup_class_called:
            self.test_cls.teardown_class()

    def setup_test(self) -> BaseTestEnd2End:
        """Setup test"""

        self.test_cls.setup_class()
        self.setup_class_called = True
        test_instance = self.test_cls()  # type: ignore

        return test_instance

    def test_setup_cls(self) -> None:
        """Test setup_class and setup"""

        test_instance = self.setup_test()
        assert isinstance(test_instance, self.test_cls)


class TestBaseTestEnd2End(BaseTest):
    """TestBaseTestEnd2End"""

    test_cls = BaseTestEnd2End

    def test_default_test_class(self) -> None:
        """Test default class attributes, prior to setup_class"""

        # BaseTestEnd2End overrides of BaseAEATestCase
        assert BaseTestEnd2End.capture_log is True
        assert BaseTestEnd2End.cli_log_options == ["-v", "DEBUG"]

        # default values likely to change
        assert BaseTestEnd2End.happy_path == ()
        assert BaseTestEnd2End.strict_check_strings == ()

        # no overwrite of parent class setup_class -> no tests needed for setup_class
        child, parent = BaseTestEnd2End, BaseTestEnd2End.__mro__[1]
        assert not child.__module__.split(".")[0] == parent.__module__.split(".")[0]
        assert child.setup_class.__func__ == parent.setup_class.__func__
