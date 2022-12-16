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

from unittest import mock
from typing import Type

import click
import pytest
from aea.test_tools.utils import as_context
from aea_test_autonomy.base_test_classes.agents import (
    BaseTestEnd2End,
    BaseTestEnd2EndExecution,
)
from aea_test_autonomy.docker.tendermint import (
    FlaskTendermintDockerImage,
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

    def test_defaults_test_instance(self) -> None:
        """Test defaults, after setup_class"""

        assert self.test_cls.agents == set()
        assert self.test_cls.subprocesses == []

        # no setup -> no tests needed for setup
        assert not hasattr(self.test_cls, "setup")


class TestBaseTestEnd2EndExecution(BaseTest):
    """TestBaseTestEnd2EndExecution"""

    test_cls = BaseTestEnd2EndExecution

    @staticmethod
    def mocked_flask_tendermint_image(nb_nodes: int) -> FlaskTendermintDockerImage:
        """Mocked FlaskTendermintDockerImage"""  # autouse fixture sets this

        tendermint_image = FlaskTendermintDockerImage(mock.Mock())
        FlaskTendermintDockerImage._extra_hosts = {}
        tendermint_image.nb_nodes = nb_nodes
        return tendermint_image

    def test_test_run_without_agents(self) -> None:
        """Test test_run without agents"""

        nb_nodes = 0

        test_instance = self.setup_test()
        test_instance._tendermint_image = self.mocked_flask_tendermint_image(nb_nodes)
        test_instance.test_run(nb_nodes=nb_nodes)

    def test_test_run_incorrect_agent_package(self) -> None:
        """Test test_run with one agent"""

        nb_nodes = 1
        test_instance = self.setup_test()
        test_instance._tendermint_image = self.mocked_flask_tendermint_image(nb_nodes)

        attribute = "agent_package"

        with pytest.raises(AttributeError, match=f"has no attribute '{attribute}'"):
            test_instance.test_run(nb_nodes)

        setattr(test_instance, attribute, "")
        with pytest.raises(click.exceptions.BadParameter):
            test_instance.test_run(nb_nodes)

        non_existent = "author/package"
        expected = f'Item "{non_existent}" not found in source folder'
        setattr(test_instance, attribute, non_existent)
        with pytest.raises(click.exceptions.ClickException, match=expected):
            test_instance.test_run(nb_nodes)

        wrong_version = "valory/hello_world:0.0.0"
        expected = "Wrong agent version in public ID: specified 0.0.0, found"
        setattr(test_instance, attribute, wrong_version)
        with pytest.raises(click.exceptions.ClickException, match=expected):
            test_instance.test_run(nb_nodes)

    def test_test_run_incorrect_skill_package(self) -> None:
        """Test incorrect skill package"""

        nb_nodes = 1
        test_instance = self.setup_test()
        test_instance._tendermint_image = self.mocked_flask_tendermint_image(nb_nodes)

        test_instance.agent_package = "valory/hello_world:0.1.0"
        attribute = "skill_package"

        with pytest.raises(AttributeError, match=f"has no attribute '{attribute}'"):
            test_instance.test_run(nb_nodes)

        for item in ("", "author/package", "valory/hello_world:0.0.0"):
            setattr(test_instance, attribute, item)  # same for "author/package"
            expected = 'Item "agent_00000" already exists in target folder "."'
            with pytest.raises(click.exceptions.ClickException, match=expected):
                test_instance.test_run(nb_nodes)
