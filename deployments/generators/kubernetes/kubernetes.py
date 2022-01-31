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

import yaml
import sys
from pathlib import Path
from typing import Any, Dict

from deployments.base_deployments import BaseDeployment, BaseDeploymentGenerator


from deployments.generators.kubernetes.templates import (
    CLUSTER_CONFIGURATION_TEMPLATE,
    HARDHAT_TEMPLATE,
    AGENT_NODE_TEMPLATE
)
from deployments.constants import PRICE_APIS, RANDOMNESS_APIS, DEPLOYED_CONTRACTS, KEYS, NETWORKS


BASE_DIRECTORY = Path() / "kubernetes_configs"
CONFIG_DIRECTORY = BASE_DIRECTORY / "build"
AEA_DIR = CONFIG_DIRECTORY / "abci_build"
AEA_KEY_DIR = AEA_DIR / "keys"

BUILD_DIR = Path("/build/configs")


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




# def main() -> None:
#     """Main function."""
#     args = get_args()
#     print(f"Building configuration {args}")
#     number_of_agents = int(args.number_of_agents)
#
#     if CONFIG_DIRECTORY.is_dir():
#         rmtree(str(CONFIG_DIRECTORY))
#
#     CONFIG_DIRECTORY.mkdir(parents=True)
#
#     if args.network == "hardhat" and not args.copy_to_build:
#         shutil.copytree(
#             str(BASE_DIRECTORY / args.network), str(CONFIG_DIRECTORY / args.network)
#         )
#
#     build_configuration_job(number_of_agents)
#
#     for i in range(number_of_agents):
#         ip_address = STARTING_IP_ADDRESS + i
#         build_agent_deployment(i, ip_address, number_of_agents)
#     print(f"Created {number_of_agents} deployment yamls and abci start scripts")
#
#     if args.copy_to_build:
#         if BUILD_DIR.exists():
#             rmtree(BUILD_DIR)
#         shutil.move(str(AEA_DIR), str(BUILD_DIR))
#         print(f"copied {number_of_agents} configs to build volume.")


def build_agent_deployment(agent_ix: int, number_of_agents: int, agent_vars: Dict[str, Any]
                           ) -> str:
    """Build agent deployment."""
    host_names = ", ".join(
        [f'"--hostname=agent-node-{i}-service"' for i in range(number_of_agents)]
    )

    agent_deployment = AGENT_NODE_TEMPLATE.format(
        validator_ix=agent_ix,
        aea_key=KEYS[agent_ix],
        number_of_validators=number_of_agents,
        host_names=host_names,
    )
    agent_deployment_yaml = yaml.load_all(agent_deployment)
    resources = []
    for resource in agent_deployment_yaml:
        if resource.get("kind") == "Deployment":
            for container in resource['spec']['template']['spec']['containers']:
                if container['name'] == 'aea':
                    container['env'] += [{"name": k, "value": f"'v'"} for k, v in agent_vars.items()]
        resources.append(resource)

    res = "\n---\n".join([yaml.safe_dump(i) for i in resources])
    return f"\n{res}\n---\n"


class KubernetesGenerator(BaseDeploymentGenerator):
    """Kubernetes Deployment Generator."""

    output_name = "build.yaml"
    output: str = ""

    def generate_config_tendermint(self, valory_application: BaseDeployment) -> str:
        """Build configuration job."""
        host_names = ", ".join(
            [f'"--hostname=agent-node-{i}-service"' for i in range(valory_application.number_of_agents)]
        )

        config_job_yaml = CLUSTER_CONFIGURATION_TEMPLATE.format(
            number_of_validators=valory_application.number_of_agents,
            host_names=host_names,
        )
        return config_job_yaml

    def generate(self, valory_application: BaseDeployment) -> str:
        """Generate the deployment."""
        self.output += self.generate_config_tendermint(valory_application)

        if self.network == "hardhat":
            self.output += HARDHAT_TEMPLATE

        agent_vars = valory_application.generate_agents()
        agents = "".join(
            [
                build_agent_deployment(i, self.number_of_agents, agent_vars[i])
                for i in range(self.number_of_agents)
            ]
        )
        self.output += agents
        return self.output


if __name__ == "__main__":
    main()
