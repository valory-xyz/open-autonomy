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

"""Test utils."""

import re
from typing import Dict
from unittest import mock

import pytest
from aea.configurations.data_types import PackageId, PublicId

from autonomy.chain.exceptions import DependencyError
from autonomy.chain.utils import (
    get_ipfs_hash_from_uri,
    parse_public_id_from_metadata,
    verify_component_dependencies,
    verify_service_dependencies,
)

from tests.test_autonomy.test_chain.base import DUMMY_HASH


def get_dummy_metadata(
    name: str = "valory/package",
    description: str = "description",
    code_uri: str = "code_uri",
    nft_hash: str = "nft_hash",
    version: str = "0.1.0",
) -> Dict:
    """Get dummy metadata."""

    return {
        "name": name,
        "description": description,
        "code_uri": code_uri,
        "image": nft_hash,
        "attributes": [{"trait_type": "version", "value": version}],
    }


def test_get_ipfs_hash_from_uri() -> None:
    """Test `get_ipfs_hash_from_uri` method"""

    assert get_ipfs_hash_from_uri("ipfs://SOME_HASH") == "SOME_HASH"


def test_verify_component_dependencies_no_dep_found_locally() -> None:
    """Test `verify_component_dependencies`"""

    with mock.patch(
        "autonomy.chain.utils.resolve_component_id", return_value=get_dummy_metadata()
    ), pytest.raises(
        DependencyError,
        match="On chain dependency with id 0 and public ID valory/package:any not found in the local package configuration",
    ):
        verify_component_dependencies(
            ledger_api=mock.MagicMock(),
            contract_address="0xdummy_contract",
            dependencies=[
                0,
            ],
            package_configuration=mock.MagicMock(package_dependencies=[]),
        )


def test_verify_component_dependencies_no_dep_found_on_chain() -> None:
    """Test `verify_component_dependencies`"""

    with pytest.raises(
        DependencyError,
        match=re.escape(
            "Please provide on chain ID as dependency for following packages; ['author/package:any']"
        ),
    ):
        verify_component_dependencies(
            ledger_api=mock.MagicMock(),
            contract_address="0xdummy_contract",
            dependencies=[],
            package_configuration=mock.MagicMock(
                package_dependencies=[
                    PackageId.from_uri_path("skill/author/package/0.1.0").with_hash(
                        DUMMY_HASH
                    )
                ]
            ),
        )


def test_verify_component_dependencies_hash_dont_match() -> None:
    """Test `verify_component_dependencies`"""

    with mock.patch(
        "autonomy.chain.utils.resolve_component_id",
        return_value=get_dummy_metadata(),
    ), pytest.raises(
        DependencyError,
        match="Package hash does not match for the on chain package and the local package",
    ):
        verify_component_dependencies(
            ledger_api=mock.MagicMock(),
            contract_address="0xdummy_contract",
            dependencies=[
                0,
            ],
            package_configuration=mock.MagicMock(
                package_dependencies=[
                    PackageId.from_uri_path("skill/valory/package/0.1.0").with_hash(
                        DUMMY_HASH
                    )
                ]
            ),
        )


def test_verify_component_dependencies_multiple_component_with_same_public_id() -> None:
    """Test `verify_component_dependencies`"""

    phash_1 = DUMMY_HASH.replace("0", "1")
    phash_2 = DUMMY_HASH.replace("0", "2")

    with mock.patch(
        "autonomy.chain.utils.resolve_component_id",
        side_effect=[
            get_dummy_metadata(code_uri=phash_1),
            get_dummy_metadata(code_uri=phash_2),
        ],
    ):
        verify_component_dependencies(
            ledger_api=mock.MagicMock(),
            contract_address="0xdummy_contract",
            dependencies=[0, 1],
            package_configuration=mock.MagicMock(
                package_dependencies=[
                    PackageId.from_uri_path(
                        "connection/valory/package/0.1.0",
                    ).with_hash(phash_1),
                    PackageId.from_uri_path(
                        "contract/valory/package/0.1.0",
                    ).with_hash(phash_2),
                ]
            ),
        )


def test_verify_component_dependencies_multiple_component_with_same_public_id_skip_hash_check() -> (
    None
):
    """Test `verify_component_dependencies`"""

    phash_1 = DUMMY_HASH.replace("0", "1")
    phash_2 = DUMMY_HASH.replace("0", "2")

    with mock.patch(
        "autonomy.chain.utils.resolve_component_id",
        side_effect=[
            get_dummy_metadata(code_uri=phash_1),
            get_dummy_metadata(code_uri=phash_2),
        ],
    ):
        verify_component_dependencies(
            ledger_api=mock.MagicMock(),
            contract_address="0xdummy_contract",
            dependencies=[0, 1],
            package_configuration=mock.MagicMock(
                package_dependencies=[
                    PackageId.from_uri_path(
                        "connection/valory/package/0.1.0",
                    ).with_hash(phash_1),
                    PackageId.from_uri_path(
                        "contract/valory/package/0.1.0",
                    ).with_hash(phash_2),
                ]
            ),
            skip_hash_check=True,
        )


def test_verify_component_dependencies_multiple_component_with_same_public_id_fail() -> (
    None
):
    """Test `verify_component_dependencies`"""

    phash_1 = DUMMY_HASH.replace("0", "1")
    phash_2 = DUMMY_HASH.replace("0", "2")

    with mock.patch(
        "autonomy.chain.utils.resolve_component_id",
        side_effect=[
            get_dummy_metadata(code_uri=phash_1),
            get_dummy_metadata(code_uri="phash_2"),
        ],
    ), pytest.raises(
        DependencyError,
        match="Package hash does not match for the on chain package and the local package; Dependency=1",
    ):
        verify_component_dependencies(
            ledger_api=mock.MagicMock(),
            contract_address="0xdummy_contract",
            dependencies=[0, 1],
            package_configuration=mock.MagicMock(
                package_dependencies=[
                    PackageId.from_uri_path(
                        "connection/valory/package/0.1.0",
                    ).with_hash(phash_1),
                    PackageId.from_uri_path(
                        "contract/valory/package/0.1.0",
                    ).with_hash(phash_2),
                ]
            ),
        )


def test_verify_service_dependencies_dep_not_found() -> None:
    """Test verify `verify_service_dependencies` method"""

    with mock.patch(
        "autonomy.chain.utils.resolve_component_id", return_value=get_dummy_metadata()
    ), pytest.raises(
        DependencyError,
        match="On chain ID of the agent does not match with the one in the service configuration",
    ):
        verify_service_dependencies(
            ledger_api=mock.MagicMock(),
            contract_address="0xdummy_contract",
            agent_id=0,
            service_configuration=mock.MagicMock(),
        )


def test_verify_service_dependencies_hash_dont_match() -> None:
    """Test verify `verify_service_dependencies` method"""

    with mock.patch(
        "autonomy.chain.utils.resolve_component_id", return_value=get_dummy_metadata()
    ), pytest.raises(
        DependencyError,
        match="Package hash does not match for the on chain package and the local package",
    ):
        verify_service_dependencies(
            ledger_api=mock.MagicMock(),
            contract_address="0xdummy_contract",
            agent_id=0,
            service_configuration=mock.MagicMock(
                agent=PublicId("valory", "package", package_hash=DUMMY_HASH)
            ),
        )


@pytest.mark.parametrize(
    "public_id_string",
    [
        "author/package_name",
        "component_type/author/name",
        "skill/author/name/0.1.0",
    ],
)
def test_parse_public_id_from_metadata(public_id_string: str) -> None:
    """Test verify `parse_public_id_from_metadata` method"""

    public_id = parse_public_id_from_metadata(
        id_string=public_id_string,
    )

    assert isinstance(public_id, PublicId)


def test_parse_public_id_from_metadata_fail() -> None:
    """Test verify `parse_public_id_from_metadata` method"""

    with pytest.raises(DependencyError, match="Invalid package name found `public_id`"):
        parse_public_id_from_metadata(
            id_string="public_id",
        )
