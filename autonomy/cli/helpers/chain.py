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

"""On-chain interaction helpers."""

from pathlib import Path
from typing import List, Optional, cast

import click
from aea.configurations.data_types import PackageType
from aea.configurations.loader import load_configuration_object
from aea_ledger_ethereum.ethereum import EthereumApi, EthereumCrypto

from autonomy.chain.base import UnitType
from autonomy.chain.config import ChainConfigs, ChainType
from autonomy.chain.exceptions import ComponentMintFailed, FailedToRetrieveTokenId
from autonomy.chain.mint import DEFAULT_NFT_IMAGE_HASH
from autonomy.chain.mint import mint_component as _mint_component
from autonomy.chain.mint import publish_metadata
from autonomy.configurations.base import PACKAGE_TYPE_TO_CONFIG_CLASS


def mint_component(  # pylint: disable=too-many-arguments
    package_path: Path,
    package_type: PackageType,
    keys: Path,
    chain_type: ChainType,
    dependencies: Optional[List[int]] = None,
    nft_image_hash: Optional[str] = None,
    password: Optional[str] = None,
) -> None:
    """Mint component."""

    chain_config = ChainConfigs.get(chain_type=chain_type)
    if chain_config.rpc is None:
        raise click.ClickException(
            f"RPC cannot be `None` for chain config; chain_type={chain_type}"
        )

    crypto = EthereumCrypto(
        private_key_path=keys,
        password=password,
    )
    ledger_api = EthereumApi(
        **{
            "address": chain_config.rpc,
            "chain_id": chain_config.chain_id,
            "is_gas_estimation_enabled": True,
        }
    )

    package_configuration = load_configuration_object(
        package_type=package_type,
        directory=package_path,
        package_type_config_class=PACKAGE_TYPE_TO_CONFIG_CLASS,
    )

    if chain_type == ChainType.LOCAL and nft_image_hash is None:
        nft_image_hash = DEFAULT_NFT_IMAGE_HASH

    if chain_type != ChainType.LOCAL and nft_image_hash is None:
        raise click.ClickException(
            f"Please provide hash for NFT image to mint component on `{chain_type.value}` chain"
        )

    metadata_hash = publish_metadata(
        public_id=package_configuration.public_id,
        package_path=package_path,
        nft_image_hash=cast(str, nft_image_hash),
        description=package_configuration.description,
    )

    try:
        token_id = _mint_component(
            ledger_api=ledger_api,
            crypto=crypto,
            metadata_hash=metadata_hash,
            component_type=UnitType.COMPONENT,
            chain_type=chain_type,
            dependencies=dependencies,
        )
    except ComponentMintFailed as e:
        raise click.ClickException(
            f"Component mint failed with following error; {e}"
        ) from e
    except FailedToRetrieveTokenId as e:
        raise click.ClickException(
            f"Component mint was successful but token ID retrieving failed with following error; {e}"
        ) from e

    click.echo("Component minted with:")
    click.echo(f"\tPublic ID: {package_configuration.public_id}")
    click.echo(f"\tMetadata Hash: {metadata_hash}")
    if token_id is not None:
        click.echo(f"\tToken ID: {token_id}")
    else:
        click.echo("Could not verify metadata hash to retrieve the token ID")
        return
