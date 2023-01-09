# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022-2023 Valory AG
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
from typing import Dict, List, Optional, cast

from aea.configurations.constants import DEFAULT_README_FILE
from aea.configurations.data_types import PublicId
from aea.contracts.base import Contract
from aea.crypto.base import Crypto, LedgerApi
from aea.helpers.cid import CID
from aea.helpers.ipfs.base import IPFSHashOnly
from aea_cli_ipfs.ipfs_utils import IPFSTool
from requests.exceptions import ConnectionError as RequestsConnectionError

from autonomy.chain.base import UnitType
from autonomy.chain.config import ChainType, ContractConfigs
from autonomy.chain.constants import (
    COMPONENT_REGISTRY_CONTRACT,
    CONTRACTS_DIR_FRAMEWORK,
    CONTRACTS_DIR_LOCAL,
    REGISTRIES_MANAGER_CONTRACT,
)
from autonomy.chain.exceptions import ComponentMintFailed, FailedToRetrieveTokenId


BASE16_HASH_PREFIX = "f01701220"
CONFIG_HASH_STRING_PREFIX = "0x"
UNIT_HASH_PREFIX = CONFIG_HASH_STRING_PREFIX + "{metadata_hash}"
DEFAULT_NFT_IMAGE_HASH = "bafybeiggnad44tftcrenycru2qtyqnripfzitv5yume4szbkl33vfd4abm"


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


def verify_and_fetch_token_id_from_event(
    event: Dict,
    unit_type: UnitType,
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


def transact(ledger_api: LedgerApi, crypto: Crypto, tx: Dict) -> Dict:
    """Make a transaction and return a receipt"""

    signed_tx = ledger_api.api.eth.account.sign_transaction(
        tx,
        private_key=crypto.private_key,
    )
    ledger_api.api.eth.send_raw_transaction(signed_tx.rawTransaction)
    tx_hash = ledger_api.api.toHex(ledger_api.api.keccak(signed_tx.rawTransaction))

    return ledger_api.api.eth.wait_for_transaction_receipt(tx_hash)


def mint_component(
    ledger_api: LedgerApi,
    crypto: Crypto,
    metadata_hash: str,
    component_type: UnitType,
    chain_type: ChainType,
    dependencies: Optional[List[int]] = None,
) -> Optional[int]:
    """Publish component on-chain."""

    registries_manager = get_contract(
        public_id=REGISTRIES_MANAGER_CONTRACT,
    )

    component_registry = get_contract(
        public_id=COMPONENT_REGISTRY_CONTRACT,
    )

    try:
        tx = registries_manager.get_create_transaction(
            ledger_api=ledger_api,
            contract_address=ContractConfigs.get(
                REGISTRIES_MANAGER_CONTRACT.name
            ).contracts[chain_type],
            owner=crypto.address,
            component_type=component_type,
            metadata_hash=metadata_hash,
            dependencies=dependencies,
        )
        transact(
            ledger_api=ledger_api,
            crypto=crypto,
            tx=tx,
        )
    except RequestsConnectionError as e:
        raise ComponentMintFailed("Cannot connect to the given RPC") from e

    try:
        for event_dict in component_registry.get_create_unit_event_filter(
            ledger_api=ledger_api,
            contract_address=ContractConfigs.get(
                COMPONENT_REGISTRY_CONTRACT.name
            ).contracts[chain_type],
        ):
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
