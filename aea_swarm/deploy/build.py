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
"""Script for generating deployment environments."""
from pathlib import Path
from typing import Optional, cast

from aea_swarm.deploy.base import BaseDeploymentGenerator, DeploymentSpec
from aea_swarm.deploy.constants import DEPLOYMENT_REPORT
from aea_swarm.deploy.generators.docker_compose.base import DockerComposeGenerator
from aea_swarm.deploy.generators.kubernetes.base import KubernetesGenerator


DEPLOYMENT_OPTIONS = {
    "kubernetes": KubernetesGenerator,
    "docker-compose": DockerComposeGenerator,
}


def generate_deployment(  # pylint: disable=too-many-arguments
    type_of_deployment: str,
    private_keys_file_path: Path,
    deployment_file_path: Path,
    package_dir: Path,
    build_dir: Path,
    number_of_agents: Optional[int] = None,
    dev_mode: bool = False,
) -> str:
    """Generate the deployment build for the valory app."""

    deployment_spec = DeploymentSpec(
        path_to_deployment_spec=str(deployment_file_path),
        private_keys_file_path=Path(private_keys_file_path),
        package_dir=package_dir,
        number_of_agents=number_of_agents,
    )

    DeploymentGenerator = DEPLOYMENT_OPTIONS.get(type_of_deployment)
    if DeploymentGenerator is None:
        raise ValueError(f"Cannot find deployment generator for {type_of_deployment}")
    deployment = cast(
        BaseDeploymentGenerator,
        DeploymentGenerator(deployment_spec=deployment_spec, build_dir=build_dir),
    )

    deployment.generate(dev_mode).generate_config_tendermint().write_config()

    return DEPLOYMENT_REPORT.substitute(
        **{
            "type": type_of_deployment,
            "agents": (
                deployment_spec.number_of_agents
                if number_of_agents is None
                else number_of_agents
            ),
            "network": deployment_spec.network,
            "size": len(deployment.output),
        }
    )
