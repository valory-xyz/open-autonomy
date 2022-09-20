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
from unittest import mock

import pytest
from aea_test_autonomy.docker.registries import SERVICE_REGISTRY
from aea_test_autonomy.fixture_helpers import registries_scope_class  # noqa: F401

from tests.conftest import ROOT_DIR, skip_docker_tests
from tests.test_autonomy.test_cli.base import BaseCliTest


@pytest.mark.usefixtures("registries_scope_class")
@pytest.mark.integration
@skip_docker_tests
class TestFromToken(BaseCliTest):
    """Test `from-token` command."""

    cli_options = ("deploy", "from-token")
    keys_file = ROOT_DIR / "deployments" / "hardhat_keys.json"
    token = 1
    chain = "staging"

    @classmethod
    def setup(cls) -> None:
        """Setup test."""

        super().setup()
        os.chdir(cls.t)

    def test_from_token(
        self,
    ) -> None:
        """Run test."""
        mock_ipfs_response = {
            "name": "valory/oracle_hardhat",
            "description": "Oracle service.",
            "code_uri": "ipfs://bafybeiansmhkoovd6jlnyurm2w4qzhpmi43gxlyenq33ioovy2rh4gziji",
            "image": "bafybeiansmhkoovd6jlnyurm2w4qzhpmi43gxlyenq33ioovy2rh4gziji",
            "attributes": [{"trait_type": "version", "value": "0.1.0"}],
        }
        with mock.patch("autonomy.cli.deploy.run_deployment"), mock.patch(
            "autonomy.cli.deploy.build_image"
        ), mock.patch("autonomy.cli.deploy.build_deployment"), mock.patch(
            "click.echo"
        ) as click_mock, mock.patch(
            "autonomy.cli.fetch.get_default_remote_registry", new=lambda: "ipfs"
        ), mock.patch(
            "autonomy.cli.fetch.get_ipfs_node_multiaddr",
            new=lambda: "/dns/registry.autonolas.tech/tcp/443/https",
        ), mock.patch(
            "autonomy.deploy.chain.ServiceRegistry._resolve_from_ipfs",
            return_value=mock_ipfs_response,
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

            assert result.exit_code == 0, click_mock.call_args_list
            assert (
                "Building service deployment using token ID: 1"
                in click_mock.call_args_list[0][0][0]
            )
            assert "Service name: " in click_mock.call_args_list[1][0][0]
            assert (
                "Downloaded service package valory/oracle_hardhat:0.1.0"
                in click_mock.call_args_list[2][0][0]
            )
            assert "Building required images" in click_mock.call_args_list[3][0][0]
            assert "Service build successful" in click_mock.call_args_list[4][0][0]
