# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021 Valory AG
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

"""Script to create environment for n agents."""

import sys
from pathlib import Path
from shutil import rmtree
from typing import List, Tuple

from env_config import KEYS, PRICE_APIS, RANDOMNESS_APIS
from env_script_templates import (
    ABCI_CONFIG_SCRIPT,
    ABCI_NODE_TEMPLATE,
    BASE_SETUP,
    DOCKER_COMPOSE_TEMPLATE,
    TENDERMINT_NODE_TEMPLATE,
)

ROOT_DIR = Path("../..").resolve().absolute()
CONFIG_DIRECTORY = Path("./").resolve() / "configure_agents"
LOGS_DIR = Path("./").resolve() / "logs"


def build_config_script(
    node_id: int,
    price_api: List[Tuple[str, str]],
    randomness_api: List[Tuple[str, str]],
    max_participants: int,
    eth_key: str,
) -> str:
    """Build `abci_n.sh` for runtime agent config."""

    extra_config = "\n".join(
        [
            f"aea config set vendor.valory.skills.price_estimation_abci.models.price_api.args.{key} {value}"
            for key, value in price_api
        ]
        + [
            f"aea config set vendor.valory.skills.price_estimation_abci.models.randomness_api.args.{key} {value}"
            for key, value in randomness_api
        ]
    )

    return ABCI_CONFIG_SCRIPT.format(
        extra_config=extra_config,
        node_id=node_id,
        max_participants=max_participants,
        eth_key=eth_key,
    )


def build_tendermint_node_config(node_id: int) -> str:
    """Build tendermint node config for docker compose."""

    return TENDERMINT_NODE_TEMPLATE.format(
        node_id=node_id,
        localnet_address_postfix=node_id + 3,
        localnet_port_range=node_id,
    )


def build_abci_node_config(node_id: int, max_participants: int) -> str:
    """Build tendermint node config for docker compose."""

    return ABCI_NODE_TEMPLATE.format(
        node_id=node_id,
        localnet_address_postfix=node_id + max_participants + 3,
        root_dir=str(ROOT_DIR),
        max_participants=max_participants,
    )


def build_docker_compose_yml(max_participants: int) -> str:
    """Build content for `docker-compose.yml`."""

    tendermint_nodes = ""
    abci_nodes = ""

    for i in range(max_participants):
        tendermint_nodes += build_tendermint_node_config(i)
        abci_nodes += build_abci_node_config(i, max_participants)

    return DOCKER_COMPOSE_TEMPLATE.format(
        tendermint_nodes=tendermint_nodes, abci_nodes=abci_nodes, root_dir=str(ROOT_DIR)
    )


def build_agent_config(node_id: int, number_of_agents: int) -> None:
    """Build agent config."""

    config_script = build_config_script(
        node_id,
        PRICE_APIS[node_id % len(PRICE_APIS)],
        RANDOMNESS_APIS[node_id % len(RANDOMNESS_APIS)],
        number_of_agents,
        KEYS[node_id],
    )

    with open(CONFIG_DIRECTORY / f"abci{node_id}.sh", "w+", encoding="utf-8") as file:
        file.write(config_script)

    with open("./docker-compose.yml", "w+", encoding="utf-8") as file:
        file.write(build_docker_compose_yml(number_of_agents))


def main() -> None:
    """Main function."""

    args = sys.argv[1:]
    try:
        number_or_agents = int(args.pop())
    except IndexError:
        number_or_agents = 4

    if CONFIG_DIRECTORY.is_dir():
        rmtree(str(CONFIG_DIRECTORY))

    CONFIG_DIRECTORY.mkdir()
    for i in range(number_or_agents):
        build_agent_config(i, number_or_agents)

    with open(CONFIG_DIRECTORY / f"base_setup.sh", "w+", encoding="utf-8") as file:
        file.write(BASE_SETUP)


if __name__ == "__main__":
    main()
