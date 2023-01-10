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

from aea.configurations.data_types import PublicId
from aea.helpers.cid import CID
from aea.helpers.ipfs.base import IPFSHashOnly
from aea_cli_ipfs.ipfs_utils import IPFSTool


IPFS_URI_PREFIX = "ipfs://"
BASE16_HASH_PREFIX = "f01701220"
CONFIG_HASH_STRING_PREFIX = "0x"
UNIT_HASH_PREFIX = CONFIG_HASH_STRING_PREFIX + "{metadata_hash}"


def serialize_metadata(
    package_hash: str,
    public_id: PublicId,
    description: str,
    nft_image_hash: str,
) -> str:
    """Serialize metadata."""
    metadata = OrderedDict(
        {
            "name": f"{public_id.author}/{public_id.name}",
            "description": description,
            "code_uri": f"{IPFS_URI_PREFIX}{package_hash}",
            "image": f"ipfs://{nft_image_hash}",
            "attributes": [{"trait_type": "version", "value": str(public_id.version)}],
        }
    )
    return json.dumps(obj=metadata)


def publish_metadata(
    public_id: PublicId,
    package_path: Path,
    nft_image_hash: str,
    description: str,
) -> str:
    """Publish service metadata."""

    ipfs_tool = IPFSTool()
    package_hash = IPFSHashOnly.get(file_path=str(package_path))
    metadata_string = serialize_metadata(
        package_hash=package_hash,
        public_id=public_id,
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

    return UNIT_HASH_PREFIX.format(metadata_hash=metadata_hash)
