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

"""Chain interaction base classes."""

from enum import Enum
from typing import Optional

from aea.configurations.data_types import PublicId
from aea.contracts.base import Contract

from autonomy.chain.constants import (
    AGENT_REGISTRY_CONTRACT,
    COMPONENT_REGISTRY_CONTRACT,
    CONTRACTS_DIR_FRAMEWORK,
    CONTRACTS_DIR_LOCAL,
    REGISTRIES_MANAGER_CONTRACT,
)


class UnitType(Enum):
    """Unit type."""

    COMPONENT = 0
    AGENT = 1


class RegistryContracts:
    """On chain registry contracts helper"""

    _registries_manager: Optional[Contract] = None
    _component_registry: Optional[Contract] = None
    _agent_registry: Optional[Contract] = None

    @staticmethod
    def get_contract(public_id: PublicId) -> Contract:
        """Load contract for given public id."""

        # check if a local package is available
        contract_dir = CONTRACTS_DIR_LOCAL / public_id.name
        if contract_dir.exists():
            return Contract.from_dir(directory=contract_dir)

        # if local package is not available use one from the data directory
        contract_dir = CONTRACTS_DIR_FRAMEWORK / public_id.name
        if not contract_dir.exists():
            raise FileNotFoundError(
                "Contract package not found in the distribution, please reinstall the package"
            )
        return Contract.from_dir(directory=contract_dir)

    @classmethod
    def registries_manager(
        cls,
    ) -> Contract:
        """Returns an instance of the registries manager contract."""
        if cls._registries_manager is None:
            cls._registries_manager = cls.get_contract(
                public_id=REGISTRIES_MANAGER_CONTRACT
            )

        return cls._registries_manager

    @classmethod
    def component_registry(
        cls,
    ) -> Contract:
        """Returns an instance of the registries manager contract."""
        if cls._component_registry is None:
            cls._component_registry = cls.get_contract(
                public_id=COMPONENT_REGISTRY_CONTRACT
            )

        return cls._component_registry

    @classmethod
    def agent_registry(
        cls,
    ) -> Contract:
        """Returns an instance of the registries manager contract."""
        if cls._agent_registry is None:
            cls._agent_registry = cls.get_contract(
                public_id=AGENT_REGISTRY_CONTRACT,
            )

        return cls._agent_registry
