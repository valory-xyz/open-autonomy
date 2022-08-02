# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2022 Valory AG
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

"""Helpers for contract tests."""

from pathlib import Path
from typing import cast

from aea.configurations.base import ComponentType, ContractConfig
from aea.configurations.loader import load_component_configuration
from aea.contracts.base import Contract, contract_registry


def get_register_contract(directory: Path) -> Contract:
    """Get and register the erc1155 contract package."""
    configuration = load_component_configuration(ComponentType.CONTRACT, directory)
    configuration._directory = directory  # pylint: disable=protected-access
    configuration = cast(ContractConfig, configuration)

    if str(configuration.public_id) not in contract_registry.specs:
        # load contract into sys modules
        Contract.from_config(configuration)

    contract = contract_registry.make(str(configuration.public_id))
    return contract
