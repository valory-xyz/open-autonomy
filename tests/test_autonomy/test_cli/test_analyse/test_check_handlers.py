# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022-2023 Valory AG
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
import shutil
from pathlib import Path
from typing import Tuple
from unittest import mock

import pytest
from aea.configurations.constants import DEFAULT_SKILL_CONFIG_FILE

from autonomy.analyse.handlers import check_handlers

from tests.conftest import ROOT_DIR
from tests.test_autonomy.test_cli.base import BaseCliTest


COMMON_HANDLERS = (
    "abci",
    "http",
    "contract_api",
    "ledger_api",
    "signing",
)

IGNORE_SKILLS = (
    "abstract_abci",
    "counter",
    "counter_client",
)


class TestCheckHandlers(BaseCliTest):
    """Test check-handlers command."""

    cli_options: Tuple[str, ...] = ("analyse", "handlers")
    config_file: Path
    config_file_temp: Path

    def setup(self) -> None:
        """Setup."""
        super().setup()

        shutil.copytree(ROOT_DIR / "packages", self.t / "packages")
        os.chdir(self.t)

        options = []
        for h in COMMON_HANDLERS:
            options += ["-h", h]

        for i in IGNORE_SKILLS:
            options += ["-i", i]

        self.cli_options = (*self.cli_options, *options)

    def test_check_handlers(
        self,
    ) -> None:
        """Run tests."""

        result = self.run_cli()
        assert result.exit_code == 0, result.output

        for yaml_file in sorted(
            Path(self.t / "packages").glob(f"*/*/*/{DEFAULT_SKILL_CONFIG_FILE}")
        ):
            if yaml_file.parent.name in IGNORE_SKILLS:
                assert f"Skipping {yaml_file.parent.name}" in result.output
            else:
                assert f"Checking {yaml_file.parent.name}" in result.output

    def test_check_handlers_fail(
        self,
    ) -> None:
        """Test check-handlers command fail."""
        result = self.run_cli(("-h", "dummy"))

        assert result.exit_code == 1, result.output
        assert "Common handler 'dummy' is not defined in" in result.output

    def test_check_handlers_missing_handler(
        self,
    ) -> None:
        """Test check-handlers command missing handler."""

        # Since the CLI catches exceptions, to test for raises we need to call check_handlers directly
        with pytest.raises(
            ValueError,
            match=r"Handler ABCIHandler declared in .* is missing from .*",
        ):
            # Mock dir() so module_attributes is = []
            with mock.patch("autonomy.analyse.handlers.dir", return_value=[]):
                # Mock Path.relative_to() and return any valid module so import_module does not fail
                with mock.patch(
                    "autonomy.analyse.handlers.load_handler_module_from_skill_path",
                    return_value=None,
                ):
                    check_handlers(
                        Path(
                            self.t,
                            "packages",
                            "valory",
                            "skills",
                            "abstract_abci",
                            "skill.yaml",
                        ),
                        [],
                    )


def test_check_handlers_missing_file() -> None:
    """Test check-handlers missing file."""

    # Since the CLI catches exceptions, to test for raises we need to call check_handlers directly
    with pytest.raises(FileNotFoundError, match="Handler file does not exist in file"):
        with mock.patch("pathlib.Path.relative_to", return_value=Path("dummy")):
            check_handlers(config_file=Path("file", "dummy"), common_handlers=[])
