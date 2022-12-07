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

"""On-chain interaction helpers."""
import json
from collections import OrderedDict
from pathlib import Path
from typing import Any, Dict, List, Optional, cast

import click
from aea.configurations.constants import DEFAULT_README_FILE
from aea.configurations.data_types import PackageType, PublicId
from aea.configurations.loader import load_configuration_object
from aea.crypto.base import Crypto, LedgerApi
from aea.helpers.cid import CID
from aea.helpers.ipfs.base import IPFSHashOnly
from aea_cli_ipfs.ipfs_utils import IPFSTool
from aea_ledger_ethereum.ethereum import EthereumApi
from requests.exceptions import ConnectionError as RequestsConnectionError

from autonomy.chain.base import ComponentRegistry, RegistriesManager
from autonomy.chain.config import ChainConfigs, ChainTypes
from autonomy.chain.exceptions import ComponentMintFailed, FailedToRetrieveTokenId
from autonomy.configurations.base import PACKAGE_TYPE_TO_CONFIG_CLASS


BASE16_HASH_PREFIX = "f01701220"
CONFIG_HASH_STRING_PREFIX = "0x"
UNIT_HASH_PREFIX = CONFIG_HASH_STRING_PREFIX + "{metadata_hash}"
DEFAULT_NFT_IMAGE_HASH = "bafybeiggnad44tftcrenycru2qtyqnripfzitv5yume4szbkl33vfd4abm"

ContractInterfaceType = Any


def serialize_metadata(
    package_hash: str,
    public_id: PublicId,
    description: str,
    nft_image_hash: str = DEFAULT_NFT_IMAGE_HASH,
) -> str:
    """Serialize metadata."""
    metadata = OrderedDict(
        {
            "name": str(public_id),
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
    ipfs_tool: IPFSTool,
    nft_image_hash: str = DEFAULT_NFT_IMAGE_HASH,
) -> str:
    """Publish service metadata."""

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


def _mint_component(
    ledger_api: LedgerApi,
    crypto: Crypto,
    metadata_hash: str,
    component_type: RegistriesManager.UnitType,
    chain_type: ChainTypes,
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
            "Cannot retrieve token ID for minted component"
        ) from e

    return None


def mint_component(
    package_path: Path,
    package_type: PackageType,
    crypto: Crypto,
    chain_type: ChainTypes,
    dependencies: Optional[List[int]] = None,
) -> None:
    """Mint a component to on-chain contract."""

    chain_config = ChainConfigs.get(chain_type=chain_type)
    if chain_config.rpc is None:
        raise click.ClickException(
            f"RPC cannot be `None` for chain config; chain_type={chain_type}"
        )

    ipfs_tool = IPFSTool()
    ledger_api = EthereumApi(
        **{
            "address": chain_config.rpc,
            "chain_id": chain_config.chain_id,
        }
    )

    package_configuration = load_configuration_object(
        package_type=package_type,
        directory=package_path,
        package_type_config_class=PACKAGE_TYPE_TO_CONFIG_CLASS,
    )

    metadata_hash = publish_metadata(
        public_id=package_configuration.public_id,
        package_path=package_path,
        ipfs_tool=ipfs_tool,
    )

    token_id = _mint_component(
        ledger_api=ledger_api,
        crypto=crypto,
        metadata_hash=metadata_hash,
        component_type=RegistriesManager.UnitType.COMPONENT,
        chain_type=chain_type,
        dependencies=dependencies,
    )

    click.echo("Component minted with:")
    click.echo(f"\tPublic ID: {package_configuration.public_id}")
    click.echo(f"\tMetadata Hash: {metadata_hash}")
    if token_id is not None:
        click.echo(f"\tToken ID: {token_id}")
    else:
        click.echo("Could not verify metadata hash to retrieve the token ID")
        return
