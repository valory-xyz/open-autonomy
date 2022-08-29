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

import os
from pathlib import Path
from typing import Dict, List, cast

from aea.configurations.base import (
    ConnectionConfig,
    ContractConfig,
    ProtocolConfig,
    SkillConfig,
)
from aea.helpers.env_vars import apply_env_variables
from aea.helpers.io import open_file
from aea.helpers.yaml_utils import yaml_load_all

from autonomy.configurations.base import Service


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

    with open_file(
        service_path / Service.default_configuration_filename, "r", encoding="utf-8"
    ) as fp:
        data = yaml_load_all(fp)

    if substitute_env_vars:
        data = cast(List[Dict], apply_env_variables(data, env_variables=os.environ))

    service_config, *overrides = data
    Service.validate_config_data(service_config)
    service_config["license_"] = service_config.pop("license")

    service = Service(**service_config)
    service.overrides = overrides

    return service
