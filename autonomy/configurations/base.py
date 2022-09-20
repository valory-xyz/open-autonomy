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

"""Base configurations."""

from collections import OrderedDict
from copy import copy
from pathlib import Path
from typing import Any, Dict, FrozenSet, List, Optional, Sequence, Tuple, cast

from aea import AEA_DIR
from aea.configurations import validation
from aea.configurations.base import (
    ComponentConfiguration,
    ComponentId,
    ConnectionConfig,
    ContractConfig,
)
from aea.configurations.base import (
    PACKAGE_TYPE_TO_CONFIG_CLASS as _PACKAGE_TYPE_TO_CONFIG_CLASS,
)
from aea.configurations.base import PackageConfiguration, ProtocolConfig, SkillConfig
from aea.configurations.constants import CONNECTION, CONTRACT, PROTOCOL, SKILL
from aea.configurations.data_types import PackageType, PublicId
from aea.helpers.base import SimpleIdOrStr, cd

from autonomy.configurations.constants import DEFAULT_SERVICE_FILE, SCHEMAS_DIR
from autonomy.configurations.validation import ConfigValidator


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


class Service(PackageConfiguration):  # pylint: disable=too-many-instance-attributes
    """Service package configuration."""

    default_configuration_filename = DEFAULT_SERVICE_FILE
    package_type = PackageType.SERVICE
    schema = str(SCHEMAS_DIR.absolute() / "service_schema.json")

    FIELDS_ALLOWED_TO_UPDATE: FrozenSet[str] = frozenset()

    __slots__ = (
        "_name",
        "_author",
        "version",
        "license",
        "fingerprint",
        "fingerprint_ignore_patterns",
        "build_entrypoint",
        "agent",
        "number_of_agents",
        "_aea_version",
        "_aea_version_specifiers",
        "_directory",
        "_overrides",
    )

    def __init__(  # pylint: disable=too-many-arguments
        self,
        name: SimpleIdOrStr,
        author: SimpleIdOrStr,
        agent: PublicId,
        version: str = "",
        license_: str = "",
        aea_version: str = "",
        fingerprint: Optional[Dict[str, str]] = None,
        fingerprint_ignore_patterns: Optional[Sequence[str]] = None,
        description: str = "",
        number_of_agents: int = 4,
        build_entrypoint: Optional[str] = None,
        overrides: Optional[List] = None,
    ) -> None:
        """Initialise object."""

        super().__init__(
            name=name,
            author=author,
            version=version,
            license_=license_,
            aea_version=aea_version,
            build_entrypoint=build_entrypoint,
            fingerprint=fingerprint,
            fingerprint_ignore_patterns=fingerprint_ignore_patterns,
        )

        self.agent = PublicId.from_str(str(agent))
        self.description = description
        self.number_of_agents = number_of_agents

        self._overrides = [] if overrides is None else overrides

    @property
    def overrides(
        self,
    ) -> List:
        """Returns component overrides."""

        return self._overrides

    @overrides.setter
    def overrides(self, obj: List) -> None:
        """Set overrides."""

        self.check_overrides_valid(obj)
        self.check_overrides_match_spec(obj)
        self._overrides = obj

    @property
    def json(
        self,
    ) -> Dict:
        """Returns an ordered Dict for service config."""

        config = OrderedDict(
            {
                "name": self.name,
                "author": self.author,
                "agent": str(self.agent),
                "version": self.version,
                "license": self.license,
                "aea_version": self.aea_version,
                "description": self.description,
                "number_of_agents": self.number_of_agents,
                "overrides": self.overrides,
                "fingerprint": self.fingerprint,
                "fingerprint_ignore_patterns": self.fingerprint_ignore_patterns,
            }
        )

        return config

    @classmethod
    def _create_or_update_from_json(cls, obj: Dict, instance: Any = None) -> "Service":
        """Create or update from json data."""

        obj = {**(instance.json if instance else {}), **copy(obj)}
        params = dict(
            name=cast(str, obj.get("name")),
            author=cast(str, obj.get("author")),
            agent=cast(str, obj.get("agent")),
            version=cast(str, obj.get("version")),
            license_=cast(str, obj.get("license")),
            aea_version=cast(str, obj.get("aea_version")),
            description=cast(str, obj.get("description")),
            number_of_agents=cast(int, obj.get("number_of_agents")),
            overrides=cast(List, obj.get("overrides", [])),
            fingerprint=cast(Dict[str, str], obj.get("fingerprint", [])),
            fingerprint_ignore_patterns=cast(
                Sequence[str], obj.get("fingerprint_ignore_patterns", [])
            ),
        )

        return cls(**params)  # type: ignore

    @classmethod
    def validate_config_data(
        cls, json_data: Dict, env_vars_friendly: bool = False
    ) -> None:
        """Validate config data."""
        ConfigValidator(cls.schema, env_vars_friendly=env_vars_friendly).validate(
            json_data
        )

    def check_overrides_match_spec(self, overrides: List) -> bool:
        """Check that overrides are valid.

        - number of overrides is 1
        - number of overrides == number of agents in spec
        - number of overrides is 0

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
                    self.number_of_agents == len(component_overrides),
                    len(component_overrides) == 0,
                    len(component_overrides) == 1,
                ]
            ):
                valid.append(True)

        if len(remaining) > 0:  # pragma: nocover
            raise ValueError(f"Override type is misspelled.\n {remaining}")

        if sum(valid) == 4:
            return True

        raise ValueError("Incorrect number of overrides for count of agents.")

    def check_overrides_valid(
        self, overrides: List, env_vars_friendly: bool = False
    ) -> Dict[ComponentId, Dict[Any, Any]]:
        """Uses the AEA helper libraries to check individual overrides."""

        component_configurations: Dict[ComponentId, Dict] = {}
        # load the other components.

        for idx, component_configuration_json in enumerate(overrides):
            component_id, _ = self.process_component_section(
                idx, component_configuration_json
            )
            if component_id in component_configurations:
                raise ValueError(
                    f"Configuration of component {component_id} occurs more than once."
                )
            component_configurations[component_id] = component_configuration_json

        return component_configurations

    def process_component_section(
        self,
        component_index: int,
        component_configuration_json: Dict,
    ) -> Tuple[ComponentId, Dict]:
        """
        Process a component configuration in an agent configuration file.

        It breaks down in:
        - extract the component id
        - validate the component configuration
        - check that there are only configurable fields

        :param component_index: the index of the component in the file.
        :param component_configuration_json: the JSON object.
        :return: the processed component configuration.
        """
        configuration = copy(component_configuration_json)
        component_id = ConfigValidator.split_component_id_and_config(
            component_index, configuration
        )

        path = Path(AEA_DIR) / "configurations" / "schemas"
        config_class = COMPONENT_CONFIGS[component_id.package_type.value]

        with cd(path):  # required to handle protected variable _SCHEMEAS_DIR
            cv = validation.ConfigValidator("definitions.json")
            try:
                cv.validate_component_configuration(component_id, configuration)
                overrides = self.try_to_process_singular_override(
                    component_id, config_class, configuration
                )
            except (ValueError, AttributeError):
                overrides = self.try_to_process_nested_fields(
                    component_id,
                    component_index,
                    config_class,
                    configuration,
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

    def try_to_process_nested_fields(  # pylint: disable=too-many-locals
        self,
        component_id: ComponentId,
        component_index: int,
        config_class: ComponentConfiguration,
        component_configuration_json: Dict,
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
            override_index = set(field_override.keys())
            if self.number_of_agents > len(override_index):
                raise ValueError(
                    f"Not enough items in override, Number of agents = {self.number_of_agents}; Number of overrides provided = {len(override_index)}"
                )

            n_fields = len(field_override)
            for override in field_override[component_index % n_fields]:
                for nested_override, nested_value in override.items():
                    for (
                        nested_override_key,
                        nested_override_value,
                    ) in nested_value.items():
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


PACKAGE_TYPE_TO_CONFIG_CLASS = {
    **_PACKAGE_TYPE_TO_CONFIG_CLASS,
    PackageType.SERVICE: Service,
}
