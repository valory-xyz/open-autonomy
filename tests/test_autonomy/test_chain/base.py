# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2023-2024 Valory AG
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

"""Test tools for CLI commands that use `autonomy.chain`"""

import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
from unittest import mock

import pytest
from aea.configurations.data_types import PackageId, PackageType, PublicId
from aea.crypto.base import Crypto, LedgerApi
from aea.helpers.base import IPFSHash
from aea_test_autonomy.configurations import ETHEREUM_KEY_DEPLOYER
from aea_test_autonomy.docker.base import skip_docker_tests
from aea_test_autonomy.fixture_helpers import registries_scope_class  # noqa: F401

from autonomy.chain.base import registry_contracts
from autonomy.chain.config import ChainType, ContractConfigs
from autonomy.chain.metadata import publish_metadata
from autonomy.chain.mint import DEFAULT_NFT_IMAGE_HASH, MintManager, UnitType
from autonomy.chain.service import ServiceManager
from autonomy.chain.subgraph.client import SubgraphClient
from autonomy.chain.utils import parse_public_id_from_metadata, resolve_component_id
from autonomy.cli.helpers.chain import MintHelper, OnChainHelper
from autonomy.cli.packages import get_package_manager

from tests.conftest import DATA_DIR
from tests.test_autonomy.test_cli.base import BaseCliTest


PACKAGES_DIR = DATA_DIR / "dummy_packages"
DUMMY_PACKAGE_MANAGER = get_package_manager(packages_dir=PACKAGES_DIR)
DUMMY_AUTHOR = "dummy_author"
DUMMY_PROTOCOL = PackageId(
    package_type=PackageType.PROTOCOL,
    public_id=PublicId(author=DUMMY_AUTHOR, name="dummy_protocol", version="0.1.0"),
)
DUMMY_CONTRACT = PackageId(
    package_type=PackageType.CONTRACT,
    public_id=PublicId(author=DUMMY_AUTHOR, name="dummy_contract", version="0.1.0"),
)
DUMMY_CONNECTION = PackageId(
    package_type=PackageType.CONNECTION,
    public_id=PublicId(author=DUMMY_AUTHOR, name="dummy_connection", version="0.1.0"),
)
DUMMY_SKILL = PackageId(
    package_type=PackageType.SKILL,
    public_id=PublicId(author=DUMMY_AUTHOR, name="dummy_skill", version="0.1.0"),
)
DUMMY_AGENT = PackageId(
    package_type=PackageType.AGENT,
    public_id=PublicId(author=DUMMY_AUTHOR, name="dummy_agent", version="0.1.0"),
)
DUMMY_SERVICE = PackageId(
    package_type=PackageType.SERVICE,
    public_id=PublicId(author=DUMMY_AUTHOR, name="dummy_service", version="0.1.0"),
)

DUMMY_HASH = "bafybei0000000000000000000000000000000000000000000000000000"
NUMBER_OF_SLOTS_PER_AGENT = 4
COST_OF_BOND_FOR_AGENT = 1000
THRESHOLD = 3
AGENT_ID = 1

DEFAULT_SERVICE_MINT_PARAMETERS = (
    "-a",
    str(AGENT_ID),
    "-n",
    str(NUMBER_OF_SLOTS_PER_AGENT),
    "-c",
    str(COST_OF_BOND_FOR_AGENT),
    "--threshold",
    str(THRESHOLD),
)


def patch_subgraph(
    response: List,
    method: str = "get_component_by_token",
) -> Any:
    """Patch subgraph client."""
    return mock.patch.object(
        SubgraphClient,
        attribute=method,
        return_value={"units": response},
    )


def _fetch_component_dependencies(cls: Any) -> Any:
    cls.dependencies = [1, 2]
    return cls


def patch_component_verification() -> Any:
    """Patch component verificaation."""
    return mock.patch.object(
        MintHelper,
        "fetch_component_dependencies",
        new=_fetch_component_dependencies,
    )


@skip_docker_tests
@pytest.mark.usefixtures("registries_scope_class")
class BaseChainInteractionTest(BaseCliTest):
    """Base chain interaction test"""

    ledger_api: LedgerApi
    crypto: Crypto
    chain_type: ChainType = ChainType.LOCAL
    mint_manager: MintManager
    service_manager: ServiceManager

    key_file: Path = ETHEREUM_KEY_DEPLOYER

    def setup(self) -> None:
        """Setup test."""
        super().setup()
        self.cli_runner.mix_stderr = False

    @classmethod
    def setup_class(cls) -> None:
        """Setup class."""
        super().setup_class()

        cls.ledger_api, cls.crypto = OnChainHelper.get_ledger_and_crypto_objects(
            chain_type=cls.chain_type,
            key=cls.key_file,
        )
        cls.mint_manager = MintManager(
            ledger_api=cls.ledger_api,
            crypto=cls.crypto,
            chain_type=cls.chain_type,
        )
        cls.service_manager = ServiceManager(
            ledger_api=cls.ledger_api,
            crypto=cls.crypto,
            chain_type=cls.chain_type,
        )

    @staticmethod
    def extract_token_id_from_output(output: str) -> int:
        """Extract token ID from output"""

        matches = re.findall(r"Token ID: (\d+)", output)
        assert len(matches) > 0

        *_, token_id = matches
        return int(token_id)

    def verify_owner_address(
        self, token_id: int, owner: str, package_id: PackageId
    ) -> None:
        """Verify minted token id"""

        if package_id.package_type == PackageType.SERVICE:
            on_chain_owner = (
                registry_contracts.service_registry.get_instance(
                    ledger_api=self.ledger_api,
                    contract_address=ContractConfigs.service_registry.contracts[
                        ChainType.LOCAL
                    ],
                )
                .functions.ownerOf(token_id)
                .call()
            )
        elif package_id.package_type == PackageType.AGENT:
            on_chain_owner = (
                registry_contracts.component_registry.get_instance(
                    ledger_api=self.ledger_api,
                    contract_address=ContractConfigs.agent_registry.contracts[
                        ChainType.LOCAL
                    ],
                )
                .functions.ownerOf(token_id)
                .call()
            )
        else:
            on_chain_owner = (
                registry_contracts.component_registry.get_instance(
                    ledger_api=self.ledger_api,
                    contract_address=ContractConfigs.component_registry.contracts[
                        ChainType.LOCAL
                    ],
                )
                .functions.ownerOf(token_id)
                .call()
            )

        assert (
            owner.lower() == on_chain_owner.lower()
        ), f"Owner verification failed; Owner address={owner}; On chain owner address={on_chain_owner}"

    def verify_minted_token_id(self, token_id: int, package_id: PackageId) -> None:
        """Verify minted token id"""

        is_agent = package_id.package_type == PackageType.AGENT
        is_service = package_id.package_type == PackageType.SERVICE

        if is_service:
            contract_address = ContractConfigs.service_registry.contracts[
                ChainType.LOCAL
            ]
        elif is_agent:
            contract_address = ContractConfigs.agent_registry.contracts[ChainType.LOCAL]
        else:
            contract_address = ContractConfigs.component_registry.contracts[
                ChainType.LOCAL
            ]

        metadata = resolve_component_id(
            ledger_api=self.ledger_api,
            contract_address=contract_address,
            token_id=token_id,
            is_agent=is_agent,
            is_service=is_service,
        )

        minted_public_id = parse_public_id_from_metadata(metadata["name"])
        assert package_id.public_id.to_any() == minted_public_id.to_any(), (
            minted_public_id,
            package_id.public_id,
        )

    @staticmethod
    def verify_and_remove_metadata_file(token_id: int) -> None:
        """Verify and remove the metadata file."""

        metadata_file = Path(f"{token_id}.json").resolve()
        assert metadata_file.exists()
        os.remove(metadata_file)

    def mint_component(
        self,
        package_id: PackageId,
        dependencies: Optional[List[int]] = None,
        service_mint_parameters: Optional[Dict] = None,
    ) -> int:
        """Mint component and return token id"""

        package_path = DUMMY_PACKAGE_MANAGER.package_path_from_package_id(
            package_id=package_id
        )
        metadata_hash, _ = publish_metadata(
            package_id=package_id,
            package_path=package_path,
            nft=IPFSHash(DEFAULT_NFT_IMAGE_HASH),
            description="Dummy package for testing",
        )
        if package_id.package_type == PackageType.SERVICE:
            assert (
                service_mint_parameters is not None
            ), "Please provide service mint parameters"
            token_id = self.mint_manager.mint_service(
                metadata_hash=metadata_hash,
                **service_mint_parameters,
            )
        else:
            token_id = self.mint_manager.mint_component(
                metadata_hash=metadata_hash,
                component_type=(
                    UnitType.AGENT
                    if package_id.package_type == PackageType.AGENT
                    else UnitType.COMPONENT
                ),
                dependencies=dependencies,
            )

        assert isinstance(token_id, int)
        return token_id
