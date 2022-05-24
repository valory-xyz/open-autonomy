# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
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

"""Service component base."""

import json
from asyncio.log import logger
from copy import copy
from pathlib import Path
from typing import Any, Dict, List, Tuple

import jsonschema
import yaml
from aea import AEA_DIR
from aea.configurations import validation
from aea.configurations.base import (
    ComponentConfiguration,
    ComponentId,
    ConnectionConfig,
    ContractConfig,
    ProtocolConfig,
    SkillConfig,
)
from aea.configurations.constants import CONNECTION, CONTRACT, PROTOCOL, SKILL
from aea.helpers.base import cd
from aea.helpers.io import open_file

from aea_swarm.configurations.base import Service
from aea_swarm.configurations.constants import SCHEMAS_DIR


COMPONENT_CONFIGS: Dict = {
    component.package_type.value: component  # type: ignore
    for component in [
        ContractConfig,
        SkillConfig,
        ProtocolConfig,
        ConnectionConfig,
    ]
}


def recurse(obj: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively explore a json object until no dictionaries remain."""
    if not any([isinstance(i, dict) for i in obj.values()]):
        return obj

    new_obj = {}
    for k, v in obj.items():
        if isinstance(v, dict):
            for k2, v2 in v.items():
                new_obj["_".join([str(k), str(k2)])] = v2
        else:
            new_obj[k] = v
    return recurse(new_obj)


def _parse_nested_override(env_var_name: str, nested_override_value: Dict) -> Dict:
    """Used for handling dictionary object 1 level below nesting."""
    overrides = recurse(nested_override_value)
    return {f"{env_var_name}_{k}".upper(): v for k, v in overrides.items()}


class ServiceConfigValidator(validation.ConfigValidator):
    """Configuration validator implementation."""

    def __init__(  # pylint: disable=super-init-not-called
        self, schema_filename: str, env_vars_friendly: bool = False
    ) -> None:
        """
        Initialize the parser for configuration files.

        :param schema_filename: the path to the JSON-schema file in 'aea/configurations/schemas'.
        :param env_vars_friendly: whether or not it is env var friendly.
        """

        with open_file(SCHEMAS_DIR / schema_filename) as fp:
            self._schema = json.load(fp)

        root_path = validation.make_jsonschema_base_uri(SCHEMAS_DIR)
        self._resolver = jsonschema.RefResolver(root_path, self._schema)
        self.env_vars_friendly = env_vars_friendly

        if env_vars_friendly:
            self._validator = validation.EnvVarsFriendlyDraft4Validator(
                self._schema, resolver=self._resolver
            )
        else:
            self._validator = validation.OwnDraft4Validator(
                self._schema, resolver=self._resolver
            )

    @staticmethod
    def check_overrides_match_spec(service_config: Dict, overrides: List) -> bool:
        """Check that overrides are valid.

        - number of overrides is 1
        - number of overrides == number of agents in spec
        - number of overrides is 0

        :param service_config: Service config
        :param overrides: List of overrides
        :return: True if overrides are valid
        """
        valid = []
        remaining = copy(overrides)

        for component in [
            CONNECTION,
            CONTRACT,
            PROTOCOL,
            SKILL,
        ]:

            component_overrides = [f for f in overrides if f["type"] == component]
            remaining = [f for f in remaining if f not in component_overrides]
            if any(
                [
                    service_config["number_of_agents"] == len(component_overrides),
                    len(component_overrides) == 0,
                    len(component_overrides) == 1,
                ]
            ):
                valid.append(True)

        if len(remaining) > 0:
            raise ValueError(f"Override type is misspelled.\n {remaining}")

        if sum(valid) == 4:
            return True

        raise ValueError(
            f"Incorrect number of overrides for count of agents.\n {service_config}"
        )

    def check_overrides_are_valid(
        self, service_config: Dict, overrides: List
    ) -> Dict[ComponentId, Dict[Any, Any]]:
        """Uses the aea helper libraries to check individual overrides."""

        component_configurations: Dict[ComponentId, Dict] = {}
        # load the other components.

        for idx, component_configuration_json in enumerate(overrides):
            component_id, _ = self.process_component_section(
                idx, component_configuration_json, service_config
            )
            if component_id in component_configurations:
                raise ValueError(
                    f"Configuration of component {component_id} occurs more than once."
                )
            component_configurations[component_id] = component_configuration_json

        return component_configurations

    @classmethod
    def process_component_section(
        cls,
        component_index: int,
        component_configuration_json: Dict,
        service_config: Dict,
    ) -> Tuple[ComponentId, Dict]:
        """
        Process a component configuration in an agent configuration file.

        It breaks down in:
        - extract the component id
        - validate the component configuration
        - check that there are only configurable fields

        :param component_index: the index of the component in the file.
        :param component_configuration_json: the JSON object.
        :param service_config: Service config
        :return: the processed component configuration.
        """
        configuration = copy(component_configuration_json)
        component_id = cls.split_component_id_and_config(component_index, configuration)

        path = Path(AEA_DIR) / "configurations" / "schemas"
        config_class = COMPONENT_CONFIGS[component_id.package_type.value]

        with cd(path):  # required to handle protected variable _SCHEMEAS_DIR
            cv = validation.ConfigValidator("definitions.json")
            try:
                cv.validate_component_configuration(component_id, configuration)
                overrides = cls.try_to_process_singular_override(
                    component_id, config_class, configuration
                )
            except ValueError as e:
                logger.debug(
                    f"Failed to parse as a singular input with {e}\nAttempting with nested fields."
                )

                overrides = cls.try_to_process_nested_fields(
                    component_id,
                    component_index,
                    config_class,
                    configuration,
                    service_config,
                )
        return component_id, overrides

    @staticmethod
    def try_to_process_singular_override(
        component_id: ComponentId,
        config_class: ComponentConfiguration,
        component_configuration_json: Dict,
    ) -> Dict:
        """Try to process component with a singular component overrides."""
        overrides = {}
        for field in config_class.FIELDS_ALLOWED_TO_UPDATE:
            env_var_base = "_".join(
                [component_id.package_type.value, component_id.name, field]
            )

            field_override = component_configuration_json.get(field, {})
            if field_override == {}:
                continue
            for nested_override, nested_value in field_override.items():
                for (
                    nested_override_key,
                    nested_override_value,
                ) in nested_value.items():
                    env_var_name = "_".join(
                        [env_var_base, nested_override, nested_override_key]
                    )
                    overrides.update(
                        _parse_nested_override(env_var_name, nested_override_value)
                    )
        return overrides

    @staticmethod
    def try_to_process_nested_fields(  # pylint: disable=too-many-locals
        component_id: ComponentId,
        component_index: int,
        config_class: ComponentConfiguration,
        component_configuration_json: Dict,
        service_config: Dict,
    ) -> Dict:
        """Try to process component with nested overrides."""
        overrides = {}
        for field in config_class.FIELDS_WITH_NESTED_FIELDS:  # type: ignore
            field_override = component_configuration_json.get(field, {})
            if field_override == {}:
                continue
            if not all(isinstance(item, int) for item in field_override.keys()):
                raise ValueError(
                    "All keys of list like override should be of type int."
                )
            nums = set(field_override.keys())

            if len(nums) != len(field_override.keys()):
                raise ValueError("Non-unique item in override")

            if len(nums) != service_config["number_of_agents"]:
                raise ValueError("Not enough items in override")

            if nums != set(range(0, service_config["number_of_agents"])):
                raise ValueError("Overrides incorrectly indexed")

            n_fields = len(field_override)
            for override in field_override[component_index % n_fields]:
                for nested_override, nested_value in override.items():
                    for (
                        nested_override_key,
                        nested_override_value,
                    ) in nested_value.items():
                        if (
                            nested_override_key
                            not in config_class.NESTED_FIELDS_ALLOWED_TO_UPDATE  # type: ignore
                        ):
                            raise ValueError("Trying to override non-nested field.")

                        env_var_name = "_".join(
                            [
                                component_id.package_type.value,
                                component_id.name,
                                field,
                                nested_override,
                                nested_override_key,
                            ]
                        )
                        overrides.update(
                            _parse_nested_override(env_var_name, nested_override_value)
                        )

        return overrides


def load_service_config(service_path: Path) -> Tuple[Service, List]:
    """Load service config from the path."""

    service_config_validator = ServiceConfigValidator(Service.schema)
    with open(
        service_path / Service.default_configuration_filename, "r", encoding="utf-8"
    ) as fp:
        service_config, *overrides = yaml.load_all(fp, Loader=yaml.SafeLoader)

    service_config_validator.validate(service_config)
    service_config_validator.check_overrides_match_spec(service_config, overrides)
    service_config_validator.check_overrides_are_valid(service_config, overrides)
    service_config["license_"] = service_config.pop("license")
    return Service(**service_config), overrides
