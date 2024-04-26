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
"""Script for generating deployment environments."""
from pathlib import Path
from typing import Dict, List, Optional, Type

from autonomy.deploy.base import BaseDeploymentGenerator, Resources, ServiceBuilder
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
    dev_mode: bool = False,
    packages_dir: Optional[Path] = None,
    open_aea_dir: Optional[Path] = None,
    agent_instances: Optional[List[str]] = None,
    multisig_address: Optional[str] = None,
    consensus_threshold: Optional[int] = None,
    log_level: str = INFO,
    apply_environment_variables: bool = False,
    image_version: Optional[str] = None,
    use_hardhat: bool = False,
    use_acn: bool = False,
    use_tm_testnet_setup: bool = False,
    image_author: Optional[str] = None,
    resources: Optional[Resources] = None,
) -> str:
    """Generate the deployment for the service."""
    if dev_mode and type_of_deployment != DockerComposeGenerator.deployment_type:
        raise RuntimeError(
            "Development mode can only be used with docker-compose deployments"
        )

    service_builder = ServiceBuilder.from_dir(
        path=service_path,
        keys_file=keys_file,
        number_of_agents=number_of_agents,
        agent_instances=agent_instances,
        apply_environment_variables=apply_environment_variables,
        dev_mode=dev_mode,
    )
    service_builder.deplopyment_type = type_of_deployment
    service_builder.log_level = log_level
    service_builder.try_update_runtime_params(
        multisig_address=multisig_address,
        agent_instances=agent_instances,
        consensus_threshold=consensus_threshold,
    )
    service_builder.try_update_abci_connection_params()

    DeploymentGenerator = DEPLOYMENT_OPTIONS[type_of_deployment]
    deployment = DeploymentGenerator(
        service_builder=service_builder,
        build_dir=build_dir,
        dev_mode=dev_mode,
        packages_dir=packages_dir,
        open_aea_dir=open_aea_dir,
        use_tm_testnet_setup=use_tm_testnet_setup,
        image_author=image_author,
        resources=resources,
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
