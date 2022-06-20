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

"""Test check-handlers command."""

import os
import platform
import shutil
from pathlib import Path
from typing import Tuple

import pytest

from tests.conftest import ROOT_DIR
from tests.test_autonomy.test_cli.base import BaseCliTest


@pytest.mark.skipif(
    platform.system() == "Windows", reason="Fix path resolutions on windows."
)
class TestCheckHandlers(BaseCliTest):
    """Test check-handlers command."""

    cli_options: Tuple[str, ...] = ("analyse", "abci", "check-handlers")
    config_file: Path
    config_file_temp: Path

    @classmethod
    def setup(cls) -> None:
        """Setup."""
        super().setup()
        shutil.copytree(ROOT_DIR / "packages", cls.t / "packages")
        os.chdir(cls.t)

    def _get_expected_output(
        self,
    ) -> str:
        """Generate expected output string."""
        return "\n".join(
            [f"Checking {file.parent}" for file in sorted(self.t.glob("**/skill.yaml"))]
        )

    def test_check_handlers(
        self,
    ) -> None:
        """Run tests."""

        result = self.run_cli(
            (
                str(self.t / "packages"),
                "--common",
                "abci,http,contract_api,ledger_api,signing",
                "--skip",
                "abstract_abci,counter,counter_client,hello_world_abci",
            )
        )

        assert result.exit_code == 0, result.output
        assert result.output.strip() == self._get_expected_output()

    def test_check_handlers_fail(
        self,
    ) -> None:
        """Test check-handlers command fail."""
        result = self.run_cli(
            (
                str(self.t / "packages"),
                "--common",
                "abci,http,contract_api,ledger_api,signing,dummy",
                "--skip",
                "abstract_abci,counter,counter_client,hello_world_abci",
            )
        )

        assert result.exit_code == 1
        assert "Common handler 'dummy' is not defined in" in result.output

    @classmethod
    def teardown(cls) -> None:
        """Teardown method."""

        os.chdir(cls.cwd)
        super().teardown()
