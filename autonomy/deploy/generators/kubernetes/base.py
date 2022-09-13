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

"""Script to create environment for benchmarking n agents."""

from pathlib import Path
from typing import Any, Dict, List, Optional, cast

import yaml

from autonomy.constants import (
    HARDHAT_IMAGE_NAME,
    HARDHAT_IMAGE_VERSION,
    OAR_IMAGE,
    TENDERMINT_IMAGE_NAME,
    TENDERMINT_IMAGE_VERSION,
)
from autonomy.deploy.base import BaseDeploymentGenerator, ServiceSpecification
from autonomy.deploy.constants import (
    DEFAULT_ENCODING,
    KEY_SCHEMA_PRIVATE_KEY,
    KUBERNETES_AGENT_KEY_NAME,
    TENDERMINT_CONFIGURATION_OVERRIDES,
)
from autonomy.deploy.generators.kubernetes.templates import (
    AGENT_NODE_TEMPLATE,
    AGENT_SECRET_TEMPLATE,
    CLUSTER_CONFIGURATION_TEMPLATE,
    HARDHAT_TEMPLATE,
)


class KubernetesGenerator(BaseDeploymentGenerator):
    """Kubernetes Deployment Generator."""

    output_name: str = "build.yaml"
    deployment_type: str = "kubernetes"

    def __init__(  # pylint: disable=too-many-arguments
        self,
        service_spec: ServiceSpecification,
        build_dir: Path,
        dev_mode: bool = False,
        packages_dir: Optional[Path] = None,
        open_aea_dir: Optional[Path] = None,
        open_autonomy_dir: Optional[Path] = None,
    ) -> None:
        """Initialise the deployment generator."""
        super().__init__(
            service_spec,
            build_dir,
            dev_mode,
            packages_dir,
            open_aea_dir,
            open_autonomy_dir,
        )
        self.resources: List[str] = []

    def build_agent_deployment(
        self,
        runtime_image: str,
        agent_ix: int,
        number_of_agents: int,
        agent_vars: Dict[str, Any],
    ) -> str:
        """Build agent deployment."""

        host_names = ", ".join(
            [f'"--hostname=abci{i}"' for i in range(number_of_agents)]
        )

        agent_deployment = AGENT_NODE_TEMPLATE.format(
            runtime_image=runtime_image,
            validator_ix=agent_ix,
            aea_key=self.service_spec.keys[agent_ix][KEY_SCHEMA_PRIVATE_KEY],
            number_of_validators=number_of_agents,
            host_names=host_names,
            tendermint_image_name=TENDERMINT_IMAGE_NAME,
            tendermint_image_version=TENDERMINT_IMAGE_VERSION,
            log_level=self.service_spec.log_level,
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

    def generate_config_tendermint(self) -> "KubernetesGenerator":
        """Build configuration job."""

        if self.tendermint_job_config is not None:  # pragma: no cover
            return self

        host_names = ", ".join(
            [
                f'"--hostname=abci{i}"'
                for i in range(self.service_spec.service.number_of_agents)
            ]
        )

        self.tendermint_job_config = CLUSTER_CONFIGURATION_TEMPLATE.format(
            valory_app=self.service_spec.service.agent.name,
            number_of_validators=self.service_spec.service.number_of_agents,
            host_names=host_names,
            tendermint_image_name=TENDERMINT_IMAGE_NAME,
            tendermint_image_version=TENDERMINT_IMAGE_VERSION,
        )

        return self

    def _apply_cluster_specific_tendermint_params(  # pylint: disable= no-self-use
        self, agent_params: List
    ) -> List:
        """Override the tendermint params to point at the localhost."""
        for agent in agent_params:
            agent.update(TENDERMINT_CONFIGURATION_OVERRIDES[self.deployment_type])
        return agent_params

    def generate(self, image_version: Optional[str] = None) -> "KubernetesGenerator":
        """Generate the deployment."""

        image_version = image_version or self.service_spec.service.agent.hash
        if self.dev_mode:
            self.resources.append(
                HARDHAT_TEMPLATE % (HARDHAT_IMAGE_NAME, HARDHAT_IMAGE_VERSION)
            )
            image_version = "dev"

        agent_vars = self.service_spec.generate_agents()  # type:ignore
        agent_vars = self._apply_cluster_specific_tendermint_params(agent_vars)
        runtime_image = OAR_IMAGE.format(
            agent=self.service_spec.service.agent.name,
            version=image_version,
        )

        agents = "\n---\n".join(
            [
                self.build_agent_deployment(
                    runtime_image=runtime_image,
                    agent_ix=i,
                    number_of_agents=self.service_spec.service.number_of_agents,
                    agent_vars=agent_vars[i],
                )
                for i in range(self.service_spec.service.number_of_agents)
            ]
        )
        self.resources.append(agents)
        self.output = "\n---\n".join(self.resources)
        return self

    def write_config(
        self,
    ) -> "KubernetesGenerator":
        """Write output to build dir"""

        output = "---\n".join([self.output, cast(str, self.tendermint_job_config)])
        if not self.build_dir.is_dir():  # pragma: no cover
            self.build_dir.mkdir()
        with open(
            self.build_dir / self.output_name, "w", encoding=DEFAULT_ENCODING
        ) as f:
            f.write(output)

        return self

    def populate_private_keys(self) -> "BaseDeploymentGenerator":
        """Populates private keys into a config map for the kubernetes deployment."""
        path = self.build_dir / "agent_keys"
        for x in range(self.service_spec.service.number_of_agents):
            key = self.service_spec.keys[x][KEY_SCHEMA_PRIVATE_KEY]
            secret = AGENT_SECRET_TEMPLATE.format(private_key=key, validator_ix=x)
            with open(
                path / KUBERNETES_AGENT_KEY_NAME.format(agent_n=x), "w", encoding="utf8"
            ) as f:
                f.write(secret)
        return self
