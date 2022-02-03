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

"""Base deployments module."""


import abc
import os
from pathlib import Path
from shutil import rmtree
from typing import Any, Dict, List, Type

import yaml
from aea.configurations import validation
from aea.configurations.validation import ConfigValidator

from deployments.constants import (
    AEA_DIRECTORY,
    CONFIG_DIRECTORY,
    DEPLOYED_CONTRACTS,
    KEYS,
    NETWORKS,
    PRICE_APIS,
    RANDOMNESS_APIS,
)


validation._SCHEMAS_DIR = os.getcwd()


class BaseDeployment:
    valory_application: str
    network: str
    number_of_agents: int

    def __init__(self, path_to_deployment_spec: str) -> None:
        self.validator = ConfigValidator(
            schema_filename="deployments/deployment_specifications/deployment_schema.json"
        )
        self.deployment_spec = yaml.load(
            open(path_to_deployment_spec), Loader=yaml.SafeLoader
        )
        self.validator.validate(self.deployment_spec)
        self.__dict__.update(self.deployment_spec)

        self.agent_spec = self.load_agent()

    def get_network(self) -> Dict[str, str]:
        """Returns the deployments network overrides"""
        return NETWORKS[self.network.network]

    def generate_agents(self) -> List:
        """Generate multiple agent."""
        return [self.generate_agent(i) for i in range(self.number_of_agents)]

    def generate_common_vars(self, agent_n: int):
        """Retrieve vars common for valory apps."""
        return {
            "AEA_KEY": KEYS[agent_n],
            "VALORY_APPLICATION": self.valory_application,
            "ABCI_HOST": f"abci{agent_n}" if self.network == "hardhat" else "",
            "MAX_PARTICIPANTS": self.number_of_agents,  # I believe that this is correct
            "TENDERMINT_URL": f"http://node{agent_n}:26657",
            "TENDERMINT_COM_URL": f"http://node{agent_n}:8080",
        }

    def get_price_api(self, agent_n: int):
        """Gets the price api for the agent."""
        price_api = PRICE_APIS[agent_n % len(PRICE_APIS)]
        return {f"PRICE_API_{k.upper()}": v for k, v in price_api}

    def get_randomness_api(self, agent_n: int):
        """Gets the randomness api for the agent."""
        randomness_api = RANDOMNESS_APIS[agent_n % len(RANDOMNESS_APIS)]
        return {f"RANDOMNESS_{k.upper()}": v for k, v in randomness_api}

    def generate_agent(self, agent_n: int) -> Dict[Any, Any]:
        """Generate next agent."""
        agent_vars = self.generate_common_vars(agent_n)
        agent_vars.update(NETWORKS[self.network])

        for section in self.agent_spec:
            if section.get("models", None):
                if "price_api" in section["models"].keys():
                    agent_vars.update(self.get_price_api(agent_n))
                if "randomness_api" in section["models"].keys():
                    agent_vars.update(self.get_randomness_api(agent_n))
            # now we fill in consensus paramters

        #             params = section.get("params", None)
        #             if params is not None:
        #                 arguments = params.get("args", None)
        #                 if arguments is not None:
        #                     period_setup = arguments.get("period_setup", None)
        #
        #             if "params" in section["models"]:
        #                 # get consensus details.
        #                 if "period_setup" in section["params"]

        return agent_vars

    def check_all_vars_present(self, agent_vars):
        """Checks whether there are any vars from the agent_spec which have not been created for the env vars."""
        return agent_vars

    def load_agent(self) -> List[Dict[str, str]]:
        """Using specified valory app, try to load the aea."""
        aea_project_path = self.locate_agent_from_package_directory()
        # TODO: validate the aea config before loading
        aea_json = list(yaml.safe_load_all(open(aea_project_path)))
        return aea_json

    def get_parameters(
        self,
    ) -> Dict:
        """Retrieve the parameters for the deployment."""

    def locate_agent_from_package_directory(self, local_registry: bool = True) -> str:
        """Using the deployment id, locate the registry and retrieve the path."""
        if local_registry is False:
            raise ValueError("Remote registry not yet supported, use local!")
        for subdir, dirs, files in os.walk(AEA_DIRECTORY):
            for file in files:
                if file == "aea-config.yaml":
                    path = os.path.join(subdir, file)
                    agent_spec = yaml.safe_load_all(open(path))
                    for spec in agent_spec:
                        agent_id = (
                            f"{spec['author']}/{spec['agent_name']}:{spec['version']}"
                        )
                        if agent_id != self.valory_application:
                            break
                        return os.path.join(subdir, file)
        raise ValueError("Agent to be deployed not located in packages.")


class BaseDeploymentGenerator:
    """Base Deployment Class."""

    deployment: BaseDeployment
    output_name: str
    old_wd: str

    def __init__(self, deployment_spec: BaseDeployment):
        """Initialise with only kwargs."""
        self.deployment_spec = deployment_spec
        self.config_dir = Path(CONFIG_DIRECTORY)
        self.network_config = NETWORKS[deployment_spec.network]

    def setup(self) -> None:
        """Set up the directory for the configuration to written to."""
        self.old_wd = os.getcwd()
        if self.config_dir.is_dir():
            rmtree(str(self.config_dir))
        self.config_dir.mkdir()

    def teardown(self) -> None:
        """Move back to original wd"""

    @abc.abstractmethod
    def generate(self, valory_application: Type[BaseDeployment]) -> str:
        """Generate the deployment configuration."""

    @abc.abstractmethod
    def generate_config_tendermint(
        self, valory_application: Type[BaseDeployment]
    ) -> str:
        """Generate the deployment configuration."""

    def get_parameters(
        self,
    ) -> Dict:
        """Retrieve the parameters for the deployment."""

    def write_config(self) -> None:
        """Write output to build dir"""

        if not self.config_dir.is_dir():
            self.config_dir.mkdir()

        with open(self.config_dir / self.output_name, "w", encoding="utf8") as f:
            f.write(self.output)


# class BaseDeployment:
#     """Base deployment class."""
#
#     valory_application: str
#     network: str
#     number_of_agents: int
#     uses_oracle_contract: bool
#     uses_safe_contract: bool
#
#     def __init__(
#         self,
#         *,
#         number_of_agents: int,
#         network: str,
#         deploy_safe_contract: bool,
#         deploy_oracle_contract: bool,
#     ):
#         """Initialise the deployment."""
#         self.network = network
#         self.number_of_agents = number_of_agents
#         self.deploy_oracle_contract = deploy_oracle_contract
#         self.deploy_safe_contract = deploy_safe_contract
#         self.output = ""
#         self.network_config = NETWORKS[self.network]
#


class CounterDeployment(BaseDeployment):
    """Simple counter deployment."""

    valory_application = "valory/counter:0.1.0"
    uses_safe_contract = False
    uses_oracle_contract = False

    def generate_agent(self, agent_n: int) -> Dict:
        """Generate next agent."""
        environment = dict(AEA_KEY=KEYS[agent_n])
        return environment

    def generate_agents(self) -> List:
        """Generate multiple agent."""
        return [self.generate_agent(i) for i in range(self.number_of_agents)]

    def setup(self) -> str:
        """Prepare agent generator."""


class PriceEstimationDeployment(BaseDeployment):
    """Price Estimation deployment."""

    valory_application = "valory/price_estimation_deployable:0.1.0"
    uses_safe_contract = True
    uses_oracle_contract = True

    def get_contracts(self) -> Dict[str, Any]:
        """If configured, return deployed contracts as env vars."""

        additional_vars = {}
        if not self.deploy_safe_contract:
            contracts = DEPLOYED_CONTRACTS[self.network]
            additional_vars.update(
                {
                    "PRICE_ESTIMATION_PARAMS_PERIOD_SETUP_SAFE_CONTRACT_ADDRESS": contracts[
                        "safe_contract_address"
                    ]
                }
            )
        if not self.deploy_oracle_contract:
            contracts = DEPLOYED_CONTRACTS[self.network]
            additional_vars.update(
                {
                    "PRICE_ESTIMATION_PARAMS_PERIOD_SETUP_ORACLE_CONTRACT_ADDRESS": contracts[
                        "oracle_contract_address"
                    ]
                }
            )
        return additional_vars

    def generate_agent(self, agent_n: int) -> Dict:
        """Generate next agent."""
        price_api = PRICE_APIS[len(PRICE_APIS) % self.number_of_agents]
        randomness_api = RANDOMNESS_APIS[len(PRICE_APIS) % self.number_of_agents]
        environment = dict(
            AEA_KEY=KEYS[agent_n],
            VALORY_APPLICATION=self.valory_application,
            ABCI_HOST=f"abci{agent_n}" if self.network == "hardhat" else "",
            PRICE_ESTIMATION_PARAMS_MAX_PARTICIPANTS=self.number_of_agents
            + 3,  # Need to confirm this ceiling
            PRICE_ESTIMATION_PARAMS_TENDERMINT_URL=f"http://node{agent_n}:26657",
            PRICE_ESTIMATION_PARAMS_TENDERMINT_COM_URL=f"http://node{agent_n}:8080",
        )

        environment.update(
            {f"PRICE_ESTIMATION_ABCI_PRICE_API_{k.upper()}": v for k, v in price_api}
        )
        environment.update(
            {
                f"PRICE_ESTIMATION_ABCI_RANDOMNESS_{k.upper()}": v
                for k, v in randomness_api
            }
        )
        additional_vars = self.get_contracts()
        environment.update(additional_vars)

        environment.update(self.network_config)
        return environment

    def generate_agents(self) -> List:
        """Use constants available to generate the configuration."""
        return [self.generate_agent(i) for i in range(self.number_of_agents)]

    def setup(self) -> str:
        """Prepare agent generator."""


class APYEstimationDeployment(BaseDeployment):
    """APY Estimation application."""

    valory_application = "valory/apy_estimation:0.1.0"
    uses_safe_contract = False
    uses_oracle_contract = False

    def generate_agent(self, agent_n: int) -> Dict:
        """Generate next agent."""
        environment = dict(AEA_KEY=KEYS[agent_n])
        return environment

    def setup(self) -> str:
        """Prepare agent generator."""
