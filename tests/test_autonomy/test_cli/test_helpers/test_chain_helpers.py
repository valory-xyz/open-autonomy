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

"""Test chain helpers."""

from unittest import mock

import click
import pytest
from aea.configurations.data_types import PackageType
from aea_test_autonomy.configurations import ETHEREUM_KEY_DEPLOYER

from autonomy.chain.config import ChainConfigs, ChainType
from autonomy.cli.helpers.chain import mint_component

from tests.conftest import ROOT_DIR
from tests.test_autonomy.test_cli.test_mint.test_mint_components import DummyContract


PACKAGE_DIR = ROOT_DIR / "packages" / "valory" / "protocols" / "abci"
DUMMY_METADATA_HASH = (
    "0xd913b5bf68193dfacb941538d5900466c449c9ec8121153f152de2e026fa7f3a"
)


publish_metadata_patch = mock.patch(
    "autonomy.cli.helpers.chain.publish_metadata", return_value=DUMMY_METADATA_HASH
)


class TestMintComponentMethod:
    """Test `mint_component` method."""

    def test_mint_component_rpc_connect_fail(
        self,
    ) -> None:
        """Test RPC connection error."""

        with pytest.raises(
            click.ClickException,
            match="Component mint failed with following error; Cannot connect to the given RPC",
        ), publish_metadata_patch:
            mint_component(
                package_path=PACKAGE_DIR,
                package_type=PackageType.PROTOCOL,
                keys=ETHEREUM_KEY_DEPLOYER,
                chain_type=ChainType.LOCAL,
            )

    def test_mint_component_token_id_retrieve_fail(
        self,
    ) -> None:
        """Test token ID retrieval failure method."""

        with pytest.raises(
            click.ClickException,
            match=(
                "Component mint was successful but token ID retrieving failed with following error; "
                "Connection interrupted while waiting for the unitId emit event"
            ),
        ), publish_metadata_patch, mock.patch(
            "autonomy.chain.mint.get_contract", return_value=DummyContract()
        ):
            with mock.patch("autonomy.chain.mint.transact"), mock.patch(
                "autonomy.cli.helpers.chain.EthereumApi.try_get_gas_pricing"
            ):
                mint_component(
                    package_path=PACKAGE_DIR,
                    package_type=PackageType.PROTOCOL,
                    keys=ETHEREUM_KEY_DEPLOYER,
                    chain_type=ChainType.LOCAL,
                )

    def test_rpc_cannot_be_none(
        self,
    ) -> None:
        """Test bad chain config."""

        with pytest.raises(
            click.ClickException,
            match="RPC cannot be `None` for chain config; chain_type=ChainType.GOERLI",
        ):
            mint_component(
                package_path=PACKAGE_DIR,
                package_type=PackageType.PROTOCOL,
                keys=ETHEREUM_KEY_DEPLOYER,
                chain_type=ChainType.GOERLI,
            )

    def test_missing_nft_hash(
        self,
    ) -> None:
        """Test NFT hash not provided failure."""

        with pytest.raises(
            click.ClickException,
            match="Please provide hash for NFT image to mint component on `goerli` chain",
        ):
            with mock.patch(
                "autonomy.cli.helpers.chain.ChainConfigs.get",
                return_value=ChainConfigs.local,
            ):
                mint_component(
                    package_path=PACKAGE_DIR,
                    package_type=PackageType.PROTOCOL,
                    keys=ETHEREUM_KEY_DEPLOYER,
                    chain_type=ChainType.GOERLI,
                )
