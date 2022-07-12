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

"""Tests for specs commands."""


import importlib
import os
import shutil
from pathlib import Path
from typing import Tuple

from autonomy.analyse.abci.app_spec import DFA

from tests.conftest import ROOT_DIR
from tests.test_autonomy.test_cli.base import BaseCliTest


class TestGenerateSpecs(BaseCliTest):
    """Test generate-app-specs"""

    cli_options: Tuple[str, ...] = ("analyse", "abci", "generate-app-specs")
    skill_path = Path("packages", "valory", "skills", "hello_world_abci", "rounds")
    app_name = "HelloWorldAbciApp"

    cls_name: str
    dfa: DFA

    @classmethod
    def setup(cls) -> None:
        """Setup class."""
        super().setup()

        module_name = ".".join(cls.skill_path.parts)
        module = importlib.import_module(module_name)
        cls.cls_name = ".".join([module_name, cls.app_name])

        abci_app_cls = getattr(module, cls.app_name)
        cls.dfa = DFA.abci_to_dfa(abci_app_cls, cls.cls_name)

    def get_expected_output(self, output_format: str) -> str:
        """Get expected output."""

        temp_file = self.t / "temp"
        self.dfa.dump(temp_file, output_format)

        return temp_file.read_text(encoding="utf-8")

    def _run_test(self, output_format: str) -> None:
        """Run test for given output format type."""

        output_file = self.t / "fsm"
        result = self.run_cli((self.cls_name, str(output_file), f"--{output_format}"))

        assert result.exit_code == 0
        assert output_file.read_text() == self.get_expected_output(output_format)

    def test_generate_yaml(
        self,
    ) -> None:
        """Run tests."""

        self._run_test(DFA.OutputFormats.YAML)

    def test_generate_json(
        self,
    ) -> None:
        """Run tests."""

        self._run_test(DFA.OutputFormats.JSON)

    def test_generate_mermaid(
        self,
    ) -> None:
        """Run tests."""

        self._run_test(DFA.OutputFormats.MERMAID)

    def test_failures(
        self,
    ) -> None:
        """Test failures."""

        *module, cls = self.cls_name.split(".")
        cls_name = ".".join([*module, "dummy", cls])
        result = self.run_cli((cls_name, "fsm", "--yaml"))

        assert result.exit_code == 1, result.output
        assert "Failed to load" in result.stdout, result.output
        assert (
            "Please, verify that AbciApps and classes are correctly defined within the module."
            in result.stdout
        ), result.output

        *module, cls = self.cls_name.split(".")
        cls_name = ".".join([*module, cls[:-1]])
        result = self.run_cli((cls_name, "fsm", "--yaml"))

        assert result.exit_code == 1, result.output
        assert """Class "HelloWorldAbciAp" is not in""" in result.stdout, result.output


class TestCheckSpecs(BaseCliTest):
    """Test `check-app-specs` command."""

    cli_options: Tuple[str, ...] = ("analyse", "abci", "check-app-specs")
    skill_path = Path("packages", "valory", "skills", "hello_world_abci", "rounds")
    app_name = "HelloWorldAbciApp"

    specification_path: Path
    cls_name: str
    dfa: DFA

    @classmethod
    def setup(cls) -> None:
        """Setup class."""
        super().setup()

        module_name = ".".join(cls.skill_path.parts)
        module = importlib.import_module(module_name)
        cls.cls_name = ".".join([module_name, cls.app_name])

        abci_app_cls = getattr(module, cls.app_name)
        cls.dfa = DFA.abci_to_dfa(abci_app_cls, cls.cls_name)

        cls.specification_path = cls.skill_path.parent / "fsm_specification.yaml"
        shutil.copytree(ROOT_DIR / "packages", cls.t / "packages")
        os.chdir(cls.t)

    def _corrupt_spec_file(
        self,
    ) -> None:
        """Corrupt spec file to fail the check."""
        content = self.specification_path.read_text()
        content = content.replace(
            "(SelectKeeperRound, ROUND_TIMEOUT): RegistrationRound\n", ""
        )
        self.specification_path.write_text(content)

    def _fix_corrupt_file(
        self,
    ) -> None:
        """Fix corrupt file."""
        self.specification_path.write_text(
            Path(*ROOT_DIR.absolute().parts, *self.specification_path.parts).read_text()
        )

    def test_one_pass(
        self,
    ) -> None:
        """Test with one class."""
        self._fix_corrupt_file()
        result = self.run_cli(
            ("--app-class", self.cls_name, "--infile", str(self.specification_path))
        )

        assert result.exit_code == 0
        assert (
            result.output
            == "Checking : packages.valory.skills.hello_world_abci.rounds.HelloWorldAbciApp\nCheck successful\n"
        )

    def test_one_fail(
        self,
    ) -> None:
        """Test with one class failing."""
        self._corrupt_spec_file()
        result = self.run_cli(
            ("--app-class", self.cls_name, "--infile", str(self.specification_path))
        )

        assert result.exit_code == 1
        assert (
            result.output
            == "Checking : packages.valory.skills.hello_world_abci.rounds.HelloWorldAbciApp\nCheck failed.\n"
        )

    def test_check_all(
        self,
    ) -> None:
        """Test --check-all flag."""

        self._fix_corrupt_file()
        result = self.run_cli(
            (
                "--check-all",
                "--packages-dir",
                str(self.t / "packages"),
            )
        )

        assert result.exit_code == 0
        assert "Check successful." in result.output

    def test_check_all_fail(
        self,
    ) -> None:
        """Test --check-all flag."""

        self._corrupt_spec_file()
        result = self.run_cli(
            (
                "--check-all",
                "--packages-dir",
                str(self.t / "packages"),
            )
        )

        assert result.exit_code == 1
        assert (
            "Specifications did not match for following definitions." in result.output
        )

    def test_failures(
        self,
    ) -> None:
        """Test with one class."""
        self._fix_corrupt_file()

        result = self.run_cli(("--infile", str(self.specification_path)))

        assert result.exit_code == 1, result.output
        assert "Please provide class name for ABCI app." in result.output, result.output

        result = self.run_cli(("--app-class", self.cls_name))

        assert result.exit_code == 1, result.output
        assert (
            "Please provide path to specification file." in result.output
        ), result.output

    @classmethod
    def teardown(cls) -> None:
        """Teardown method."""
        os.chdir(cls.cwd)
        super().teardown()
