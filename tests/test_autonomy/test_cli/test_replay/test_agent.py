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
import shutil
from pathlib import Path
from typing import Any, Tuple
from unittest import mock

from autonomy.cli import cli
from autonomy.replay.agent import AgentRunner

from tests.conftest import ROOT_DIR, skip_docker_tests
from tests.test_autonomy.test_cli.base import BaseCliTest


DOCKER_COMPOSE_DATA = {
    "version": "2.4",
    "services": {
        "abci0": {
            "mem_limit": "1024m",
            "mem_reservation": "256M",
            "cpus": 1,
            "container_name": "abci0",
            "image": "valory/open-autonomy-open-aea:oracle_deployable-0.1.0",
            "environment": [
                "LOG_FILE=DUMMY",
                "AEA_KEY=DUMMY",
                "VALORY_APPLICATION=DUMMY",
                "ABCI_HOST=DUMMY",
                "MAX_PARTICIPANTS=DUMMY",
                "TENDERMINT_URL=DUMMY",
                "TENDERMINT_COM_URL=DUMMY",
                "ID=DUMMY",
                "SKILL_ORACLE_ABCI_MODELS_PRICE_API_ARGS_URL=DUMMY",
                "SKILL_ORACLE_ABCI_MODELS_PRICE_API_ARGS_API_ID=DUMMY",
                "SKILL_ORACLE_ABCI_MODELS_PRICE_API_ARGS_PARAMETERS=DUMMY",
                "SKILL_ORACLE_ABCI_MODELS_PRICE_API_ARGS_RESPONSE_KEY=DUMMY",
                "SKILL_ORACLE_ABCI_MODELS_PRICE_API_ARGS_HEADERS=DUMMY",
                "SKILL_ORACLE_ABCI_MODELS_RANDOMNESS_API_ARGS_URL=DUMMY",
                "SKILL_ORACLE_ABCI_MODELS_RANDOMNESS_API_ARGS_API_ID=DUMMY",
                "SKILL_ORACLE_ABCI_MODELS_PARAMS_ARGS_OBSERVATION_INTERVAL=DUMMY",
                "SKILL_ORACLE_ABCI_MODELS_PARAMS_ARGS_BROADCAST_TO_SERVER=DUMMY",
                "SKILL_ORACLE_ABCI_MODELS_SERVER_API_ARGS_URL=DUMMY",
                "SKILL_ORACLE_ABCI_MODELS_BENCHMARK_TOOL_ARGS_LOG_DIR=DUMMY",
                "LEDGER_ADDRESS=DUMMY",
                "LEDGER_CHAIN_ID=DUMMY",
            ],
        }
    },
}


def ctrl_c(*args: Any) -> None:
    """Send control C."""

    raise KeyboardInterrupt()


@skip_docker_tests
class TestAgentRunner(BaseCliTest):
    """Test agent runner tool."""

    cli_options: Tuple[str, ...] = ("replay", "agent")
    packages_dir: Path = ROOT_DIR / "packages"
    output_dir: Path = ROOT_DIR
    keys_path: Path = ROOT_DIR / "deployments" / "keys" / "hardhat_keys.json"

    def setup(self) -> None:
        """Setup test method."""
        super().setup()

        shutil.copytree(
            self.packages_dir / "valory" / "services" / "hello_world",
            self.t / "hello_world",
        )
        os.chdir(self.t / "hello_world")

    def test_run(self) -> None:
        """Test run."""

        with mock.patch("os.chown"):
            result = self.cli_runner.invoke(
                cli,
                (
                    "deploy",
                    "build",
                    str(self.keys_path),
                    "--force",
                    "--local",
                    "--o",
                    str(self.t / "abci_build"),
                ),
            )

        assert result.exit_code == 0, result.output

        build_dir = self.t / "abci_build"
        with mock.patch.object(AgentRunner, "start", new=ctrl_c), mock.patch.object(
            AgentRunner, "stop"
        ) as stop_mock, mock.patch(
            "autonomy.cli.replay.load_docker_config", new=lambda x: DOCKER_COMPOSE_DATA
        ):
            result = self.run_cli(
                ("--registry", str(self.packages_dir), "0", "--build", str(build_dir))
            )
            assert result.exit_code == 0, result.output
            stop_mock.assert_any_call()
