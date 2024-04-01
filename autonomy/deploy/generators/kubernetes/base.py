# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2024 Valory AG
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
from aea.configurations.constants import DEFAULT_LEDGER, LEDGER, PRIVATE_KEY

from autonomy.constants import (
    HARDHAT_IMAGE_NAME,
    HARDHAT_IMAGE_VERSION,
    OAR_IMAGE,
    TENDERMINT_IMAGE_NAME,
    TENDERMINT_IMAGE_VERSION,
)
from autonomy.deploy.base import (
    BaseDeploymentGenerator,
    DEFAULT_RESOURCE_VALUES,
    Resources,
    tm_write_to_log,
)
from autonomy.deploy.constants import DEFAULT_ENCODING, KUBERNETES_AGENT_KEY_NAME
from autonomy.deploy.generators.kubernetes.templates import (
    AGENT_NODE_TEMPLATE,
    AGENT_SECRET_TEMPLATE,
    CLUSTER_CONFIGURATION_TEMPLATE,
    HARDHAT_TEMPLATE,
    PORTS_CONFIG_DEPLOYMENT,
    PORT_CONFIG_DEPLOYMENT,
    PVC_TEMPLATE,
    SECRET_KEY_TEMPLATE,
    SECRET_STRING_DATA_TEMPLATE,
    VOLUME_CLAIM_TEMPLATE,
    VOLUME_MOUNT_TEMPLATE,
)


class KubernetesGenerator(BaseDeploymentGenerator):
    """Kubernetes Deployment Generator."""

    output_name: str = "build.yaml"
    deployment_type: str = "kubernetes"

    build: List[str]

    def build_agent_deployment(  # pylint: disable=too-many-locals,too-many-arguments
        self,
        runtime_image: str,
        agent_ix: int,
        number_of_agents: int,
        agent_vars: Dict[str, Any],
        agent_ports: Optional[Dict[int, int]] = None,
        resources: Optional[Resources] = None,
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

        if self.service_builder.multiledger:
            keys = ""
            for keypair in cast(
                List[Dict[str, str]], self.service_builder.keys[agent_ix]
            ):
                keys += SECRET_KEY_TEMPLATE.format(
                    ledger=keypair.get(LEDGER, DEFAULT_LEDGER)
                )
        else:
            keys = SECRET_KEY_TEMPLATE.format(
                ledger=cast(List[Dict[str, str]], self.service_builder.keys)[
                    agent_ix
                ].get(LEDGER, DEFAULT_LEDGER)
            )

        volume_mounts = ""
        volume_claims = ""
        extra_volumes = self.service_builder.service.deployment_config.get(
            "agent", {}
        ).get("volumes", {})
        for host_dir, mount_path in extra_volumes.items():
            host_path = Path(host_dir).resolve()
            name = host_path.name.replace("_", "-")
            volume_claims += VOLUME_CLAIM_TEMPLATE.format(name=name)
            volume_mounts += VOLUME_MOUNT_TEMPLATE.format(
                mount_path=mount_path, name=name
            )

        resources = resources if resources is not None else DEFAULT_RESOURCE_VALUES
        agent_deployment = AGENT_NODE_TEMPLATE.format(
            runtime_image=runtime_image,
            validator_ix=agent_ix,
            number_of_validators=number_of_agents,
            host_names=host_names,
            tendermint_image_name=TENDERMINT_IMAGE_NAME,
            tendermint_image_version=TENDERMINT_IMAGE_VERSION,
            log_level=self.service_builder.log_level,
            agent_ports_deployment=agent_ports_deployment,
            keys=keys,
            write_to_log=str(tm_write_to_log()).lower(),
            agent_cpu_request=resources["agent"]["requested"]["cpu"],
            agent_memory_request=resources["agent"]["requested"]["memory"],
            agent_cpu_limit=resources["agent"]["limit"]["cpu"],
            agent_memory_limit=resources["agent"]["limit"]["memory"],
            volume_mounts=volume_mounts,
            volume_claims=volume_claims,
        )
        agent_deployment_yaml = yaml.load_all(agent_deployment, Loader=yaml.FullLoader)  # type: ignore
        build = []
        for resource in agent_deployment_yaml:
            if resource.get("kind") == "Deployment":
                for container in resource["spec"]["template"]["spec"]["containers"]:
                    if container["name"] == "aea":
                        container["env"] += [
                            {"name": k, "value": f"{v}"} for k, v in agent_vars.items()
                        ]
            build.append(resource)

        res = "\n---\n".join([yaml.safe_dump(i) for i in build])
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

        pvcs = ""
        extra_volumes = self.service_builder.service.deployment_config.get(
            "agent", {}
        ).get("volumes", {})
        for host_dir, _ in extra_volumes.items():
            host_path = Path(host_dir).resolve()
            name = host_path.name.replace("_", "-")
            pvcs += PVC_TEMPLATE.format(
                name=name,
            )
            host_path.mkdir(exist_ok=True, parents=True)

        self.tendermint_job_config = CLUSTER_CONFIGURATION_TEMPLATE.format(
            valory_app=self.service_builder.service.agent.name,
            number_of_validators=self.service_builder.service.number_of_agents,
            host_names=host_names,
            tendermint_image_name=TENDERMINT_IMAGE_NAME,
            tendermint_image_version=TENDERMINT_IMAGE_VERSION,
            pvcs=pvcs,
        )

        return self

    def generate(
        self,
        image_version: Optional[str] = None,
        use_hardhat: bool = False,
        use_acn: bool = False,
    ) -> "KubernetesGenerator":
        """Generate the deployment."""
        self.build = []
        image_version = image_version or self.service_builder.service.agent.hash
        if self.dev_mode:
            image_version = "dev"

        if use_hardhat:
            self.build.append(
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
                    resources=self.resources,
                )
                for i in range(self.service_builder.service.number_of_agents)
            ]
        )
        self.build.append(agents)
        self.output = "\n---\n".join(self.build)
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

    def _populate_keys(self) -> None:
        """Populate the keys directory"""
        path = self.build_dir / "agent_keys"
        for x in range(self.service_builder.service.number_of_agents):
            ledger = cast(List[Dict[str, str]], self.service_builder.keys)[x].get(
                LEDGER, DEFAULT_LEDGER
            )
            key = cast(List[Dict[str, str]], self.service_builder.keys)[x][PRIVATE_KEY]
            string_data = SECRET_STRING_DATA_TEMPLATE.format(
                ledger=ledger, private_key=key
            )
            secret = AGENT_SECRET_TEMPLATE.format(
                validator_ix=x, string_data=string_data[:-1]
            )
            with open(
                path / KUBERNETES_AGENT_KEY_NAME.format(agent_n=x), "w", encoding="utf8"
            ) as f:
                f.write(secret)

    def _populate_keys_multiledger(self) -> None:
        """Populate the keys directory with multiple set of keys"""
        path = self.build_dir / "agent_keys"
        for x in range(self.service_builder.service.number_of_agents):
            string_data = ""
            for keypair in cast(List[List[Dict[str, str]]], self.service_builder.keys)[
                x
            ]:
                ledger = keypair.get(LEDGER, DEFAULT_LEDGER)
                string_data += SECRET_STRING_DATA_TEMPLATE.format(
                    ledger=ledger, private_key=keypair[PRIVATE_KEY]
                )
            secret = AGENT_SECRET_TEMPLATE.format(
                validator_ix=x, string_data=string_data[:-1]
            )
            with open(
                path / KUBERNETES_AGENT_KEY_NAME.format(agent_n=x), "w", encoding="utf8"
            ) as f:
                f.write(secret)

    def populate_private_keys(self) -> "BaseDeploymentGenerator":
        """Populates private keys into a config map for the kubernetes deployment."""
        if self.service_builder.multiledger:
            self._populate_keys_multiledger()
        else:
            self._populate_keys()
        return self
