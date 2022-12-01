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

import os
from collections import OrderedDict
from copy import copy
from typing import Any, Dict, FrozenSet, List, Optional, Sequence, Tuple, cast

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
from aea.configurations.data_types import PackageType, PublicId
from aea.exceptions import AEAValidationError
from aea.helpers.base import SimpleIdOrStr
from aea.helpers.env_vars import apply_env_variables, generate_env_vars_recursively

from autonomy.configurations.constants import DEFAULT_SERVICE_CONFIG_FILE, SCHEMAS_DIR
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


class Service(PackageConfiguration):  # pylint: disable=too-many-instance-attributes
    """Service package configuration."""

    default_configuration_filename = DEFAULT_SERVICE_CONFIG_FILE
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

    def check_overrides_valid(
        self, overrides: List, env_vars_friendly: bool = False
    ) -> None:
        """Uses the AEA helper libraries to check individual overrides."""
        base_validator = validation.ConfigValidator("definitions.json")
        processed = []
        for component_configuration_json in overrides:
            configuration, component_id, has_multiple_overrides = self.process_metadata(
                configuration=copy(component_configuration_json)
            )
            if component_id in processed:
                raise AEAValidationError(
                    f"Overrides for component {component_id} are defined more than once"
                )
            if has_multiple_overrides:
                for idx in range(self.number_of_agents):
                    try:
                        _configuration = cast(Dict, configuration[idx])
                    except KeyError as e:
                        raise AEAValidationError(
                            f"Not enough overrides for component {component_id};"
                            f" Number of agents: {self.number_of_agents}"
                        ) from e

                    base_validator.validate_component_configuration(
                        component_id=component_id,
                        configuration=_configuration,
                        env_vars_friendly=env_vars_friendly,
                    )
            else:
                base_validator.validate_component_configuration(
                    component_id=component_id,
                    configuration=configuration,
                    env_vars_friendly=env_vars_friendly,
                )

            processed.append(component_id)

    @staticmethod
    def process_metadata(
        configuration: Dict,
    ) -> Tuple[Dict, ComponentId, bool]:
        """Process component override metadata."""

        component_id = ComponentId(
            component_type=cast(str, configuration.pop("type")),
            public_id=PublicId.from_str(
                cast(
                    str,
                    configuration.pop("public_id"),
                ),
            ),
        )
        _ = configuration.pop("extra", {})
        has_multiple_overrides = all(
            map(lambda x: isinstance(x, int), configuration.keys())
        )
        return configuration, component_id, has_multiple_overrides

    def process_component_overrides(
        self,
        agent_idx: int,
        component_configuration_json: Dict,
    ) -> Dict:
        """
        Process a component configuration in an agent configuration file.

        :param agent_idx: Index of the agent.
        :param component_configuration_json: the JSON object.
        :return: the processed component configuration.
        """

        configuration, component_id, has_multiple_overrides = self.process_metadata(
            configuration=copy(component_configuration_json)
        )

        if has_multiple_overrides:
            configuration = configuration.get(agent_idx, {})
            if configuration == {}:
                raise ValueError(
                    f"Overrides not provided for agent {agent_idx}; component={component_id}"
                )
        configuration = apply_env_variables(
            data=configuration, env_variables=os.environ.copy()
        )
        env_var_dict = self.generate_environment_variables(
            component_id=component_id,
            component_configuration_json=configuration,
        )

        return env_var_dict

    @staticmethod
    def generate_environment_variables(
        component_id: ComponentId,
        component_configuration_json: Dict,
    ) -> Dict:
        """Try to process component with a singular component overrides."""
        config_class = cast(
            ComponentConfiguration,
            COMPONENT_CONFIGS.get(component_id.package_type.value),
        )
        env_var_dict = {}
        export_path_prefix = [
            component_id.package_type.value,
            component_id.name,
        ]
        for field in config_class.FIELDS_ALLOWED_TO_UPDATE:
            field_data = component_configuration_json.get(field, {})
            if field_data == {}:
                continue
            env_var_dict.update(
                generate_env_vars_recursively(
                    data=field_data,
                    export_path=[*export_path_prefix, field],
                )
            )

        return env_var_dict


PACKAGE_TYPE_TO_CONFIG_CLASS = {
    **_PACKAGE_TYPE_TO_CONFIG_CLASS,
    PackageType.SERVICE: Service,
}
