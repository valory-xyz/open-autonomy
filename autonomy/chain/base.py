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

from aea.configurations.data_types import PublicId
from aea.contracts.base import Contract
from aea.crypto.base import Crypto, LedgerApi

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

    def __init__(self) -> None:
        """Initialize object."""

        self._registries_manager = None
        self._component_registry = None
        self._agent_registry = None

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

    @property
    def registries_manager(
        self,
    ) -> Contract:
        """Returns an instance of the registries manager contract."""
        if self._registries_manager is None:
            self._registries_manager = self.get_contract(
                public_id=REGISTRIES_MANAGER_CONTRACT
            )

        return self._registries_manager

    @property
    def component_registry(
        self,
    ) -> Contract:
        """Returns an instance of the registries manager contract."""
        if self._component_registry is None:
            self._component_registry = self.get_contract(
                public_id=COMPONENT_REGISTRY_CONTRACT
            )

        return self._component_registry

    @property
    def agent_registry(
        self,
    ) -> Contract:
        """Returns an instance of the registries manager contract."""
        if self._agent_registry is None:
            self._agent_registry = self.get_contract(
                public_id=AGENT_REGISTRY_CONTRACT,
            )

        return self._agent_registry
