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

"""Test utils."""

from typing import Dict

import pytest
from aea.configurations.data_types import PublicId

from autonomy.chain.exceptions import DependencyError
from autonomy.chain.utils import get_ipfs_hash_from_uri, parse_public_id_from_metadata


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
