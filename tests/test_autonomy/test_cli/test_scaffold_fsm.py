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
from typing import Dict

import click.testing
import pytest
from aea.cli.utils.config import get_default_author_from_cli_config
from aea.test_tools.test_cases import AEATestCaseMany

# trigger population of autonomy commands
import autonomy.cli.core  # noqa

from packages.valory import skills
from packages.valory.skills.abstract_round_abci.base import _MetaPayload


VALORY_SKILLS_PATH = Path(os.path.join(*skills.__package__.split("."))).absolute()
fsm_specifications = list(VALORY_SKILLS_PATH.glob("**/fsm_specification.yaml"))


class BaseScaffoldFSMTest(AEATestCaseMany):
    """Test `scaffold fsm` subcommand."""

    _t: TemporaryDirectory
    agent_name: str = "test_agent"

    old_tx_type_to_payload_cls: Dict

    @classmethod
    def setup_class(cls) -> None:
        """Setup class."""
        super().setup_class()

        cls.author = get_default_author_from_cli_config()

    def setup(
        self,
    ) -> None:
        """Setup test."""

        # we need to store the current value of the meta-class attribute
        # _MetaPayload.transaction_type_to_payload_cls, and restore it
        # in the teardown function. We do a shallow copy so we avoid
        # to modify the old mapping during the execution of the tests.
        self.old_tx_type_to_payload_cls = copy(
            _MetaPayload.transaction_type_to_payload_cls
        )
        _MetaPayload.transaction_type_to_payload_cls = {}

        self.run_cli_command(
            "create",
            "--local",
            "--empty",
            self.agent_name,
            "--author",
            self.author,
        )

    def teardown(
        self,
    ) -> None:
        """Teardown test."""
        _MetaPayload.transaction_type_to_payload_cls = self.old_tx_type_to_payload_cls  # type: ignore
        with suppress(OSError, FileExistsError, PermissionError):
            shutil.rmtree(str(Path(self.t, self.agent_name)))

    def scaffold_fsm(self, fsm_spec_file: Path) -> click.testing.Result:
        """Scaffold FSM."""

        *_, skill_name, _ = fsm_spec_file.parts
        skill_name = f"test_skill_{skill_name}"
        scaffold_args = ["scaffold", "fsm", skill_name, "--local", "--spec"]
        cli_args = [
            *scaffold_args,
            fsm_spec_file,
        ]
        scaffold_result = self.run_cli_command(*cli_args, cwd=self.t / self.agent_name)

        return scaffold_result


class TestScaffoldFSM(BaseScaffoldFSMTest):
    """Test `scaffold fsm` subcommand."""

    @pytest.mark.parametrize("fsm_spec_file", fsm_specifications)
    def test_scaffold_fsm(
        self, fsm_spec_file: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test scaffold files are loadable."""

        *_, skill_name, _ = fsm_spec_file.parts
        skill_name = f"test_skill_{skill_name}"
        scaffold_result = self.scaffold_fsm(fsm_spec_file)
        assert scaffold_result.exit_code == 0

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
        scaffold_result = self.scaffold_fsm(fsm_spec_file)
        assert scaffold_result.exit_code == 0
        cli_args = [
            "-m",
            "aea.cli",
            "test",
            "by-path",
            str(self.t / self.agent_name / "skills" / skill_name),
        ]

        # we use a subprocess rather than click.CliRunner because we want to isolate
        # the Python environment of the current pytest process with the subcall to pytest.main
        # from the AEA command `aea test by-path ...`
        result = self.start_subprocess(*cli_args)
        result.wait(timeout=60.0)
        assert result.returncode == 0
