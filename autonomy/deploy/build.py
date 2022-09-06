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
from typing import List, Optional, cast

from autonomy.deploy.base import BaseDeploymentGenerator, ServiceSpecification
from autonomy.deploy.constants import DEPLOYMENT_REPORT, INFO
from autonomy.deploy.generators.docker_compose.base import DockerComposeGenerator
from autonomy.deploy.generators.kubernetes.base import KubernetesGenerator


DEPLOYMENT_OPTIONS = {
    "kubernetes": KubernetesGenerator,
    "docker-compose": DockerComposeGenerator,
}


def generate_deployment(  # pylint: disable=too-many-arguments, too-many-locals
    type_of_deployment: str,
    private_keys_file_path: Path,
    service_path: Path,
    build_dir: Path,
    number_of_agents: Optional[int] = None,
    private_keys_password: Optional[str] = None,
    dev_mode: bool = False,
    packages_dir: Optional[Path] = None,
    open_aea_dir: Optional[Path] = None,
    open_autonomy_dir: Optional[Path] = None,
    agent_instances: Optional[List[str]] = None,
    log_level: str = INFO,
    substitute_env_vars: bool = False,
    image_version: Optional[str] = None,
) -> str:
    """Generate the deployment build for the valory app."""

    service_spec = ServiceSpecification(
        service_path=service_path,
        keys=private_keys_file_path,
        private_keys_password=private_keys_password,
        number_of_agents=number_of_agents,
        agent_instances=agent_instances,
        log_level=log_level,
        substitute_env_vars=substitute_env_vars,
    )

    DeploymentGenerator = DEPLOYMENT_OPTIONS.get(type_of_deployment)
    if DeploymentGenerator is None:  # pragma: no cover
        raise ValueError(f"Cannot find deployment generator for {type_of_deployment}")

    deployment = cast(
        BaseDeploymentGenerator,
        DeploymentGenerator(
            service_spec=service_spec,
            build_dir=build_dir,
            dev_mode=dev_mode,
            packages_dir=packages_dir,
            open_aea_dir=open_aea_dir,
            open_autonomy_dir=open_autonomy_dir,
        ),
    )

    (
        deployment.generate(image_version=image_version)
        .generate_config_tendermint()
        .write_config()
        .populate_private_keys()
    )

    return DEPLOYMENT_REPORT.substitute(
        **{
            "type": type_of_deployment,
            "agents": service_spec.service.number_of_agents,
            "size": len(deployment.output),
        }
    )
