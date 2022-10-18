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

"""Test 'scaffold fsm' subcommand."""

import importlib.util
import os
import shutil
from contextlib import suppress
from copy import copy
from importlib.machinery import ModuleSpec
from pathlib import Path
from tempfile import TemporaryDirectory

import click.testing
import pytest
from aea.cli.utils.config import get_default_author_from_cli_config
from aea.configurations.constants import PACKAGES
from aea.test_tools.test_cases import AEATestCaseEmpty

# trigger population of autonomy commands
import autonomy.cli.core  # noqa

from packages.valory import skills
from packages.valory.skills.abstract_round_abci.base import _MetaPayload

from tests.conftest import ROOT_DIR


VALORY_SKILLS_PATH = Path(os.path.join(*skills.__package__.split("."))).absolute()
fsm_specifications = list(VALORY_SKILLS_PATH.glob("**/fsm_specification.yaml"))


class BaseScaffoldFSMTest(AEATestCaseEmpty):
    """Test `scaffold fsm` subcommand."""

    _t: TemporaryDirectory

    @classmethod
    def setup_class(cls) -> None:
        """Setup class."""
        # we need to store the current value of the meta-class attribute
        # _MetaPayload.transaction_type_to_payload_cls, and restore it
        # in the teardown function. We do a shallow copy so we avoid
        # to modify the old mapping during the execution of the tests.
        cls.old_tx_type_to_payload_cls = copy(
            _MetaPayload.transaction_type_to_payload_cls
        )
        _MetaPayload.transaction_type_to_payload_cls = {}
        super().setup_class()

        cls.author = get_default_author_from_cli_config()

    @classmethod
    def setup(
        cls,
    ) -> None:
        """Setup test."""

        cls._t = TemporaryDirectory()
        cls.t = Path(cls._t.name)
        cls.packages_dir_path = str(cls.t / PACKAGES)

        shutil.copytree(ROOT_DIR / PACKAGES, cls.packages_dir_path)

        cls.cwd = Path.cwd()
        os.chdir(cls.t)

        cls.run_cli_command(
            "--registry-path",
            str(cls.packages_dir_path),
            "create",
            "--local",
            "--empty",
            cls.agent_name,
            "--author",
            cls.author,
        )

    def scaffold_fsm(self, fsm_spec_file: Path) -> click.testing.Result:
        """Scaffold FSM."""

        *_, skill_name, _ = fsm_spec_file.parts
        skill_name = f"test_skill_{skill_name}"
        scaffold_args = ["scaffold", "fsm", skill_name, "--local", "--spec"]
        cli_args = [
            "--registry-path",
            self.packages_dir_path,
            *scaffold_args,
            fsm_spec_file,
        ]
        scaffold_result = self.run_cli_command(*cli_args, cwd=self.t / self.agent_name)
        push_result = self.run_cli_command(
            "--registry-path",
            str(self.packages_dir_path),
            "push",
            "--local",
            "skill",
            f"{self.author}/{skill_name}",
            cwd=self.t / self.agent_name,
        )

        return scaffold_result, push_result

    @classmethod
    def teardown_class(cls) -> None:
        """Teardown the test class."""
        _MetaPayload.transaction_type_to_payload_cls = cls.old_tx_type_to_payload_cls  # type: ignore

    @classmethod
    def teardown(
        cls,
    ) -> None:
        """Teardown test."""
        os.chdir(cls.cwd)
        with suppress(OSError, PermissionError):
            cls._t.cleanup()


class TestScaffoldFSM(BaseScaffoldFSMTest):
    """Test `scaffold fsm` subcommand."""

    @pytest.mark.parametrize("fsm_spec_file", fsm_specifications)
    def test_scaffold_fsm(
        self, fsm_spec_file: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test scaffold fsm."""

        *_, skill_name, _ = fsm_spec_file.parts
        skill_name = f"test_skill_{skill_name}"
        scaffold_result, push_result = self.scaffold_fsm(fsm_spec_file)
        assert scaffold_result.exit_code == 0
        assert push_result.exit_code == 0

        monkeypatch.syspath_prepend(self.t)
        path = self.t / self.author / "skills" / skill_name
        for file in path.rglob("**/*.py"):
            module_spec = importlib.util.spec_from_file_location("name", file)
            assert isinstance(module_spec, ModuleSpec)
            module_type = importlib.util.module_from_spec(module_spec)
            module_spec.loader.exec_module(module_type)  # type: ignore


class TestScaffoldFSMAutonomyTests(BaseScaffoldFSMTest):
    """Test `scaffold fsm` subcommand."""

    @pytest.mark.parametrize("fsm_spec_file", fsm_specifications)
    def test_autonomy_test(self, fsm_spec_file: Path) -> None:
        """Run autonomy test on the scaffolded skill"""

        *_, skill_name, _ = fsm_spec_file.parts
        skill_name = f"test_skill_{skill_name}"
        self.scaffold_fsm(fsm_spec_file)
        cli_args = [
            "--registry-path",
            str(self.packages_dir_path),
            "test",
            "by-path",
            str(self.t / "packages" / self.author / "skills" / skill_name),
        ]

        result = self.run_cli_command(*cli_args)
        assert result.exit_code == 0
