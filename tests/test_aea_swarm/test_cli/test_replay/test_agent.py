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
from typing import Tuple
from unittest import mock
from tests.test_aea_swarm.test_cli.base import BaseCliTest
from tests.conftest import ROOT_DIR
from aea_swarm.cli import cli


class TestAgentRunner(BaseCliTest):
    """Test agent runner tool."""

    cli_options: Tuple[str, ...] = ("replay", "agent")
    packages_dir: Path = ROOT_DIR / "packages"
    output_dir: Path = ROOT_DIR
    keys_path: Path = ROOT_DIR / "deployments" / "keys" / "hardhat_keys.json"

    @classmethod
    def setup(cls) -> None:
        """Setup."""
        super().setup()

        os.chdir(ROOT_DIR)

    def test_run(
        self,
    ) -> None:
        """Test run."""

        self.cli_runner.invoke(
            cli,
            (
                "deploy",
                "build",
                "deployment",
                "valory/oracle_hardhat",
                str(self.keys_path),
                "--package-dir",
                str(self.packages_dir),
                "--force",
            ),
        )

        with mock.patch("aea_swarm.replay.agent.AgentRunner") as mock_obj:
            self.run_cli(("0",))
            mock_obj.assert_any_call()
