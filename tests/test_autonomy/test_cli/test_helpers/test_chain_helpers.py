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
from autonomy.chain.mint import registry_contracts
from autonomy.cli.helpers.chain import (
    MintHelper,
    activate_service,
    deploy_service,
    get_ledger_and_crypto_objects,
    register_instance,
    terminate_service,
    unbond_service,
)

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


def test_activate_service_timeout_failure() -> None:
    """Test `activate_service` method"""

    with pytest.raises(
        click.ClickException,
        match="Could not verify the service activation in given time",
    ):
        with mock.patch.object(
            registry_contracts._service_registry,
            "verify_service_has_been_activated",
            return_value=False,
        ), mock.patch.object(
            registry_contracts._service_manager,
            "get_activate_registration_transaction",
            return_value=False,
        ), mock.patch(
            "autonomy.chain.service.transact"
        ), mock.patch(
            "autonomy.chain.service.get_service_info",
            return_value=(1, None, ServiceState.PRE_REGISTRATION.value, None),
        ):
            activate_service(
                service_id=0,
                key=ETHEREUM_KEY_DEPLOYER,
                chain_type=ChainType.LOCAL,
                timeout=1.0,
            )


def test_register_instance_timeout_failure() -> None:
    """Test `deploy_service` method"""

    with pytest.raises(
        click.ClickException,
        match="Could not verify the instance registration for {'0x'} in given time",
    ):
        with mock.patch.object(
            registry_contracts._service_registry,
            "verify_agent_instance_registration",
            return_value=[],
        ), mock.patch.object(
            registry_contracts._service_manager,
            "get_register_instance_transaction",
            return_value=False,
        ), mock.patch(
            "autonomy.chain.service.transact"
        ), mock.patch(
            "autonomy.chain.service.get_service_info",
            return_value=(1, None, ServiceState.ACTIVE_REGISTRATION.value, None),
        ):
            register_instance(
                service_id=0,
                instances=["0x"],
                agent_ids=[1],
                key=ETHEREUM_KEY_DEPLOYER,
                chain_type=ChainType.LOCAL,
                timeout=1.0,
            )


def test_deploy_service_timeout_failure() -> None:
    """Test `deploy_service` method"""

    with pytest.raises(
        click.ClickException,
        match="Could not verify the service deployment for service 0 in given time",
    ):
        with mock.patch.object(
            registry_contracts._service_registry,
            "verify_service_has_been_deployed",
            return_value=False,
        ), mock.patch.object(
            registry_contracts._service_manager,
            "get_service_deploy_transaction",
            return_value=False,
        ), mock.patch(
            "autonomy.chain.service.transact"
        ), mock.patch(
            "autonomy.chain.service.get_service_info",
            return_value=(1, None, ServiceState.FINISHED_REGISTRATION.value, None),
        ):
            deploy_service(
                service_id=0,
                key=ETHEREUM_KEY_DEPLOYER,
                chain_type=ChainType.LOCAL,
                timeout=1.0,
            )


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
            terminate_service(
                service_id=0,
                key=ETHEREUM_KEY_DEPLOYER,
                chain_type=ChainType.LOCAL,
            )


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
            terminate_service(
                service_id=0,
                key=ETHEREUM_KEY_DEPLOYER,
                chain_type=ChainType.LOCAL,
            )


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
            unbond_service(
                service_id=0,
                key=ETHEREUM_KEY_DEPLOYER,
                chain_type=ChainType.LOCAL,
            )


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
            unbond_service(
                service_id=0,
                key=ETHEREUM_KEY_DEPLOYER,
                chain_type=ChainType.LOCAL,
            )


def test_get_ledger_and_crypto_objects() -> None:
    """Test `get_ledger_and_crypto_objects` for hardware wallet support"""

    with mock.patch.object(EthereumHWICrypto, "entity"):
        ledger_api, crypto = get_ledger_and_crypto_objects(
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
