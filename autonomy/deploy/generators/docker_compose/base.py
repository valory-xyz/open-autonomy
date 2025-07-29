# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2025 Valory AG
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
import logging
import os
import socket
from copy import deepcopy
from pathlib import Path
from string import Template
from typing import Dict, List, Optional, Set, cast

import yaml
from aea.configurations.constants import (
    DEFAULT_LEDGER,
    LEDGER,
    PRIVATE_KEY,
    PRIVATE_KEY_PATH_SCHEMA,
)
from docker import DockerClient, from_env
from docker.constants import DEFAULT_NPIPE, IS_WINDOWS_PLATFORM
from docker.errors import DockerException

from autonomy.configurations.constants import DEFAULT_SERVICE_CONFIG_FILE
from autonomy.constants import (
    ACN_IMAGE_NAME,
    ACN_IMAGE_VERSION,
    DEVELOPMENT_IMAGE,
    DOCKER_COMPOSE_YAML,
    HARDHAT_IMAGE_NAME,
    HARDHAT_IMAGE_VERSION,
    OAR_IMAGE,
    TENDERMINT_IMAGE_NAME,
    TENDERMINT_IMAGE_VERSION,
)
from autonomy.deploy.base import (
    BaseDeploymentGenerator,
    DEFAULT_RESOURCE_VALUES,
    LOOPBACK,
    Resources,
    tm_write_to_log,
)
from autonomy.deploy.constants import (
    DEFAULT_ENCODING,
    DEPLOYMENT_AGENT_KEY_DIRECTORY_SCHEMA,
    DEPLOYMENT_KEY_DIRECTORY,
    INFO,
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
AGENT_ENV_TEMPLATE = Template("agent_${node_id}.env")


def get_docker_client() -> DockerClient:
    """Load docker client."""
    try:
        return from_env()
    except DockerException:
        return DockerClient(
            DEFAULT_NPIPE
            if IS_WINDOWS_PLATFORM
            else f"unix://{Path.home()}/.docker/desktop/docker.sock"
        )


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
        user=os.environ.get("UID", "1000"),
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


def to_env_file(agent_vars: Dict, node_id: int, build_dir: Path) -> None:
    """Create a env file under the `agent_build` folder."""
    agent_vars["PYTHONHASHSEED"] = 0
    agent_vars["LOG_FILE"] = f"/logs/aea_{node_id}.txt"
    env_file_path = build_dir / AGENT_ENV_TEMPLATE.substitute(node_id=node_id)
    with open(env_file_path, "w", encoding=DEFAULT_ENCODING) as env_file:
        for key, value in agent_vars.items():
            env_file.write(f"{key}={value}\n")


def build_agent_config(  # pylint: disable=too-many-arguments,too-many-locals
    node_id: int,
    build_dir: Path,
    container_name: str,
    agent_vars: Dict,
    runtime_image: str,
    network_name: str,
    network_address: str,
    dev_mode: bool = False,
    package_dir: Optional[Path] = None,
    open_aea_dir: Optional[Path] = None,
    agent_ports: Optional[Dict[int, int]] = None,
    extra_volumes: Optional[Dict[str, str]] = None,
    resources: Optional[Resources] = None,
) -> str:
    """Build agent config."""
    resources = resources if resources is not None else DEFAULT_RESOURCE_VALUES
    to_env_file(agent_vars, node_id, build_dir)
    config = ABCI_NODE_TEMPLATE.format(
        node_id=node_id,
        container_name=container_name,
        network_address=network_address,
        runtime_image=runtime_image,
        env_file=f"agent_{node_id}.env",
        user=f"{os.getuid()}:{os.getgid()}",
        network_name=network_name,
        agent_memory_request=resources["agent"]["requested"]["memory"],
        agent_cpu_limit=resources["agent"]["limit"]["cpu"],
        agent_memory_limit=resources["agent"]["limit"]["memory"],
    )

    if dev_mode:
        config += "      - ./persistent_data/benchmarks:/benchmarks:Z\n"
        config += "      - ./persistent_data/venvs:/root/.local/share/virtualenvs:Z\n"
        config += f"      - {package_dir}:/root/packages:rw\n"
        config += f"      - {open_aea_dir}:/open-aea\n"

    if extra_volumes is not None:
        for host_dir, container_dir in extra_volumes.items():
            config += f"      - {host_dir}:{container_dir}:Z\n"
            (build_dir / host_dir).resolve().mkdir(exist_ok=True, parents=True)

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
        used_subnets: Optional[Set[str]] = None,
    ) -> None:
        """Initialize."""
        self.name = name
        self.base = base
        self.used_subnets = set() if used_subnets is None else used_subnets
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
        docker = get_docker_client()
        used_subnets = self.used_subnets
        for network in docker.networks.list():
            # Network already exists
            if f"abci_build_{self.name}" == network.attrs["Name"]:
                config, *_ = network.attrs["IPAM"]["Config"]
                return cast(
                    ipaddress.IPv4Network, ipaddress.ip_network(config["Subnet"])
                )
            if network.attrs["IPAM"]["Config"] is None:
                continue
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


class Port:
    """Class to find host port for a service."""

    def __init__(self) -> None:
        """Initialize."""
        self._used_ports: Set[int] = set()

    @staticmethod
    def is_port_available(port: int) -> bool:
        """Check if the port is available."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind((LOOPBACK, port))
                return True  # Port is occupied, binding failed
            except socket.error:
                return False  # Port is free, binding successful

    def get_next_port(self, from_port: int) -> int:
        """Get the next available port from the given from_port."""
        port = from_port
        while not self.is_port_available(port):
            self._used_ports.add(port)
            port += 1

        self._used_ports.add(port)
        return port


class DockerComposeGenerator(BaseDeploymentGenerator):
    """Class to automate the generation of Deployments."""

    output_name: str = DOCKER_COMPOSE_YAML
    deployment_type: str = "docker-compose"

    def _find_occupied_networks(self, network_name: str) -> Set[str]:
        """Find occupied networks on the host system."""
        used_ports: Dict[str, str] = {}  # find occupied ports
        for config_name in ("agent", "tendermint"):
            for port_mapping in (
                self.service_builder.service.deployment_config.get(config_name, {})
                .get("ports", {})
                .values()
            ):
                for host_port, _ in port_mapping.items():
                    if host_port in used_ports:
                        print(
                            f"WARNING: Port {host_port} is already used by {used_ports[host_port]}."
                        )
                    else:
                        used_ports[str(host_port)] = DEFAULT_SERVICE_CONFIG_FILE

        used_networks = set()  # find occupied networks
        for build in Path.cwd().glob("abci_build_*"):
            if not (build / DOCKER_COMPOSE_YAML).exists():
                continue

            compose_config = yaml.safe_load((build / DOCKER_COMPOSE_YAML).read_text())
            for subnet in (
                compose_config.get("networks", {})
                .get(network_name, {})
                .get("ipam", {})
                .get("config", [])
            ):
                used_networks.add(subnet["subnet"])

            services = compose_config.get("services", {})
            for name, service in services.items():
                for port_mapping_str in service.get("ports", []):
                    port_mapping = port_mapping_str.split(":")
                    if len(port_mapping) != 2:
                        continue

                    host_port = port_mapping[0]
                    if host_port in used_ports:
                        print(
                            f"WARNING: Port {host_port} is already used by {used_ports[host_port]}."
                            f" Please adjust the port in {build / DOCKER_COMPOSE_YAML} manually.",
                        )
                    else:
                        used_ports[host_port] = name

        return used_networks

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
            validators=self.service_builder.service.number_of_agents,
            hosts=hosts,
            user=os.environ.get("UID", "1000"),
        )
        client = get_docker_client()
        image = f"{TENDERMINT_IMAGE_NAME}:{TENDERMINT_IMAGE_VERSION}"

        run_log = client.containers.run(
            image=image,
            volumes={f"{self.build_dir}/nodes": {"bind": "/tendermint", "mode": "z"}},
            entrypoint=self.tendermint_job_config,
            remove=True,
        )
        print(run_log.decode())

        return self

    def generate(  # pylint: disable=too-many-locals
        self,
        image_version: Optional[str] = None,
        use_hardhat: bool = False,
        use_acn: bool = False,
    ) -> "DockerComposeGenerator":
        """Generate the new configuration."""
        network_name = self.service_builder.get_network_name()
        used_networks = self._find_occupied_networks(network_name)
        network = Network(name=network_name, used_subnets=used_networks)
        image_version = image_version or self.service_builder.service.agent.hash
        if self.dev_mode:
            runtime_image = DEVELOPMENT_IMAGE
        else:
            runtime_image = OAR_IMAGE.format(
                image_author=self.image_author,
                agent=self.service_builder.service.agent.name,
                version=image_version,
            )

        agent_ports = self.service_builder.service.deployment_config.get(
            "agent", {}
        ).get("ports", {})
        if not agent_ports:
            agent_ports = {}

        port = Port()
        updated_ports = deepcopy(agent_ports)
        for i, configured_ports in agent_ports.items():
            for configured_host_port, configured_agent_port in configured_ports.items():
                if not port.is_port_available(configured_host_port):
                    next_available_port = port.get_next_port(configured_host_port)
                    logging.warning(
                        f"Port {configured_host_port} is already in use. "
                        f"Using the {next_available_port=} instead."
                    )
                    updated_ports[i][next_available_port] = configured_agent_port
                    del updated_ports[i][configured_host_port]

        agent_vars = self.service_builder.generate_agents()
        agents = "".join(
            [
                build_agent_config(
                    node_id=i,
                    container_name=self.service_builder.get_abci_container_name(
                        index=i
                    ),
                    build_dir=self.build_dir,
                    runtime_image=runtime_image,
                    agent_vars=agent_vars[i],
                    dev_mode=self.dev_mode,
                    package_dir=self.packages_dir,
                    open_aea_dir=self.open_aea_dir,
                    agent_ports=updated_ports.get(i),
                    network_name=network_name,
                    network_address=network.next_address,
                    resources=self.resources,
                    extra_volumes=self.service_builder.service.deployment_config.get(
                        "agent", {}
                    ).get("volumes"),
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

    def _populate_keys(self) -> None:
        """Populate the keys directory"""
        keys_dir = self.build_dir / DEPLOYMENT_KEY_DIRECTORY
        for x in range(self.service_builder.service.number_of_agents):
            path = keys_dir / DEPLOYMENT_AGENT_KEY_DIRECTORY_SCHEMA.format(agent_n=x)
            ledger = cast(List[Dict[str, str]], self.service_builder.keys)[x].get(
                LEDGER, DEFAULT_LEDGER
            )
            key = cast(List[Dict[str, str]], self.service_builder.keys)[x][PRIVATE_KEY]
            keys_file = path / PRIVATE_KEY_PATH_SCHEMA.format(ledger)
            path.mkdir()
            with keys_file.open(mode="w", encoding=DEFAULT_ENCODING) as f:
                f.write(key)

    def _populate_keys_multiledger(self) -> None:
        """Populate the keys directory with multiple set of keys"""
        keys_dir = self.build_dir / DEPLOYMENT_KEY_DIRECTORY
        for x in range(self.service_builder.service.number_of_agents):
            path = keys_dir / DEPLOYMENT_AGENT_KEY_DIRECTORY_SCHEMA.format(agent_n=x)
            path.mkdir(exist_ok=True)
            for keypair in cast(List[List[Dict[str, str]]], self.service_builder.keys)[
                x
            ]:
                ledger = keypair.get(LEDGER, DEFAULT_LEDGER)
                key = keypair[PRIVATE_KEY]
                keys_file = path / PRIVATE_KEY_PATH_SCHEMA.format(ledger)
                with keys_file.open(mode="w", encoding=DEFAULT_ENCODING) as f:
                    f.write(key)

    def populate_private_keys(
        self,
    ) -> "DockerComposeGenerator":
        """Populate the private keys to the build directory for docker-compose mapping."""
        if self.service_builder.multiledger:
            self._populate_keys_multiledger()
        else:
            self._populate_keys()
        return self
