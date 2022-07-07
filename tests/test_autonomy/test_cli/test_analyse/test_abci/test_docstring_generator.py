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

"""Tests for docstring generator."""


import os
import shutil
from pathlib import Path
from typing import Tuple

from tests.conftest import ROOT_DIR
from tests.test_autonomy.test_cli.base import BaseCliTest


class TestDocstrings(BaseCliTest):
    """Test `autonomy analyse abci docstrings`."""

    rounds_file_original: Path
    rounds_file_temp: Path
    cli_options: Tuple[str, ...] = ("analyse", "abci", "docstrings")
    rounds_file = Path("packages", "valory", "skills", "hello_world_abci", "rounds.py")

    @classmethod
    def setup(
        cls,
    ) -> None:
        """Setup class."""

        super().setup()

        shutil.copytree(ROOT_DIR / "packages", cls.t / "packages")
        os.chdir(cls.t)

        cls.rounds_file_original = Path(*ROOT_DIR.parts, *cls.rounds_file.parts)
        cls.rounds_file_temp = Path(*cls.t.parts, *cls.rounds_file.parts)

    def _get_expected_output(
        self,
    ) -> str:
        """Return expected output."""
        expcted_output = ""
        for file in sorted(self.t.glob("packages/*/skills/*/rounds.py")):
            expcted_output += f"Processing: {file.relative_to(self.t)}\n"
        return expcted_output

    def _corrupt_round_file(
        self,
    ) -> None:
        """Corrupt a round file."""

        string_to_replace = """3. ResetAndPauseRound
            - done: 1.
            - reset timeout: 0.
            - no majority: 0.\n"""

        rounds_file_content = self.rounds_file_original.read_text()
        rounds_file_content = rounds_file_content.replace(string_to_replace, "")
        self.rounds_file_temp.write_text(rounds_file_content)

    def _fix_round_file(
        self,
    ) -> None:
        """Fix the corrupted round file."""
        self.rounds_file_temp.write_text(self.rounds_file_original.read_text())

    def test_docstring_check(
        self,
    ) -> None:
        """Test after check"""

        packages_dir = (
            self.t.resolve().absolute().relative_to(Path.cwd().resolve().absolute())
            / "packages"
        )
        self.run_cli((str(packages_dir),))
        result = self.run_cli((str(packages_dir), "--check"))

        expcted_output = self._get_expected_output()
        expcted_output += "No update needed.\n"
        assert result.exit_code == 0, result.output
        assert result.output == expcted_output

    def test_docstring_check_fail(
        self,
    ) -> None:
        """Test after check"""

        packages_dir = (
            self.t.resolve().absolute().relative_to(Path.cwd().resolve().absolute())
            / "packages"
        )
        self.run_cli((str(packages_dir),))

        self._corrupt_round_file()
        result = self.run_cli((str(packages_dir), "--check"))
        self._fix_round_file()

        expcted_output = self._get_expected_output()
        expcted_output += (
            "Error: Following files needs updating.\n"
            + "\n"
            + str(Path("packages", "valory", "skills", "hello_world_abci", "rounds.py"))
            + "\n"
        )
        assert result.exit_code == 1, result.output
        assert result.output == expcted_output

    def test_fix_docstring(
        self,
    ) -> None:
        """Test after check"""

        packages_dir = (
            self.t.resolve().absolute().relative_to(Path.cwd().resolve().absolute())
            / "packages"
        )
        self.run_cli((str(packages_dir),))

        self._corrupt_round_file()
        result = self.run_cli((str(packages_dir),))

        expcted_output = self._get_expected_output()
        expcted_output += (
            "\nUpdated following files.\n"
            + "\n"
            + str(Path("packages", "valory", "skills", "hello_world_abci", "rounds.py"))
            + "\n"
        )
        assert result.exit_code == 0, result.output
        assert result.output == expcted_output
