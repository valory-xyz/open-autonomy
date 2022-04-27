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

from typing import Any, Dict, List, Type

import yaml

from deployments.base_deployments import BaseDeployment, BaseDeploymentGenerator
from deployments.constants import TENDERMINT_CONFIGURATION_OVERRIDES
from deployments.generators.kubernetes.templates import (
    AGENT_NODE_TEMPLATE,
    CLUSTER_CONFIGURATION_TEMPLATE,
)


class KubernetesGenerator(BaseDeploymentGenerator):
    """Kubernetes Deployment Generator."""

    output_name = "build.yaml"
    deployment_type = "kubernetes"

    def __init__(
        self,
        deployment_spec: BaseDeployment,
    ) -> None:
        """Initialise the deployment generator."""
        super().__init__(deployment_spec)
        self.output = ""
        self.resources: List[str] = []

    def build_agent_deployment(
        self,
        image_name: str,
        agent_ix: int,
        number_of_agents: int,
        agent_vars: Dict[str, Any],
    ) -> str:
        """Build agent deployment."""
        host_names = ", ".join(
            [f'"--hostname=abci{i}"' for i in range(number_of_agents)]
        )

        agent_deployment = AGENT_NODE_TEMPLATE.format(
            valory_app=image_name,
            validator_ix=agent_ix,
            aea_key=self.deployment_spec.private_keys[agent_ix],
            number_of_validators=number_of_agents,
            host_names=host_names,
        )
        agent_deployment_yaml = yaml.load_all(agent_deployment, Loader=yaml.FullLoader)  # type: ignore
        resources = []
        for resource in agent_deployment_yaml:
            if resource.get("kind") == "Deployment":
                for container in resource["spec"]["template"]["spec"]["containers"]:
                    if container["name"] == "aea":
                        container["env"] += [
                            {"name": k, "value": f"{v}"} for k, v in agent_vars.items()
                        ]
            resources.append(resource)

        res = "\n---\n".join([yaml.safe_dump(i) for i in resources])
        return res

    def generate_config_tendermint(
        self, valory_application: Type[BaseDeployment]
    ) -> str:
        """Build configuration job."""
        host_names = ", ".join(
            [
                f'"--hostname=abci{i}"'
                for i in range(valory_application.number_of_agents)
            ]
        )

        config_job_yaml = CLUSTER_CONFIGURATION_TEMPLATE.format(
            number_of_validators=valory_application.number_of_agents,
            host_names=host_names,
        )
        return config_job_yaml

    def _apply_cluster_specific_tendermint_params(  # pylint: disable= no-self-use
        self, agent_params: List
    ) -> List:
        """Override the tendermint params to point at the localhost."""
        for agent in agent_params:
            agent.update(TENDERMINT_CONFIGURATION_OVERRIDES[self.deployment_type])
        return agent_params

    def generate(self, valory_application: Type[BaseDeployment]) -> str:
        """Generate the deployment."""
        self.resources.append(self.generate_config_tendermint(valory_application))
        agent_vars = valory_application.generate_agents()  # type:ignore
        agent_vars = self._apply_cluster_specific_tendermint_params(agent_vars)
        agent_vars = self.get_deployment_network_configuration(agent_vars)
        image_name = valory_application.agent_public_id.name
        agents = "\n---\n".join(
            [
                self.build_agent_deployment(
                    image_name, i, self.deployment_spec.number_of_agents, agent_vars[i]
                )
                for i in range(self.deployment_spec.number_of_agents)
            ]
        )
        self.resources.append(agents)
        self.output = "\n---\n".join(self.resources)
        return self.output

    def write_config(  # pylint: disable=arguments-differ
        self, configure_tendermint_resource: str = ""
    ) -> None:
        """Write output to build dir"""

        if configure_tendermint_resource == "":
            output = self.output
        else:
            output = "---\n".join([self.output, configure_tendermint_resource])

        if not self.config_dir.is_dir():
            self.config_dir.mkdir()

        with open(self.config_dir / self.output_name, "w", encoding="utf8") as f:
            f.write(output)
