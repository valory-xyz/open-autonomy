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

"""Test metadata helpers."""

import tempfile
from pathlib import Path
from unittest import mock

import pytest
from aea.configurations.constants import DEFAULT_README_FILE
from aea.configurations.data_types import PackageId, PublicId
from aea.helpers.base import IPFSHash

from autonomy.chain.metadata import NFTHashOrPath, publish_metadata, serialize_metadata
from autonomy.chain.mint import DEFAULT_NFT_IMAGE_HASH

from tests.conftest import DATA_DIR
from tests.test_autonomy.test_chain.base import DUMMY_HASH


def test_serialize_metadata() -> None:
    """Test serialize metadata."""
    expected_string = """{"name":"skill/author/name/latest","description":"Some package","code_uri":"ipfs://bafybei0000000000000000000000000000000000000000000000000000","image":"ipfs://bafybeiggnad44tftcrenycru2qtyqnripfzitv5yume4szbkl33vfd4abm","attributes":[{"trait_type":"version","value":"latest"}]}"""
    metadata_string = serialize_metadata(
        package_hash=DUMMY_HASH,
        package_id=PackageId(
            package_type="skill", public_id=PublicId(author="author", name="name")
        ),
        description="Some package",
        nft_image_hash=DEFAULT_NFT_IMAGE_HASH,
    )

    assert metadata_string == expected_string


@pytest.mark.parametrize(
    "nft",
    (
        IPFSHash(DEFAULT_NFT_IMAGE_HASH),
        DATA_DIR / "nft.png",
    ),
)
def test_publish_metadata(nft: NFTHashOrPath) -> None:
    """Test publish metadata tool with dummy config."""

    expected_hash = "0x338a96df1d172c1d6f11a0460d075d80b62eea67134b2d0a52a7df34495d45d1"
    with mock.patch(
        "autonomy.chain.metadata.IPFSHashOnly.get", return_value=DUMMY_HASH
    ):
        with tempfile.TemporaryDirectory() as temp_dir:
            package_path = Path(temp_dir)
            (package_path / DEFAULT_README_FILE).write_text("Description")

            metadata_hash, _ = publish_metadata(
                package_id=PackageId(
                    package_type="skill",
                    public_id=PublicId(author="author", name="name"),
                ),
                package_path=package_path,
                nft=nft,
                description="",
            )

    assert metadata_hash == expected_hash
