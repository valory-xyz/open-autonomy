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
import json
import os
from copy import copy
from logging import getLogger
from pathlib import Path
from shutil import rmtree
from typing import Any, Dict, List, Tuple, Type

import jsonschema
import yaml
from aea import AEA_DIR
from aea.cli.utils.package_utils import try_get_item_source_path
from aea.configurations import validation
from aea.configurations.base import (
    ComponentConfiguration,
    ComponentId,
    ConnectionConfig,
    ContractConfig,
    ProtocolConfig,
    SkillConfig,
)
from aea.configurations.constants import (
    AGENTS,
    CONNECTION,
    CONTRACT,
    DEFAULT_AEA_CONFIG_FILE,
    PROTOCOL,
    SKILL,
)
from aea.configurations.data_types import PublicId
from aea.helpers.base import cd
from aea.helpers.io import open_file

from deployments.constants import CONFIG_DIRECTORY, KEYS, NETWORKS, PACKAGES_DIRECTORY


COMPONENT_CONFIGS: Dict = {
    component.package_type.value: component  # type: ignore
    for component in [
        ContractConfig,
        SkillConfig,
        ProtocolConfig,
        ConnectionConfig,
    ]
}
logger = getLogger(__name__)


def _parse_nested_override(env_var_name: str, nested_override_value: Dict) -> Dict:
    """Used for handling dictionary object 1 level below nesting."""
    overrides = {}
    if not any([isinstance(i, dict) for i in nested_override_value.values()]):
        overrides.update(
            {f"{env_var_name}_{k}".upper(): v for k, v in nested_override_value.items()}
        )
    else:
        for k1, v1 in nested_override_value.items():
            for k2, v2 in v1.items():
                overrides.update({f"{env_var_name}_{k1}_{k2}".upper(): v2})
    return overrides


class DeploymentConfigValidator(validation.ConfigValidator):
    """Configuration validator implementation."""

    def __init__(  # pylint: disable=super-init-not-called
        self, schema_filename: str, env_vars_friendly: bool = False
    ) -> None:
        """
        Initialize the parser for configuration files.

        :param schema_filename: the path to the JSON-schema file in 'aea/configurations/schemas'.
        :param env_vars_friendly: whether or not it is env var friendly.
        """
        self.overrides: List = []
        self.deployment_spec: Dict[str, Any] = {}
        base_uri = Path(__file__).parent
        with open_file(base_uri / schema_filename) as fp:
            self._schema = json.load(fp)
        root_path = validation.make_jsonschema_base_uri(base_uri)
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

    def validate_deployment(self, deployment_spec: Dict, overrides: List) -> bool:
        """Sense check the deployment spec."""
        self.validate(deployment_spec)
        self.deployment_spec = deployment_spec
        self.overrides = overrides
        self.check_overrides_match_spec()
        self.check_overrides_are_valid()
        return True  # add in call to check to see if overrides are valid

    def check_overrides_match_spec(self) -> bool:
        """Check that overrides are valid.

        - number of overrides is 1
        - number of overrides == number of agents in spec
        - number of overrides is 0
        """
        valid = []
        remaining = copy(self.overrides)
        for component in [
            CONNECTION,
            CONTRACT,
            PROTOCOL,
            SKILL,
        ]:

            component_overrides = [f for f in self.overrides if f["type"] == component]
            remaining = [f for f in remaining if f not in component_overrides]

            if any(
                [
                    self.deployment_spec["number_of_agents"]
                    == len(component_overrides),
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
            f"Incorrect number of overrides for count of agents.\n {self.deployment_spec}"
        )

    def check_overrides_are_valid(self) -> Dict[ComponentId, Dict[Any, Any]]:
        """Uses the aea helper libraries to check individual overrides."""
        component_configurations: Dict[ComponentId, Dict] = {}
        # load the other components.

        for i, component_configuration_json in enumerate(self.overrides):
            component_id, _ = self.process_component_section(
                i, component_configuration_json
            )
            if component_id in component_configurations:
                raise ValueError(
                    f"Configuration of component {component_id} occurs more than once."
                )
            component_configurations[component_id] = component_configuration_json
        return component_configurations

    def process_component_section(
        self, component_index: int, component_configuration_json: Dict
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
        component_id = self.split_component_id_and_config(
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
            except ValueError as e:
                logger.debug(
                    f"Failed to parse as a singular input with {e}\nAttempting with nested fields."
                )

                overrides = self.try_to_process_nested_fields(
                    component_id, component_index, config_class, configuration
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
                    env_vars = {
                        f"{env_var_name}_{k}".upper(): v
                        for k, v in nested_override_value.items()
                    }
                    overrides.update(env_vars)
        return overrides

    def try_to_process_nested_fields(
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
            nums = set(field_override.keys())
            assert len(nums) == len(
                field_override.keys()
            ), "Non-unique item in override"
            assert (
                len(nums) == self.deployment_spec["number_of_agents"]
            ), "Not enough items in override"
            assert nums == set(
                range(0, self.deployment_spec["number_of_agents"])
            ), "Overrides incorrectly indexed"
            for override in field_override[component_index]:
                for nested_override, nested_value in override.items():
                    for (
                        nested_override_key,
                        nested_override_value,
                    ) in nested_value.items():
                        assert (
                            nested_override_key
                            in config_class.NESTED_FIELDS_ALLOWED_TO_UPDATE  # type: ignore
                        ), "Trying to override non-nested field."

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


class BaseDeployment:
    """Class to assist with generating deployments."""

    valory_application: str
    network: str
    number_of_agents: int

    def __init__(self, path_to_deployment_spec: str) -> None:
        """Initialize the Base Deployment."""
        self.overrides: list = []
        self.validator = DeploymentConfigValidator(
            schema_filename="deployments/deployment_schema.json"
        )
        with open(path_to_deployment_spec, "r", encoding="utf8") as file:
            for ix, document in enumerate(yaml.load_all(file, Loader=yaml.SafeLoader)):
                if ix == 0:
                    self.deployment_spec = document
                else:
                    self.overrides.append(document)

        self.validator.validate_deployment(self.deployment_spec, self.overrides)
        self.__dict__.update(self.deployment_spec)
        self.agent_public_id = PublicId.from_str(self.valory_application)
        self.agent_spec = self.load_agent()

    def _process_model_args_overrides(self, agent_n: int) -> Dict:
        """Generates env vars based on model overrides."""
        final_overrides = {}
        for component_configuration_json in self.overrides:
            _, overrides = self.validator.process_component_section(
                agent_n, component_configuration_json
            )
            final_overrides.update(overrides)
        return final_overrides

    def generate_agents(self) -> List:
        """Generate multiple agent."""
        return [self.generate_agent(i) for i in range(self.number_of_agents)]

    def generate_common_vars(self, agent_n: int) -> Dict:
        """Retrieve vars common for valory apps."""
        return {
            "AEA_KEY": KEYS[agent_n],
            "VALORY_APPLICATION": self.valory_application,
            "ABCI_HOST": f"abci{agent_n}" if self.network == "hardhat" else "",
            "MAX_PARTICIPANTS": self.number_of_agents,  # I believe that this is correct
            "TENDERMINT_URL": f"http://node{agent_n}:26657",
            "TENDERMINT_COM_URL": f"http://node{agent_n}:8080",
        }

    def generate_agent(self, agent_n: int) -> Dict[Any, Any]:
        """Generate next agent."""
        agent_vars = self.generate_common_vars(agent_n)
        if len(self.overrides) == 0:
            return agent_vars
        overrides = self._process_model_args_overrides(agent_n)
        agent_vars.update(overrides)
        return agent_vars

    def load_agent(self) -> List[Dict[str, str]]:
        """Using specified valory app, try to load the aea."""
        aea_project_path = self.locate_agent_from_package_directory()
        with open(aea_project_path, "r", encoding="utf8") as file:
            aea_json = list(yaml.safe_load_all(file))
        return aea_json

    def locate_agent_from_package_directory(self, local_registry: bool = True) -> str:
        """Using the deployment id, locate the registry and retrieve the path."""
        if local_registry is False:
            raise ValueError("Remote registry not yet supported, use local!")
        source_path = try_get_item_source_path(
            str(PACKAGES_DIRECTORY),
            self.agent_public_id.author,
            AGENTS,
            self.agent_public_id.name,
        )
        return str(Path(source_path) / DEFAULT_AEA_CONFIG_FILE)


class BaseDeploymentGenerator:
    """Base Deployment Class."""

    deployment: BaseDeployment
    output_name: str
    old_wd: str
    deployment_type: str

    def __init__(self, deployment_spec: BaseDeployment):
        """Initialise with only kwargs."""
        self.network_config = NETWORKS[self.deployment_type][deployment_spec.network]
        self.deployment_spec = deployment_spec
        self.config_dir = Path(CONFIG_DIRECTORY)
        self.output = ""

    def setup(self) -> None:
        """Set up the directory for the configuration to written to."""
        self.old_wd = os.getcwd()
        if self.config_dir.is_dir():
            rmtree(str(self.config_dir))
        self.config_dir.mkdir()

    def teardown(self) -> None:
        """Move back to original wd"""
        os.chdir(self.old_wd)

    @abc.abstractmethod
    def generate(self, valory_application: Type[BaseDeployment]) -> str:
        """Generate the deployment configuration."""

    @abc.abstractmethod
    def generate_config_tendermint(
        self, valory_application: Type[BaseDeployment]
    ) -> str:
        """Generate the deployment configuration."""

    def write_config(self) -> None:
        """Write output to build dir"""

        if not self.config_dir.is_dir():
            self.config_dir.mkdir()

        with open(self.config_dir / self.output_name, "w", encoding="utf8") as f:
            f.write(self.output)

    def get_deployment_network_configuration(
        self, agent_vars: List[Dict[str, Any]]
    ) -> List:
        """Retrieve the appropriate network configuration based on deployment & network."""
        for agent in agent_vars:
            agent.update(self.network_config)
        return agent_vars
