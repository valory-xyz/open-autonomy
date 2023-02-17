# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2023 Valory AG
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


"""Tools for analysing the service for deployment readiness"""

import copy
import logging
import re
from typing import Dict, List, Optional, OrderedDict, Set, cast

from aea.configurations.base import AgentConfig, SkillConfig
from aea.configurations.data_types import (
    ComponentId,
    ComponentType,
    PackageId,
    PublicId,
)
from aea.crypto.base import LedgerApi
from aea.helpers.cid import to_v0
from aea.helpers.logging import setup_logger
from jsonschema.exceptions import ValidationError
from jsonschema.validators import Draft4Validator
from requests.exceptions import ConnectionError as RequestConnectionError

from autonomy.chain.base import ServiceState
from autonomy.chain.config import ChainType
from autonomy.chain.service import get_service_info
from autonomy.configurations.base import Service


ABCI_CONNECTION_SCHEMA = {
    "type": "object",
    "properties": {
        "config": {
            "type": "object",
            "required": [
                "host",
                "port",
                "use_tendermint",
            ],
        },
        "required": ["config"],
    },
}

LEDGER_CONNECTION_SCHEMA = {
    "type": "object",
    "properties": {
        "config": {
            "type": "object",
            "properties": {
                "ledger_apis": {
                    "type": "object",
                    "properties": {
                        "ethereum": {
                            "type": "object",
                            "required": [
                                "address",
                                "chain_id",
                                "poa_chain",
                                "default_gas_price_strategy",
                            ],
                        },
                    },
                    "additionalProperties": False,
                    "minProperties": 1,
                }
            },
            "required": ["ledger_apis"],
        },
    },
    "required": ["config"],
}

ABCI_SKILL_SCHEMA = {
    "type": "object",
    "properties": {
        "models": {
            "type": "object",
            "properties": {
                "params": {
                    "type": "object",
                    "properties": {
                        "args": {
                            "type": "object",
                            "properties": {
                                "setup": {
                                    "type": "object",
                                    "required": [
                                        "safe_contract_address",
                                        "all_participants",
                                        "consensus_threshold",
                                    ],
                                }
                            },
                            "required": [
                                "setup",
                                "service_registry_address",
                                "share_tm_config_on_startup",
                                "on_chain_service_id",
                            ],
                        },
                    },
                    "required": [
                        "args",
                    ],
                },
            },
            "required": [
                "params",
            ],
        }
    },
    "required": ["models"],
}

ABCI_SKILL_MODEL_PARAMS_SCHEMA = {
    "type": "object",
    "properties": {
        "setup": {
            "type": "object",
            "required": [
                "safe_contract_address",
                "all_participants",
                "consensus_threshold",
            ],
        }
    },
    "required": [
        "genesis_config",
        "service_id",
        "tendermint_url",
        "max_healthcheck",
        "round_timeout_seconds",
        "sleep_time",
        "retry_timeout",
        "retry_attempts",
        "keeper_timeout",
        "observation_interval",
        "drand_public_key",
        "tendermint_com_url",
        "tendermint_max_retries",
        "tendermint_check_sleep_delay",
        "reset_tendermint_after",
        "cleanup_history_depth",
        "cleanup_history_depth_current",
        "request_timeout",
        "request_retry_delay",
        "tx_timeout",
        "max_attempts",
        "service_registry_address",
        "on_chain_service_id",
        "share_tm_config_on_startup",
        "tendermint_p2p_url",
        "setup",
    ],
}

ABCI = "abci"
LEDGER = "ledger"

UNKNOWN_LEDGER_RE = re.compile(r".*\(\'(.*)\' was unexpected\)")
ABCI_CONNECTION_VALIDATOR = Draft4Validator(schema=ABCI_CONNECTION_SCHEMA)
LEDGER_CONNECTION_VALIDATOR = Draft4Validator(schema=LEDGER_CONNECTION_SCHEMA)
ABCI_SKILL_VALIDATOR = Draft4Validator(schema=ABCI_SKILL_SCHEMA)
ABCI_SKILL_MODEL_PARAMS_VALIDATOR = Draft4Validator(
    schema=ABCI_SKILL_MODEL_PARAMS_SCHEMA
)


class ServiceValidationFailed(Exception):
    """Raise when service validation fails."""


class ServiceAnalyser:
    """Tools to analyse a service"""

    def __init__(
        self,
        service_config: Service,
        is_on_chain_check: bool = False,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        """Initialise object."""

        self.service_config = service_config
        self.is_on_chain_check = is_on_chain_check
        self.logger = logger or setup_logger(name="ServiceAnalyser")

    def check_on_chain_state(
        self,
        ledger_api: LedgerApi,
        chain_type: ChainType,
        token_id: int,
    ) -> None:
        """Check on-chain state of a service."""
        if not self.is_on_chain_check:
            return

        self.logger.info("Checking if the service is deployed on-chain")
        try:
            (*_, _service_state, _) = get_service_info(
                ledger_api=ledger_api, chain_type=chain_type, token_id=token_id
            )
        except RequestConnectionError as e:
            raise ServiceValidationFailed(
                "On chain service validation failed, could not connect to the RPC"
            ) from e

        service_state = ServiceState(_service_state)
        if service_state != ServiceState.DEPLOYED:
            self.logger.warning(
                f"Service needs to be in deployed state on-chain; Current state={service_state}"
            )

    def check_agent_dependencies_published(
        self, agent_config: AgentConfig, ipfs_pins: Set[str]
    ) -> None:
        """Check if the agent package is published or not"""

        if not self.is_on_chain_check:
            return

        self.logger.info("Checking if agent dependencies are published")
        for dependency in agent_config.package_dependencies:
            if to_v0(dependency.package_hash) not in ipfs_pins:
                raise ServiceValidationFailed(
                    f"Package required for service {self.service_config.public_id} is not published on the IPFS registry"
                    f"\n\tagent: {self.service_config.agent.without_hash()}"
                    f"\n\tpackage: {dependency}"
                )
            self.logger.info(
                f"\t{dependency.public_id.without_hash()} of type {dependency.package_type} is present"
            )

    def _check_overrides_recursively(
        self,
        check_from: Dict,
        check_with: Dict,
        check_from_name: str,
        check_with_name: str,
        path: Optional[List[str]] = None,
    ) -> None:
        """
        Check overrides recursively

        :param check_from: Configuration to check from
        :param check_with: Configuration to compare against
        :param check_from_name: Name for the `check_from` config
        :param check_with_name: Name for the `check_with` config
        :param path: JSON path to the object
        """

        path = path or []
        path_str = ".".join(path)

        # service has them and agent does not - warning
        check_from_set, check_with_set = set(check_from), set(check_with)

        missing = check_with_set - check_from_set
        if len(missing) > 0:
            message = (
                f"{check_with_name} contains configuration which is missing from {check_from_name}\n"
                f"\tPath: {path_str}\n"
                f"\tMissing parameters: {missing}\n"
            )
            self.logger.warning(message)

        missing = check_from_set - check_with_set
        if len(missing) > 0:
            message = (
                f"{check_from_name} contains configuration which is missing from {check_with_name}\n"
                f"\tPath: {path_str}\n"
                f"\tMissing parameters: {missing}\n"
            )
            self.logger.warning(message)

        for key in check_with_set.intersection(check_from_set):
            if not isinstance(check_from[key], (dict, Dict, OrderedDict)):
                continue

            self._check_overrides_recursively(
                check_from=check_from[key],
                check_with=check_with[key],
                check_from_name=check_from_name,
                check_with_name=check_with_name,
                path=[*path, key],
            )

    def cross_verify_overrides(
        self, agent_config: AgentConfig, skill_config: SkillConfig
    ) -> None:
        """Cross verify overrides between service config and agent config"""

        self.logger.info("Cross verifying overrides between agent and service")
        agent_overrides = set(agent_config.component_configurations)
        service_overrides = {
            PackageId(
                package_type=component_override["type"],
                public_id=PublicId.from_str(component_override["public_id"]),
            )
            for component_override in self.service_config.overrides
        }

        missing_from_agent = service_overrides - agent_overrides
        if len(missing_from_agent) > 0:
            raise ServiceValidationFailed(
                "Service config has an overrides which are not defined in the agent config; "
                f"packages with missing overrides={missing_from_agent}"
            )

        skill_override_from_agent = agent_config.component_configurations[
            skill_config.package_id
        ]
        skill_config_to_check = {
            "models": {
                "params": {"args": skill_config.json["models"]["params"]["args"]},
            }
        }
        if "benchmark_tool" in skill_config.json["models"]:
            skill_config_to_check["models"]["benchmark_tool"] = {
                "args": skill_config.json["models"]["benchmark_tool"]["args"]
            }

        for override in self.service_config.overrides:
            (
                skill_override_from_service,
                component_id,
                has_multiple_overrides,
            ) = Service.process_metadata(copy.deepcopy(override))
            if skill_config.component_id == component_id:
                if not has_multiple_overrides:
                    self._check_overrides_recursively(
                        check_from=skill_override_from_service,
                        check_with=skill_override_from_agent,
                        check_from_name=str(self.service_config.package_id),
                        check_with_name=str(agent_config.package_id),
                    )
                    continue

                for (
                    key,
                    _skill_override_from_service,
                ) in skill_override_from_service.items():
                    self.logger.info(f"Verifying the skill override with index {key}")
                    self._check_overrides_recursively(
                        check_from=_skill_override_from_service,
                        check_with=skill_override_from_agent,
                        check_from_name=str(self.service_config.package_id),
                        check_with_name=str(agent_config.package_id),
                    )

        self.logger.info("Cross verifying overrides between skill and agent")
        self._check_overrides_recursively(
            check_from=skill_override_from_agent,
            check_with=skill_config_to_check,
            check_from_name=str(agent_config.package_id),
            check_with_name=str(skill_config.package_id),
        )

    @staticmethod
    def _validate_override(
        validator: Draft4Validator,
        overrides: Dict,
        has_multiple_overrides: bool,
        error_message: str,
    ) -> None:
        """Run validator on the given override."""
        try:
            if has_multiple_overrides:
                _ = list(map(validator.validate, overrides.values()))
            else:
                validator.validate(overrides)
        except ValidationError as e:
            raise ServiceValidationFailed(error_message.format(error=e.message)) from e

    @classmethod
    def validate_override(
        cls,
        component_id: ComponentId,
        override: Dict,
        has_multiple_overrides: bool,
    ) -> None:
        """Validate override"""

        if (
            component_id.component_type == ComponentType.SKILL
            and ABCI in component_id.name
        ):
            cls._validate_override(
                validator=ABCI_SKILL_VALIDATOR,
                overrides=override,
                has_multiple_overrides=has_multiple_overrides,
                error_message="ABCI skill validation failed; {error}",
            )
        if (
            component_id.component_type == ComponentType.CONNECTION
            and component_id.name == ABCI
        ):
            cls._validate_override(
                validator=ABCI_CONNECTION_VALIDATOR,
                overrides=override,
                has_multiple_overrides=has_multiple_overrides,
                error_message="ABCI connection validation failed; {error}",
            )
        if (
            component_id.component_type == ComponentType.CONNECTION
            and component_id.name == LEDGER
        ):
            try:
                cls._validate_override(
                    validator=LEDGER_CONNECTION_VALIDATOR,
                    overrides=override,
                    has_multiple_overrides=has_multiple_overrides,
                    error_message="Ledger connection validation failed; {error}",
                )
            except ServiceValidationFailed as e:
                (msg, *_) = e.args
                unknown_ledger_match = UNKNOWN_LEDGER_RE.match(msg)
                if unknown_ledger_match is None:
                    raise

                (unknown_ledger,) = cast(re.Match, unknown_ledger_match).groups()
                logging.warning(
                    f"Unknown ledger configuration found with name `{unknown_ledger}`"
                )

    def validate_skill_config(self, skill_config: SkillConfig) -> None:
        """Check required overrides."""

        self.logger.info("Validating skill overrides")
        model_params = skill_config.models.read("params")
        self._validate_override(
            validator=ABCI_SKILL_MODEL_PARAMS_VALIDATOR,
            overrides=model_params.args,
            has_multiple_overrides=False,
            error_message="ABCI skill model parameter validation failed; {error}",
        )

    def validate_agent_overrides(self, agent_config: AgentConfig) -> None:
        """Check required overrides."""

        self.logger.info("Validating agent overrides")
        for (
            component_id,
            component_config,
        ) in agent_config.component_configurations.items():
            self.validate_override(
                component_id=component_id,
                override=component_config,
                has_multiple_overrides=False,
            )

    def validate_service_overrides(self) -> None:
        """Check required overrides."""

        self.logger.info("Validating service overrides")
        for _component_config in self.service_config.overrides:
            (
                component_config,
                component_id,
                has_multiple_overrides,
            ) = Service.process_metadata(configuration=_component_config.copy())
            self.logger.info(f"Validating {component_id} from the service overrides")
            self.validate_override(
                component_id=component_id,
                override=component_config,
                has_multiple_overrides=has_multiple_overrides,
            )
