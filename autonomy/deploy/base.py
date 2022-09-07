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
from typing import Any, Dict, List, Optional

from aea.configurations.base import (
    ConnectionConfig,
    ContractConfig,
    ProtocolConfig,
    SkillConfig,
)

from autonomy.configurations.base import Service
from autonomy.configurations.loader import load_service_config
from autonomy.deploy.constants import (
    DEFAULT_ENCODING,
    INFO,
    KEY_SCHEMA_ADDRESS,
    KEY_SCHEMA_PRIVATE_KEY,
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

    def __init__(  # pylint: disable=too-many-arguments
        self,
        service_path: Path,
        keys: Path,
        number_of_agents: Optional[int] = None,
        private_keys_password: Optional[str] = None,
        agent_instances: Optional[List[str]] = None,
        log_level: str = INFO,
        substitute_env_vars: bool = False,
    ) -> None:
        """Initialize the Base Deployment."""
        self.keys: List = []
        self.private_keys_password = private_keys_password
        self.service = load_service_config(
            service_path, substitute_env_vars=substitute_env_vars
        )
        self.log_level = log_level

        # we allow configurable number of agents independent of the
        # number of agent instances for local development purposes

        if number_of_agents is not None:
            self.service.number_of_agents = number_of_agents

        self.agent_instances = agent_instances
        self.read_keys(keys)

    def read_keys(self, file_path: Path) -> None:
        """Read in keys from a file on disk."""

        keys = json.loads(file_path.read_text(encoding=DEFAULT_ENCODING))
        for key in keys:
            if {KEY_SCHEMA_ADDRESS, KEY_SCHEMA_PRIVATE_KEY} != set(key.keys()):
                raise ValueError("Key file incorrectly formatted.")

        if self.agent_instances is not None:
            keys = [kp for kp in keys if kp["address"] in self.agent_instances]
            if not keys:
                raise ValueError(
                    "Cannot find the provided keys in the list of the agent instances."
                )
            self.service.number_of_agents = len(keys)

        self.keys = keys
        if self.service.number_of_agents > len(self.keys):
            raise ValueError("Number of agents cannot be greater than available keys.")

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
        if self.agent_instances is None:
            return [
                self.generate_agent(i) for i in range(self.service.number_of_agents)
            ]

        idx_mappings = {address: i for i, address in enumerate(self.agent_instances)}
        agent_override_idx = [
            (i, idx_mappings[kp["address"]]) for i, kp in enumerate(self.keys)
        ]
        return [self.generate_agent(i, idx) for i, idx in agent_override_idx]

    def generate_common_vars(self, agent_n: int) -> Dict:
        """Retrieve vars common for valory apps."""
        agent_vars = {
            "ID": agent_n,
            "AEA_AGENT": self.service.agent,
            "ABCI_HOST": ABCI_HOST.format(agent_n),
            "MAX_PARTICIPANTS": self.service.number_of_agents,
            "TENDERMINT_URL": TENDERMINT_NODE.format(agent_n),
            "TENDERMINT_COM_URL": TENDERMINT_COM.format(agent_n),
            "LOG_LEVEL": self.log_level,
        }

        if self.private_keys_password is not None:
            agent_vars["AEA_PASSWORD"] = self.private_keys_password
        return agent_vars

    def generate_agent(
        self, agent_n: int, override_idx: Optional[int] = None
    ) -> Dict[Any, Any]:
        """Generate next agent."""
        agent_vars = self.generate_common_vars(agent_n)
        if len(self.service.overrides) == 0:
            return agent_vars

        if override_idx is None:
            override_idx = agent_n

        overrides = self.process_model_args_overrides(override_idx)
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
    dev_mode: bool
    packages_dir: Path
    open_aea_dir: Path
    open_autonomy_dir: Path

    def __init__(  # pylint: disable=too-many-arguments
        self,
        service_spec: ServiceSpecification,
        build_dir: Path,
        dev_mode: bool = False,
        packages_dir: Optional[Path] = None,
        open_aea_dir: Optional[Path] = None,
        open_autonomy_dir: Optional[Path] = None,
    ):
        """Initialise with only kwargs."""
        self.service_spec = service_spec
        self.build_dir = Path(build_dir)
        self.tendermint_job_config: Optional[str] = None
        self.dev_mode = dev_mode
        self.packages_dir = packages_dir or Path.cwd().absolute() / "packages"
        self.open_aea_dir = open_aea_dir or Path.home().absolute() / "open-aea"
        self.open_autonomy_dir = (
            open_autonomy_dir or Path.home().absolute() / "open-autonomy"
        )

    @abc.abstractmethod
    def generate(
        self, image_version: Optional[str] = None
    ) -> "BaseDeploymentGenerator":
        """Generate the deployment configuration."""

    @abc.abstractmethod
    def generate_config_tendermint(self) -> "BaseDeploymentGenerator":
        """Generate the deployment configuration."""

    @abc.abstractmethod
    def populate_private_keys(
        self,
    ) -> "BaseDeploymentGenerator":
        """Populate the private keys to the deployment."""

    def write_config(self) -> "BaseDeploymentGenerator":
        """Write output to build dir"""

        with open(self.build_dir / self.output_name, "w", encoding="utf8") as f:
            f.write(self.output)
        return self
