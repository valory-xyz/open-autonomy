# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022-2026 Valory AG
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
from aea.configurations.loader import parse_service_yaml
from aea.helpers.env_vars import apply_env_variables
from aea.helpers.io import open_file

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
            "usage of environment variables is default now.",
            DeprecationWarning,
            stacklevel=2,
        )

    with open_file(
        service_path / Service.default_configuration_filename, "r", encoding="utf-8"
    ) as fp:
        service_config, overrides = parse_service_yaml(fp)

    # Here we apply the environment variables to base service config only.
    # The overrides keep their raw form; env variables are applied on them
    # when they are processed for export.
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
