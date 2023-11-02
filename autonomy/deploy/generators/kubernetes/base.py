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

"""Script to create environment for benchmarking n agents."""

from pathlib import Path
from typing import Any, Dict, List, Optional, cast

import yaml
from aea.configurations.constants import DEFAULT_LEDGER

from autonomy.constants import (
    HARDHAT_IMAGE_NAME,
    HARDHAT_IMAGE_VERSION,
    OAR_IMAGE,
    TENDERMINT_IMAGE_NAME,
    TENDERMINT_IMAGE_VERSION,
)
from autonomy.deploy.base import BaseDeploymentGenerator, ServiceBuilder
from autonomy.deploy.constants import (
    DEFAULT_ENCODING,
    KEY_SCHEMA_PRIVATE_KEY,
    KEY_SCHEMA_TYPE,
    KUBERNETES_AGENT_KEY_NAME,
)
from autonomy.deploy.generators.kubernetes.templates import (
    AGENT_NODE_TEMPLATE,
    AGENT_SECRET_TEMPLATE,
    CLUSTER_CONFIGURATION_TEMPLATE,
    HARDHAT_TEMPLATE,
    PORTS_CONFIG_DEPLOYMENT,
    PORT_CONFIG_DEPLOYMENT,
)


class KubernetesGenerator(BaseDeploymentGenerator):
    """Kubernetes Deployment Generator."""

    output_name: str = "build.yaml"
    deployment_type: str = "kubernetes"

    def __init__(  # pylint: disable=too-many-arguments
        self,
        service_builder: ServiceBuilder,
        build_dir: Path,
        dev_mode: bool = False,
        packages_dir: Optional[Path] = None,
        open_aea_dir: Optional[Path] = None,
        open_autonomy_dir: Optional[Path] = None,
        use_tm_testnet_setup: bool = False,
        image_author: Optional[str] = None,
    ) -> None:
        """Initialise the deployment generator."""
        super().__init__(
            service_builder=service_builder,
            build_dir=build_dir,
            use_tm_testnet_setup=use_tm_testnet_setup,
            dev_mode=dev_mode,
            packages_dir=packages_dir,
            open_aea_dir=open_aea_dir,
            open_autonomy_dir=open_autonomy_dir,
            image_author=image_author,
        )
        self.resources: List[str] = []

    def build_agent_deployment(
        self,
        runtime_image: str,
        agent_ix: int,
        number_of_agents: int,
        agent_vars: Dict[str, Any],
        agent_ports: Optional[Dict[int, int]] = None,
    ) -> str:
        """Build agent deployment."""

        host_names = ", ".join(
            [f'"--hostname=abci{i}"' for i in range(number_of_agents)]
        )

        agent_ports_deployment = ""
        if agent_ports is not None:
            port_mappings = map(
                lambda x: PORT_CONFIG_DEPLOYMENT.format(port=x[0]),
                agent_ports.items(),
            )
            agent_ports_deployment = "\n".join(
                [PORTS_CONFIG_DEPLOYMENT, *port_mappings]
            )

        agent_deployment = AGENT_NODE_TEMPLATE.format(
            runtime_image=runtime_image,
            validator_ix=agent_ix,
            aea_key=self.service_builder.keys[agent_ix][KEY_SCHEMA_PRIVATE_KEY],
            number_of_validators=number_of_agents,
            host_names=host_names,
            tendermint_image_name=TENDERMINT_IMAGE_NAME,
            tendermint_image_version=TENDERMINT_IMAGE_VERSION,
            log_level=self.service_builder.log_level,
            agent_ports_deployment=agent_ports_deployment,
            ledger=self.service_builder.keys[agent_ix].get(
                KEY_SCHEMA_TYPE, DEFAULT_LEDGER
            ),
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
                for i in range(self.service_builder.service.number_of_agents)
            ]
        )

        self.tendermint_job_config = CLUSTER_CONFIGURATION_TEMPLATE.format(
            valory_app=self.service_builder.service.agent.name,
            number_of_validators=self.service_builder.service.number_of_agents,
            host_names=host_names,
            tendermint_image_name=TENDERMINT_IMAGE_NAME,
            tendermint_image_version=TENDERMINT_IMAGE_VERSION,
        )

        return self

    def generate(
        self,
        image_version: Optional[str] = None,
        use_hardhat: bool = False,
        use_acn: bool = False,
    ) -> "KubernetesGenerator":
        """Generate the deployment."""

        image_version = image_version or self.service_builder.service.agent.hash

        if self.dev_mode:
            image_version = "dev"

        if use_hardhat:
            self.resources.append(
                HARDHAT_TEMPLATE % (HARDHAT_IMAGE_NAME, HARDHAT_IMAGE_VERSION)
            )

        if use_acn:
            # insert an ACN node into resources
            ...

        agent_vars = self.service_builder.generate_agents()  # type:ignore
        runtime_image = OAR_IMAGE.format(
            image_author=self.image_author,
            agent=self.service_builder.service.agent.name,
            version=image_version,
        )

        agents = "\n---\n".join(
            [
                self.build_agent_deployment(
                    runtime_image=runtime_image,
                    agent_ix=i,
                    number_of_agents=self.service_builder.service.number_of_agents,
                    agent_vars=agent_vars[i],
                    agent_ports=(
                        self.service_builder.service.deployment_config.get("agent", {})
                        .get("ports", {})
                        .get(i)
                    ),
                )
                for i in range(self.service_builder.service.number_of_agents)
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
        for x in range(self.service_builder.service.number_of_agents):
            ledger = self.service_builder.keys[x].get(KEY_SCHEMA_TYPE, DEFAULT_LEDGER)
            key = self.service_builder.keys[x][KEY_SCHEMA_PRIVATE_KEY]
            secret = AGENT_SECRET_TEMPLATE.format(
                private_key=key, validator_ix=x, ledger=ledger
            )
            with open(
                path / KUBERNETES_AGENT_KEY_NAME.format(agent_n=x), "w", encoding="utf8"
            ) as f:
                f.write(secret)
        return self
