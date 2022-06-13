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

from pathlib import Path
from typing import Dict

import yaml
from aea.configurations.base import (
    ConnectionConfig,
    ContractConfig,
    ProtocolConfig,
    SkillConfig,
)

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


def load_service_config(service_path: Path) -> Service:
    """Load service config from the path."""

    with open(
        service_path / Service.default_configuration_filename, "r", encoding="utf-8"
    ) as fp:
        service_config, *overrides = yaml.load_all(fp, Loader=yaml.SafeLoader)

    Service.validate_config_data(service_config)
    service_config["license_"] = service_config.pop("license")

    service = Service(**service_config)
    service.overrides = overrides

    return service
