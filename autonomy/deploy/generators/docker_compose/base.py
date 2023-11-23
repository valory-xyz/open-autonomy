# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2023 Valory AG
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

"""Docker-compose Deployment Generator."""
import ipaddress
from pathlib import Path
from typing import Dict, Optional, cast

from aea.configurations.constants import DEFAULT_LEDGER, PRIVATE_KEY_PATH_SCHEMA
from docker import from_env

from autonomy.constants import (
    ACN_IMAGE_NAME,
    ACN_IMAGE_VERSION,
    DOCKER_COMPOSE_YAML,
    HARDHAT_IMAGE_NAME,
    HARDHAT_IMAGE_VERSION,
    OAR_IMAGE,
    TENDERMINT_IMAGE_NAME,
    TENDERMINT_IMAGE_VERSION,
)
from autonomy.deploy.base import BaseDeploymentGenerator, tm_write_to_log
from autonomy.deploy.constants import (
    DEFAULT_ENCODING,
    DEPLOYMENT_AGENT_KEY_DIRECTORY_SCHEMA,
    DEPLOYMENT_KEY_DIRECTORY,
    INFO,
    KEY_SCHEMA_PRIVATE_KEY,
    KEY_SCHEMA_TYPE,
)
from autonomy.deploy.generators.docker_compose.templates import (
    ABCI_NODE_TEMPLATE,
    ACN_NODE_TEMPLATE,
    DOCKER_COMPOSE_TEMPLATE,
    HARDHAT_NODE_TEMPLATE,
    PORTS,
    PORT_MAPPING_CONFIG,
    TENDERMINT_CONFIG_TEMPLATE,
    TENDERMINT_NODE_TEMPLATE,
)


NETWORK_ADDRESS_OFFSET = 1
BASE_SUBNET = cast(ipaddress.IPv4Network, ipaddress.ip_network("192.167.11.0/24"))
SUBNET_OVERFLOW = 256

DEFAULT_PACKAGES_PATH = Path.cwd().absolute() / "packages"
DEFAULT_OPEN_AEA_DIR: Path = Path.home().absolute() / "open-aea"
DEFAULT_OPEN_AUTONOMY_DIR: Path = Path.home().absolute() / "open-autonomy"


def build_tendermint_node_config(  # pylint: disable=too-many-arguments
    node_id: int,
    container_name: str,
    abci_node: str,
    network_name: str,
    network_address: str,
    dev_mode: bool = False,
    log_level: str = INFO,
    tendermint_ports: Optional[Dict[int, int]] = None,
) -> str:
    """Build tendermint node config for docker compose."""
    config = TENDERMINT_NODE_TEMPLATE.format(
        node_id=node_id,
        container_name=container_name,
        abci_node=abci_node,
        network_address=network_address,
        localnet_port_range=node_id,
        log_level=log_level,
        tendermint_image_name=TENDERMINT_IMAGE_NAME,
        tendermint_image_version=TENDERMINT_IMAGE_VERSION,
        network_name=network_name,
        write_to_log=str(tm_write_to_log()).lower(),
    )

    if dev_mode:
        config += "      - ./persistent_data/tm_state:/tm_state:Z"
        config = config.replace("DEV_MODE=0", "DEV_MODE=1")

    if tendermint_ports is not None:
        port_mappings = map(
            lambda x: PORT_MAPPING_CONFIG.format(host_port=x[0], container_port=x[1]),
            tendermint_ports.items(),
        )
        port_config = "\n".join([PORTS, *port_mappings])
        config += port_config
        config += "\n"

    return config


def build_agent_config(  # pylint: disable=too-many-arguments
    node_id: int,
    container_name: str,
    agent_vars: Dict,
    runtime_image: str,
    network_name: str,
    network_address: str,
    dev_mode: bool = False,
    package_dir: Path = DEFAULT_PACKAGES_PATH,
    open_aea_dir: Path = DEFAULT_OPEN_AEA_DIR,
    open_autonomy_dir: Path = DEFAULT_OPEN_AUTONOMY_DIR,
    agent_ports: Optional[Dict[int, int]] = None,
) -> str:
    """Build agent config."""

    agent_vars_string = "\n".join([f"      - {k}={v}" for k, v in agent_vars.items()])
    config = ABCI_NODE_TEMPLATE.format(
        node_id=node_id,
        container_name=container_name,
        agent_vars=agent_vars_string,
        network_address=network_address,
        runtime_image=runtime_image,
        network_name=network_name,
    )

    if dev_mode:
        config += "      - ./persistent_data/benchmarks:/benchmarks:Z\n"
        config += (
            "      - ./persistent_data/venvs:/home/ubuntu/.local/share/virtualenvs:Z\n"
        )
        config += f"      - {package_dir}:/home/ubuntu/packages:rw\n"
        config += f"      - {open_aea_dir}:/open-aea\n"
        config += f"      - {open_autonomy_dir}:/open-autonomy\n"

    if agent_ports is not None:
        port_mappings = map(
            lambda x: PORT_MAPPING_CONFIG.format(host_port=x[0], container_port=x[1]),
            agent_ports.items(),
        )
        port_config = "\n".join([PORTS, *port_mappings])
        config += port_config
        config += "\n"

    return config


class Network:
    """Class to represent network of the service."""

    def __init__(
        self,
        name: str,
        base: ipaddress.IPv4Network = BASE_SUBNET,
    ) -> None:
        """Initialize."""
        self.name = name
        self.base = base
        self.subnet = self.build()

        self._address_offeset = NETWORK_ADDRESS_OFFSET

    @staticmethod
    def next_subnet(subnet: ipaddress.IPv4Network) -> ipaddress.IPv4Network:
        """Calculat next available subnet."""
        new_address = subnet.network_address + SUBNET_OVERFLOW
        return cast(
            ipaddress.IPv4Network,
            ipaddress.ip_network(f"{new_address}/{subnet.prefixlen}"),
        )

    def build(
        self,
    ) -> ipaddress.IPv4Network:
        """Initialize network params."""
        docker = from_env()
        used_subnets = set()
        for network in docker.networks.list():
            # Network already exists
            if f"abci_build_{self.name}" == network.attrs["Name"]:
                config, *_ = network.attrs["IPAM"]["Config"]
                return cast(
                    ipaddress.IPv4Network, ipaddress.ip_network(config["Subnet"])
                )
            for config in network.attrs["IPAM"]["Config"]:
                used_subnets.add(config["Subnet"])

        subnet = self.base
        while str(subnet) in used_subnets:
            subnet = self.next_subnet(subnet=subnet)
        return subnet

    @property
    def next_address(self) -> str:
        """Returns the next IP address string."""
        self._address_offeset += 1
        return str(self.subnet.network_address + self._address_offeset)


class DockerComposeGenerator(BaseDeploymentGenerator):
    """Class to automate the generation of Deployments."""

    output_name: str = DOCKER_COMPOSE_YAML
    deployment_type: str = "docker-compose"

    def generate_config_tendermint(self) -> "DockerComposeGenerator":
        """Generate the command to configure tendermint testnet."""

        if not self.use_tm_testnet_setup:
            return self

        hosts = " ".join(
            [
                "--hostname=" + self.service_builder.get_tm_container_name(index=k)
                for k in range(self.service_builder.service.number_of_agents)
            ]
        )
        self.tendermint_job_config = TENDERMINT_CONFIG_TEMPLATE.format(
            validators=self.service_builder.service.number_of_agents, hosts=hosts
        )
        client = from_env()
        image = f"{TENDERMINT_IMAGE_NAME}:{TENDERMINT_IMAGE_VERSION}"

        run_log = client.containers.run(
            image=image,
            volumes={f"{self.build_dir}/nodes": {"bind": "/tendermint", "mode": "z"}},
            entrypoint=self.tendermint_job_config,
        )
        print(run_log.decode())

        return self

    def generate(
        self,
        image_version: Optional[str] = None,
        use_hardhat: bool = False,
        use_acn: bool = False,
    ) -> "DockerComposeGenerator":
        """Generate the new configuration."""

        network_name = f"service_{self.service_builder.service.name}_localnet"
        network = Network(name=network_name)
        image_version = image_version or self.service_builder.service.agent.hash
        if self.dev_mode:
            image_version = "dev"

        runtime_image = OAR_IMAGE.format(
            image_author=self.image_author,
            agent=self.service_builder.service.agent.name,
            version=image_version,
        )
        agent_vars = self.service_builder.generate_agents()
        agents = "".join(
            [
                build_agent_config(
                    node_id=i,
                    container_name=self.service_builder.get_abci_container_name(
                        index=i
                    ),
                    runtime_image=runtime_image,
                    agent_vars=agent_vars[i],
                    dev_mode=self.dev_mode,
                    package_dir=self.packages_dir,
                    open_aea_dir=self.open_aea_dir,
                    open_autonomy_dir=self.open_autonomy_dir,
                    agent_ports=(
                        self.service_builder.service.deployment_config.get("agent", {})
                        .get("ports", {})
                        .get(i)
                    ),
                    network_name=network_name,
                    network_address=network.next_address,
                )
                for i in range(self.service_builder.service.number_of_agents)
            ]
        )
        tendermint_nodes = "".join(
            [
                build_tendermint_node_config(
                    node_id=i,
                    container_name=self.service_builder.get_tm_container_name(index=i),
                    abci_node=self.service_builder.get_abci_container_name(index=i),
                    dev_mode=self.dev_mode,
                    log_level=self.service_builder.log_level,
                    tendermint_ports=(
                        self.service_builder.service.deployment_config.get(
                            "tendermint", {}
                        )
                        .get("ports", {})
                        .get(i)
                    ),
                    network_name=network_name,
                    network_address=network.next_address,
                )
                for i in range(self.service_builder.service.number_of_agents)
            ]
        )

        hardhat_node = ""
        if use_hardhat:
            hardhat_node = HARDHAT_NODE_TEMPLATE.format(
                hardhat_image_name=HARDHAT_IMAGE_NAME,
                hardhat_image_version=HARDHAT_IMAGE_VERSION,
                network_name=network_name,
                network_address=network.next_address,
            )

        acn_node = ""
        if use_acn:
            acn_node = ACN_NODE_TEMPLATE.format(
                acn_image_name=ACN_IMAGE_NAME,
                acn_image_version=ACN_IMAGE_VERSION,
                network_name=network_name,
                network_address=network.next_address,
            )

        self.output = DOCKER_COMPOSE_TEMPLATE.format(
            abci_nodes=agents,
            tendermint_nodes=tendermint_nodes,
            hardhat_node=hardhat_node,
            acn_node=acn_node,
            network_name=network_name,
            subnet=str(network.subnet),
        )

        return self

    def populate_private_keys(
        self,
    ) -> "DockerComposeGenerator":
        """Populate the private keys to the build directory for docker-compose mapping."""
        keys_dir = self.build_dir / DEPLOYMENT_KEY_DIRECTORY
        for x in range(self.service_builder.service.number_of_agents):
            path = keys_dir / DEPLOYMENT_AGENT_KEY_DIRECTORY_SCHEMA.format(agent_n=x)
            ledger = self.service_builder.keys[x].get(KEY_SCHEMA_TYPE, DEFAULT_LEDGER)
            key = self.service_builder.keys[x][KEY_SCHEMA_PRIVATE_KEY]
            keys_file = path / PRIVATE_KEY_PATH_SCHEMA.format(ledger)
            path.mkdir()
            with keys_file.open(mode="w", encoding=DEFAULT_ENCODING) as f:
                f.write(key)

        return self
