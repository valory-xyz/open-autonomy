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

"""Develop CLI module."""

import time
from pathlib import Path
from typing import Any, Dict

import click
import yaml

from autonomy.constants import DEFAULT_BUILD_FOLDER
from autonomy.deploy.constants import PERSISTENT_DATA_DIR, TM_STATE_DIR
from autonomy.replay.agent import AgentRunner
from autonomy.replay.tendermint import build_tendermint_apps
from autonomy.replay.utils import fix_address_books, fix_config_files


REGISTRY_PATH = Path("packages/").absolute()
BUILD_DIR = Path(DEFAULT_BUILD_FOLDER).absolute()


@click.group(name="replay")
def replay_group() -> None:
    """Replay tools for agent services."""


@replay_group.command(name="agent")
@click.argument("agent", type=int, required=True)
@click.option(
    "--build",
    "build_path",
    type=click.Path(exists=True, dir_okay=True),
    default=BUILD_DIR,
    help="Path to build dir.",
)
@click.option(
    "--registry",
    "registry_path",
    type=click.Path(exists=True, dir_okay=True),
    default=REGISTRY_PATH,
    help="Path to registry folder.",
)
def run_agent(agent: int, build_path: Path, registry_path: Path) -> None:
    """Agent runner."""
    build_path = Path(build_path).absolute()
    registry_path = Path(registry_path).absolute()

    docker_compose_file = build_path / "docker-compose.yaml"
    docker_compose_config = load_docker_config(docker_compose_file)
    agent_data = docker_compose_config["services"][f"abci{agent}"]
    runner = AgentRunner(agent, agent_data, registry_path)
    try:
        runner.start()
        while True:  # pragma: nocover
            time.sleep(1)
    except KeyboardInterrupt:
        runner.stop()


@replay_group.command(name="tendermint")
@click.option(
    "--build",
    "build_dir",
    type=click.Path(dir_okay=True, exists=True),
    default=BUILD_DIR,
    help="Path to build directory.",
)
def run_tendermint(build_dir: Path) -> None:
    """Tendermint runner."""

    build_dir = Path(build_dir).absolute()
    dump_dir = build_dir / PERSISTENT_DATA_DIR / TM_STATE_DIR

    fix_address_books(build_dir)
    fix_config_files(build_dir)

    proxy_app, tendermint_network = build_tendermint_apps()

    try:
        tendermint_network.init(dump_dir)
    except FileNotFoundError as e:
        raise click.ClickException(str(e)) from e

    try:
        tendermint_network.start()
        proxy_app.run(host="localhost", port=8080)
    except KeyboardInterrupt:
        tendermint_network.stop()


def load_docker_config(file_path: Path) -> Dict[str, Any]:  # pragma: nocover
    """Load docker config."""
    with open(str(file_path), "r", encoding="utf-8") as fp:
        docker_compose_config = yaml.safe_load(fp)

    return docker_compose_config
