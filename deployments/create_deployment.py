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
from argparse import ArgumentParser
from textwrap import dedent
from typing import Any

from deployments.base_deployments import (
    APYEstimationDeployment,
    CounterDeployment,
    PriceEstimationDeployment,
)
from deployments.constants import NETWORKS
from deployments.generators.docker_compose.docker_compose import DockerComposeGenerator
from deployments.generators.kubernetes.kubernetes import KubernetesGenerator


DEPLOYMENT_OPTIONS = {
    "kubernetes": KubernetesGenerator,
    "docker-compose": DockerComposeGenerator,
}

AGENTS = {
    k.valory_application: k
    for k in [
        CounterDeployment,
        PriceEstimationDeployment,
        APYEstimationDeployment,
    ]
}


def parse_args() -> Any:
    """Parse cli arguments."""
    parser = ArgumentParser(
        description="Generic Deployment Generator for Valory Stack."
    )

    deploy_type = parser.add_argument_group(title="Deployment Targets")
    deploy_type.add_argument(
        "-ct",
        "--tendermint_configuration",
        help="Run to produce build step for tendermint validator nodes.",
        action="store_true",
        default=False,
    )
    deploy_type.add_argument(
        "-type",
        "--type_of_deployment",
        help="The underlying deployment mechanism to generate for.",
        choices=DEPLOYMENT_OPTIONS.keys(),
    )
    deploy_type.add_argument(
        "-app",
        "--valory_application",
        help="The Valory Agent Stack to be deployed.",
        choices=AGENTS.keys(),
        required=True,
    )

    deployment_parameters = parser.add_argument_group("deployment_parameters")
    deployment_parameters.add_argument("-n", "--number_of_agents", type=int, default=4)
    deployment_parameters.add_argument(
        "-b", "--copy_to_build", action="store_true", default=False
    )
    deployment_parameters.add_argument(
        "-dsc", "--deploy_safe_contract", action="store_true", default=False
    )
    deployment_parameters.add_argument(
        "-doc", "--deploy_oracle_contract", action="store_true", default=False
    )
    deployment_parameters.add_argument(
        "-net",
        "--network",
        help="Network to be used for deployment",
        choices=NETWORKS.keys(),
        required=True,
    )

    args = parser.parse_args()
    return args


def main() -> None:
    """Main Function."""
    args = parse_args()
    deployment_generator = DEPLOYMENT_OPTIONS[args.type_of_deployment]
    deployment = deployment_generator(
        number_of_agents=args.number_of_agents,
        network=args.network,
    )

    agent_generator = AGENTS[args.valory_application](
        number_of_agents=args.number_of_agents,
        network=args.network,
        deploy_oracle_contract=args.deploy_oracle_contract,
        deploy_safe_contract=args.deploy_safe_contract,
    )

    deployment.generate(agent_generator)

    run_command = deployment.generate_config_tendermint(agent_generator)

    deployment.write_config()

    report = dedent(
        f"""\
    Generated Deployment!\n\n
    Application:          {args.valory_application}
    Type:                 {args.type_of_deployment}
    Agents:               {args.number_of_agents}
    Network:              {args.network}
    Build Length          {len(deployment.output)}
    """
    )

    print(report)
    if args.tendermint_configuration:
        res = os.popen(run_command)  # nosec:
        print(res.read())
    else:
        print(
            f"To configure tendermint for specified Deployment please run: \n\n{run_command}"
        )


if __name__ == "__main__":
    main()
