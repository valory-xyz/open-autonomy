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
import logging
import os
from copy import copy
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from warnings import warn

from aea.configurations.base import (
    ConnectionConfig,
    ContractConfig,
    ProtocolConfig,
    SkillConfig,
)
from aea.configurations.constants import SKILL
from aea.configurations.data_types import PublicId

from autonomy.configurations.base import Service
from autonomy.configurations.loader import load_service_config
from autonomy.deploy.constants import (
    DEFAULT_ENCODING,
    INFO,
    KEY_SCHEMA_ADDRESS,
    KEY_SCHEMA_PRIVATE_KEY,
)


ENV_VAR_ID = "ID"
ENV_VAR_AEA_AGENT = "AEA_AGENT"
ENV_VAR_ABCI_HOST = "ABCI_HOST"
ENV_VAR_MAX_PARTICIPANTS = "MAX_PARTICIPANTS"
ENV_VAR_TENDERMINT_URL = "TENDERMINT_URL"
ENV_VAR_TENDERMINT_COM_URL = "TENDERMINT_COM_URL"
ENV_VAR_LOG_LEVEL = "LOG_LEVEL"
ENV_VAR_AEA_PASSWORD = "AEA_PASSWORD"  # nosec

SETUP_PARAM_PATH = ("models", "params", "args", "setup")
SAFE_CONTRACT_ADDRESS = "safe_contract_address"
ALL_PARTICIPANTS = "all_participants"

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


class NotValidKeysFile(Exception):
    """Raise when provided keys file is not valid."""


class ServiceBuilder:
    """Class to assist with generating deployments."""

    log_level: str = INFO

    def __init__(  # pylint: disable=too-many-arguments
        self,
        service: Service,
        keys: Optional[List[Dict[str, str]]] = None,
        private_keys_password: Optional[str] = None,
        agent_instances: Optional[List[str]] = None,
        apply_environment_variables: bool = False,
    ) -> None:
        """Initialize the Base Deployment."""
        if apply_environment_variables:
            warn(  # pragma: no cover
                "`apply_environment_variables` argument is deprecated and will be removed in v1.0.0, "
                "usage of environment varibales is default now.",
                DeprecationWarning,
                stacklevel=2,
            )

        self.service = service

        self._keys = keys or []
        self._agent_instances = agent_instances
        self._private_keys_password = private_keys_password

    @property
    def private_keys_password(
        self,
    ) -> Optional[str]:
        """Service password for agent keys."""

        password = self._private_keys_password
        if password is None:
            password = os.environ.get("AUTONOLAS_SERVICE_PASSWORD")

        return password

    @property
    def agent_instances(
        self,
    ) -> Optional[List[str]]:
        """Agent instances."""

        return self._agent_instances

    @agent_instances.setter
    def agent_instances(self, instances: List[str]) -> None:
        """Agent instances setter."""

        if self.keys:
            self.verify_agent_instances(
                keys=self.keys,
                agent_instances=instances,
            )

        self._agent_instances = instances

    @property
    def keys(
        self,
    ) -> List[Dict[str, str]]:
        """Keys."""
        return self._keys

    @classmethod
    def from_dir(  # pylint: disable=too-many-arguments
        cls,
        path: Path,
        keys_file: Optional[Path] = None,
        number_of_agents: Optional[int] = None,
        private_keys_password: Optional[str] = None,
        agent_instances: Optional[List[str]] = None,
        apply_environment_variables: bool = False,
    ) -> "ServiceBuilder":
        """Service builder from path."""
        service = load_service_config(
            service_path=path,
        )
        if number_of_agents is not None:
            service.number_of_agents = number_of_agents

        service_builder = cls(
            service=service,
            apply_environment_variables=apply_environment_variables,
            private_keys_password=private_keys_password,
        )

        if keys_file is not None:
            service_builder.read_keys(keys_file=keys_file)

        if agent_instances is not None:
            service_builder.agent_instances = agent_instances

        return service_builder

    @staticmethod
    def verify_agent_instances(
        keys: List[Dict[str, str]],
        agent_instances: List[str],
    ) -> None:
        """Cross verify agent instances with the keys."""
        addresses = {kp["address"] for kp in keys}
        instances = set(agent_instances)

        key_not_in_instances = addresses.difference(instances)
        if key_not_in_instances:
            raise NotValidKeysFile(
                f"Key file contains keys which are not registered as instances; invalid keys={key_not_in_instances}"
            )

        instances_not_in_keys = instances.difference(addresses)
        if instances_not_in_keys:
            logging.warning(
                f"Key file does not contain key pair for following instances {instances_not_in_keys}"
            )

        keys_found_with_instances = instances.intersection(addresses)
        logging.info(
            f"Found following keys with registered instances {keys_found_with_instances}"
        )

    def read_keys(self, keys_file: Path) -> None:
        """Read in keys from a file on disk."""

        try:
            keys = json.loads(keys_file.read_text(encoding=DEFAULT_ENCODING))
        except json.decoder.JSONDecodeError as e:
            raise NotValidKeysFile(
                "Error decoding keys file, please check the content of the file"
            ) from e

        for key in keys:
            if {KEY_SCHEMA_ADDRESS, KEY_SCHEMA_PRIVATE_KEY} != set(key.keys()):
                raise NotValidKeysFile("Key file incorrectly formatted.")

        if self.agent_instances is not None:
            self.verify_agent_instances(
                keys=keys,
                agent_instances=self.agent_instances,
            )
            self.service.number_of_agents = len(keys)

        if self.service.number_of_agents > len(keys):
            raise NotValidKeysFile(
                "Number of agents cannot be greater than available keys."
            )

        self._keys = keys

    @staticmethod
    def _try_update_setup_data(
        data: List[Tuple[str, Any]],
        override: Dict,
        skill_id: PublicId,
        has_multiple_overrides: bool = False,
    ) -> None:
        """Try update the `safe_contract_address` parameter"""

        def _get_params_dict(override_dict: Dict) -> Optional[Dict]:
            """Returns `setup` param dict"""
            try:
                _key_0, *_keys = SETUP_PARAM_PATH
                setup_param = override_dict[_key_0]
                for key in _keys:
                    setup_param = setup_param[key]
                return setup_param
            except KeyError:
                logging.warning(
                    f"Could not update the setup parameter for {skill_id}; "
                    f"Configuration does not contain the json path to the setup parameter"
                )
                return None

        def _try_update_setup_params(
            setup_param: Optional[Dict],
            setup_data: List[Tuple[str, Any]],
        ) -> None:
            """Update"""
            if setup_param is None:
                return

            for param, value in setup_data:
                setup_param[param] = value

        if not has_multiple_overrides:
            setup_param = _get_params_dict(override_dict=override)
            _try_update_setup_params(setup_param=setup_param, setup_data=data)
            return

        for agent_idx in override:
            setup_param = _get_params_dict(override_dict=override[agent_idx])
            _try_update_setup_params(setup_param=setup_param, setup_data=data)

    def try_update_runtime_params(
        self,
        multisig_address: Optional[str] = None,
        agent_instances: Optional[List[str]] = None,
    ) -> None:
        """Try and update setup parameters."""

        param_overrides: List[Tuple[str, Any]] = []
        if multisig_address is not None:
            param_overrides.append(
                (SAFE_CONTRACT_ADDRESS, [multisig_address]),
            )

        if agent_instances is not None:
            param_overrides.append(
                (ALL_PARTICIPANTS, [agent_instances]),
            )

        overrides = copy(self.service.overrides)
        for override in overrides:
            (
                override,
                component_id,
                has_multiple_overrides,
            ) = self.service.process_metadata(
                configuration=override,
            )

            if component_id.component_type.value == SKILL:
                self._try_update_setup_data(
                    data=param_overrides,
                    override=override,
                    skill_id=component_id.public_id,
                    has_multiple_overrides=has_multiple_overrides,
                )

            override["type"] = component_id.package_type.value
            override["public_id"] = str(component_id.public_id)

        self.service.overrides = overrides

    def process_component_overrides(self, agent_n: int) -> Dict:
        """Generates env vars based on model overrides."""
        final_overrides = {}
        for component_configuration_json in self.service.overrides:
            env_var_dict = self.service.process_component_overrides(
                agent_n, component_configuration_json
            )
            final_overrides.update(env_var_dict)
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
        """Retrieve vars common for agent."""
        agent_vars = {
            ENV_VAR_ID: agent_n,
            ENV_VAR_AEA_AGENT: self.service.agent,
            ENV_VAR_ABCI_HOST: ABCI_HOST.format(agent_n),
            ENV_VAR_MAX_PARTICIPANTS: self.service.number_of_agents,
            ENV_VAR_TENDERMINT_URL: TENDERMINT_NODE.format(agent_n),
            ENV_VAR_TENDERMINT_COM_URL: TENDERMINT_COM.format(agent_n),
            ENV_VAR_LOG_LEVEL: self.log_level,
        }

        if self.private_keys_password is not None:
            agent_vars[ENV_VAR_AEA_PASSWORD] = self.private_keys_password

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

        agent_vars.update(
            self.process_component_overrides(agent_n=override_idx),
        )
        return agent_vars


class BaseDeploymentGenerator(abc.ABC):
    """Base Deployment Class."""

    service_builder: ServiceBuilder
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
        service_builder: ServiceBuilder,
        build_dir: Path,
        dev_mode: bool = False,
        packages_dir: Optional[Path] = None,
        open_aea_dir: Optional[Path] = None,
        open_autonomy_dir: Optional[Path] = None,
    ):
        """Initialise with only kwargs."""

        self.service_builder = service_builder
        self.build_dir = build_dir
        self.dev_mode = dev_mode
        self.packages_dir = packages_dir or Path.cwd().absolute() / "packages"
        self.open_aea_dir = open_aea_dir or Path.home().absolute() / "open-aea"
        self.open_autonomy_dir = (
            open_autonomy_dir or Path.home().absolute() / "open-autonomy"
        )

        self.tendermint_job_config: Optional[str] = None

    @abc.abstractmethod
    def generate(
        self,
        image_version: Optional[str] = None,
        use_hardhat: bool = False,
        use_acn: bool = False,
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
