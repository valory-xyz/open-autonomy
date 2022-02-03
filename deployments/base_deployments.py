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
    KEYS,
    NETWORKS,
    PRICE_APIS,
    RANDOMNESS_APIS,
)


validation._SCHEMAS_DIR = os.getcwd()  # pylint: disable=protected-access


def get_price_api(agent_n: int) -> Dict:
    """Gets the price api for the agent."""
    price_api = PRICE_APIS[agent_n % len(PRICE_APIS)]
    return {f"PRICE_API_{k.upper()}": v for k, v in price_api}


def get_randomness_api(agent_n: int) -> Dict:
    """Gets the randomness api for the agent."""
    randomness_api = RANDOMNESS_APIS[agent_n % len(RANDOMNESS_APIS)]
    return {f"RANDOMNESS_{k.upper()}": v for k, v in randomness_api}


class BaseDeployment:
    """Class to assist with generating deployments."""

    valory_application: str
    network: str
    number_of_agents: int

    def __init__(self, path_to_deployment_spec: str) -> None:
        """Initialize the Base Deployment."""
        self.validator = ConfigValidator(
            schema_filename="deployments/deployment_specifications/deployment_schema.json"
        )
        with open(path_to_deployment_spec, "r", encoding="utf8") as file:
            self.deployment_spec = yaml.load(file, Loader=yaml.SafeLoader)
        self.validator.validate(self.deployment_spec)
        self.__dict__.update(self.deployment_spec)

        self.agent_spec = self.load_agent()

    def get_network(self) -> Dict[str, Any]:
        """Returns the deployments network overrides"""
        return NETWORKS[self.network]

    def generate_agents(self) -> List:
        """Generate multiple agent."""
        return [self.generate_agent(i) for i in range(self.number_of_agents)]

    def generate_common_vars(self, agent_n: int) -> Dict:
        """Retrieve vars common for valory apps."""
        return {
            "AEA_KEY": KEYS[agent_n],
            "VALORY_APPLICATION": self.valory_application,
            "ABCI_HOST": f"abci{agent_n}" if self.network == "hardhat" else "",
            "MAX_PARTICIPANTS": self.number_of_agents,  # I believe that this is correct
            "TENDERMINT_URL": f"http://node{agent_n}:26657",
            "TENDERMINT_COM_URL": f"http://node{agent_n}:8080",
        }

    def generate_agent(self, agent_n: int) -> Dict[Any, Any]:
        """Generate next agent."""
        agent_vars = self.generate_common_vars(agent_n)
        agent_vars.update(NETWORKS[self.network])

        for section in self.agent_spec:
            if section.get("models", None):
                if "price_api" in section["models"].keys():  # type: ignore
                    agent_vars.update(get_price_api(agent_n))
                if "randomness_api" in section["models"].keys():  # type: ignore
                    agent_vars.update(get_randomness_api(agent_n))
        return agent_vars

    def load_agent(self) -> List[Dict[str, str]]:
        """Using specified valory app, try to load the aea."""
        aea_project_path = self.locate_agent_from_package_directory()
        # TODO: validate the aea config before loading
        with open(aea_project_path, "r", encoding="utf8") as file:
            aea_json = list(yaml.safe_load_all(file))
        return aea_json

    def get_parameters(
        self,
    ) -> Dict:
        """Retrieve the parameters for the deployment."""

    def locate_agent_from_package_directory(self, local_registry: bool = True) -> str:
        """Using the deployment id, locate the registry and retrieve the path."""
        if local_registry is False:
            raise ValueError("Remote registry not yet supported, use local!")
        for subdir, _, files in os.walk(AEA_DIRECTORY):
            for file in files:
                if file == "aea-config.yaml":
                    path = os.path.join(subdir, file)
                    with open(path, "r", encoding="utf-8") as aea_path:  # type: ignore
                        agent_spec = yaml.safe_load_all(aea_path)
                        for spec in agent_spec:
                            agent_id = f"{spec['author']}/{spec['agent_name']}:{spec['version']}"
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
        self.output = ""

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
