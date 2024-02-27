# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022-2024 Valory AG
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

import re
import tempfile
from pathlib import Path
from unittest import mock

import click
import pytest
from aea.configurations.data_types import PackageType
from aea_test_autonomy.configurations import ETHEREUM_KEY_DEPLOYER

from autonomy.chain.base import ServiceState
from autonomy.chain.config import ChainConfigs, ChainType
from autonomy.chain.mint import DEFAULT_NFT_IMAGE_HASH, registry_contracts
from autonomy.cli.helpers.chain import MintHelper, OnChainHelper, ServiceHelper

from tests.conftest import ROOT_DIR
from tests.test_autonomy.test_chain.base import patch_subgraph


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


def _get_ledger_and_crypto_objects_patch() -> mock._patch:
    return mock.patch.object(
        OnChainHelper,
        "get_ledger_and_crypto_objects",
        return_value=(mock.MagicMock(), mock.MagicMock()),
    )


class TestMintComponentMethod:
    """Test `mint_component` method."""

    def test_mint_component_rpc_connect_fail(
        self,
    ) -> None:
        """Test RPC connection error."""

        with pytest.raises(
            click.ClickException,
            match=re.escape(
                "Component mint failed with following error; RPCError(Cannot connect to the given RPC)"
            ),
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
                ).verify_nft().fetch_component_dependencies().publish_metadata().mint_component()

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
            ).verify_nft().fetch_component_dependencies().publish_metadata().mint_component()

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
                ).verify_nft().fetch_component_dependencies().publish_metadata().mint_component()


class TestRequiredEnvVars:
    """Test required env var check works."""

    _component_failure = (
        "Addresses for following contracts are None, please set them using their respective environment variables\n"
        "- Set `registries_manager` address using `CUSTOM_REGISTRIES_MANAGER_ADDRESS`\n"
        "- Set `component_registry` address using `CUSTOM_COMPONENT_REGISTRY_ADDRESS`"
    )

    _service_failure = (
        "Addresses for following contracts are None, please set them using their respective environment variables\n"
        "- Set `service_manager` address using `CUSTOM_SERVICE_MANAGER_ADDRESS`\n"
        "- Set `service_registry` address using `CUSTOM_SERVICE_REGISTRY_ADDRESS`"
    )

    def test_component_mint(self) -> None:
        """Test component mint env vars."""
        with _get_ledger_and_crypto_objects_patch(), pytest.raises(
            click.ClickException,
            match=self._component_failure,
        ):
            mint_helper = MintHelper(
                chain_type=ChainType.CUSTOM,
                key=ETHEREUM_KEY_DEPLOYER,
            )
            mint_helper.mint_component()

    def test_component_update(self) -> None:
        """Test component update env vars."""
        with _get_ledger_and_crypto_objects_patch(), pytest.raises(
            click.ClickException,
            match=self._component_failure,
        ):
            mint_helper = MintHelper(
                chain_type=ChainType.CUSTOM,
                key=ETHEREUM_KEY_DEPLOYER,
            )
            mint_helper.update_component()

    def test_servic_mint(self) -> None:
        """Test component update env vars."""
        with _get_ledger_and_crypto_objects_patch(), pytest.raises(
            click.ClickException,
            match=self._service_failure,
        ):
            mint_helper = MintHelper(
                chain_type=ChainType.CUSTOM,
                key=ETHEREUM_KEY_DEPLOYER,
            )
            mint_helper.mint_service(1, 1, 1)

    def test_service_update(self) -> None:
        """Test component update env vars."""
        with _get_ledger_and_crypto_objects_patch(), pytest.raises(
            click.ClickException,
            match=self._service_failure,
        ):
            mint_helper = MintHelper(
                chain_type=ChainType.CUSTOM,
                key=ETHEREUM_KEY_DEPLOYER,
            )
            mint_helper.update_service(1, 1, 1)

    def test_activate_service(self) -> None:
        """Test component update env vars."""
        with _get_ledger_and_crypto_objects_patch(), pytest.raises(
            click.ClickException,
            match=self._service_failure,
        ):
            mint_helper = ServiceHelper(
                service_id=1,
                chain_type=ChainType.CUSTOM,
                key=ETHEREUM_KEY_DEPLOYER,
            )
            mint_helper.check_is_service_token_secured().activate_service()

    def test_register_instances(self) -> None:
        """Test component update env vars."""
        with _get_ledger_and_crypto_objects_patch(), pytest.raises(
            click.ClickException,
            match=self._service_failure,
        ):
            mint_helper = ServiceHelper(
                service_id=1,
                chain_type=ChainType.CUSTOM,
                key=ETHEREUM_KEY_DEPLOYER,
            )
            mint_helper.check_is_service_token_secured().register_instance(["0x"], [1])

    def test_deploy_instances(self) -> None:
        """Test component update env vars."""
        with _get_ledger_and_crypto_objects_patch(), pytest.raises(
            click.ClickException,
            match=(
                "Addresses for following contracts are None, please set them using their respective environment variables\n"
                "- Set `service_manager` address using `CUSTOM_SERVICE_MANAGER_ADDRESS`\n"
                "- Set `service_registry` address using `CUSTOM_SERVICE_REGISTRY_ADDRESS`\n"
                "- Set `gnosis_safe_proxy_factory` address using `CUSTOM_GNOSIS_SAFE_PROXY_FACTORY_ADDRESS`\n"
                "- Set `gnosis_safe_same_address_multisig` address using `CUSTOM_GNOSIS_SAFE_SAME_ADDRESS_MULTISIG_ADDRESS`"
            ),
        ):
            mint_helper = ServiceHelper(
                service_id=1,
                chain_type=ChainType.CUSTOM,
                key=ETHEREUM_KEY_DEPLOYER,
            )
            mint_helper.check_is_service_token_secured().deploy_service()

    def test_unbond(self) -> None:
        """Test component update env vars."""
        with _get_ledger_and_crypto_objects_patch(), pytest.raises(
            click.ClickException,
            match=self._service_failure,
        ):
            mint_helper = ServiceHelper(
                service_id=1,
                chain_type=ChainType.CUSTOM,
                key=ETHEREUM_KEY_DEPLOYER,
            )
            mint_helper.check_is_service_token_secured().unbond_service()


class TestDependencyVerification:
    """Test dependency verification."""

    def test_token_found(
        self,
    ) -> None:
        """Test NFT hash not provided failure."""

        with mock.patch(
            "autonomy.cli.helpers.chain.ChainConfigs.get",
            return_value=ChainConfigs.local,
        ), patch_subgraph(
            response=[{"tokenId": "1", "publicId": "valory/ipfs"}],
            method="get_record_by_package_id",
        ):
            helpers = (
                MintHelper(
                    chain_type=ChainType.ETHEREUM,
                    key=ETHEREUM_KEY_DEPLOYER,
                )
                .load_package_configuration(
                    package_path=ROOT_DIR
                    / "packages"
                    / "valory"
                    / "connections"
                    / "ipfs",
                    package_type=PackageType.CONNECTION,
                )
                .fetch_component_dependencies()
            )

            assert helpers.dependencies == [1]

    def test_no_token_found(
        self,
    ) -> None:
        """Test NFT hash not provided failure."""

        with mock.patch(
            "autonomy.cli.helpers.chain.ChainConfigs.get",
            return_value=ChainConfigs.local,
        ), patch_subgraph(
            response=[],
            method="get_record_by_package_id",
        ), pytest.raises(
            click.ClickException, match="Could not find on-chain token for valory/ipfs"
        ):
            MintHelper(
                chain_type=ChainType.ETHEREUM,
                key=ETHEREUM_KEY_DEPLOYER,
            ).load_package_configuration(
                package_path=ROOT_DIR / "packages" / "valory" / "connections" / "ipfs",
                package_type=PackageType.CONNECTION,
            ).fetch_component_dependencies()

    def test_no_agent_found(
        self,
    ) -> None:
        """Test NFT hash not provided failure."""

        with mock.patch(
            "autonomy.cli.helpers.chain.ChainConfigs.get",
            return_value=ChainConfigs.local,
        ), patch_subgraph(
            response=[],
            method="get_component_by_token",
        ), pytest.raises(
            click.ClickException,
            match="No agents found with token ID 1",
        ):
            MintHelper(
                chain_type=ChainType.ETHEREUM,
                key=ETHEREUM_KEY_DEPLOYER,
            ).load_package_configuration(
                package_path=ROOT_DIR
                / "packages"
                / "valory"
                / "services"
                / "register_reset",
                package_type=PackageType.SERVICE,
            ).verify_service_dependencies(
                agent_id=1
            )

    def test_wrong_agent_found(
        self,
    ) -> None:
        """Test NFT hash not provided failure."""

        with mock.patch(
            "autonomy.cli.helpers.chain.ChainConfigs.get",
            return_value=ChainConfigs.local,
        ), patch_subgraph(
            response=[{"tokenId": "1", "publicId": "valory/ipfs"}],
            method="get_component_by_token",
        ), pytest.raises(
            click.ClickException,
            match=(
                "Public ID `valory/ipfs:any` for token 1 does not match with "
                "the one defained in the service package `valory/register_reset:any`"
            ),
        ):
            MintHelper(
                chain_type=ChainType.ETHEREUM,
                key=ETHEREUM_KEY_DEPLOYER,
            ).load_package_configuration(
                package_path=ROOT_DIR
                / "packages"
                / "valory"
                / "services"
                / "register_reset",
                package_type=PackageType.SERVICE,
            ).verify_service_dependencies(
                agent_id=1
            )

    def test_agent_found(
        self,
    ) -> None:
        """Test NFT hash not provided failure."""

        with mock.patch(
            "autonomy.cli.helpers.chain.ChainConfigs.get",
            return_value=ChainConfigs.local,
        ), patch_subgraph(
            response=[{"tokenId": "1", "publicId": "valory/register_reset"}],
            method="get_component_by_token",
        ):
            helper = (
                MintHelper(
                    chain_type=ChainType.ETHEREUM,
                    key=ETHEREUM_KEY_DEPLOYER,
                )
                .load_package_configuration(
                    package_path=ROOT_DIR
                    / "packages"
                    / "valory"
                    / "services"
                    / "register_reset",
                    package_type=PackageType.SERVICE,
                )
                .verify_service_dependencies(agent_id=1)
            )
            assert helper.agent_id == 1


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


@pytest.mark.skip(reason="https://github.com/valory-xyz/open-aea/issues/671")
def test_get_ledger_and_crypto_objects() -> None:
    """Test `get_ledger_and_crypto_objects` for hardware wallet support"""
    from aea_ledger_ethereum_hwi.hwi import EthereumHWIApi, EthereumHWICrypto

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
        ).verify_nft().fetch_component_dependencies().publish_metadata().mint_component()


def test_verify_service_dependencies_failures() -> None:
    """Test `verify_service_dependencies` failures"""

    with pytest.raises(
        click.ClickException,
        match="Error interacting with subgraph",
    ), mock.patch.object(
        MintHelper,
        "get_ledger_and_crypto_objects",
        return_value=(mock.MagicMock(), mock.MagicMock()),
    ):
        MintHelper(
            key=ETHEREUM_KEY_DEPLOYER,
            chain_type=ChainType.ETHEREUM,
            subgraph="http://localhost:8888",
        ).load_package_configuration(
            package_path=PACKAGE_DIR,
            package_type=PackageType.PROTOCOL,
        ).verify_nft(
            nft=DEFAULT_NFT_IMAGE_HASH,
        ).verify_service_dependencies(
            agent_id=1
        )


def test_token_secure_check_on_custom_chain() -> None:
    """Test token_secure is False on custom chain."""

    with _get_ledger_and_crypto_objects_patch():
        service_helper = ServiceHelper(
            service_id=1, chain_type=ChainType.CUSTOM, key=ETHEREUM_KEY_DEPLOYER
        )
        assert service_helper.check_is_service_token_secured().token_secured is False


def test_mint_with_token_on_custom_chain() -> None:
    """Test minting with token on L2 chains fail."""

    with _get_ledger_and_crypto_objects_patch(), pytest.raises(
        click.ClickException, match="Cannot use custom token for bonding on L2 chains"
    ):
        MintHelper(  # nosec
            chain_type=ChainType.CUSTOM, key=ETHEREUM_KEY_DEPLOYER
        ).mint_service(
            number_of_slots=1,
            cost_of_bond=1,
            threshold=1,
            token="0x",
        )


@pytest.mark.parametrize(
    argnames="key",
    argvalues=(
        "0xdf57089febbacf7ba0bc227dafbffa9fc08a93fdc68e1e42411a14efcf23656e\n",
        "df57089febbacf7ba0bc227dafbffa9fc08a93fdc68e1e42411a14efcf23656",
        "0x9fe46736679d2d9a65f0992f2272de9f3c7fa6e0",
    ),
)
def test_wrong_private_key_format(key: str) -> None:
    """Test an error is raised if the private key format is wrong."""
    with tempfile.TemporaryDirectory() as temp_dir, pytest.raises(
        click.ClickException,
        match=(
            "Cannot load private key for following possible reasons\n"
            "- Wrong key format\n"
            "- Wrong key length\n"
            "- Trailing spaces or new line characters"
        ),
    ):
        file = Path(temp_dir, "key.txt")
        file.write_text(key)
        OnChainHelper.load_crypto(file=file)
