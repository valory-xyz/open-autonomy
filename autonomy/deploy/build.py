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

from autonomy.constants import (
    HARDHAT_IMAGE_VERSION,
    IMAGE_VERSION,
    TENDERMINT_IMAGE_VERSION,
)
from autonomy.deploy.base import BaseDeploymentGenerator, ServiceSpecification
from autonomy.deploy.constants import DEPLOYMENT_REPORT
from autonomy.deploy.generators.docker_compose.base import DockerComposeGenerator
from autonomy.deploy.generators.kubernetes.base import KubernetesGenerator


DEPLOYMENT_OPTIONS = {
    "kubernetes": KubernetesGenerator,
    "docker-compose": DockerComposeGenerator,
}


def generate_deployment(  # pylint: disable=too-many-arguments
    type_of_deployment: str,
    private_keys_file_path: Path,
    service_path: Path,
    build_dir: Path,
    number_of_agents: Optional[int] = None,
    private_keys_password: Optional[str] = None,
    dev_mode: bool = False,
    version: Optional[str] = None,
) -> str:
    """Generate the deployment build for the valory app."""

    if version is None:
        image_versions = {
            "agent": IMAGE_VERSION,
            "hardhat": HARDHAT_IMAGE_VERSION,
            "tendermint": TENDERMINT_IMAGE_VERSION,
        }
    else:
        image_versions = {
            "agent": version,
            "hardhat": version,
            "tendermint": version,
        }

    service_spec = ServiceSpecification(
        service_path=service_path,
        keys=private_keys_file_path,
        private_keys_password=private_keys_password,
        number_of_agents=number_of_agents,
    )

    DeploymentGenerator = DEPLOYMENT_OPTIONS.get(type_of_deployment)
    if DeploymentGenerator is None:  # pragma: no cover
        raise ValueError(f"Cannot find deployment generator for {type_of_deployment}")
    deployment = cast(
        BaseDeploymentGenerator,
        DeploymentGenerator(service_spec=service_spec, build_dir=build_dir),
    )

    deployment.generate(image_versions, dev_mode).generate_config_tendermint(
        image_versions["tendermint"]
    ).write_config().populate_private_keys()

    return DEPLOYMENT_REPORT.substitute(
        **{
            "type": type_of_deployment,
            "agents": service_spec.service.number_of_agents,
            "network": service_spec.service.network,
            "size": len(deployment.output),
        }
    )
