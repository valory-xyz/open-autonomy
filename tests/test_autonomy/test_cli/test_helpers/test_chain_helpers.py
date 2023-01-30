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
from aea_test_autonomy.configurations import ETHEREUM_KEY_DEPLOYER

from autonomy.chain.base import ServiceState
from autonomy.chain.config import ChainConfigs, ChainType
from autonomy.chain.mint import registry_contracts
from autonomy.cli.helpers.chain import (
    activate_service,
    deploy_service,
    mint_component,
    mint_service,
    register_instance,
)

from tests.conftest import ROOT_DIR
from tests.test_autonomy.test_cli.test_mint.test_mint_components import DummyContract


PACKAGE_DIR = ROOT_DIR / "packages" / "valory" / "protocols" / "abci"
DUMMY_METADATA_HASH = (
    "0xd913b5bf68193dfacb941538d5900466c449c9ec8121153f152de2e026fa7f3a"
)


publish_metadata_patch = mock.patch(
    "autonomy.cli.helpers.chain.publish_metadata", return_value=DUMMY_METADATA_HASH
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
                mint_component(
                    package_path=PACKAGE_DIR,
                    package_type=PackageType.PROTOCOL,
                    keys=ETHEREUM_KEY_DEPLOYER,
                    chain_type=ChainType.LOCAL,
                    dependencies=[],
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
        ):
            with publish_metadata_patch, mock.patch.object(
                registry_contracts, "_component_registry", DummyContract()
            ), mock.patch.object(
                registry_contracts, "_registries_manager", DummyContract()
            ), mock.patch(
                "autonomy.chain.mint.transact"
            ), mock.patch(
                "autonomy.cli.helpers.chain.EthereumApi.try_get_gas_pricing"
            ):
                mint_component(
                    package_path=PACKAGE_DIR,
                    package_type=PackageType.PROTOCOL,
                    keys=ETHEREUM_KEY_DEPLOYER,
                    chain_type=ChainType.LOCAL,
                    dependencies=[],
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
                dependencies=[],
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
                    dependencies=[],
                )

    def test_mint_component_timeout(
        self,
    ) -> None:
        """Test timeout error."""

        with pytest.raises(
            click.ClickException,
            match=(
                "Component mint was successful but token ID retrieving failed with following error; "
                "Could not retrieve the token in given time limit."
            ),
        ):
            with mock.patch(
                "autonomy.cli.helpers.chain.verify_component_dependencies"
            ), mock.patch("autonomy.cli.helpers.chain.publish_metadata"), mock.patch(
                "autonomy.chain.mint.transact"
            ), mock.patch.object(
                registry_contracts._registries_manager,
                "get_create_transaction",
                return_value=False,
            ), mock.patch.object(
                registry_contracts._component_registry,
                "filter_token_id_from_emitted_events",
                return_value=None,
            ):
                mint_component(
                    package_path=PACKAGE_DIR,
                    package_type=PackageType.PROTOCOL,
                    keys=ETHEREUM_KEY_DEPLOYER,
                    chain_type=ChainType.LOCAL,
                    dependencies=[],
                    timeout=1.0,
                )


def test_mint_service_timeout() -> None:
    """Test timeout error."""

    with pytest.raises(
        click.ClickException,
        match=(
            "Service mint was successful but token ID retrieving failed with following error; "
            "Could not retrieve the token in given time limit"
        ),
    ):
        with mock.patch(
            "autonomy.cli.helpers.chain.verify_service_dependencies"
        ), mock.patch(
            "autonomy.cli.helpers.chain.load_configuration_object"
        ), mock.patch(
            "autonomy.cli.helpers.chain.publish_metadata"
        ), mock.patch(
            "autonomy.chain.mint.transact"
        ), mock.patch.object(
            registry_contracts._service_manager,
            "get_create_transaction",
            return_value=False,
        ), mock.patch.object(
            registry_contracts._service_registry,
            "filter_token_id_from_emitted_events",
            return_value=None,
        ):
            mint_service(
                package_path=PACKAGE_DIR,
                keys=ETHEREUM_KEY_DEPLOYER,
                chain_type=ChainType.LOCAL,
                agent_id=1,
                number_of_slots=4,
                cost_of_bond=1,
                threshold=3,
                timeout=1.0,
            )


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
                keys=ETHEREUM_KEY_DEPLOYER,
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
                keys=ETHEREUM_KEY_DEPLOYER,
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
                keys=ETHEREUM_KEY_DEPLOYER,
                chain_type=ChainType.LOCAL,
                timeout=1.0,
            )
