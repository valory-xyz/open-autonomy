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

"""Tools to build and run agents from existing deployments."""

import contextlib
import os
import shutil
import signal
import subprocess  # nosec
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Dict, List, Optional

from aea_ledger_ethereum.test_tools.constants import ETHEREUM_PRIVATE_KEY_FILE


class AgentRunner:
    """Agent runner."""

    agent_id: int
    agent_data: Dict[str, str]
    registry_path: Path
    process: Optional[subprocess.Popen]  # nosec
    aea_cli: List[str] = [sys.executable, "-m", "aea.cli"]
    agent_alias: str = "agent"

    def __init__(self, agent_id: int, agent_data: Dict, registry_path: Path) -> None:
        """Initialize object."""

        self.agent_id = agent_id
        self.agent_data = agent_data
        self.registry_path = registry_path
        self.agent_env = os.environ.copy()
        self.agent_dir = TemporaryDirectory()  # pylint: disable=consider-using-with
        self.cwd = Path(".").resolve().absolute()

        agent_env_data = self.agent_data["environment"]
        for env_var in agent_env_data:
            key, value = env_var.split("=")
            self.agent_env[key] = value

        # TODO: Create appropriate constants
        self.agent_env["ABCI_HOST"] = "localhost"
        self.agent_env["ABCI_PORT"] = f"2665{self.agent_id}"
        self.agent_env["TENDERMINT_URL"] = f"http://localhost:8080/{self.agent_id}"
        self.agent_env["TENDERMINT_COM_URL"] = f"http://localhost:8080/{self.agent_id}"

    def start(
        self,
    ) -> None:
        """Start process."""

        agent_dir = Path(self.agent_dir.name)
        os.chdir(agent_dir)

        # TODO: replace with more appropriate env var name; we mean an agent here
        print(f"Loading {self.agent_env['VALORY_APPLICATION']}")
        subprocess.run(  # nosec  # pylint: disable=subprocess-run-check
            [
                *self.aea_cli,
                "--registry-path",
                str(self.registry_path),
                "fetch",
                self.agent_env["VALORY_APPLICATION"],
                "--local",
                "--alias",
                self.agent_alias,
            ],
            env=self.agent_env,
        )
        os.chdir(agent_dir / self.agent_alias)
        Path(agent_dir, self.agent_alias, ETHEREUM_PRIVATE_KEY_FILE).write_text(
            self.agent_env["AEA_KEY"], encoding="utf-8"
        )

        subprocess.run(  # nosec # pylint: disable=subprocess-run-check
            [*self.aea_cli, "add-key", "ethereum"], env=self.agent_env
        )
        subprocess.run(  # nosec # pylint: disable=subprocess-run-check
            [*self.aea_cli, "install"], env=self.agent_env
        )
        self.process = subprocess.Popen(  # nosec # pylint: disable=subprocess-run-check,consider-using-with
            [*self.aea_cli, "run", "--aev"], env=self.agent_env
        )

    def stop(
        self,
    ) -> None:
        """Stop the process."""

        os.chdir(str(self.cwd))
        with contextlib.suppress(OSError, PermissionError, FileNotFoundError):
            shutil.rmtree(str(self.agent_dir))

        if self.process is None:
            return  # pragma: no cover

        self.process.poll()
        if self.process.returncode is None:  # stop only pending processes
            os.kill(self.process.pid, signal.SIGTERM)

        self.process.wait(timeout=5)
        self.process.terminate()
        self.process = None
