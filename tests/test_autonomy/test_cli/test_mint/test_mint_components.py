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

"""Test `mint` command group."""

from typing import Any
from unittest import mock

import pytest
from aea.configurations.data_types import PackageId
from aea_test_autonomy.configurations import ETHEREUM_KEY_DEPLOYER
from aea_test_autonomy.fixture_helpers import registries_scope_class  # noqa: F401

from autonomy.chain.config import ChainConfigs, ChainType
from autonomy.chain.service import get_service_info
from autonomy.cli.helpers.chain import OnChainHelper

from tests.test_autonomy.test_chain.base import (
    BaseChainInteractionTest,
    DEFAULT_SERVICE_MINT_PARAMETERS,
    DUMMY_AGENT,
    DUMMY_CONNECTION,
    DUMMY_CONTRACT,
    DUMMY_PACKAGE_MANAGER,
    DUMMY_PROTOCOL,
    DUMMY_SERVICE,
    DUMMY_SKILL,
    patch_component_verification,
    patch_subgraph,
)
from tests.test_autonomy.test_cli.base import BaseCliTest


CUSTOM_OWNER = "0x8626F6940E2EB28930EFB4CEF49B2D1F2C9C1199"


class DummyContract:
    """Dummy contract"""

    def get_create_events(self, *args: Any, **kwargs: Any) -> None:
        """Dummy method implementation"""

    def get_create_transaction(self, *args: Any, **kwargs: Any) -> None:
        """Dummy method implementation"""


@patch_component_verification()
class TestMintComponents(BaseChainInteractionTest):
    """Test `autonomy develop mint` command."""

    cli_options = ("mint",)

    @pytest.mark.parametrize(
        argnames=("package_id"),
        argvalues=(
            DUMMY_PROTOCOL,
            DUMMY_CONTRACT,
            DUMMY_CONNECTION,
            DUMMY_SKILL,
            DUMMY_AGENT,
        ),
    )
    def test_mint_components(self, package_id: PackageId) -> None:
        """Test mint components."""

        commands = [
            package_id.package_type.value,
            str(
                DUMMY_PACKAGE_MANAGER.package_path_from_package_id(
                    package_id=package_id
                )
            ),
            "--key",
            str(ETHEREUM_KEY_DEPLOYER),
        ]

        result = self.run_cli(commands=tuple(commands))
        assert result.exit_code == 0, result.stderr
        assert "Component minted with:" in result.output
        assert "Metadata Hash:" in result.output
        assert "Token ID:" in result.output
        token_id = self.extract_token_id_from_output(output=result.output)
        self.verify_minted_token_id(
            token_id=token_id,
            package_id=package_id,
        )

        commands += ["--update", str(token_id)]
        result = self.run_cli(commands=tuple(commands))

        assert result.exit_code == 0, result.stderr
        assert "Component hash updated:" in result.output
        assert f"Token ID: {token_id}" in result.output
        self.verify_and_remove_metadata_file(token_id=token_id)

    def test_mint_component_with_owner(
        self,
    ) -> None:
        """Test mint components."""

        commands = [
            DUMMY_PROTOCOL.package_type.value,
            str(
                DUMMY_PACKAGE_MANAGER.package_path_from_package_id(
                    package_id=DUMMY_PROTOCOL
                )
            ),
            "--key",
            str(ETHEREUM_KEY_DEPLOYER),
            "--owner",
            CUSTOM_OWNER,
        ]

        result = self.run_cli(commands=tuple(commands))
        assert result.exit_code == 0, result.output
        assert "Component minted with:" in result.output
        assert "Metadata Hash:" in result.output
        assert "Token ID:" in result.output

        token_id = self.extract_token_id_from_output(output=result.output)
        self.verify_owner_address(
            token_id=token_id,
            owner=CUSTOM_OWNER,
            package_id=DUMMY_PROTOCOL,
        )
        self.verify_and_remove_metadata_file(token_id=token_id)

    def test_mint_service(
        self,
    ) -> None:
        """Test mint components."""
        agent_id = self.mint_component(package_id=DUMMY_AGENT, dependencies=[1])
        commands = [
            DUMMY_SERVICE.package_type.value,
            str(
                DUMMY_PACKAGE_MANAGER.package_path_from_package_id(
                    package_id=DUMMY_SERVICE
                )
            ),
            "--key",
            str(ETHEREUM_KEY_DEPLOYER),
            "-a",
            str(agent_id),
            *DEFAULT_SERVICE_MINT_PARAMETERS[2:],
        ]

        with patch_subgraph(
            response=[{"tokenId": agent_id, "publicId": "dummy_author/dummy_agent"}]
        ):
            result = self.run_cli(commands=tuple(commands))

        assert result.exit_code == 0, result
        assert "Service minted with:" in result.output
        assert "Metadata Hash:" in result.output
        assert "Token ID:" in result.output

        token_id = self.extract_token_id_from_output(output=result.output)
        self.verify_minted_token_id(
            token_id=token_id,
            package_id=DUMMY_SERVICE,
        )

        commands += ["--update", str(token_id)]
        with patch_subgraph(
            response=[{"tokenId": agent_id, "publicId": "dummy_author/dummy_agent"}]
        ):
            result = self.run_cli(commands=tuple(commands))
        assert result.exit_code == 0, result.stderr
        assert "Service updated with:" in result.output
        assert f"Token ID: {token_id}" in result.output
        self.verify_and_remove_metadata_file(token_id=token_id)

    def test_mint_service_without_threshold(
        self,
    ) -> None:
        """Test mint components."""
        agent_id = self.mint_component(package_id=DUMMY_AGENT, dependencies=[1])
        commands = [
            DUMMY_SERVICE.package_type.value,
            str(
                DUMMY_PACKAGE_MANAGER.package_path_from_package_id(
                    package_id=DUMMY_SERVICE
                )
            ),
            "--key",
            str(ETHEREUM_KEY_DEPLOYER),
            "-a",
            str(agent_id),
            *DEFAULT_SERVICE_MINT_PARAMETERS[2:-2],
        ]

        with patch_subgraph(
            response=[{"tokenId": agent_id, "publicId": "dummy_author/dummy_agent"}]
        ):
            result = self.run_cli(commands=tuple(commands))

        assert result.exit_code == 0, result.output
        assert "Service minted with:" in result.output
        assert "Metadata Hash:" in result.output
        assert "Token ID:" in result.output

        token_id = self.extract_token_id_from_output(output=result.output)
        self.verify_minted_token_id(
            token_id=token_id,
            package_id=DUMMY_SERVICE,
        )
        ledger_api, _ = OnChainHelper.get_ledger_and_crypto_objects(
            chain_type=ChainType.LOCAL
        )
        _, _, _, threshold, *_ = get_service_info(
            ledger_api=ledger_api, chain_type=ChainType.LOCAL, token_id=token_id
        )
        assert threshold == 3

        # Test updates
        commands += ["--update", str(token_id)]
        with patch_subgraph(
            response=[{"tokenId": agent_id, "publicId": "dummy_author/dummy_agent"}]
        ):
            result = self.run_cli(commands=tuple(commands))
        assert result.exit_code == 0, result.stderr
        assert "Service updated with:" in result.output
        assert f"Token ID: {token_id}" in result.output

        self.verify_and_remove_metadata_file(token_id=token_id)

        ledger_api, _ = OnChainHelper.get_ledger_and_crypto_objects(
            chain_type=ChainType.LOCAL
        )
        _, _, _, threshold, *_ = get_service_info(
            ledger_api=ledger_api, chain_type=ChainType.LOCAL, token_id=token_id
        )
        assert threshold == 3

    def test_update_service_failure(
        self,
    ) -> None:
        """Test mint components."""
        agent_id = self.mint_component(package_id=DUMMY_AGENT, dependencies=[1])
        commands = [
            DUMMY_SERVICE.package_type.value,
            str(
                DUMMY_PACKAGE_MANAGER.package_path_from_package_id(
                    package_id=DUMMY_SERVICE
                )
            ),
            "--key",
            str(ETHEREUM_KEY_DEPLOYER),
            "-a",
            str(agent_id),
            *DEFAULT_SERVICE_MINT_PARAMETERS[2:],
        ]

        with patch_subgraph(
            response=[{"tokenId": agent_id, "publicId": "dummy_author/dummy_agent"}]
        ):
            result = self.run_cli(commands=tuple(commands))

        assert result.exit_code == 0, result
        assert "Service minted with:" in result.output
        assert "Metadata Hash:" in result.output
        assert "Token ID:" in result.output

        token_id = self.extract_token_id_from_output(output=result.output)
        self.verify_minted_token_id(
            token_id=token_id,
            package_id=DUMMY_SERVICE,
        )
        self.service_manager.activate(service_id=token_id)

        commands += ["--update", str(token_id)]
        with patch_subgraph(
            response=[{"tokenId": agent_id, "publicId": "dummy_author/dummy_agent"}]
        ):
            result = self.run_cli(commands=tuple(commands))

        assert result.exit_code == 1, result.stdout
        assert (
            "Cannot update service hash, service needs to be in the pre-registration state"
            in result.stderr
        )
        self.verify_and_remove_metadata_file(token_id=token_id)

    def test_mint_service_with_owner(
        self,
    ) -> None:
        """Test mint components."""
        agent_id = self.mint_component(package_id=DUMMY_AGENT, dependencies=[1])
        commands = (
            DUMMY_SERVICE.package_type.value,
            str(
                DUMMY_PACKAGE_MANAGER.package_path_from_package_id(
                    package_id=DUMMY_SERVICE
                )
            ),
            "--key",
            str(ETHEREUM_KEY_DEPLOYER),
            "-a",
            str(agent_id),
            *DEFAULT_SERVICE_MINT_PARAMETERS[2:],
            "--owner",
            CUSTOM_OWNER,
        )
        with patch_subgraph(
            response=[{"tokenId": agent_id, "publicId": "dummy_author/dummy_agent"}]
        ):
            result = self.run_cli(commands=commands)

        assert result.exit_code == 0, result
        assert "Service minted with:" in result.output
        assert "Metadata Hash:" in result.output
        assert "Token ID:" in result.output

        token_id = self.extract_token_id_from_output(output=result.output)
        self.verify_owner_address(
            token_id=token_id,
            owner=CUSTOM_OWNER,
            package_id=DUMMY_SERVICE,
        )
        self.verify_and_remove_metadata_file(token_id=token_id)

    def test_bad_owner_string(
        self,
    ) -> None:
        """Test connection error."""
        with patch_subgraph(
            response=[{"tokenId": 1, "publicId": "dummy_author/dummy_agent"}]
        ):
            result = self.run_cli(
                commands=(
                    "service",
                    str(
                        DUMMY_PACKAGE_MANAGER.package_path_from_package_id(
                            package_id=DUMMY_SERVICE
                        )
                    ),
                    "--key",
                    str(ETHEREUM_KEY_DEPLOYER),
                    *DEFAULT_SERVICE_MINT_PARAMETERS,
                    "--owner",
                    "0xowner",
                ),
            )
        self.cli_runner.mix_stderr = True
        assert result.exit_code == 1, result.output
        assert "Invalid owner address 0xowner" in result.stderr

    def test_fail_dependency_does_not_match_service(
        self,
    ) -> None:
        """Test token id retrieval failure."""
        with mock.patch.object(
            ChainConfigs, "get", return_value=ChainConfigs.local
        ), mock.patch(
            "autonomy.chain.utils.resolve_component_id",
            return_value={"name": "skill/author/name"},
        ):
            result = self.run_cli(
                commands=(
                    "--use-ethereum",
                    DUMMY_SERVICE.package_type.value,
                    str(
                        DUMMY_PACKAGE_MANAGER.package_path_from_package_id(
                            DUMMY_SERVICE
                        )
                    ),
                    "--key",
                    str(ETHEREUM_KEY_DEPLOYER),
                    "--nft",
                    "Qmbh9SQLbNRawh9Km3PMEDSxo77k1wib8fYZUdZkhPBiev",
                    *DEFAULT_SERVICE_MINT_PARAMETERS,
                ),
            )

        assert result.exit_code == 1, result.output
        assert (
            "Error: Public ID `valory/hello_world:any` for token 1 does not "
            "match with the one defained in the service package `dummy_author/dummy_agent:any`"
            in result.stderr
        )

    def test_dry_run(self) -> None:
        """Test dry run."""
        result = self.run_cli(
            commands=(
                "--dry-run",
                DUMMY_PROTOCOL.package_type.value,
                str(
                    DUMMY_PACKAGE_MANAGER.package_path_from_package_id(
                        package_id=DUMMY_PROTOCOL
                    )
                ),
                "--key",
                str(ETHEREUM_KEY_DEPLOYER),
            )
        )
        assert result.exit_code == 0, result.stderr
        assert "=== Dry run output ===" in result.output


class TestConnectionError(BaseCliTest):
    """Test connection error."""

    cli_options = ("mint",)

    def test_connection_error(self) -> None:
        """Test connection error."""
        self.cli_runner.mix_stderr = False
        result = self.run_cli(
            commands=(
                "protocol",
                str(
                    DUMMY_PACKAGE_MANAGER.package_path_from_package_id(
                        package_id=DUMMY_PROTOCOL
                    )
                ),
                "--key",
                str(ETHEREUM_KEY_DEPLOYER),
            ),
        )
        assert result.exit_code == 1, result.output
        assert "RPCError(Cannot connect to the given RPC)" in result.stderr
