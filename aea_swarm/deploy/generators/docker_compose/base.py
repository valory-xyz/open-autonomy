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
import logging
import subprocess  # nosec
from pathlib import Path
from typing import Dict, IO, cast

from aea_swarm.constants import (
    DEFAULT_IMAGE_VERSION,
    OPEN_AEA_IMAGE_NAME,
    TENDERMINT_IMAGE_NAME,
)
from aea_swarm.deploy.base import BaseDeploymentGenerator
from aea_swarm.deploy.generators.docker_compose.templates import (
    ABCI_NODE_TEMPLATE,
    DOCKER_COMPOSE_TEMPLATE,
    TENDERMINT_CONFIG_TEMPLATE,
    TENDERMINT_NODE_TEMPLATE,
)


def build_tendermint_node_config(node_id: int, dev_mode: bool = False) -> str:
    """Build tendermint node config for docker compose."""

    config = TENDERMINT_NODE_TEMPLATE.format(
        node_id=node_id,
        localnet_address_postfix=node_id + 3,
        localnet_port_range=node_id,
        tendermint_image_name=TENDERMINT_IMAGE_NAME,
        tendermint_image_version=DEFAULT_IMAGE_VERSION,
    )

    if dev_mode:
        config += "      - ./persistent_data/tm_state:/tm_state:Z"
        config = config.replace("DEV_MODE=0", "DEV_MODE=1")

    return config


def build_agent_config(  # pylint: disable=too-many-arguments
    valory_app: str,
    node_id: int,
    number_of_agents: int,
    agent_vars: Dict,
    dev_mode: bool = False,
    package_dir: Path = Path.cwd().absolute() / "packages",
    open_aea_dir: Path = Path.cwd().absolute().parent / "open-aea",
    open_aea_image_name: str = OPEN_AEA_IMAGE_NAME,
    open_aea_image_version: str = DEFAULT_IMAGE_VERSION,
) -> str:
    """Build agent config."""

    config = ABCI_NODE_TEMPLATE.format(
        valory_app=valory_app,
        node_id=node_id,
        agent_vars="".join([f"      - {k}={v}\n" for k, v in agent_vars.items()]),
        localnet_address_postfix=node_id + number_of_agents + 3,
        open_aea_image_name=open_aea_image_name,
        open_aea_image_version=open_aea_image_version,
    )

    if dev_mode:
        config += "      - ./persistent_data/benchmarks:/benchmarks:Z\n"
        config += (
            "      - ./persistent_data/venvs:/home/ubuntu/.local/share/virtualenvs:Z\n"
        )
        config += f"      - {package_dir}:/home/ubuntu/packages:rw\n"
        config += f"      - {open_aea_dir}:/open-aea\n"

    return config


class DockerComposeGenerator(BaseDeploymentGenerator):
    """Class to automate the generation of Deployments."""

    output_name: str = "docker-compose.yaml"
    deployment_type: str = "docker-compose"

    def generate_config_tendermint(
        self,
    ) -> "DockerComposeGenerator":
        """Generate the command to configure tendermint testnet."""

        logging.info("9")

        if self.tendermint_job_config is not None:
            return self

        logging.info("10")
        run_cmd = TENDERMINT_CONFIG_TEMPLATE.format(
            hosts=" \\\n".join(
                [
                    f"--hostname=node{k}"
                    for k in range(self.deployment_spec.number_of_agents)
                ]
            ),
            validators=self.deployment_spec.number_of_agents,
            build_dir=self.build_dir,
            tendermint_image_name=TENDERMINT_IMAGE_NAME,
            tendermint_image_version=DEFAULT_IMAGE_VERSION,
        )
        logging.info("11")
        self.tendermint_job_config = " ".join(
            [
                f
                for f in run_cmd.replace("\n", "").replace("\\", "").split(" ")
                if f != ""
            ]
        )

        logging.info("12")
        process = subprocess.Popen(  # pylint: disable=consider-using-with  # nosec
            self.tendermint_job_config.split(),
            stdout=subprocess.PIPE,
            universal_newlines=True,
        )
        for line in iter(cast(IO[str], process.stdout).readline, ""):
            if line == "":
                break
            logging.info(f"[Tendermint] {line.strip()}")

        logging.info(f"Process Exited with {process.stdout}")
        logging.info("12")
        return self

    def generate(
        self,
        dev_mode: bool = False,
    ) -> "DockerComposeGenerator":
        """Generate the new configuration."""

        logging.info("5")
        agent_vars = self.deployment_spec.generate_agents()
        agent_vars = self.get_deployment_network_configuration(agent_vars)
        image_name = self.deployment_spec.agent_public_id.name
        logging.info("6")

        if dev_mode:
            version = "dev"
        else:
            version = DEFAULT_IMAGE_VERSION

        logging.info("7")
        agents = "".join(
            [
                build_agent_config(
                    image_name,
                    i,
                    self.deployment_spec.number_of_agents,
                    agent_vars[i],
                    dev_mode,
                    open_aea_image_version=version,
                )
                for i in range(self.deployment_spec.number_of_agents)
            ]
        )
        logging.info("8")
        tendermint_nodes = "".join(
            [
                build_tendermint_node_config(i, dev_mode)
                for i in range(self.deployment_spec.number_of_agents)
            ]
        )
        logging.info("9")
        self.output = DOCKER_COMPOSE_TEMPLATE.format(
            abci_nodes=agents,
            tendermint_nodes=tendermint_nodes,
        )

        return self
