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

import json
import os
import shutil
from pathlib import Path
from typing import Tuple

from tests.conftest import ROOT_DIR
from tests.test_autonomy.test_cli.base import BaseCliTest


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
        cls.config_file = ROOT_DIR / "scripts" / "handler_config.json"
        cls.config_file_temp = cls.t / "handler_config.json"

        os.chdir(cls.t)

    def _create_config_file(
        self,
    ) -> None:
        """Create config file."""
        self.config_file_temp.write_text(self.config_file.read_text())

    def _create_bad_config_file(
        self,
    ) -> None:
        """Create config file."""
        config_content = self.config_file.read_text()
        config_data = json.loads(config_content)
        config_data["common_handlers"] += [
            "dummy",
        ]

        self.config_file_temp.write_text(json.dumps(config_data))

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
        self._create_config_file()
        result = self.run_cli(
            (str(self.t / "packages"), f"--handler-config={self.config_file_temp}")
        )

        assert result.exit_code == 0, result.output
        assert result.output.strip() == self._get_expected_output()

    def test_check_handlers_fail(
        self,
    ) -> None:
        """Test check-handlers command fail."""
        self._create_bad_config_file()
        result = self.run_cli(
            (str(self.t / "packages"), f"--handler-config={self.config_file_temp}")
        )

        assert result.exit_code == 1
        assert "Common handler 'dummy' is not defined in" in result.output

    @classmethod
    def teardown(cls) -> None:
        """Teardown method."""

        os.chdir(cls.cwd)
        super().teardown()
