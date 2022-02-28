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
"""Script for generating deployment environments."""
import os
from pathlib import Path
from typing import Dict, Optional

from deployments.base_deployments import BaseDeployment
from deployments.constants import DEPLOYMENT_REPORT
from deployments.generators.docker_compose.docker_compose import DockerComposeGenerator
from deployments.generators.kubernetes.kubernetes import KubernetesGenerator


AGENTS: Dict[str, str] = {
    "oracle_hardhat": "./deployments/deployment_specifications/price_estimation_hardhat.yaml",
    "oracle_ropsten": "./deployments/deployment_specifications/price_estimation_ropsten.yaml",
    "apy_hardhat": "./deployments/deployment_specifications/apy_estimation_hardhat.yaml",
}


DEPLOYMENT_OPTIONS = {
    "kubernetes": KubernetesGenerator,
    "docker-compose": DockerComposeGenerator,
}


def generate_deployment(
    type_of_deployment: str,
    configure_tendermint: bool,
    private_keys_file_path: str,
    valory_application: Optional[str] = None,
    deployment_file_path: Optional[str] = None,
) -> str:
    """Generate the deployment build for the valory app."""
    deployment_generator = DEPLOYMENT_OPTIONS[type_of_deployment]
    if valory_application is not None and deployment_file_path is None:
        deployment_file_path = AGENTS[valory_application]
    elif valory_application is None and deployment_file_path is not None:
        if not Path(deployment_file_path).exists():
            raise ValueError("Specified deployment path does not exist!")
    else:
        raise ValueError(
            "Much specify either a path to a deployment or a known application."
        )

    app_instance = BaseDeployment(
        path_to_deployment_spec=deployment_file_path,
        private_keys_file_path=Path(private_keys_file_path),
    )
    deployment = deployment_generator(deployment_spec=app_instance)
    deployment.generate(app_instance)  # type: ignore
    run_command = deployment.generate_config_tendermint(app_instance)  # type: ignore
    deployment.write_config()
    report = DEPLOYMENT_REPORT.substitute(
        **{
            "app": valory_application,
            "type": type_of_deployment,
            "agents": app_instance.number_of_agents,
            "network": app_instance.network,
            "size": len(deployment.output),
        }
    )
    if type_of_deployment == DockerComposeGenerator.deployment_type:
        if configure_tendermint:
            res = os.popen(run_command)  # nosec:
            print(res.read())
        else:
            print(
                f"To configure tendermint for deployment please run: \n\n{run_command}"
            )
    elif type_of_deployment == KubernetesGenerator.deployment_type:
        if configure_tendermint:
            deployment.write_config(run_command)  # type:ignore
        else:
            print("To configure tendermint please run generate and run a config job.")
    return report
