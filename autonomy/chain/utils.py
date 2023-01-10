# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2023 Valory AG
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

"""Utility functions."""
from json import JSONDecodeError
from typing import Dict, List

from aea.configurations.base import PackageConfiguration
from aea.configurations.data_types import PublicId
from aea.crypto.base import LedgerApi
from requests import get as r_get
from requests.exceptions import ConnectionError

from autonomy.chain.base import RegistryContracts
from autonomy.chain.exceptions import FailedToRetrieveComponentMetadata, DependencyError
from autonomy.chain.metadata import IPFS_URI_PREFIX


def get_ipfs_hash_from_uri(uri: str) -> None:
    """Split IPFS hash from the ipfs uri"""

    return uri.replace(IPFS_URI_PREFIX, "")


def resolve_component_id(
    registry_contracts: RegistryContracts,
    ledger_api: LedgerApi,
    contract_address: str,
    token_id: int,
) -> Dict:
    """Resolve component ID"""

    metadata_uri = registry_contracts.component_registry.get_token_uri(
        ledger_api=ledger_api,
        contract_address=contract_address,
        token_id=token_id,
    )

    try:
        return r_get(url=metadata_uri).json()
    except (ConnectionError, JSONDecodeError) as e:
        raise FailedToRetrieveComponentMetadata() from e


def verify_component_dependencies(
    registry_contracts: RegistryContracts,
    ledger_api: LedgerApi,
    contract_address: str,
    dependencies: List[int],
    package_configuration: PackageConfiguration,
    skip_hash_check: bool = False,
) -> None:
    """Verify package dependencies using on-chain metadata."""

    public_id_to_hash: Dict[PublicId, str] = {}
    for dependency in package_configuration.package_dependencies:
        public_id_to_hash[dependency.public_id.to_any()] = dependency.package_hash

    for dependency_id in dependencies:
        component_metadata = resolve_component_id(
            registry_contracts=registry_contracts,
            contract_address=contract_address,
            ledger_api=ledger_api,
            token_id=dependency_id,
        )
        component_public_id = PublicId.from_str(component_metadata["name"]).to_any()
        if component_public_id not in public_id_to_hash:
            raise DependencyError(
                f"On chain dependency with id {dependency_id} not found in the local package configuration"
            )

        package_hash = public_id_to_hash.pop(component_public_id)
        if skip_hash_check:
            continue

        if package_hash != get_ipfs_hash_from_uri(uri=component_metadata["code_uri"]):
            raise DependencyError(
                "Package hash does not match for the on chain package and the local package"
            )

    if len(public_id_to_hash):
        missing_deps = list(map(str, public_id_to_hash.keys()))
        raise DependencyError(
            f"Please provide on chain ID as dependency for following packages; {missing_deps}"
        )
