#!/usr/bin/env python3
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

import shutil
import sys
from argparse import ArgumentParser, Namespace
from ipaddress import IPv4Address
from pathlib import Path
from shutil import rmtree
from typing import List, Tuple


BASE_DIRECTORY = Path() / "kubernetes_configs"
CONFIG_DIRECTORY = BASE_DIRECTORY / "build"
STARTING_IP_ADDRESS = IPv4Address("192.167.11.3")
AEA_DIR = CONFIG_DIRECTORY / "abci_build"
AEA_KEY_DIR = AEA_DIR / "keys"

BUILD_DIR = Path("/build/configs")

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
        ("url", "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"),
        ("api_id", "coinmarketcap"),
        (
            "headers",
            """'[["Accepts","application/json"], ["X-CMC_PRO_API_KEY","2142662b-985c-4862-82d7-e91457850c2a"]]'  --type list""",
        ),
        ("parameters", """'[["symbol","BTC"], ["convert","USD"]]'  --type list"""),
        ("response_key", "'data:BTC:quote:USD:price'"),
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


NETWORKS = {
    "hardhat": {"network_endpoint": "http://hardhat:8545", "chain_id": 3},
    "ropsten": {
        "network_endpoint": "https://ropsten.infura.io/v3/2980beeca3544c9fbace4f24218afcd4",
        "chain_id": 3,
    },
}


DEPLOYED_CONTRACTS = {
    "ropsten": {
        "safe_contract_address": "0x7AbCC2424811c342BC9A9B52B1621385d7406676",
        "oracle_contract_address": "0xB555E44648F6Ff759F64A5B451AB845B0450EA57",
    }
}

ABCI_CONFIG_SCRIPT: str = """#!/usr/bin/bash

echo -n $AEA_KEY >  ethereum_private_key.txt

aea add-key ethereum
aea config set agent.skill_exception_policy "just_log"
aea config set agent.connection_exception_policy "just_log"
aea config set vendor.valory.connections.abci.config.use_tendermint False
aea config set vendor.valory.skills.price_estimation_abci.models.params.args.consensus.max_participants {max_participants}
aea config set vendor.valory.skills.price_estimation_abci.models.params.args.round_timeout_seconds 5
aea config set vendor.valory.skills.price_estimation_abci.models.params.args.tendermint_url http://localhost:26657
aea config set vendor.valory.skills.price_estimation_abci.models.params.args.tendermint_com_url "http://localhost:8080"
aea config set vendor.valory.skills.price_estimation_abci.models.params.args.reset_tendermint_after 100 --type int
aea config set vendor.valory.skills.price_estimation_abci.models.params.args.observation_interval 1200 --type int
aea config set vendor.valory.skills.price_estimation_abci.models.params.args.max_healthcheck 1200 --type int
aea config set vendor.valory.connections.ledger.config.ledger_apis.ethereum.address "{network_endpoint}"
aea config set vendor.valory.connections.ledger.config.ledger_apis.ethereum.chain_id {chain_id} --type int
{extra_config}
aea build
"""


AGENT_NODE_TEMPLATE: str = """apiVersion: v1
kind: Service
metadata:
  name: agent-node-{validator_ix}-service
  labels:
    run: agent-node-{validator_ix}-service
spec:
  ports:
  - port: 26656
    protocol: TCP
    name: tcp1
  - port: 26657
    protocol: TCP
    name: tcp2
  selector:
    app: agent-node-{validator_ix}
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: agent-node-{validator_ix}
spec:
  replicas: 1
  selector:
    matchLabels:
      app: agent-node-{validator_ix}
  template:
    metadata:
      labels:
        app: agent-node-{validator_ix}
    spec:
      imagePullSecrets:
      - name: regcred
      restartPolicy: Always
      containers:
      - name: tendermint
        image: valory/localnode
        ports:
          - containerPort: 26656
          - containerPort: 26657
        workingDir: /tendermint
        command: ["/bin/bash"]
        env:
          - name: HOSTNAME
            value: "agent-node-{validator_ix}"
          - name: ID
            value: "{validator_ix}"
        args:
          - wrapper.sh
          - node
          - "--consensus.create_empty_blocks=false"
          - "--proxy_app=tcp://localhost:26658"
        volumeMounts:
          - mountPath: /tendermint
            name: build
      - name: aea
        image: valory/oracle-poc
        args: ["../run.sh", ]
        command:
          - /bin/bash
        env:
          - name: HOSTNAME
            value: "agent-node-{validator_ix}"
          - name: CLUSTERED
            value: "1"
          - name: AEA_KEY
            value: "{aea_key}"
        volumeMounts:
          - mountPath: /build
            name: build
      volumes:
        - name: build
          persistentVolumeClaim:
            claimName: 'build-vol'
"""


CLUSTER_CONFIGURATION_TEMPLATE: str = """apiVersion: batch/v1
kind: Job
metadata:
  name: config-nodes
spec:
  template:
    spec:
      imagePullSecrets:
      - name: regcred
      containers:
      - name: config-nodes
        image: valory/localnode
        args: ["testnet",
         "--config",
         "/etc/tendermint/config-template.toml",
         "--o",  ".", {host_names},
         "--v", "{number_of_validators}"
         ]
        volumeMounts:
          - mountPath: /tendermint
            name: build
      - name: aea
        image: valory/oracle-poc
        command:
          - /usr/bin/python
        env:
          - name: NUMBER_OF_NODES
            value: "{number_of_validators}"
        args: {config_command}
        volumeMounts:
          - mountPath: /build
            name: build
      volumes:
        - name: build
          persistentVolumeClaim:
            claimName: 'build-vol'
      restartPolicy: Never
  backoffLimit: 4
"""


def build_config_script(
    node_id: int,
    price_api: List[Tuple[str, str]],
    randomness_api: List[Tuple[str, str]],
    parameters: Namespace,
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

    if not parameters.deploy_safe_contract:
        safe_contract_address = DEPLOYED_CONTRACTS[parameters.network][
            "safe_contract_address"
        ]
        extra_config += f'\naea config set vendor.valory.skills.price_estimation_abci.models.params.args.period_setup.safe_contract_address "{safe_contract_address}"'

    if not parameters.deploy_oracle_contract:
        oracle_contract_address = DEPLOYED_CONTRACTS[parameters.network][
            "oracle_contract_address"
        ]
        extra_config += f'\naea config set vendor.valory.skills.price_estimation_abci.models.params.args.period_setup.oracle_contract_address "{oracle_contract_address}"'

    network_endpoint, chain_id = NETWORKS[parameters.network].values()

    return ABCI_CONFIG_SCRIPT.format(
        extra_config=extra_config,
        node_id=node_id,
        max_participants=parameters.number_of_agents,
        network_endpoint=network_endpoint,
        chain_id=chain_id,
    )


def build_configuration_job(number_of_agents: int) -> None:
    """Build configuration job."""
    host_names = ", ".join(
        [f'"--hostname=agent-node-{i}-service"' for i in range(number_of_agents)]
    )

    config_command = ["../configure_agents/create_env.py", "-b"] + sys.argv[1:]
    config_job_yaml = CLUSTER_CONFIGURATION_TEMPLATE.format(
        number_of_validators=number_of_agents,
        host_names=host_names,
        config_command=config_command,
    )
    with open(CONFIG_DIRECTORY / "config_job.yaml", "w+", encoding="utf-8") as file:
        file.write(config_job_yaml)


def build_agent_deployment(
    agent_ix: int, ip_address: IPv4Address, number_of_agents: int
) -> None:
    """Build agent deployment."""
    host_names = ", ".join(
        [f'"--hostname=agent-node-{i}-service"' for i in range(number_of_agents)]
    )

    config_command = ["../configure_agents/create_env.py", "-b"] + sys.argv[1:]
    agent_deployment_yaml = AGENT_NODE_TEMPLATE.format(
        validator_ix=agent_ix,
        ip_address=str(ip_address),
        aea_key=KEYS[agent_ix],
        number_of_validators=number_of_agents,
        host_names=host_names,
        config_command=config_command,
    )
    with open(
        CONFIG_DIRECTORY / f"agent_node_deployment-{agent_ix}.yaml",
        "w+",
        encoding="utf-8",
    ) as file:
        file.write(agent_deployment_yaml)


def get_args():
    """Parse cli Arguments"""
    parser = ArgumentParser()

    parser.add_argument("-n", "--number_of_agents", type=int, default=4)
    parser.add_argument("-b", "--copy_to_build", action="store_true", default=False)
    parser.add_argument(
        "-dsc", "--deploy_safe_contract", action="store_true", default=False
    )
    parser.add_argument(
        "-doc", "--deploy_oracle_contract", action="store_true", default=False
    )
    parser.add_argument(
        "-net",
        "--network",
        help="Network to be used for deployment",
        choices=NETWORKS.keys(),
        required=True,
    )
    return parser.parse_args()


def main() -> None:
    """Main function."""
    args = get_args()
    print(f"Building configuration {args}")
    number_of_agents = int(args.number_of_agents)

    if CONFIG_DIRECTORY.is_dir():
        rmtree(str(CONFIG_DIRECTORY))

    CONFIG_DIRECTORY.mkdir(parents=True)

    if args.network == "hardhat" and not args.copy_to_build:
        shutil.copytree(
            str(BASE_DIRECTORY / args.network), str(CONFIG_DIRECTORY / args.network)
        )

    build_configuration_job(number_of_agents)

    for i in range(number_of_agents):
        ip_address = STARTING_IP_ADDRESS + i
        build_agent_deployment(i, ip_address, number_of_agents)
    print(f"Created {number_of_agents} deployment yamls and abci start scripts")

    if args.copy_to_build:
        if BUILD_DIR.exists():
            rmtree(BUILD_DIR)
        shutil.move(str(AEA_DIR), str(BUILD_DIR))
        print(f"copied {number_of_agents} configs to build volume.")


class KubernetesGenerator:
    """Kubernetes Deployment Generator."""


if __name__ == "__main__":
    main()
