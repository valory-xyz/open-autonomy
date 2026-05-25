# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2024-2026 Valory AG
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

import pytest

from autonomy.cli import cli
from autonomy.constants import DEFAULT_BUILD_FOLDER
from autonomy.deploy.base import (
    TENDERMINT_COM_URL_PARAM,
    TENDERMINT_URL_PARAM,
    build_hash_id,
)
from autonomy.replay.agent import AgentRunner

from tests.conftest import ROOT_DIR, skip_docker_tests
from tests.test_autonomy.test_cli.base import BaseCliTest

OS_ENV_PATCH = mock.patch.dict(
    os.environ, values={**os.environ, "ALL_PARTICIPANTS": "[]"}, clear=True
)

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
                "ID=DUMMY",
                "LOG_FILE=DUMMY",
                "AEA_KEY=DUMMY",
                "AEA_AGENT=DUMMY",
                "ABCI_HOST=DUMMY",
                f"SKILL_ORACLE_ABCI_MODELS_PARAMS_ARGS_{TENDERMINT_URL_PARAM.upper()}=DUMMY",
                f"SKILL_ORACLE_ABCI_MODELS_PARAMS_ARGS_{TENDERMINT_COM_URL_PARAM.upper()}=DUMMY",
                "SKILL_ORACLE_ABCI_MODELS_PRICE_API_ARGS_URL=DUMMY",
                "SKILL_ORACLE_ABCI_MODELS_PRICE_API_ARGS_API_ID=DUMMY",
                "SKILL_ORACLE_ABCI_MODELS_PRICE_API_ARGS_PARAMETERS=DUMMY",
                "SKILL_ORACLE_ABCI_MODELS_PRICE_API_ARGS_RESPONSE_KEY=DUMMY",
                "SKILL_ORACLE_ABCI_MODELS_PRICE_API_ARGS_HEADERS=DUMMY",
                "SKILL_ORACLE_ABCI_MODELS_RANDOMNESS_API_ARGS_URL=DUMMY",
                "SKILL_ORACLE_ABCI_MODELS_RANDOMNESS_API_ARGS_API_ID=DUMMY",
                "SKILL_ORACLE_ABCI_MODELS_PARAMS_ARGS_RESET_PAUSE_DURATION=DUMMY",
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


class TestAgentRunnerValidation:
    """Unit-level coverage for the ``AgentRunner`` env-validation paths.

    These exercise the new ``ValueError`` guards added so that a build
    directory missing required env vars or carrying malformed entries
    surfaces a single-line Click error instead of a Python traceback.
    """

    @staticmethod
    def _service_with_env(env: list) -> dict:
        """Build a minimal docker-compose service block with the given env list."""
        return {
            "image": "valory/test:0.1.0",
            "environment": env,
        }

    def test_init_rejects_service_without_environment_block(self) -> None:
        """``AgentRunner.__init__`` rejects a service dict missing ``environment``."""
        with pytest.raises(ValueError, match=r"has no .environment. block"):
            AgentRunner(0, {"image": "valory/test:0.1.0"}, Path("."))

    def test_init_rejects_env_entry_without_equals_sign(self) -> None:
        """``AgentRunner.__init__`` rejects env entries not formatted as KEY=VALUE."""
        with pytest.raises(ValueError, match=r"not.*formatted as KEY=VALUE"):
            AgentRunner(
                0,
                self._service_with_env(["AEA_AGENT", "AEA_KEY=key"]),
                Path("."),
            )

    def test_init_preserves_equals_in_value(self) -> None:
        """Values containing ``=`` (e.g. base64 tokens) must round-trip whole.

        Splitting on the first ``=`` only is what makes this work.
        """
        runner = AgentRunner(
            0,
            self._service_with_env(["TOKEN=aGVsbG8=world=", "AEA_AGENT=v/a:0:b"]),
            Path("."),
        )
        assert runner.agent_env["TOKEN"] == "aGVsbG8=world="

    def test_start_rejects_missing_aea_agent(self, tmp_path: Path) -> None:
        """``start()`` raises ValueError with the rename hint when ``AEA_AGENT`` is absent."""
        runner = AgentRunner(
            0,
            self._service_with_env(["AEA_KEY=0xabc"]),
            tmp_path,
        )
        with pytest.raises(ValueError, match=r"VALORY_APPLICATION.*AEA_AGENT.*rename"):
            runner.start()

    def test_start_rejects_missing_aea_key(self, tmp_path: Path) -> None:
        """``start()`` raises ValueError when ``AEA_KEY`` is absent."""
        runner = AgentRunner(
            0,
            self._service_with_env(["AEA_AGENT=valory/agent:0.1.0:bafy"]),
            tmp_path,
        )
        # Bypass the aea fetch subprocess so we exercise only the env-var guard
        # path; the test would otherwise spawn a real subprocess and fail in CI.
        with mock.patch("autonomy.replay.agent.subprocess"), pytest.raises(
            ValueError, match=r"AEA_KEY"
        ):
            runner.start()


@skip_docker_tests
class TestAgentRunner(BaseCliTest):
    """Test agent runner tool."""

    cli_options: Tuple[str, ...] = ("replay", "agent")
    packages_dir: Path = ROOT_DIR / "packages"
    output_dir: Path = ROOT_DIR
    keys_path: Path = ROOT_DIR / "deployments" / "keys" / "hardhat_keys.json"

    def setup_method(self) -> None:
        """Setup test method."""
        super().setup_method()

        shutil.copytree(
            self.packages_dir / "valory" / "services" / "register_reset",
            self.t / "register_reset",
        )
        os.chdir(self.t / "register_reset")

    def test_run(self) -> None:
        """Test run."""

        build_dir = self.t / DEFAULT_BUILD_FOLDER.format(build_hash_id())
        with mock.patch("os.chown"), OS_ENV_PATCH:
            result = self.cli_runner.invoke(
                cli,
                (
                    "deploy",
                    "build",
                    str(self.keys_path),
                    "--local",
                    "--o",
                    str(build_dir),
                ),
            )

        assert result.exit_code == 0, result.output

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
