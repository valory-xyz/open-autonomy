# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022-2023 Valory AG
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

import os
from pathlib import Path
from typing import Dict
from warnings import warn

from aea.configurations.base import (
    ConnectionConfig,
    ContractConfig,
    ProtocolConfig,
    SkillConfig,
)
from aea.helpers.env_vars import apply_env_variables
from aea.helpers.io import open_file
from aea.helpers.yaml_utils import yaml_load_all

from autonomy.configurations.base import Service, load_dependencies


COMPONENT_CONFIGS: Dict = {
    component.package_type.value: component  # type: ignore
    for component in [
        ContractConfig,
        SkillConfig,
        ProtocolConfig,
        ConnectionConfig,
    ]
}


def load_service_config(
    service_path: Path, substitute_env_vars: bool = False
) -> Service:
    """Load service config from the path."""

    if substitute_env_vars:
        warn(
            "`substitute_env_vars` argument is deprecated and will be removed in v1.0.0, "
            "usage of environment varibales is default now.",
            DeprecationWarning,
            stacklevel=2,
        )

    # TODO: align with open-aea _load_service_config & handle data == None and other validation errors
    with open_file(
        service_path / Service.default_configuration_filename, "r", encoding="utf-8"
    ) as fp:
        data = yaml_load_all(fp)

    # Here we apply the environment variables to base service config only
    # We apply the environment variables to the overrides when processing
    # them to export as environment variables
    service_config, *overrides = data
    service_config = apply_env_variables(
        service_config, env_variables=os.environ.copy()
    )

    if "dependencies" in service_config:
        dependencies = load_dependencies(
            dependencies=service_config.pop("dependencies")
        )
    else:
        dependencies = {}
        warn(
            "`dependencies` parameter not defined in the service",
            FutureWarning,
            stacklevel=2,
        )
        print("WARNING: `dependencies` parameter not defined in the service")

    Service.validate_config_data(service_config)
    service_config["license_"] = service_config.pop("license")

    service = Service(**service_config, dependencies=dependencies)
    service.overrides = overrides

    return service
