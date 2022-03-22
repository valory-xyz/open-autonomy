import os
import signal
import subprocess
import time
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Dict, Optional

import click
import yaml


REGISTRY_PATH = Path("packages/").absolute()
BUILD_DIR = Path("deployments/build/").absolute()
DOCKER_COMPOSE_FILE = BUILD_DIR / "docker-compose.yaml"


with open(str(DOCKER_COMPOSE_FILE), "r", encoding="utf-8") as fp:
    DOCKER_COMPOSE_CONFIG = yaml.safe_load(fp)


class AgentRunner:
    """Agent runner."""

    agent_id: int
    agent_data: Dict[str, str]
    process: Optional[subprocess.Popen]

    def __init__(self, agent_id: int) -> None:
        """Initialize object."""

        self.agent_id = agent_id
        self.agent_data = DOCKER_COMPOSE_CONFIG["services"][f"abci{self.agent_id}"]
        self.agent_env = os.environ.copy()
        self.agent_dir = TemporaryDirectory()

        agent_env_data = self.agent_data["environment"]
        for env_var in agent_env_data:
            key, value = env_var.split("=")
            self.agent_env[key] = value

        self.agent_env["ABCI_HOST"] = "localhost"
        self.agent_env["ABCI_PORT"] = f"2665{self.agent_id}"
        self.agent_env["TENDERMINT_URL"] = f"http://localhost:2664{self.agent_id}"
        self.agent_env["TENDERMINT_COM_URL"] = f"http://localhost:8080/{self.agent_id}"

    def start(
        self,
    ) -> None:
        """Start process."""

        agent_dir = Path(self.agent_dir.name)

        os.chdir(agent_dir)
        subprocess.run(
            ["cowsay", f"Loading {self.agent_env['VALORY_APPLICATION']}"],
            env=self.agent_env,
        )
        subprocess.run(
            [
                "python",
                "-m",
                "aea.cli",
                "--registry-path",
                str(REGISTRY_PATH),
                "fetch",
                self.agent_env["VALORY_APPLICATION"],
                "--local",
                "--alias",
                "agent",
            ],
            env=self.agent_env,
        )
        os.chdir(agent_dir / "agent")
        Path(agent_dir, "agent", "ethereum_private_key.txt").write_text(
            self.agent_env["AEA_KEY"]
        )

        subprocess.run(["aea", "add-key", "ethereum"], env=self.agent_env)
        subprocess.run(["aea", "install"], env=self.agent_env)
        self.process = subprocess.Popen(["aea", "run", "--aev"], env=self.agent_env)

    def stop(
        self,
    ) -> None:
        """Stop the process."""
        self.agent_dir.cleanup()
        if self.process is None:
            return

        os.kill(os.getpgid(self.process.pid), signal.SIGTERM)


@click.command()
@click.argument("agent", type=int, required=True)
def main(agent: int) -> None:
    """Agent runner."""
    runner = AgentRunner(agent)
    try:
        runner.start()
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        runner.stop()


if __name__ == "__main__":
    main()
