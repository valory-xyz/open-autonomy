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

"""Helpers for minting components"""

import json
from collections import OrderedDict
from pathlib import Path
from typing import Any, Dict, List, Optional, cast

from aea.configurations.constants import DEFAULT_README_FILE
from aea.configurations.data_types import PublicId
from aea.crypto.base import Crypto, LedgerApi
from aea.helpers.cid import CID
from aea.helpers.ipfs.base import IPFSHashOnly
from aea_cli_ipfs.ipfs_utils import IPFSTool
from requests.exceptions import ConnectionError as RequestsConnectionError

from autonomy.chain.base import ComponentRegistry, RegistriesManager
from autonomy.chain.config import ChainType
from autonomy.chain.exceptions import ComponentMintFailed, FailedToRetrieveTokenId


BASE16_HASH_PREFIX = "f01701220"
CONFIG_HASH_STRING_PREFIX = "0x"
UNIT_HASH_PREFIX = CONFIG_HASH_STRING_PREFIX + "{metadata_hash}"
DEFAULT_NFT_IMAGE_HASH = "bafybeiggnad44tftcrenycru2qtyqnripfzitv5yume4szbkl33vfd4abm"

ContractInterfaceType = Any


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
            "code_uri": f"ipfs://{package_hash}",
            "image": f"ipfs://{nft_image_hash}",
            "attributes": [{"trait_type": "version", "value": str(public_id.version)}],
        }
    )
    return json.dumps(obj=metadata)


def publish_metadata(
    public_id: PublicId,
    package_path: Path,
    nft_image_hash: str,
) -> str:
    """Publish service metadata."""

    ipfs_tool = IPFSTool()
    package_hash = IPFSHashOnly.get(file_path=str(package_path))
    metadata_string = serialize_metadata(
        package_hash=package_hash,
        public_id=public_id,
        description=Path(package_path, DEFAULT_README_FILE).read_text(encoding="utf-8"),
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


def verify_and_fetch_token_id_from_event(
    event: Dict,
    unit_type: RegistriesManager.UnitType,
    metadata_hash: str,
    ledger_api: LedgerApi,
) -> Optional[int]:
    """Verify and extract token id from a registry event"""
    event_args = event["args"]
    if event_args["uType"] == unit_type.value:
        hash_bytes32 = cast(bytes, event_args["unitHash"]).hex()
        unit_hash_bytes = UNIT_HASH_PREFIX.format(metadata_hash=hash_bytes32).encode()
        metadata_hash_bytes = ledger_api.api.toBytes(text=metadata_hash)
        if unit_hash_bytes == metadata_hash_bytes:
            return cast(int, event_args["unitId"])

    return None


def mint_component(
    ledger_api: LedgerApi,
    crypto: Crypto,
    metadata_hash: str,
    component_type: RegistriesManager.UnitType,
    chain_type: ChainType,
    dependencies: Optional[List[int]] = None,
) -> Optional[int]:
    """Publish component on-chain."""

    registries_manager = RegistriesManager(
        ledger_api=ledger_api,
        crypto=crypto,
        chain_type=chain_type,
    )

    component_registry = ComponentRegistry(
        ledger_api=ledger_api,
        crypto=crypto,
        chain_type=chain_type,
    )

    try:
        registries_manager.create(
            component_type=component_type,
            metadata_hash=metadata_hash,
            dependencies=dependencies,
        )
    except RequestsConnectionError as e:
        raise ComponentMintFailed("Cannot connect to the given RPC") from e

    try:
        for event_dict in component_registry.get_create_unit_event_filter():
            token_id = verify_and_fetch_token_id_from_event(
                event=event_dict,
                unit_type=component_type,
                metadata_hash=metadata_hash,
                ledger_api=ledger_api,
            )
            if token_id is not None:
                return token_id
    except RequestsConnectionError as e:
        raise FailedToRetrieveTokenId(
            "Connection interrupted while waiting for the unitId emit event"
        ) from e

    return None
