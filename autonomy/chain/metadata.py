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

"""Metadata helpers."""

import json
from collections import OrderedDict
from pathlib import Path
from typing import Tuple, Union

from aea.configurations.data_types import PackageId
from aea.helpers.base import IPFSHash
from aea.helpers.cid import CID, to_v1
from aea.helpers.ipfs.base import IPFSHashOnly
from aea_cli_ipfs.ipfs_utils import IPFSTool


IPFS_URI_PREFIX = "ipfs://"
BASE16_HASH_PREFIX = "f01701220"
CONFIG_HASH_STRING_PREFIX = "0x"
UNIT_HASH_PREFIX = CONFIG_HASH_STRING_PREFIX + "{metadata_hash}"

NFTHashOrPath = Union[Path, IPFSHash]


def serialize_metadata(
    package_hash: str,
    package_id: PackageId,
    description: str,
    nft_image_hash: str,
) -> str:
    """Serialize metadata."""
    metadata = OrderedDict(
        {
            "name": package_id.to_uri_path,
            "description": description,
            "code_uri": f"{IPFS_URI_PREFIX}{package_hash}",
            "image": f"ipfs://{nft_image_hash}",
            "attributes": [{"trait_type": "version", "value": str(package_id.version)}],
        }
    )
    return json.dumps(obj=metadata, separators=(",", ":"))


def publish_metadata(
    package_id: PackageId,
    package_path: Path,
    nft: NFTHashOrPath,
    description: str,
) -> Tuple[str, str]:
    """Publish service metadata."""
    ipfs_tool = IPFSTool()
    if isinstance(nft, IPFSHash):
        nft_image_hash = str(nft)
    else:
        _, nft_image_hash, _ = ipfs_tool.add(
            str(nft.resolve()),
            wrap_with_directory=False,
        )
        nft_image_hash = to_v1(nft_image_hash)

    package_hash = IPFSHashOnly.get(file_path=str(package_path))
    metadata_string = serialize_metadata(
        package_hash=package_hash,
        package_id=package_id,
        description=description,
        nft_image_hash=nft_image_hash,
    )

    metadata_hash = ipfs_tool.client.add_str(metadata_string)
    metadata_hash = (
        CID.from_string(metadata_hash)
        .to_v1()
        .encode("base16")
        .decode()
        .replace(BASE16_HASH_PREFIX, "")
    )
    return UNIT_HASH_PREFIX.format(metadata_hash=metadata_hash), metadata_string
