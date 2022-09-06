# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2022 Valory AG
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
from pathlib import Path
from typing import Dict, Optional

from aea.configurations.constants import DEFAULT_PRIVATE_KEY_FILE
from docker import from_env

from autonomy.constants import (
    OAR_IMAGE,
    TENDERMINT_IMAGE_NAME,
    TENDERMINT_IMAGE_VERSION,
)
from autonomy.deploy.base import BaseDeploymentGenerator
from autonomy.deploy.constants import (
    DEFAULT_ENCODING,
    DEPLOYMENT_AGENT_KEY_DIRECTORY_SCHEMA,
    DEPLOYMENT_KEY_DIRECTORY,
    INFO,
    KEY_SCHEMA_PRIVATE_KEY,
)
from autonomy.deploy.generators.docker_compose.templates import (
    ABCI_NODE_TEMPLATE,
    DOCKER_COMPOSE_TEMPLATE,
    TENDERMINT_CONFIG_TEMPLATE,
    TENDERMINT_NODE_TEMPLATE,
)


def build_tendermint_node_config(
    node_id: int,
    dev_mode: bool = False,
    log_level: str = INFO,
) -> str:
    """Build tendermint node config for docker compose."""

    config = TENDERMINT_NODE_TEMPLATE.format(
        node_id=node_id,
        localnet_address_postfix=node_id + 3,
        localnet_port_range=node_id,
        log_level=log_level,
        tendermint_image_name=TENDERMINT_IMAGE_NAME,
        tendermint_image_version=TENDERMINT_IMAGE_VERSION,
    )

    if dev_mode:
        config += "      - ./persistent_data/tm_state:/tm_state:Z"
        config = config.replace("DEV_MODE=0", "DEV_MODE=1")

    return config


def build_agent_config(  # pylint: disable=too-many-arguments
    node_id: int,
    number_of_agents: int,
    agent_vars: Dict,
    runtime_image: str,
    dev_mode: bool = False,
    package_dir: Path = Path.cwd().absolute() / "packages",
    open_aea_dir: Path = Path.home().absolute() / "open-aea",
    open_autonomy_dir: Path = Path.home().absolute() / "open-autonomy",
) -> str:
    """Build agent config."""

    agent_vars_string = "\n".join([f"      - {k}={v}" for k, v in agent_vars.items()])
    config = ABCI_NODE_TEMPLATE.format(
        node_id=node_id,
        agent_vars=agent_vars_string,
        localnet_address_postfix=node_id + number_of_agents + 3,
        runtime_image=runtime_image,
    )

    if dev_mode:
        config += "      - ./persistent_data/benchmarks:/benchmarks:Z\n"
        config += (
            "      - ./persistent_data/venvs:/home/ubuntu/.local/share/virtualenvs:Z\n"
        )
        config += f"      - {package_dir}:/home/ubuntu/packages:rw\n"
        config += f"      - {open_aea_dir}:/open-aea\n"
        config += f"      - {open_autonomy_dir}:/open-autonomy\n"

    return config


class DockerComposeGenerator(BaseDeploymentGenerator):
    """Class to automate the generation of Deployments."""

    output_name: str = "docker-compose.yaml"
    deployment_type: str = "docker-compose"

    def generate_config_tendermint(self) -> "DockerComposeGenerator":
        """Generate the command to configure tendermint testnet."""

        hosts = (
            " \\\n".join(
                [
                    f"--hostname=node{k}"
                    for k in range(self.service_spec.service.number_of_agents)
                ]
            ),
        )
        self.tendermint_job_config = TENDERMINT_CONFIG_TEMPLATE.format(
            validators=self.service_spec.service.number_of_agents, hosts=hosts
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

    def generate(self, image_version: Optional[str] = None) -> "DockerComposeGenerator":
        """Generate the new configuration."""

        image_version = image_version or self.service_spec.service.agent.hash
        if self.dev_mode:
            image_version = "dev"

        agent_vars = self.service_spec.generate_agents()
        runtime_image = OAR_IMAGE.format(
            agent=self.service_spec.service.agent.name,
            version=image_version,
        )

        agents = "".join(
            [
                build_agent_config(
                    node_id=i,
                    number_of_agents=self.service_spec.service.number_of_agents,
                    runtime_image=runtime_image,
                    agent_vars=agent_vars[i],
                    dev_mode=self.dev_mode,
                    package_dir=self.packages_dir,
                    open_aea_dir=self.open_aea_dir,
                    open_autonomy_dir=self.open_autonomy_dir,
                )
                for i in range(self.service_spec.service.number_of_agents)
            ]
        )
        tendermint_nodes = "".join(
            [
                build_tendermint_node_config(
                    node_id=i,
                    dev_mode=self.dev_mode,
                    log_level=self.service_spec.log_level,
                )
                for i in range(self.service_spec.service.number_of_agents)
            ]
        )
        self.output = DOCKER_COMPOSE_TEMPLATE.format(
            abci_nodes=agents,
            tendermint_nodes=tendermint_nodes,
        )

        return self

    def populate_private_keys(
        self,
    ) -> "DockerComposeGenerator":
        """Populate the private keys to the build directory for docker-compose mapping."""
        for x in range(self.service_spec.service.number_of_agents):
            path = (
                self.build_dir
                / DEPLOYMENT_KEY_DIRECTORY
                / DEPLOYMENT_AGENT_KEY_DIRECTORY_SCHEMA.format(agent_n=x)
            )
            path.mkdir()
            with open(
                path / DEFAULT_PRIVATE_KEY_FILE, "w", encoding=DEFAULT_ENCODING
            ) as f:
                f.write(str(self.service_spec.keys[x][KEY_SCHEMA_PRIVATE_KEY]))
        return self
