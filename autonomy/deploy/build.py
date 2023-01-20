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
"""Script for generating deployment environments."""
from pathlib import Path
from typing import Dict, List, Optional, Type

from autonomy.deploy.base import BaseDeploymentGenerator, ServiceBuilder
from autonomy.deploy.constants import DEPLOYMENT_REPORT, INFO
from autonomy.deploy.generators.docker_compose.base import DockerComposeGenerator
from autonomy.deploy.generators.kubernetes.base import KubernetesGenerator


DEPLOYMENT_OPTIONS: Dict[str, Type[BaseDeploymentGenerator]] = {
    "kubernetes": KubernetesGenerator,
    "docker-compose": DockerComposeGenerator,
}


def generate_deployment(  # pylint: disable=too-many-arguments, too-many-locals
    type_of_deployment: str,
    keys_file: Path,
    service_path: Path,
    build_dir: Path,
    number_of_agents: Optional[int] = None,
    private_keys_password: Optional[str] = None,
    dev_mode: bool = False,
    packages_dir: Optional[Path] = None,
    open_aea_dir: Optional[Path] = None,
    open_autonomy_dir: Optional[Path] = None,
    agent_instances: Optional[List[str]] = None,
    multisig_address: Optional[str] = None,
    log_level: str = INFO,
    apply_environment_variables: bool = False,
    image_version: Optional[str] = None,
    use_hardhat: bool = False,
    use_acn: bool = False,
) -> str:
    """Generate the deployment for the service."""

    service_builder = ServiceBuilder.from_dir(
        path=service_path,
        keys_file=keys_file,
        number_of_agents=number_of_agents,
        private_keys_password=private_keys_password,
        agent_instances=agent_instances,
        apply_environment_variables=apply_environment_variables,
    )
    service_builder.log_level = log_level
    service_builder.try_update_runtime_params(
        multisig_address=multisig_address,
        agent_instances=agent_instances,
    )

    DeploymentGenerator = DEPLOYMENT_OPTIONS[type_of_deployment]
    deployment = DeploymentGenerator(
        service_builder=service_builder,
        build_dir=build_dir,
        dev_mode=dev_mode,
        packages_dir=packages_dir,
        open_aea_dir=open_aea_dir,
        open_autonomy_dir=open_autonomy_dir,
    )

    (
        deployment.generate(
            image_version=image_version,
            use_acn=use_acn,
            use_hardhat=use_hardhat,
        )
        .generate_config_tendermint()
        .write_config()
        .populate_private_keys()
    )

    return DEPLOYMENT_REPORT.substitute(
        **{
            "type": type_of_deployment,
            "agents": service_builder.service.number_of_agents,
            "size": len(deployment.output),
        }
    )
