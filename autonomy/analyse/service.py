# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2023-2024 Valory AG
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
import os
import re
from typing import Any, Dict, List, Optional, OrderedDict, Set, Union, cast

from aea.configurations.base import AgentConfig, SkillConfig
from aea.configurations.data_types import (
    ComponentId,
    ComponentType,
    PackageId,
    PublicId,
)
from aea.crypto.base import LedgerApi
from aea.helpers.cid import to_v0
from aea.helpers.env_vars import apply_env_variables
from aea.helpers.logging import setup_logger
from jsonschema.exceptions import ValidationError as SchemaValidationError
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
        "max_healthcheck",
        "round_timeout_seconds",
        "sleep_time",
        "retry_timeout",
        "retry_attempts",
        "keeper_timeout",
        "reset_pause_duration",
        "drand_public_key",
        "tendermint_url",
        "tendermint_com_url",
        "tendermint_p2p_url",
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
        "use_termination",
        "use_slashing",
        "slash_cooldown_hours",
        "slash_threshold_amount",
        "light_slash_unit_amount",
        "serious_slash_unit_amount",
        "setup",
    ],
}

ABCI = "abci"
LEDGER = "ledger"
TERMINATION_ABCI = PublicId(author="valory", name="termination_abci", version="any")
SLASHING_ABCI = PublicId(author="valory", name="slashing_abci", version="any")
ENV_VAR_RE = re.compile(
    r"^\$\{(?P<name>[A-Z_0-9]+)?:?(?P<type>bool|int|float|str|list|dict)?:?(?P<value>.+)?\}$"
)
REQUIRED_PROPERTY_RE = re.compile(r"'(.*)' is a required property")
PROPERTY_NOT_ALLOWED_RE = re.compile(
    r"Additional properties are not allowed \((('(.*)'(,)? )+)(was|were) unexpected\)"
)


class CustomSchemaValidationError(SchemaValidationError):
    """Custom schema validation error to report all errors at once."""

    def __init__(
        self,
        extra_properties: Optional[List[str]] = None,
        missing_properties: Optional[List[str]] = None,
        not_having_enough_properties: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize object."""
        self.extra_properties = extra_properties or []
        self.missing_properties = missing_properties or []
        self.not_having_enough_properties = not_having_enough_properties or []
        self.should_raise = False
        error_strings = []
        if len(self.extra_properties) > 0:
            self.should_raise = True
            self.extra_properties_error = "Additional properties found " + ", ".join(
                map(lambda x: f"'{x}'", self.extra_properties)
            )
            error_strings.append(self.extra_properties_error)

        if len(self.missing_properties) > 0:
            self.should_raise = True
            self.missing_properties_error = (
                "Following properties are require but missing "
                + ", ".join(map(lambda x: f"'{x}'", self.missing_properties))
            )
            error_strings.append(self.missing_properties_error)

        if len(self.not_having_enough_properties) > 0:
            self.should_raise = True
            self.not_having_enough_properties_error = ";".join(
                self.not_having_enough_properties
            )
            error_strings.append(self.not_having_enough_properties_error)

        message = ";".join(error_strings)
        super().__init__(message, **kwargs)


class CustomSchemaValidator(Draft4Validator):
    """Custom schema validator to report all missing fields at once."""

    def validate(self, *args: Any, **kwargs: Any) -> None:
        """Validate and raise all errors at once."""
        missing = []
        extra = []
        not_enough_properties = []
        for error in self.iter_errors(*args, **kwargs):
            message = cast(SchemaValidationError, error).message
            missing_property_check = REQUIRED_PROPERTY_RE.match(message)
            if missing_property_check is not None:
                (missing_property,) = cast(re.Match, missing_property_check).groups()
                missing.append(missing_property)
                continue

            property_not_allowed_check = PROPERTY_NOT_ALLOWED_RE.match(message)
            if property_not_allowed_check is not None:
                extra += re.findall(
                    "[a-zA-Z0-9]+", property_not_allowed_check.groups()[0]
                )
                continue

            if "does not have enough properties" in message:
                not_enough_properties.append(message)

        error = CustomSchemaValidationError(
            extra_properties=extra,
            missing_properties=missing,
            not_having_enough_properties=not_enough_properties,
        )
        if error.should_raise:
            raise error


ABCI_CONNECTION_VALIDATOR = CustomSchemaValidator(schema=ABCI_CONNECTION_SCHEMA)
LEDGER_CONNECTION_VALIDATOR = CustomSchemaValidator(schema=LEDGER_CONNECTION_SCHEMA)
ABCI_SKILL_VALIDATOR = CustomSchemaValidator(schema=ABCI_SKILL_SCHEMA)
ABCI_SKILL_MODEL_PARAMS_VALIDATOR = CustomSchemaValidator(
    schema=ABCI_SKILL_MODEL_PARAMS_SCHEMA
)


class ServiceValidationFailed(Exception):
    """Raise when service validation fails."""


class ServiceAnalyser:
    """Tools to analyse a service"""

    def __init__(
        self,
        service_config: Service,
        abci_skill_id: PublicId,
        is_on_chain_check: bool = False,
        logger: Optional[logging.Logger] = None,
        skip_warnings: bool = False,
    ) -> None:
        """Initialise object."""

        self.service_config = service_config
        self.abci_skill_id = abci_skill_id
        self.is_on_chain_check = is_on_chain_check
        self.logger = logger or setup_logger(name="autonomy.analyse")
        self.skip_warning = skip_warnings

    def _warn(self, msg: str) -> None:
        """Raise warning."""
        if self.skip_warning:  # pragma: nocover
            return
        self.logger.warning(msg=msg)

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
            self._warn(
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
            self._warn(message)

        missing = check_from_set - check_with_set
        if len(missing) > 0:
            message = (
                f"{check_from_name} contains configuration which is missing from {check_with_name}\n"
                f"\tPath: {path_str}\n"
                f"\tMissing parameters: {missing}\n"
            )
            self._warn(message)

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

    def cross_verify_overrides(  # pylint: disable=too-many-locals
        self,
        agent_config: AgentConfig,
        skill_config: SkillConfig,
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

        # Skip abci connection since it's not required to be manually overridden
        missing_from_service = [
            cid
            for cid in agent_overrides - service_overrides
            if cid.public_id.name != ABCI
            and cid.component_type != ComponentType.CONNECTION
        ]
        if len(missing_from_service) > 0:
            self._warn(
                "\n\t- ".join(
                    map(
                        str,
                        [
                            "Overrides with following component IDs are defined in the agent configuration but not in the service configuration",
                            *missing_from_service,
                        ],
                    )
                )
            )

        missing_from_agent = service_overrides - agent_overrides
        if len(missing_from_agent) > 0:
            raise ServiceValidationFailed(
                "\n\t- ".join(
                    map(
                        str,
                        [
                            "Overrides with following component IDs are defined in the service configuration but not in the agent configuration",
                            *missing_from_agent,
                        ],
                    )
                )
            )

        skill_override_from_agent = apply_env_variables(
            agent_config.component_configurations[skill_config.package_id],
            env_variables=os.environ.copy(),
        )
        skill_config_to_check: Dict[str, Dict] = {"models": {}}
        skill_config_json = copy.deepcopy(skill_config.json)
        skill_config_to_check["models"]["params"] = {
            "args": skill_config_json["models"]["params"]["args"]
        }
        if "benchmark_tool" in skill_config_json["models"]:
            skill_config_to_check["models"]["benchmark_tool"] = {
                "args": skill_config_json["models"]["benchmark_tool"]["args"]
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
                break

        self.logger.info("Cross verifying overrides between skill and agent")
        self._check_overrides_recursively(
            check_from=skill_override_from_agent,
            check_with=skill_config_to_check,
            check_from_name=str(agent_config.package_id),
            check_with_name=str(skill_config.package_id),
        )

    @classmethod
    def validate_override_env_vars(
        cls,
        overrides: Union[OrderedDict, dict],
        validate_env_var_name: bool = False,
        json_path: Optional[List[str]] = None,
    ) -> List[str]:
        """Validate environment variables."""
        errors = []
        json_path = json_path or []
        for key, value in overrides.items():
            if key in (
                "target_skill_id",
                "identifier",
                "ledger_id",
                "message_format",
                "not_after",
                "not_before",
                "save_path",
                "is_abstract",
            ):
                continue  # pragma: nocover
            _json_path = [*json_path, str(key)]
            if isinstance(value, (dict, OrderedDict)):
                errors += cls.validate_override_env_vars(
                    value,
                    validate_env_var_name=validate_env_var_name,
                    json_path=_json_path,
                )
            elif isinstance(value, list):
                for i, obj in enumerate(value):
                    if not isinstance(obj, (dict, OrderedDict)):
                        continue  # pragma: nocover
                    errors += cls.validate_override_env_vars(
                        obj,
                        validate_env_var_name=validate_env_var_name,
                        json_path=[*_json_path, str(i)],
                    )
            else:
                json_path_str = ".".join(_json_path)
                try:
                    re_result = ENV_VAR_RE.match(value)
                    if re_result is None:
                        errors.append(
                            f"`{json_path_str}` needs environment variable defined in following format "
                            "${ENV_VAR_NAME:DATA_TYPE:DEFAULT_VALUE}"
                        )
                        continue

                    result = re_result.groupdict()
                    if validate_env_var_name and result.get("name") is None:
                        errors.append(
                            f"Enviroment variable template for `{json_path_str}` does not have variable name defined"
                        )

                    if result.get("type") is None:
                        errors.append(
                            f"Enviroment variable template for `{json_path_str}` does not have type defined"
                        )
                        continue

                    if result.get("value") is None:
                        errors.append(
                            f"Enviroment variable template for `{json_path_str}` does not have default value defined"
                        )
                        continue

                    apply_env_variables(
                        data={key: value}, env_variables=os.environ.copy()
                    )
                except TypeError:
                    errors.append(
                        f"`{json_path_str}` needs to be defined as a environment variable"
                    )
                except (ValueError, KeyError) as e:
                    errors.append(
                        f"`{json_path_str}` validation failed with following error; {e}"
                    )

        return errors

    def validate_agent_override_env_vars(self, agent_config: AgentConfig) -> None:
        """Check if all of the overrides are defined as a env vars in the agent config"""

        self.logger.info(
            f"Validating agent {agent_config.public_id} overrides for environment variable definitions"
        )
        for package_id, override in agent_config.component_configurations.items():
            errors = self.validate_override_env_vars(overrides=override)
            if len(errors) > 0:
                raise ServiceValidationFailed(
                    "\n\t- ".join(
                        [
                            f"{package_id} environment variable validation failed with following error",
                            *errors,
                        ]
                    ),
                )

    def validate_service_override_env_vars(self) -> None:
        """Check if all of the overrides are defined as a env vars in the agent config"""
        self.logger.info(
            f"Validating service {self.service_config.public_id} overrides for environment variable definitions"
        )
        errors = []
        for _component_config in self.service_config.overrides:
            (
                component_config,
                component_id,
                _,
            ) = Service.process_metadata(configuration=_component_config.copy())
            errors = self.validate_override_env_vars(
                overrides=component_config, validate_env_var_name=True
            )
            if len(errors) > 0:
                raise ServiceValidationFailed(
                    "\n\t- ".join(
                        [
                            f"{component_id} environment variable validation failed with following error",
                            *errors,
                        ]
                    ),
                )

    @staticmethod
    def _validate_override(
        validator: Draft4Validator,
        overrides: Dict,
        has_multiple_overrides: bool,
        error_message: str,
        raise_custom_exception: bool = True,
    ) -> None:
        """Run validator on the given override."""

        def _validate_override(
            validator: Draft4Validator,
            overrides: Dict,
            error_message: str,
        ) -> None:
            try:
                validator.validate(overrides)
            except CustomSchemaValidationError as e:
                if raise_custom_exception:
                    raise ServiceValidationFailed(
                        error_message.format(error=e.message)
                    ) from e
                raise

        if has_multiple_overrides:
            for idx, override in overrides.items():
                _validate_override(
                    validator=validator,
                    overrides=override,
                    error_message=f"{error_message} at override index {idx}",
                )
        else:
            _validate_override(
                validator=validator,
                overrides=overrides,
                error_message=error_message,
            )

    def validate_override(
        self,
        component_id: ComponentId,
        override: Dict,
        has_multiple_overrides: bool,
    ) -> None:
        """Validate override"""

        if component_id.public_id == self.abci_skill_id:
            self._validate_override(
                validator=ABCI_SKILL_VALIDATOR,
                overrides=override,
                has_multiple_overrides=has_multiple_overrides,
                error_message=(
                    "ABCI Skill `"
                    + str(component_id.public_id)
                    + "` override validation failed; {error}"
                ),
            )

        if (
            component_id.component_type == ComponentType.CONNECTION
            and component_id.name == ABCI
        ):
            self._validate_override(
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
                self._validate_override(
                    validator=LEDGER_CONNECTION_VALIDATOR,
                    overrides=override,
                    has_multiple_overrides=has_multiple_overrides,
                    error_message="{error}",
                    raise_custom_exception=False,
                )
            except CustomSchemaValidationError as e:
                if len(e.not_having_enough_properties) > 0:
                    raise ServiceValidationFailed(
                        f"{component_id} override needs at least one ledger API definition"
                    ) from e

                if len(e.missing_properties) > 0:
                    raise ServiceValidationFailed(
                        f"Ledger connection validation failed; {e.missing_properties_error}"
                    ) from e

                if len(e.extra_properties) > 0:
                    self._warn(
                        "\n\t- ".join(
                            [
                                f"Following unknown ledgers found in the {component_id} override",
                                *e.extra_properties,
                            ]
                        )
                    )

    def _check_for_dependency(
        self, dependencies: Set[PublicId], dependency: PublicId
    ) -> None:
        """Check termination ABCI skill is an dependency for the agent"""
        for _dependency in dependencies:
            if _dependency.to_any() == dependency:
                return
        self.logger.warning(f"{dependency} is not defined as a dependency")

    def validate_skill_config(self, skill_config: SkillConfig) -> None:
        """Check required overrides."""

        self.logger.info(f"Validating ABCI skill {skill_config.public_id}")
        model_params = skill_config.models.read("params")
        if model_params is None:
            raise ServiceValidationFailed(
                f"The chained ABCI skill `{skill_config.public_id}` does not contain `params` model"
            )

        self._validate_override(
            validator=ABCI_SKILL_MODEL_PARAMS_VALIDATOR,
            overrides=model_params.args,
            has_multiple_overrides=False,
            error_message="ABCI skill validation failed; {error}",
        )
        self._check_for_dependency(skill_config.skills, TERMINATION_ABCI)
        self._check_for_dependency(skill_config.skills, SLASHING_ABCI)
        self.logger.info("No issues found in the ABCI skill configuration")

    def validate_agent_overrides(self, agent_config: AgentConfig) -> None:
        """Check required overrides."""

        self.logger.info(f"Validating agent {agent_config.public_id} overrides")
        errors = []
        for (
            component_id,
            component_config,
        ) in agent_config.component_configurations.items():
            try:
                self.validate_override(
                    component_id=component_id,
                    override=component_config,
                    has_multiple_overrides=False,
                )
            except ServiceValidationFailed as e:
                errors.append(str(e))

        if len(errors) > 0:
            error_string = "\n\t- ".join(errors)
            raise ServiceValidationFailed(
                "Agent overrides validation failed with following errors"
                f"\n\t- {error_string}"
            )

        self._check_for_dependency(agent_config.skills, TERMINATION_ABCI)
        self._check_for_dependency(agent_config.skills, SLASHING_ABCI)
        self.logger.info("No issues found in the agent overrides")

    def validate_service_overrides(self) -> None:
        """Check required overrides."""

        self.logger.info("Validating service overrides")
        errors = []
        for _component_config in self.service_config.overrides:
            (
                component_config,
                component_id,
                has_multiple_overrides,
            ) = Service.process_metadata(configuration=_component_config.copy())
            try:
                self.validate_override(
                    component_id=component_id,
                    override=component_config,
                    has_multiple_overrides=has_multiple_overrides,
                )
            except ServiceValidationFailed as e:
                errors.append(str(e))

        if len(errors) > 0:
            error_string = "\n\t- ".join(errors)
            raise ServiceValidationFailed(
                "Service overrides validation failed with following errors"
                f"\n\t- {error_string}"
            )

        self.logger.info("No issues found in the service overrides")
