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

"""Script to create environment for benchmarking n agents."""

import sys

from typing import List, Tuple
from pathlib import Path
from shutil import rmtree

CONFIG_DIRECTORY = Path() / "configure_agents"

KEYS: List[str] = [
    "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80",
    "0x59c6995e998f97a5a0044966f0945389dc9e86dae88c7a8412f4603b6b78690d",
    "0x5de4111afa1a4b94908f83103eb1f1706367c2e68ca870fc3fb9a804cdab365a",
    "0x7c852118294e51e653712a81e05800f419141751be58f605c371e15141b007a6",
    "0x47e179ec197488593b187f80a00eb0da91f1b9d0b13f8733639f19c30a34926a",
    "0x8b3a350cf5c34c9194ca85829a2df0ec3153be0318b5e2d3348e872092edffba",
    "0x92db14e403b83dfe3df233f83dfa3a0d7096f21ca9b0d6d6b8d88b2b4ec1564e",
    "0x4bbbf85ce3377467afe5d46f804f221813b2bb87f24d81f60f1fcdbf7cbf4356",
    "0xdbda1821b80551c9d65939329250298aa3472ba22feea921c0cf5d620ea67b97",
    "0x2a871d0798f97d79848a013d4936a73bf4cc922c825d33c1cf7073dff6d409c6",
    "0xf214f2b2cd398c806f84e317254e0f0b801d0643303237d97a22a48e01628897",
    "0x701b615bbdfb9de65240bc28bd21bbc0d996645a3dd57e7b12bc2bdf6f192c82",
    "0xa267530f49f8280200edf313ee7af6b827f2a8bce2897751d06a843f644967b1",
    "0x47c99abed3324a2707c28affff1267e45918ec8c3f20b8aa892e8b065d2942dd",
    "0xc526ee95bf44d8fc405a158bb884d9d1238d99f0612e9f33d006bb0789009aaa",
    "0x8166f546bab6da521a8369cab06c5d2b9e46670292d85c875ee9ec20e84ffb61",
    "0xea6c44ac03bff858b476bba40716402b03e41b8e97e276d1baec7c37d42484a0",
    "0x689af8efa8c651a91ad287602527f3af2fe9f6501a7ac4b061667b5a93e037fd",
    "0xde9be858da4a475276426320d5e9262ecfc3ba460bfac56360bfa6c4c28b4ee0",
    "0xdf57089febbacf7ba0bc227dafbffa9fc08a93fdc68e1e42411a14efcf23656e",
]

RANDOMNESS_APIS: List[List[Tuple[str, str]]] = [
    [
        ("url", "https://drand.cloudflare.com/public/latest"),
        ("api_id", "cloudflare"),
    ],
    [
        ("url", "https://api.drand.sh/public/latest"),
        ("api_id", "protocollabs1"),
    ],
    [
        ("url", "https://api2.drand.sh/public/latest"),
        ("api_id", "protocollabs2"),
    ],
    [
        ("url", "https://api3.drand.sh/public/latest"),
        ("api_id", "protocollabs3"),
    ],
]

PRICE_APIS: List[List[Tuple[str, str]]] = [
    [
        ("url", "https://api.coingecko.com/api/v3/simple/price"),
        ("api_id", "coingecko"),
        (
            "parameters",
            """'[["ids", "bitcoin"],["vs_currencies", "usd"]]'  --type list""",
        ),
        ("response_key", "'bitcoin:usd'"),
    ],
    [
        (
            "url",
            "https://ftx.com/api/markets/BTC/USD",
        ),
        ("api_id", "ftx"),
        ("response_key", "result:last"),
    ],
    [
        ("url", "https://api.coinbase.com/v2/prices/BTC-USD/buy"),
        ("api_id", "coinbase"),
        ("response_key", "'data:amount'"),
    ],
    [
        ("url", "https://api.binance.com/api/v3/ticker/price"),
        ("api_id", "binance"),
        ("parameters", """'[["symbol", "BTCUSDT"]]' --type list"""),
        ("response_key", "price"),
    ],
]

ABCI_CONFIG_SCRIPT: str = """
#!/usr/bin/env sh

cp ../configure_agents/keys/ethereum_private_key_{node_id}.txt ethereum_private_key.txt

aea add-key ethereum

aea config set vendor.valory.connections.abci.config.use_tendermint False
aea config set vendor.valory.skills.price_estimation_abci.models.params.args.consensus.max_participants {max_participants}
aea config set vendor.valory.skills.price_estimation_abci.models.params.args.round_timeout_seconds 5
aea config set vendor.valory.skills.price_estimation_abci.models.params.args.tendermint_url http://node{node_id}:26657
aea config set vendor.valory.connections.ledger.config.ledger_apis.ethereum.address http://hardhat:8545
{extra_config}
aea build
"""

DOCKER_COMPOSE_TEMPLATE: str = """version: "3"

services:
  hardhat:
    container_name: hardhat
    image: "node:16.7.0"
    ports:
      - "8545:8545"
    volumes:
      - ../../third_party/safe-contracts:/home/ubuntu/build
    working_dir: /home/ubuntu/build
    entrypoint: "/bin/bash"
    command: [ "/usr/local/bin/yarn", "run", "hardhat", "node", "--port", "8545"]
    networks:
      localnet:
        ipv4_address: 192.167.11.2

{tendermint_nodes}

{abci_nodes}

networks:
  localnet:
    driver: bridge
    ipam:
      driver: default
      config:
        - subnet: 192.167.11.0/24
"""

TENDERMINT_NODE_TEMPLATE: str = """
  node{node_id}:
    container_name: node{node_id}
    image: "tendermint/localnode"
    cpus: 0.1
    environment:
      - ID={node_id}
      - LOG=${{LOG:-tendermint.log}}
    volumes:
      - ./build:/tendermint:Z
    working_dir: /tendermint
    entrypoint: /bin/bash
    command: wait-for-it.sh -t 120 hardhat:8545 -- wrapper.sh node --consensus.create_empty_blocks=true --proxy_app=tcp://abci{node_id}:26658
    networks:
      localnet:
        ipv4_address: 192.167.11.{localnet_address_postfix}
    depends_on:
      - hardhat
"""

ABCI_NODE_TEMPLATE: str = """
  abci{node_id}:
    container_name: abci{node_id}
    image: "valory/price_estimation:0.1.0"
    build:
      context: ../..
      dockerfile: benchmark/check_consensus_time/Dockerfile
    volumes:
      - ./:/home/ubuntu/build
      - ./logs/:/logs:z
    entrypoint: /bin/bash
    command: ["/usr/bin/wait-for-it", "-t", "120", "hardhat:8545", "--", "../run.sh", "abci{node_id}"]
    networks:
      localnet:
        ipv4_address: 192.167.11.{localnet_address_postfix}
    depends_on:
      - hardhat
      - node{node_id}
"""


def build_config_script(
    node_id: int,
    price_api: List[Tuple[str, str]],
    randomness_api: List[Tuple[str, str]],
    max_participants: int,
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
        extra_config=extra_config, node_id=node_id, max_participants=max_participants
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
        node_id=node_id, localnet_address_postfix=node_id + max_participants + 3
    )


def build_docker_compose_yml(max_participants: int) -> str:
    """Build content for `docker-compose.yml`."""

    tendermint_nodes = ""
    abci_nodes = ""

    for i in range(max_participants):
        tendermint_nodes += build_tendermint_node_config(i)
        abci_nodes += build_abci_node_config(i, max_participants)

    return DOCKER_COMPOSE_TEMPLATE.format(
        tendermint_nodes=tendermint_nodes, abci_nodes=abci_nodes
    )


def build_agent_config(node_id: int, number_of_agents: int) -> None:
    """Build agent config."""

    config_script = build_config_script(
        node_id,
        PRICE_APIS[node_id % len(PRICE_APIS)],
        RANDOMNESS_APIS[node_id % len(RANDOMNESS_APIS)],
        number_of_agents,
    )

    with open(CONFIG_DIRECTORY / f"abci{node_id}.sh", "w+", encoding="utf-8") as file:
        file.write(config_script)

    with open(
        CONFIG_DIRECTORY / "keys" / f"ethereum_private_key_{node_id}.txt",
        "w+",
        encoding="utf-8",
    ) as file:
        file.write(KEYS[node_id])

    with open("./docker-compose.yml", "w+", encoding="utf-8") as file:
        file.write(build_docker_compose_yml(number_of_agents))


def main() -> None:
    """Main function."""

    args = sys.argv[1:]
    number_or_agents = int(args.pop())

    if CONFIG_DIRECTORY.is_dir():
        rmtree(str(CONFIG_DIRECTORY))

    CONFIG_DIRECTORY.mkdir()
    (CONFIG_DIRECTORY / "keys").mkdir()

    for i in range(number_or_agents):
        build_agent_config(i, number_or_agents)


if __name__ == "__main__":
    main()
