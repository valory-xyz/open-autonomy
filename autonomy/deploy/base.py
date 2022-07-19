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

"""Base deployments module."""
import abc
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, cast

from aea.configurations.base import (
    ConnectionConfig,
    ContractConfig,
    ProtocolConfig,
    SkillConfig,
)

from autonomy.configurations.base import Service
from autonomy.configurations.loader import load_service_config
from autonomy.constants import TENDERMINT_IMAGE_VERSION
from autonomy.deploy.constants import (
    DEFAULT_ENCODING,
    KEY_SCHEMA_ADDRESS,
    KEY_SCHEMA_ENCRYPTED_KEY,
    KEY_SCHEMA_UNENCRYPTED_KEY,
    NETWORKS,
)


ABCI_HOST = "abci{}"
TENDERMINT_NODE = "http://node{}:26657"
TENDERMINT_COM = "http://node{}:8080"
COMPONENT_CONFIGS: Dict = {
    component.package_type.value: component  # type: ignore
    for component in [
        ContractConfig,
        SkillConfig,
        ProtocolConfig,
        ConnectionConfig,
    ]
}


class ServiceSpecification:
    """Class to assist with generating deployments."""

    service: Service
    overrides: List
    packages_dir: Path

    def __init__(
        self,
        service_path: Path,
        keys: Path,
        number_of_agents: Optional[int] = None,
        private_keys_password: Optional[str] = None,
    ) -> None:
        """Initialize the Base Deployment."""
        self.private_keys: List = []
        self.private_keys_password = private_keys_password
        self.service = load_service_config(service_path)
        if number_of_agents is not None:
            self.service.number_of_agents = number_of_agents

        self.read_keys(keys)
        if self.service.number_of_agents > len(self.private_keys):
            raise ValueError("Number of agents cannot be greater than available keys.")

    def read_keys(self, file_path: Path) -> None:
        """Read in keys from a file on disk."""

        keys = json.loads(file_path.read_text(encoding=DEFAULT_ENCODING))

        key_schema = (
            KEY_SCHEMA_UNENCRYPTED_KEY
            if self.private_keys_password is None
            else KEY_SCHEMA_ENCRYPTED_KEY
        )
        for key in keys:
            for required_key in [KEY_SCHEMA_ADDRESS, key_schema]:
                if required_key not in key.keys():
                    raise ValueError("Key file incorrectly formatted.")
            self.private_keys.append(key[key_schema])

    def process_model_args_overrides(self, agent_n: int) -> Dict:
        """Generates env vars based on model overrides."""
        final_overrides = {}
        for component_configuration_json in self.service.overrides:
            _, overrides = self.service.process_component_section(
                agent_n, component_configuration_json
            )
            final_overrides.update(overrides)
        return final_overrides

    def generate_agents(self) -> List:
        """Generate multiple agent."""
        return [self.generate_agent(i) for i in range(self.service.number_of_agents)]

    def generate_common_vars(self, agent_n: int) -> Dict:
        """Retrieve vars common for valory apps."""
        agent_vars = {
            "ID": agent_n,
            "VALORY_APPLICATION": self.service.agent,
            "ABCI_HOST": ABCI_HOST.format(agent_n),
            "MAX_PARTICIPANTS": self.service.number_of_agents,
            "TENDERMINT_URL": TENDERMINT_NODE.format(agent_n),
            "TENDERMINT_COM_URL": TENDERMINT_COM.format(agent_n),
        }

        if self.private_keys_password is not None:
            agent_vars["AEA_PASSWORD"] = self.private_keys_password
        return agent_vars

    def generate_agent(self, agent_n: int) -> Dict[Any, Any]:
        """Generate next agent."""
        agent_vars = self.generate_common_vars(agent_n)
        if len(self.service.overrides) == 0:
            return agent_vars
        overrides = self.process_model_args_overrides(agent_n)
        agent_vars.update(overrides)
        for var_name, value in agent_vars.items():
            if any([isinstance(value, list), isinstance(value, dict)]):
                agent_vars[var_name] = json.dumps(value)
        return agent_vars


class BaseDeploymentGenerator:
    """Base Deployment Class."""

    service_spec: ServiceSpecification
    output_name: str
    deployment_type: str
    build_dir: Path
    output: str
    tendermint_job_config: Optional[str]

    def __init__(self, service_spec: ServiceSpecification, build_dir: Path):
        """Initialise with only kwargs."""
        self.network_config = NETWORKS[self.deployment_type][
            cast(str, service_spec.service.network)
        ]
        self.service_spec = service_spec
        self.build_dir = Path(build_dir)
        self.tendermint_job_config: Optional[str] = None

    @abc.abstractmethod
    def generate(
        self,
        image_versions: Dict[str, str],
        dev_mode: bool = False,
    ) -> "BaseDeploymentGenerator":
        """Generate the deployment configuration."""

    @abc.abstractmethod
    def generate_config_tendermint(
        self, image_version: str = TENDERMINT_IMAGE_VERSION
    ) -> "BaseDeploymentGenerator":
        """Generate the deployment configuration."""

    @abc.abstractmethod
    def populate_private_keys(
        self,
    ) -> "BaseDeploymentGenerator":
        """Populate the private keys to the deployment."""

    def get_deployment_network_configuration(
        self, agent_vars: List[Dict[str, Any]]
    ) -> List:
        """Retrieve the appropriate network configuration based on deployment & network."""
        for agent in agent_vars:
            agent.update(self.network_config)
        return agent_vars

    def write_config(self) -> "BaseDeploymentGenerator":
        """Write output to build dir"""

        with open(self.build_dir / self.output_name, "w", encoding="utf8") as f:
            f.write(self.output)
        return self
