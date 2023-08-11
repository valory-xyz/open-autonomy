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

"""Test `from-token` command."""

import json
import os
from pathlib import Path
from unittest import mock

import pytest
from aea.cli.registry.settings import REMOTE_IPFS
from aea_test_autonomy.fixture_helpers import registries_scope_class  # noqa: F401

from autonomy.chain.exceptions import FailedToRetrieveComponentMetadata

from tests.conftest import ROOT_DIR, skip_docker_tests
from tests.test_autonomy.test_chain.base import BaseChainInteractionTest


MOCK_IPFS_RESPONSE = {
    "name": "valory/oracle_hardhat",
    "description": "Oracle service.",
    "code_uri": "ipfs://bafybeiansmhkoovd6jlnyurm2w4qzhpmi43gxlyenq33ioovy2rh4gziji",
    "image": "bafybeiansmhkoovd6jlnyurm2w4qzhpmi43gxlyenq33ioovy2rh4gziji",
    "attributes": [{"trait_type": "version", "value": "0.1.0"}],
}
REGISTERED_KEYS = [
    {
        "address": "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266",
        "private_key": "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80",
    },
    {
        "address": "0x70997970C51812dc3A010C7d01b50e0d17dc79C8",
        "private_key": "0x59c6995e998f97a5a0044966f0945389dc9e86dae88c7a8412f4603b6b78690d",
    },
    {
        "address": "0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC",
        "private_key": "0x5de4111afa1a4b94908f83103eb1f1706367c2e68ca870fc3fb9a804cdab365a",
    },
    {
        "address": "0x90F79bf6EB2c4f870365E785982E1f101E93b906",
        "private_key": "0x7c852118294e51e653712a81e05800f419141751be58f605c371e15141b007a6",
    },
]

run_deployment_patch = mock.patch("autonomy.cli.helpers.deployment.run_deployment")
build_image_patch = mock.patch("autonomy.cli.helpers.deployment.build_image")
default_remote_registry_patch = mock.patch(
    "autonomy.cli.helpers.registry.get_default_remote_registry",
    new=lambda: REMOTE_IPFS,
)
default_ipfs_node_patch = mock.patch(
    "autonomy.cli.helpers.registry.get_ipfs_node_multiaddr",
    new=lambda: "/dns/registry.autonolas.tech/tcp/443/https",
)
ipfs_resolve_patch = mock.patch(
    "autonomy.cli.helpers.deployment.resolve_component_id",
    return_value=MOCK_IPFS_RESPONSE,
)


@pytest.mark.integration
@skip_docker_tests
class TestFromToken(BaseChainInteractionTest):
    """Test `from-token` command."""

    cli_options = ("deploy", "from-token")
    token = 1
    chain = "staging"
    keys_file: Path

    def setup(self) -> None:
        """Setup test method."""
        super().setup()

        os.chdir(self.t)
        self.keys_file = self.t / "keys.json"
        self.keys_file.write_text(json.dumps(REGISTERED_KEYS))

    def test_from_token(
        self,
    ) -> None:
        """Run test."""

        service_dir = self.t / "service"
        service_dir.mkdir()

        service_file = service_dir / "service.yaml"
        service_file.write_text(
            (
                ROOT_DIR
                / "tests"
                / "data"
                / "dummy_service_config_files"
                / "service_0.yaml"
            ).read_text()
        )

        with mock.patch(
            "autonomy.cli.helpers.deployment.fetch_service_ipfs",
            return_value=service_dir,
        ), (
            run_deployment_patch
        ), (
            build_image_patch
        ), default_remote_registry_patch, default_ipfs_node_patch, ipfs_resolve_patch:
            result = self.run_cli(
                (
                    str(self.token),
                    str(self.keys_file),
                )
            )

            assert result.exit_code == 0, result.stdout
            assert "Service name: valory/oracle_hardhat" in result.stdout
            assert "Building required images" in result.stdout
            assert "Service build successful" in result.stdout

    def test_from_token_kubernetes(
        self,
    ) -> None:
        """Run test."""

        service_dir = self.t / "service"
        service_dir.mkdir()

        service_file = service_dir / "service.yaml"
        service_file.write_text(
            (
                ROOT_DIR
                / "tests"
                / "data"
                / "dummy_service_config_files"
                / "service_0.yaml"
            ).read_text()
        )

        with mock.patch(
            "autonomy.cli.helpers.deployment.fetch_service_ipfs",
            return_value=service_dir,
        ), run_deployment_patch as rdp, (
            build_image_patch
        ), default_remote_registry_patch, default_ipfs_node_patch, ipfs_resolve_patch:
            result = self.run_cli(
                (str(self.token), str(self.keys_file), "--kubernetes")
            )

            assert result.exit_code == 0, result.stdout
            assert "Service name: valory/oracle_hardhat" in result.stdout
            assert "Building required images" in result.stdout
            assert "Service build successful" in result.stdout
            assert "Type:                 kubernetes" in result.stdout
            assert "Running deployment" not in result.output

            rdp.assert_not_called()

        assert (self.t / "service" / "abci_build" / "build.yaml").exists()

    def test_fail_on_chain_resolve_connection_error(self) -> None:
        """Run test."""

        with (
            run_deployment_patch
        ), (
            build_image_patch
        ), (
            default_remote_registry_patch
        ), default_ipfs_node_patch, ipfs_resolve_patch, mock.patch(
            "autonomy.cli.helpers.deployment.resolve_component_id",
            side_effect=FailedToRetrieveComponentMetadata(
                "Error connecting RPC endpoint"
            ),
        ):
            result = self.run_cli(
                (
                    str(self.token),
                    str(self.keys_file),
                )
            )

            assert result.exit_code == 1, result.stdout
            assert "Error connecting RPC endpoint" in result.stderr, result.output

    def test_fail_on_chain_resolve_bad_contract_call(self) -> None:
        """Run test."""

        with (
            run_deployment_patch
        ), (
            build_image_patch
        ), (
            default_remote_registry_patch
        ), default_ipfs_node_patch, ipfs_resolve_patch, mock.patch(
            "autonomy.cli.helpers.deployment.resolve_component_id",
            side_effect=Exception,
        ):
            result = self.run_cli(
                (
                    str(self.token),
                    str(self.keys_file),
                )
            )

            assert result.exit_code == 1, result.stdout
            assert "Cannot find the service registry deployment;" in result.stderr
