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

"""Test chain helpers."""

from unittest import mock

import click
import pytest
from aea.configurations.data_types import PackageType
from aea_ledger_ethereum_hwi.hwi import EthereumHWIApi, EthereumHWICrypto
from aea_test_autonomy.configurations import ETHEREUM_KEY_DEPLOYER

from autonomy.chain.base import ServiceState
from autonomy.chain.config import ChainConfigs, ChainType
from autonomy.chain.exceptions import FailedToRetrieveComponentMetadata
from autonomy.chain.mint import DEFAULT_NFT_IMAGE_HASH, registry_contracts
from autonomy.cli.helpers.chain import MintHelper, OnChainHelper, ServiceHelper

from tests.conftest import ROOT_DIR


PACKAGE_DIR = ROOT_DIR / "packages" / "valory" / "protocols" / "abci"
DUMMY_METADATA_HASH = (
    "0xd913b5bf68193dfacb941538d5900466c449c9ec8121153f152de2e026fa7f3a"
)


publish_metadata_patch = mock.patch(
    "autonomy.cli.helpers.chain.publish_metadata",
    return_value=(DUMMY_METADATA_HASH, ""),
)

_ = registry_contracts.service_registry
_ = registry_contracts.service_manager
_ = registry_contracts.registries_manager
_ = registry_contracts.component_registry
_ = registry_contracts.service_manager


class TestMintComponentMethod:
    """Test `mint_component` method."""

    def test_mint_component_rpc_connect_fail(
        self,
    ) -> None:
        """Test RPC connection error."""

        with pytest.raises(
            click.ClickException,
            match="Component mint failed with following error; Cannot connect to the given RPC",
        ):
            with publish_metadata_patch, mock.patch(
                "autonomy.chain.mint.Crypto.sign_transaction"
            ):
                MintHelper(
                    chain_type=ChainType.LOCAL,
                    key=ETHEREUM_KEY_DEPLOYER,
                ).load_package_configuration(
                    package_path=PACKAGE_DIR,
                    package_type=PackageType.PROTOCOL,
                ).verify_nft().verify_component_dependencies(
                    dependencies=(),  # type: ignore
                ).publish_metadata().mint_component()

    def test_rpc_cannot_be_none(
        self,
    ) -> None:
        """Test bad chain config."""

        with pytest.raises(
            click.ClickException,
            match=(
                "RPC URL cannot be `None`, "
                "Please set the environment variable for goerli chain "
                "using `GOERLI_CHAIN_RPC` environment variable"
            ),
        ):
            MintHelper(
                chain_type=ChainType.GOERLI,
                key=ETHEREUM_KEY_DEPLOYER,
            ).load_package_configuration(
                package_path=PACKAGE_DIR,
                package_type=PackageType.PROTOCOL,
            ).verify_nft().verify_component_dependencies(
                dependencies=(),  # type: ignore
            ).publish_metadata().mint_component()

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
                MintHelper(
                    chain_type=ChainType.GOERLI,
                    key=ETHEREUM_KEY_DEPLOYER,
                ).load_package_configuration(
                    package_path=PACKAGE_DIR,
                    package_type=PackageType.PROTOCOL,
                ).verify_nft().verify_component_dependencies(
                    dependencies=(),  # type: ignore
                ).publish_metadata().mint_component()


@pytest.mark.parametrize(
    argnames=("state", "error"),
    argvalues=(
        (ServiceState.NON_EXISTENT, "Service does not exist"),
        (ServiceState.PRE_REGISTRATION, "Service not active"),
        (ServiceState.TERMINATED_BONDED, "Service already terminated"),
    ),
)
def test_terminate_service_failures(state: ServiceState, error: str) -> None:
    """Test `terminate_service` method"""

    with pytest.raises(
        click.ClickException,
        match=error,
    ):
        with mock.patch(
            "autonomy.chain.service.get_service_info",
            return_value=(1, None, state.value, None),
        ):
            ServiceHelper(
                service_id=0,
                key=ETHEREUM_KEY_DEPLOYER,
                chain_type=ChainType.LOCAL,
            ).terminate_service()


def test_terminate_service_contract_failure() -> None:
    """Test `terminate_service` method"""

    with pytest.raises(
        click.ClickException,
        match="Service termination failed",
    ), mock.patch.object(
        registry_contracts._service_manager,
        "get_terminate_service_transaction",
        side_effect=ValueError,
    ):
        with mock.patch(
            "autonomy.chain.service.get_service_info",
            return_value=(1, None, ServiceState.FINISHED_REGISTRATION.value, None),
        ):
            ServiceHelper(
                service_id=0,
                key=ETHEREUM_KEY_DEPLOYER,
                chain_type=ChainType.LOCAL,
            ).terminate_service()


@pytest.mark.parametrize(
    argnames=("state", "error"),
    argvalues=(
        (ServiceState.NON_EXISTENT, "Service does not exist"),
        (
            ServiceState.PRE_REGISTRATION,
            "Service needs to be in terminated-bonded state",
        ),
    ),
)
def test_unbond_service_failures(state: ServiceState, error: str) -> None:
    """Test `terminate_service` method"""

    with pytest.raises(
        click.ClickException,
        match=error,
    ):
        with mock.patch(
            "autonomy.chain.service.get_service_info",
            return_value=(1, None, state.value, None),
        ):
            ServiceHelper(
                service_id=0,
                key=ETHEREUM_KEY_DEPLOYER,
                chain_type=ChainType.LOCAL,
            ).unbond_service()


def test_unbond_service_contract_failure() -> None:
    """Test `unbond_service` method"""

    with pytest.raises(
        click.ClickException,
        match="Service unbond failed",
    ), mock.patch.object(
        registry_contracts._service_manager,
        "get_unbond_service_transaction",
        side_effect=ValueError,
    ):
        with mock.patch(
            "autonomy.chain.service.get_service_info",
            return_value=(1, None, ServiceState.TERMINATED_BONDED.value, None),
        ):
            ServiceHelper(
                service_id=0,
                key=ETHEREUM_KEY_DEPLOYER,
                chain_type=ChainType.LOCAL,
            ).unbond_service()


def test_get_ledger_and_crypto_objects() -> None:
    """Test `get_ledger_and_crypto_objects` for hardware wallet support"""

    with mock.patch.object(EthereumHWICrypto, "entity"):
        ledger_api, crypto = OnChainHelper.get_ledger_and_crypto_objects(
            chain_type=ChainType.LOCAL,
            hwi=True,
        )

    assert isinstance(ledger_api, EthereumHWIApi)
    assert isinstance(crypto, EthereumHWICrypto)


def test_get_ledger_and_crypto_failure() -> None:
    """Test `get_ledger_and_crypto_objects` failures"""

    with pytest.raises(
        click.ClickException,
        match="Please provide key path using `--key` or use `--hwi` if you want to use a hardware wallet",
    ):
        MintHelper(
            chain_type=ChainType.GOERLI,
        ).load_package_configuration(
            package_path=PACKAGE_DIR,
            package_type=PackageType.PROTOCOL,
        ).verify_nft().verify_component_dependencies(
            dependencies=(),  # type: ignore
        ).publish_metadata().mint_component()


def test_verify_component_dependencies_failures() -> None:
    """Test `verify_component_dependencies` failures"""

    with pytest.raises(
        click.ClickException,
        match=("Dependency verification failed"),
    ), mock.patch.object(
        MintHelper,
        "get_ledger_and_crypto_objects",
        return_value=(mock.MagicMock(), mock.MagicMock()),
    ), mock.patch(
        "autonomy.cli.helpers.chain.verify_component_dependencies",
        side_effect=FailedToRetrieveComponentMetadata,
    ):
        MintHelper(
            key=ETHEREUM_KEY_DEPLOYER,
            chain_type=ChainType.ETHEREUM,
        ).load_package_configuration(
            package_path=PACKAGE_DIR,
            package_type=PackageType.PROTOCOL,
        ).verify_nft(
            nft=DEFAULT_NFT_IMAGE_HASH,
        ).verify_component_dependencies(
            dependencies=(1,),  # type: ignore
        )


def test_verify_service_dependencies_failures() -> None:
    """Test `verify_service_dependencies` failures"""

    with pytest.raises(
        click.ClickException,
        match=("Dependency verification failed"),
    ), mock.patch.object(
        MintHelper,
        "get_ledger_and_crypto_objects",
        return_value=(mock.MagicMock(), mock.MagicMock()),
    ), mock.patch(
        "autonomy.cli.helpers.chain.verify_service_dependencies",
        side_effect=FailedToRetrieveComponentMetadata,
    ):
        MintHelper(
            key=ETHEREUM_KEY_DEPLOYER,
            chain_type=ChainType.ETHEREUM,
        ).load_package_configuration(
            package_path=PACKAGE_DIR,
            package_type=PackageType.PROTOCOL,
        ).verify_nft(
            nft=DEFAULT_NFT_IMAGE_HASH,
        ).verify_service_dependencies(
            agent_id=1
        )
