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

"""Test agent runner."""


import os
from pathlib import Path
from typing import Any, Tuple
from unittest import mock

from autonomy.cli import cli
from autonomy.replay.tendermint import TendermintNetwork

from tests.conftest import ROOT_DIR
from tests.test_autonomy.test_cli.base import BaseCliTest


def ctrl_c(*args: Any) -> None:
    """Send control C."""

    raise KeyboardInterrupt()


class TestAgentRunner(BaseCliTest):
    """Test agent runner tool."""

    cli_options: Tuple[str, ...] = ("replay", "tendermint")
    packages_dir: Path = ROOT_DIR / "packages"
    output_dir: Path = ROOT_DIR
    keys_path: Path = ROOT_DIR / "deployments" / "keys" / "hardhat_keys.json"

    @classmethod
    def setup(cls) -> None:
        """Setup."""
        super().setup()

        os.chdir(ROOT_DIR)

    def test_run(self) -> None:
        """Test run."""

        self.cli_runner.invoke(
            cli,
            (
                "deploy",
                "build",
                "deployment",
                "valory/oracle_hardhat",
                str(self.keys_path),
                "--packages-dir",
                str(self.packages_dir),
                "--force",
            ),
        )

        with mock.patch.object(TendermintNetwork, "init"), mock.patch.object(
            TendermintNetwork, "start", new=ctrl_c
        ), mock.patch.object(TendermintNetwork, "stop") as stop_mock:
            result = self.run_cli(())
            assert result.exit_code == 0
            stop_mock.assert_any_call()
