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

"""Base deployments module."""
import abc
import json
import logging
import os
from copy import copy, deepcopy
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union, cast
from warnings import warn

from aea.cli.generate_key import _generate_multiple_keys
from aea.configurations.base import (
    ConnectionConfig,
    ContractConfig,
    ProtocolConfig,
    SkillConfig,
)
from aea.configurations.constants import ADDRESS, LEDGER, PRIVATE_KEY, SKILL
from aea.configurations.data_types import PackageType, PublicId
from aea.helpers.env_vars import apply_env_variables
from typing_extensions import TypedDict

from autonomy.analyse.service import ABCI
from autonomy.configurations.base import Service
from autonomy.configurations.loader import load_service_config
from autonomy.constants import DEFAULT_DOCKER_IMAGE_AUTHOR
from autonomy.deploy.constants import DEFAULT_ENCODING, INFO


ENV_VAR_ID = "ID"
ENV_VAR_AEA_AGENT = "AEA_AGENT"
ENV_VAR_LOG_LEVEL = "LOG_LEVEL"
ENV_VAR_AEA_PASSWORD = "AEA_PASSWORD"  # nosec
ENV_VAR_DEPENDENCIES = "DEPENDENCIES"  # nosec
ENV_VAR_OPEN_AUTONOMY_TM_WRITE_TO_LOG = "OPEN_AUTONOMY_TM_WRITE_TO_LOG"

PARAM_ARGS_PATH = ("models", "params", "args")
SETUP_PARAM_PATH = (*PARAM_ARGS_PATH, "setup")
SAFE_CONTRACT_ADDRESS = "safe_contract_address"
ALL_PARTICIPANTS = "all_participants"
CONSENSUS_THRESHOLD = "consensus_threshold"


DEFAULT_ABCI_PORT = 26658


KUBERNETES_DEPLOYMENT = "kubernetes"
DOCKER_COMPOSE_DEPLOYMENT = "docker-compose"

LOOPBACK = "127.0.0.1"
LOCALHOST = "localhost"
TENDERMINT_P2P_PORT = 26656

TENDERMINT_NODE = "http://{host}:26657"
TENDERMINT_COM = "http://{host}:8080"

TENDERMINT_NODE_LOCAL = f"http://{LOCALHOST}:26657"
TENDERMINT_COM_LOCAL = f"http://{LOCALHOST}:8080"

TENDERMINT_URL_PARAM = "tendermint_url"
TENDERMINT_COM_URL_PARAM = "tendermint_com_url"

TENDERMINT_P2P_URL = "{host}:{port}"
TENDERMINT_P2P_URL_PARAM = "tendermint_p2p_url"
TENDERMINT_P2P_URL_ENV_VAR = "TM_P2P_NODE_URL_{}"

COMPONENT_CONFIGS: Dict = {
    component.package_type.value: component  # type: ignore
    for component in [
        ContractConfig,
        SkillConfig,
        ProtocolConfig,
        ConnectionConfig,
    ]
}

DEFAULT_AGENT_MEMORY_LIMIT = int(os.environ.get("AUTONOMY_AGENT_MEMORY_LIMIT", 1024))
DEFAULT_AGENT_CPU_LIMIT = float(os.environ.get("AUTONOMY_AGENT_CPU_LIMIT", 1.0))
DEFAULT_AGENT_MEMORY_REQUEST = int(os.environ.get("AUTONOMY_AGENT_MEMORY_REQUEST", 256))
DEFAULT_AGENT_CPU_REQUEST = float(os.environ.get("AUTONOMY_AGENT_CPU_REQUEST", 1.0))


def tm_write_to_log() -> bool:
    """Check the environment variable to see if the user wants to write to log file or not."""
    return os.getenv(ENV_VAR_OPEN_AUTONOMY_TM_WRITE_TO_LOG, "true").lower() == "true"


class NotValidKeysFile(Exception):
    """Raise when provided keys file is not valid."""


class ResourceValues(TypedDict):
    """Resource type."""

    cpu: Optional[float]
    memory: Optional[int]


class Resource(TypedDict):
    """Resource values."""

    requested: ResourceValues
    limit: ResourceValues


class Resources(TypedDict):
    """Deployment resources."""

    agent: Resource


DEFAULT_RESOURCE_VALUES = Resources(
    {
        "agent": {
            "limit": {
                "cpu": DEFAULT_AGENT_CPU_LIMIT,
                "memory": DEFAULT_AGENT_MEMORY_LIMIT,
            },
            "requested": {
                "cpu": DEFAULT_AGENT_CPU_REQUEST,
                "memory": DEFAULT_AGENT_MEMORY_REQUEST,
            },
        }
    }
)


class ServiceBuilder:  # pylint: disable=too-many-instance-attributes
    """Class to assist with generating deployments."""

    deplopyment_type: str = DOCKER_COMPOSE_DEPLOYMENT
    log_level: str = INFO

    def __init__(  # pylint: disable=too-many-arguments
        self,
        service: Service,
        keys: Optional[List[Union[List[Dict[str, str]], Dict[str, str]]]] = None,
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

        self._service_name_clean = self.service.name.replace("_", "")
        self._keys = keys or []
        self._agent_instances = agent_instances
        self._all_participants = self.try_get_all_participants()
        self.multiledger = False

    def get_abci_container_name(self, index: int) -> str:
        """Format ABCI container name."""
        return f"{self._service_name_clean}_abci_{index}"

    def get_tm_container_name(self, index: int) -> str:
        """Format tendermint container name."""
        return f"{self._service_name_clean}_tm_{index}"

    def try_get_all_participants(self) -> Optional[List[str]]:
        """Try get all participants from the ABCI overrides"""
        for override in deepcopy(self.service.overrides):
            try:
                (
                    override,
                    component_id,
                    has_multiple_overrides,
                ) = self.service.process_metadata(
                    configuration=override,
                )
                if (
                    component_id.component_type.value == SKILL
                    and has_multiple_overrides
                ):
                    override, *_ = override.values()

                override = apply_env_variables(
                    data=override,
                    env_variables=os.environ.copy(),
                )
                setup_param = self._get_config_from_json_path(
                    override_dict=override, json_path=SETUP_PARAM_PATH
                )
                all_participants = setup_param.get(ALL_PARTICIPANTS)
                if all_participants is not None:
                    return all_participants
            except KeyError:
                continue
        return None

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
                addresses=set(
                    self._get_addresses(
                        keys=self.keys,
                        multiledger=self.multiledger,
                    )
                ),
                agent_instances=instances,
            )

        self._agent_instances = instances

    @property
    def keys(
        self,
    ) -> List[Union[List[Dict[str, str]], Dict[str, str]]]:
        """Keys."""
        return self._keys

    @classmethod
    def from_dir(  # pylint: disable=too-many-arguments
        cls,
        path: Path,
        keys_file: Optional[Path] = None,
        number_of_agents: Optional[int] = None,
        agent_instances: Optional[List[str]] = None,
        apply_environment_variables: bool = False,
        dev_mode: bool = False,
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
        )

        if keys_file is not None:
            if dev_mode and not keys_file.exists():
                # TODO: Add multiledger support
                _generate_multiple_keys(
                    n=service.number_of_agents,
                    type_="ethereum",
                    file=keys_file,
                )
            service_builder.read_keys(keys_file=keys_file)

        if agent_instances is not None:
            service_builder.agent_instances = agent_instances

        return service_builder

    @staticmethod
    def _get_addresses(
        keys: List[Union[List[Dict[str, str]], Dict[str, str]]],
        multiledger: bool = False,
    ) -> List[str]:
        """Get ethereum addresses"""
        if multiledger:
            addresses = []
            for i, _keys in enumerate(cast(List[List[Dict[str, str]]], keys)):
                for _keypair in _keys:
                    if _keypair["ledger"] == "ethereum":
                        addresses.append(_keypair["address"])
                if len(addresses) != i + 1:
                    raise ValueError(f"Ethereum key not found in keyset: {_keys}")
            return addresses
        return [kp["address"] for kp in cast(List[Dict[str, str]], keys)]

    @staticmethod
    def verify_agent_instances(addresses: Set[str], agent_instances: List[str]) -> None:
        """Cross verify agent instances with the keys."""
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

    @staticmethod
    def _validate_keypair(keypair: Dict, ledger_required: bool = False) -> None:
        """Validate keys set."""
        if ledger_required:
            if {ADDRESS, PRIVATE_KEY, LEDGER} != set(keypair.keys()):
                raise NotValidKeysFile("Key file incorrectly formatted")
            return

        if {ADDRESS, PRIVATE_KEY} != set(keypair.keys()) and {
            ADDRESS,
            PRIVATE_KEY,
            LEDGER,
        } != set(keypair.keys()):
            raise NotValidKeysFile("Key file incorrectly formatted.")

    def read_keys(self, keys_file: Path) -> None:
        """Read in keys from a file on disk."""

        try:
            keys = json.loads(keys_file.read_text(encoding=DEFAULT_ENCODING))
        except json.decoder.JSONDecodeError as e:  # pragma: nocover
            raise NotValidKeysFile(
                "Error decoding keys file, please check the content of the file"
            ) from e

        if isinstance(keys[0], list):
            self.multiledger = True
            for _keys in keys:
                for _keypair in _keys:
                    self._validate_keypair(keypair=_keypair, ledger_required=True)
        else:
            for _keypair in keys:
                self._validate_keypair(keypair=_keypair)

        if self.agent_instances is not None:
            self.verify_agent_instances(
                addresses=set(
                    self._get_addresses(
                        keys=keys,
                        multiledger=self.multiledger,
                    )
                ),
                agent_instances=self.agent_instances,
            )
            self.service.number_of_agents = len(keys)

        if self._all_participants is not None and len(self._all_participants) > 0:
            unwanted_keys = set(
                self._get_addresses(
                    keys=keys,
                    multiledger=self.multiledger,
                )
            ) - set(self._all_participants)
            if len(unwanted_keys) > 0:
                raise NotValidKeysFile(
                    f"Key file contains keys which are not a part of the `all_participants` parameter; keys={unwanted_keys}"
                )
            self.service.number_of_agents = len(keys)

        if self.service.number_of_agents > len(keys):
            raise NotValidKeysFile(
                "Number of agents cannot be greater than available keys."
            )

        self._keys = keys

    @staticmethod
    def _get_config_from_json_path(
        override_dict: Dict,
        json_path: Tuple[str, ...],
    ) -> Dict:
        """Returns `setup` param dict"""

        _key_0, *_keys = json_path
        config = override_dict[_key_0]
        for key in _keys:
            config = config[key]
        return config

    @classmethod
    def _try_update_setup_data(
        cls,
        data: List[Tuple[str, Any]],
        override: Dict,
        skill_id: PublicId,
        has_multiple_overrides: bool = False,
    ) -> None:
        """Try update the setup parameters"""

        def _try_update_setup_params(
            setup_param: Optional[Dict],
            setup_data: List[Tuple[str, Any]],
        ) -> None:
            """Update"""
            if setup_param is None:  # pragma: nocover
                return

            for param, value in setup_data:
                setup_param[param] = value

        try:
            if not has_multiple_overrides:
                setup_param = cls._get_config_from_json_path(
                    override_dict=override, json_path=SETUP_PARAM_PATH
                )
                _try_update_setup_params(setup_param=setup_param, setup_data=data)
                return

            for agent_idx in override:
                setup_param = cls._get_config_from_json_path(
                    override_dict=override[agent_idx], json_path=SETUP_PARAM_PATH
                )
                _try_update_setup_params(setup_param=setup_param, setup_data=data)
        except KeyError:
            logging.warning(
                f"Could not update the setup parameter for {skill_id}; "
                f"Configuration does not contain the json path to the setup parameter"
            )

    def _try_update_tendermint_params(
        self,
        override: Dict,
        skill_id: PublicId,
        has_multiple_overrides: bool = False,
    ) -> None:
        """Try update the tendermint parameters"""

        is_kubernetes_deployment = self.deplopyment_type == KUBERNETES_DEPLOYMENT

        def _update_tendermint_params(
            param_args: Dict,
            idx: int,
            is_kubernetes_deployment: bool = False,
        ) -> None:
            """Update tendermint params"""
            if is_kubernetes_deployment:
                param_args[TENDERMINT_URL_PARAM] = TENDERMINT_NODE_LOCAL
                param_args[TENDERMINT_COM_URL_PARAM] = TENDERMINT_COM_LOCAL
            else:
                param_args[TENDERMINT_URL_PARAM] = TENDERMINT_NODE.format(
                    host=self.get_tm_container_name(index=idx)
                )
                param_args[TENDERMINT_COM_URL_PARAM] = TENDERMINT_COM.format(
                    host=self.get_tm_container_name(index=idx)
                )

            if TENDERMINT_P2P_URL_PARAM not in param_args:
                tm_p2p_url = os.environ.get(
                    TENDERMINT_P2P_URL_ENV_VAR.format(idx),
                    TENDERMINT_P2P_URL.format(
                        host=self.get_tm_container_name(index=idx),
                        port=TENDERMINT_P2P_PORT,
                    ),
                )
                param_args[TENDERMINT_P2P_URL_PARAM] = tm_p2p_url

        try:
            if self.service.number_of_agents == 1:
                if has_multiple_overrides:
                    for agent_idx in override:
                        param_args = self._get_config_from_json_path(
                            override_dict=override[agent_idx], json_path=PARAM_ARGS_PATH
                        )
                        _update_tendermint_params(
                            param_args=param_args,
                            idx=0,
                            is_kubernetes_deployment=is_kubernetes_deployment,
                        )
                else:
                    param_args = self._get_config_from_json_path(
                        override_dict=override, json_path=PARAM_ARGS_PATH
                    )
                    _update_tendermint_params(
                        param_args=param_args,
                        idx=0,
                        is_kubernetes_deployment=is_kubernetes_deployment,
                    )
                return

            if not has_multiple_overrides:
                _base_overrride = deepcopy(override)
                override.clear()
                for i in range(self.get_maximum_participants()):
                    override[i] = deepcopy(_base_overrride)

            for agent_idx in override:
                param_args = self._get_config_from_json_path(
                    override_dict=override[agent_idx], json_path=PARAM_ARGS_PATH
                )
                _update_tendermint_params(
                    param_args=param_args,
                    idx=agent_idx,
                    is_kubernetes_deployment=is_kubernetes_deployment,
                )
        except KeyError:  # pragma: nocover
            logging.warning(
                f"Could not update the tendermint parameter for {skill_id}; "
                f"Configuration does not contain the json path to the setup parameter"
            )

    def try_update_runtime_params(
        self,
        multisig_address: Optional[str] = None,
        agent_instances: Optional[List[str]] = None,
        consensus_threshold: Optional[int] = None,
    ) -> None:
        """Try and update setup parameters."""

        param_overrides: List[Tuple[str, Any]] = []
        if multisig_address is not None:
            param_overrides.append(
                (SAFE_CONTRACT_ADDRESS, multisig_address),
            )

        if agent_instances is not None:
            param_overrides.append(
                (ALL_PARTICIPANTS, agent_instances),
            )

        if consensus_threshold is not None:
            param_overrides.append(
                (CONSENSUS_THRESHOLD, consensus_threshold),
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
                self._try_update_tendermint_params(
                    override=override,
                    skill_id=component_id.public_id,
                    has_multiple_overrides=has_multiple_overrides,
                )

            override["type"] = component_id.package_type.value
            override["public_id"] = str(component_id.public_id)

        self.service.overrides = overrides

    def get_maximum_participants(self) -> int:
        """Returns the maximum number of participants"""

        if self._all_participants is not None and len(self._all_participants) > 0:
            return len(self._all_participants)

        if self.agent_instances is not None:
            return len(self.agent_instances)

        return max(len(self.keys), self.service.number_of_agents)

    def _update_abci_connection_config(
        self,
        overrides: Dict,
        has_multiple_overrides: bool = False,
    ) -> Dict:
        """Update ABCI connection config"""

        processed_overrides = deepcopy(overrides)
        if self.service.number_of_agents == 1:
            processed_overrides["config"]["host"] = (
                LOOPBACK
                if self.deplopyment_type == KUBERNETES_DEPLOYMENT
                else self.get_abci_container_name(index=0)
            )
            processed_overrides["config"]["port"] = processed_overrides["config"].get(
                "port", DEFAULT_ABCI_PORT
            )
            return processed_overrides

        if not has_multiple_overrides:
            processed_overrides = {}
            for i in range(self.get_maximum_participants()):
                processed_overrides[i] = deepcopy(overrides)

        for idx, override in processed_overrides.items():
            override["config"]["host"] = (
                LOOPBACK
                if self.deplopyment_type == KUBERNETES_DEPLOYMENT
                else self.get_abci_container_name(index=idx)
            )
            override["config"]["port"] = override["config"].get(
                "port", DEFAULT_ABCI_PORT
            )
            processed_overrides[idx] = override

        return processed_overrides

    def try_update_abci_connection_params(
        self,
    ) -> None:
        """Try and update ledger connection parameters."""

        for override in deepcopy(self.service.overrides):
            (
                override,
                component_id,
                has_multiple_overrides,
            ) = self.service.process_metadata(
                configuration=override,
            )

            if (
                component_id.package_type == PackageType.CONNECTION
                and component_id.name == ABCI
            ):
                service_has_connection_overrides = True
                abci_connection_overrides = override
                break
        else:
            service_has_connection_overrides = False
            (
                abci_connection_overrides,
                component_id,
                has_multiple_overrides,
            ) = self.service.process_metadata(
                configuration={
                    "public_id": "valory/abci:0.1.0",
                    "type": PackageType.CONNECTION.value,
                    "config": {
                        "host": LOCALHOST,
                        "port": DEFAULT_ABCI_PORT,
                    },
                }
            )
        processed_overrides = self._update_abci_connection_config(
            overrides=abci_connection_overrides,
            has_multiple_overrides=has_multiple_overrides,
        )
        processed_overrides["public_id"] = str(component_id.public_id)
        processed_overrides["type"] = PackageType.CONNECTION.value
        service_overrides = deepcopy(self.service.overrides)
        if service_has_connection_overrides:
            service_overrides = [
                override
                for override in service_overrides
                if override["public_id"] != str(component_id.public_id)
                or override["type"] != PackageType.CONNECTION.value
            ]

        service_overrides.append(processed_overrides)
        self.service.overrides = service_overrides

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
        addresses = self._get_addresses(
            keys=self.keys,
            multiledger=self.multiledger,
        )
        if self._all_participants is not None and len(self._all_participants) > 0:
            idx_mappings = {
                address: i for i, address in enumerate(self._all_participants)
            }
            agent_override_idx = [
                (i, idx_mappings[kp]) for i, kp in enumerate(addresses)
            ]
            return [self.generate_agent(i, idx) for i, idx in agent_override_idx]
        if self.agent_instances is None:
            return [
                self.generate_agent(i) for i in range(self.service.number_of_agents)
            ]
        idx_mappings = {address: i for i, address in enumerate(self.agent_instances)}
        agent_override_idx = [(i, idx_mappings[kp]) for i, kp in enumerate(addresses)]
        return [self.generate_agent(i, idx) for i, idx in agent_override_idx]

    def generate_common_vars(self, agent_n: int) -> Dict:
        """Retrieve vars common for agent."""
        agent_vars = {
            ENV_VAR_ID: agent_n,
            ENV_VAR_AEA_AGENT: self.service.agent,
            ENV_VAR_LOG_LEVEL: self.log_level,
        }
        if self.deplopyment_type == DOCKER_COMPOSE_DEPLOYMENT:
            agent_vars[ENV_VAR_AEA_PASSWORD] = "$OPEN_AUTONOMY_PRIVATE_KEY_PASSWORD"
        else:
            agent_vars[ENV_VAR_AEA_PASSWORD] = os.environ.get(
                "OPEN_AUTONOMY_PRIVATE_KEY_PASSWORD", ""
            )
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


class BaseDeploymentGenerator(abc.ABC):  # pylint: disable=too-many-instance-attributes
    """Base Deployment Class."""

    service_builder: ServiceBuilder
    output_name: str
    deployment_type: str
    build_dir: Path
    output: str
    tendermint_job_config: Optional[str]
    dev_mode: bool
    use_tm_testnet_setup: bool

    packages_dir: Optional[Path]
    open_aea_dir: Optional[Path]
    resources: Resources

    def __init__(  # pylint: disable=too-many-arguments
        self,
        service_builder: ServiceBuilder,
        build_dir: Path,
        use_tm_testnet_setup: bool = False,
        dev_mode: bool = False,
        packages_dir: Optional[Path] = None,
        open_aea_dir: Optional[Path] = None,
        image_author: Optional[str] = None,
        resources: Optional[Resources] = None,
    ):
        """Initialise with only kwargs."""

        self.service_builder = service_builder
        self.build_dir = build_dir
        self.use_tm_testnet_setup = use_tm_testnet_setup
        self.dev_mode = dev_mode
        self.packages_dir = packages_dir
        self.open_aea_dir = open_aea_dir

        self.tendermint_job_config: Optional[str] = None
        self.image_author = image_author or DEFAULT_DOCKER_IMAGE_AUTHOR
        self.resources = resources if resources is not None else DEFAULT_RESOURCE_VALUES

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
