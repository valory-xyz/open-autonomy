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

from deployments.constants import CONFIG_DIRECTORY, KEYS, PRICE_APIS, RANDOMNESS_APIS


class BaseDeployment(abc.ABC):
    """Base deployment class."""

    valory_application: str
    network: str
    number_of_agents: int

    def __init__(self, *, number_of_agents: int, network: str):
        """Initialise the deployment."""
        self.network = network
        self.number_of_agents = number_of_agents

    @abc.abstractmethod
    def generate_agents(self) -> List[Dict]:
        """Generate next agent."""

    @abc.abstractmethod
    def generate_agent(self, agent_n: int) -> Dict[Any, Any]:
        """Generate next agent."""

    @abc.abstractmethod
    def setup(self) -> str:
        """Prepare agent generator."""


class CounterDeployment(BaseDeployment):
    """Simple counter deployment."""

    valory_application = "valory/counter:0.1.0"

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
        return environment

    def generate_agents(self) -> List:
        """Use constants available to generate the configuration."""
        return [self.generate_agent(i) for i in range(self.number_of_agents)]

    def setup(self) -> str:
        """Prepare agent generator."""


class APYEstimationDeployment(BaseDeployment):
    """APY Estimation application."""

    valory_application = "valory/apy_estimation:0.1.0"

    def generate_agent(self, agent_n: int) -> Dict:
        """Generate next agent."""
        environment = dict(AEA_KEY=KEYS[agent_n])
        return environment

    def generate_agents(self) -> List:
        """Generate multiple agent."""
        return [self.generate_agent(i) for i in range(self.number_of_agents)]

    def setup(self) -> str:
        """Prepare agent generator."""


class BaseDeploymentGenerator(abc.ABC):
    """Base Deployment Class."""

    old_wd: str
    output: str
    deployment: BaseDeployment
    output_name: str

    def setup(self) -> None:
        """Set up the directory for the configuration to written to."""
        self.old_wd = os.getcwd()
        if self.config_dir.is_dir():
            rmtree(str(self.config_dir))
        self.config_dir.mkdir()

    def teardown(self) -> None:
        """Move back to original wd"""

    def __init__(
        self, number_of_agents: int, network: str, config_dir: str = str(CONFIG_DIRECTORY)
    ):
        """Initialise with only kwargs."""
        self.number_of_agents = number_of_agents
        self.network = network
        self.config_dir = Path(config_dir)

    @abc.abstractmethod
    def generate(self, valory_application: Type[BaseDeployment]) -> str:
        """Generate the deployment configuration."""

    @abc.abstractmethod
    def generate_config_tendermint(self, valory_application: Type[BaseDeployment]) -> str:
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
