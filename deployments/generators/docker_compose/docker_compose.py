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

"""Docker-compose Deployment Generator."""
from typing import Dict, Type

from deployments.base_deployments import BaseDeployment, BaseDeploymentGenerator

from .templates import (
    ABCI_NODE_TEMPLATE,
    DOCKER_COMPOSE_TEMPLATE,
    HARDHAT_NODE_TEMPLATE,
    TENDERMINT_CONFIG_TEMPLATE,
    TENDERMINT_NODE_TEMPLATE,
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


def build_agent_config(node_id: int, number_of_agents: int, agent_vars: Dict) -> str:
    """Build agent config."""

    return ABCI_NODE_TEMPLATE.format(
        node_id=node_id,
        agent_vars="".join([f"      - {k}={v}\n" for k, v in agent_vars.items()]),
        localnet_address_postfix=node_id + number_of_agents + 3,
    )


class DockerComposeGenerator(BaseDeploymentGenerator):
    """Class to automate the generation of Deployments."""

    output_name = "docker-compose.yaml"

    def __init__(
        self,
        deployment_spec: BaseDeployment
    ) -> None:
        """Initialise the deployment generator."""
        super().__init__(deployment_spec)
        self.output = ""
        self.config_cmd = ""
        self.hardhat = ""
        if self.deployment_spec.network == "hardhat":
            self.hardhat = HARDHAT_NODE_TEMPLATE

    def generate_config_tendermint(
        self, valory_application: Type[BaseDeployment]
    ) -> str:
        """Generate the command to configure tendermint testnet."""
        run_cmd = TENDERMINT_CONFIG_TEMPLATE.format(
            hosts=" \\\n".join(
                [f"--hostname=node{k}" for k in range(self.deployment_spec.number_of_agents)]
            ),
            validators=self.deployment_spec.number_of_agents,
        )
        self.config_cmd = " ".join(
            [
                f
                for f in run_cmd.replace("\n", "").replace("\\", "").split(" ")
                if f != ""
            ]
        )
        return self.config_cmd

    def generate(self, valory_application: Type[BaseDeployment]) -> str:
        """Generate the new configuration."""

        agent_vars = valory_application.generate_agents()  # type: ignore

        agents = "".join(
            [
                build_agent_config(i, self.deployment_spec.number_of_agents, agent_vars[i])
                for i in range(self.deployment_spec.number_of_agents)
            ]
        )
        tendermint_nodes = "".join(
            [build_tendermint_node_config(i) for i in range(self.deployment_spec.number_of_agents)]
        )

        self.output = DOCKER_COMPOSE_TEMPLATE.format(
            abci_nodes=agents,
            tendermint_nodes=tendermint_nodes,
            hardhat_chain=self.hardhat,
        )
        return self.output
