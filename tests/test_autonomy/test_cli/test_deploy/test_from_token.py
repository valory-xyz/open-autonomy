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

"""Test `from-token` command."""

import os
from typing import Any
from unittest import mock

import pytest
from aea.cli.registry.settings import REMOTE_IPFS
from aea_test_autonomy.docker.registries import SERVICE_REGISTRY
from aea_test_autonomy.fixture_helpers import registries_scope_class  # noqa: F401

from autonomy.cli.helpers.deployment import (
    BadFunctionCallOutput,
    RequestsConnectionError,
)
from autonomy.deploy.chain import ServiceRegistry

from tests.conftest import ROOT_DIR, skip_docker_tests
from tests.test_autonomy.test_cli.base import BaseCliTest


MOCK_IPFS_RESPONSE = {
    "name": "valory/oracle_hardhat",
    "description": "Oracle service.",
    "code_uri": "ipfs://bafybeiansmhkoovd6jlnyurm2w4qzhpmi43gxlyenq33ioovy2rh4gziji",
    "image": "bafybeiansmhkoovd6jlnyurm2w4qzhpmi43gxlyenq33ioovy2rh4gziji",
    "attributes": [{"trait_type": "version", "value": "0.1.0"}],
}

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
    "autonomy.deploy.chain.ServiceRegistry._resolve_from_ipfs",
    return_value=MOCK_IPFS_RESPONSE,
)


@pytest.mark.usefixtures("registries_scope_class")
@pytest.mark.integration
@skip_docker_tests
class TestFromToken(BaseCliTest):
    """Test `from-token` command."""

    cli_options = ("deploy", "from-token")
    keys_file = ROOT_DIR / "deployments" / "keys" / "hardhat_keys.json"
    token = 1
    chain = "staging"

    def setup(self) -> None:
        """Setup test method."""
        super().setup()

        os.chdir(self.t)

    def test_from_token(
        self,
        capsys: Any,
    ) -> None:
        """Run test."""

        with run_deployment_patch, build_image_patch, default_remote_registry_patch, default_ipfs_node_patch, ipfs_resolve_patch:
            result = self.run_cli(
                (
                    str(self.token),
                    str(self.keys_file),
                    "--rpc",
                    "http://localhost:8545/",
                    "--sca",
                    SERVICE_REGISTRY,
                )
            )

            out, err = capsys.readouterr()

            assert result.exit_code == 0, err
            assert "Service name: valory/oracle_hardhat" in out, err
            assert "Downloaded service package valory/oracle_hardhat:0.1.0" in out, err
            assert "Building required images" in out, err
            assert "Service build successful" in out, err

    def test_fail_on_chain_resolve_connection_error(self) -> None:
        """Run test."""

        with run_deployment_patch, build_image_patch, default_remote_registry_patch, default_ipfs_node_patch, ipfs_resolve_patch, mock.patch.object(
            ServiceRegistry, "resolve_token_id", side_effect=RequestsConnectionError
        ):
            result = self.run_cli(
                (
                    str(self.token),
                    str(self.keys_file),
                    "--rpc",
                    "http://localhost:8545/",
                    "--sca",
                    SERVICE_REGISTRY,
                )
            )

            assert result.exit_code == 1, result.stdout
            assert (
                "Error connecting RPC endpoint; RPC=http://localhost:8545/"
                in result.stdout
            )

    def test_fail_on_chain_resolve_bad_contract_call(self) -> None:
        """Run test."""

        with run_deployment_patch, build_image_patch, default_remote_registry_patch, default_ipfs_node_patch, ipfs_resolve_patch, mock.patch.object(
            ServiceRegistry, "resolve_token_id", side_effect=BadFunctionCallOutput
        ):
            result = self.run_cli(
                (
                    str(self.token),
                    str(self.keys_file),
                    "--rpc",
                    "http://localhost:8545/",
                    "--sca",
                    SERVICE_REGISTRY,
                )
            )

            assert result.exit_code == 1, result.stdout
            assert "Cannot find the service registry deployment;" in result.stdout
