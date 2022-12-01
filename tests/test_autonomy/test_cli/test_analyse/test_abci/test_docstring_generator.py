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
from pathlib import Path
from typing import Tuple
from unittest import mock

from aea.configurations.constants import PACKAGES

from packages.valory.skills.hello_world_abci import rounds

from tests.conftest import ROOT_DIR
from tests.test_autonomy.test_cli.base import BaseCliTest


class TestDocstrings(BaseCliTest):
    """Test `autonomy analyse docstrings`."""

    rounds_file_original: Path
    rounds_file_temp: Path
    skill_name: str = "hello_world_abci"
    cli_options: Tuple[str, ...] = ("analyse", "docstrings")
    rounds_file = Path(PACKAGES, "valory", "skills", skill_name, "rounds.py")

    def setup(
        self,
    ) -> None:
        """Setup test method."""
        super().setup()

        os.chdir(self.t)

        packages_dir = self.t / PACKAGES
        packages_dir.mkdir()

        (packages_dir / "valory").mkdir()
        (packages_dir / "valory" / "skills").mkdir()
        (packages_dir / "valory" / "skills" / self.skill_name).mkdir()

        self.rounds_file_original = Path(*ROOT_DIR.parts, *self.rounds_file.parts)
        self.rounds_file_temp = Path(*self.t.parts, *self.rounds_file.parts)

        self.rounds_file_temp.write_text(self.rounds_file_original.read_text())

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

        string_to_replace = """4. ResetAndPauseRound
            - done: 1.
            - no majority: 0.
            - reset timeout: 0.\n"""

        rounds_file_content = self.rounds_file_original.read_text()
        rounds_file_content = rounds_file_content.replace(string_to_replace, "")
        self.rounds_file_temp.write_text(rounds_file_content)

    def test_docstring_check(
        self,
    ) -> None:
        """Test after check"""

        self.run_cli()
        result = self.run_cli()

        assert result.exit_code == 0, result.output
        assert f"Processing skill {self.skill_name} with author valory" in result.output
        assert "No update needed." in result.output

    def test_docstring_check_fail(
        self,
    ) -> None:
        """Test after check"""

        self.run_cli()
        self._corrupt_round_file()

        new_callable = mock.PropertyMock(return_value=str(self.rounds_file_temp))
        with mock.patch.object(rounds, "__file__", new_callable=new_callable):
            result = self.run_cli()

        assert result.exit_code == 1, result.output
        assert "Error: Following files needs updating" in result.output

    def test_fix_docstring(
        self,
    ) -> None:
        """Test after check"""

        self._corrupt_round_file()
        assert (
            self.rounds_file_temp.read_text() != self.rounds_file_original.read_text()
        )

        new_callable = mock.PropertyMock(return_value=str(self.rounds_file_temp))
        with mock.patch.object(rounds, "__file__", new_callable=new_callable):
            result = self.run_cli(("--update",))
        assert result.exit_code == 0, result.output
        assert "Updated following files" in result.output
        assert (
            self.rounds_file_temp.read_text() == self.rounds_file_original.read_text()
        )
