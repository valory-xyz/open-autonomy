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


class AgentRunner:
    """Agent runner."""

    agent_id: int
    agent_data: Dict[str, str]
    registry_path: Path
    process: Optional[subprocess.Popen]

    def __init__(self, agent_id: int, agent_data: Dict, registry_path: Path) -> None:
        """Initialize object."""

        self.agent_id = agent_id
        self.agent_data = agent_data
        self.registry_path = registry_path
        self.agent_env = os.environ.copy()
        self.agent_dir = TemporaryDirectory()

        agent_env_data = self.agent_data["environment"]
        for env_var in agent_env_data:
            key, value = env_var.split("=")
            self.agent_env[key] = value

        self.agent_env["ABCI_HOST"] = "localhost"
        self.agent_env["ABCI_PORT"] = f"2665{self.agent_id}"
        self.agent_env["TENDERMINT_URL"] = f"http://localhost:8080"
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
                str(self.registry_path),
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
@click.option(
    "--build",
    "build_path",
    type=click.Path(exists=True, dir_okay=True),
    default=BUILD_DIR,
)
@click.option(
    "--registry",
    "registry_path",
    type=click.Path(exists=True, dir_okay=True),
    default=REGISTRY_PATH,
)
def main(agent: int, build_path: Path, registry_path: Path) -> None:
    """Agent runner."""
    build_path = Path(build_path).absolute()
    registry_path = Path(registry_path).absolute()

    docker_compose_file = build_path / "docker-compose.yaml"
    with open(str(docker_compose_file), "r", encoding="utf-8") as fp:
        docker_compose_config = yaml.safe_load(fp)
    agent_data = docker_compose_config["services"][f"abci{agent}"]
    runner = AgentRunner(agent, agent_data, registry_path)
    try:
        runner.start()
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        runner.stop()


if __name__ == "__main__":
    main()
