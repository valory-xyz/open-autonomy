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
import subprocess  # nosec
from pathlib import Path
from typing import Dict, IO, cast

from aea.configurations.constants import DEFAULT_PRIVATE_KEY_FILE

from autonomy.constants import (
    IMAGE_VERSION,
    OPEN_AEA_IMAGE_NAME,
    TENDERMINT_IMAGE_NAME,
    TENDERMINT_IMAGE_VERSION,
)
from autonomy.deploy.base import BaseDeploymentGenerator
from autonomy.deploy.constants import (
    DEFAULT_ENCODING,
    DEPLOYMENT_AGENT_KEY_DIRECTORY_SCHEMA,
    DEPLOYMENT_KEY_DIRECTORY,
)
from autonomy.deploy.generators.docker_compose.templates import (
    ABCI_NODE_TEMPLATE,
    DOCKER_COMPOSE_TEMPLATE,
    TENDERMINT_CONFIG_TEMPLATE,
    TENDERMINT_NODE_TEMPLATE,
)


def build_tendermint_node_config(
    node_id: int, dev_mode: bool = False, image_version: str = TENDERMINT_IMAGE_VERSION
) -> str:
    """Build tendermint node config for docker compose."""

    config = TENDERMINT_NODE_TEMPLATE.format(
        node_id=node_id,
        localnet_address_postfix=node_id + 3,
        localnet_port_range=node_id,
        tendermint_image_name=TENDERMINT_IMAGE_NAME,
        tendermint_image_version=image_version,
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
    open_aea_image_version: str = IMAGE_VERSION,
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
        self, image_version: str = TENDERMINT_IMAGE_NAME
    ) -> "DockerComposeGenerator":
        """Generate the command to configure tendermint testnet."""

        if self.tendermint_job_config is not None:  # pragma: no cover
            return self

        run_cmd = TENDERMINT_CONFIG_TEMPLATE.format(
            hosts=" \\\n".join(
                [
                    f"--hostname=node{k}"
                    for k in range(self.service_spec.service.number_of_agents)
                ]
            ),
            validators=self.service_spec.service.number_of_agents,
            build_dir=self.build_dir,
            tendermint_image_name=TENDERMINT_IMAGE_NAME,
            tendermint_image_version=image_version,
        )
        self.tendermint_job_config = " ".join(
            [
                f
                for f in run_cmd.replace("\n", "").replace("\\", "").split(" ")
                if f != ""
            ]
        )

        process = subprocess.Popen(  # pylint: disable=consider-using-with  # nosec
            self.tendermint_job_config.split(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
        )

        for line in iter(cast(IO[str], process.stdout).readline, ""):
            if line == "":  # pragma: nocover
                break
            print(f"[Tendermint] {line.strip()}")

        if "Unable to find image" in cast(IO[str], process.stderr).read():
            raise RuntimeError(
                f"Cannot find {TENDERMINT_IMAGE_NAME}:{image_version}, Please build images first."
            )
        return self

    def generate(
        self,
        image_versions: Dict[str, str],
        dev_mode: bool = False,
    ) -> "DockerComposeGenerator":
        """Generate the new configuration."""

        agent_vars = self.service_spec.generate_agents()
        agent_vars = self.get_deployment_network_configuration(agent_vars)
        image_name = self.service_spec.service.agent.name

        if dev_mode:
            image_versions["agent"] = "dev"

        agents = "".join(
            [
                build_agent_config(
                    image_name,
                    i,
                    self.service_spec.service.number_of_agents,
                    agent_vars[i],
                    dev_mode,
                    open_aea_image_version=image_versions["agent"],
                )
                for i in range(self.service_spec.service.number_of_agents)
            ]
        )
        tendermint_nodes = "".join(
            [
                build_tendermint_node_config(i, dev_mode, image_versions["tendermint"])
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
                f.write(str(self.service_spec.private_keys[x]))
        return self
