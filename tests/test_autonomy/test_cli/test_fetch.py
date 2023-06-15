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

"""Test fetch command."""

import os
import shutil
from pathlib import Path
from unittest import mock

from aea.cli.fetch import NotAnAgentPackage
from aea.configurations.constants import (
    DEFAULT_README_FILE,
    DEFAULT_SERVICE_CONFIG_FILE,
)
from aea.configurations.loader import ConfigLoader
from aea.helpers.base import cd
from aea.helpers.io import open_file

from autonomy.cli.helpers.registry import IPFSTool
from autonomy.configurations.base import Service

from tests.conftest import ROOT_DIR
from tests.test_autonomy.base import get_dummy_service_config
from tests.test_autonomy.test_cli.base import BaseCliTest, cli


IPFS_REGISTRY = "/dns/registry.autonolas.tech/tcp/443/https"


class FetchTest(BaseCliTest):
    """FetchTest base class"""

    packages_dir: Path
    package_type: str  # agent or service

    def setup(self) -> None:
        """Setup class."""

        super().setup()

        self.packages_dir = self.t / "packages"
        self.cli_options = (
            "--registry-path",
            str(self.packages_dir),
            "fetch",
            f"--{self.package_type}",
        )

        shutil.copytree(ROOT_DIR / "packages", self.packages_dir)
        os.chdir(self.t)


class TestFetchAgentCommand(FetchTest):
    """Test fetch agent command"""

    package_type = "agent"

    def test_fetch_agent(self) -> None:
        """Test fetch agent"""

        result = self.run_cli(("--local", "valory/counter"))
        assert result.exit_code == 0
        assert "Agent counter successfully fetched." in result.stdout

    def test_not_an_agent_package_raises(self) -> None:
        """Test fetch agent"""

        expected = "Error: Downloaded packages is not an agent package, if you intend to download a service please use `--service` flag or check the hash"
        with mock.patch("autonomy.cli.fetch.do_fetch", side_effect=NotAnAgentPackage):
            result = self.run_cli(("--remote", "valory/counter"))
            assert result.exit_code == 1
            assert expected in result.stdout


class TestFetchServiceCommand(FetchTest):
    """Test fetch service command."""

    package_type = "service"

    def test_fetch_service_local(
        self,
    ) -> None:
        """Test fetch service."""

        service = self.t / "counter"
        result = self.run_cli(("--local", "valory/counter"))

        assert result.exit_code == 0, result.output
        assert service.exists()

        result = self.run_cli(("--local", "valory/counter"))
        assert result.exit_code == 1, result.output
        assert (
            'Item "counter" already exists in target folder' in result.output
        ), result.output

        shutil.rmtree(service)

    def test_publish_and_fetch_service_ipfs(self) -> None:
        """Test fetch service."""
        expected_hash = "bafybeicojucnpgeud7lmomfkppwbnxpnbtfwvqritalkzessfjbcze27re"

        service_dir = self.t / "dummy_service"
        service_file = service_dir / DEFAULT_SERVICE_CONFIG_FILE
        service_dir.mkdir()
        with open_file(service_file, "w+") as fp:
            service_conf, *overrides = get_dummy_service_config()
            service_conf["overrides"] = overrides
            service = Service.from_json(service_conf)
            ConfigLoader(Service.schema, Service).dump(service, fp)

        (service_dir / DEFAULT_README_FILE).write_text("Dummy Service")

        with mock.patch(
            "autonomy.cli.helpers.registry.get_default_remote_registry",
            new=lambda: "ipfs",
        ), mock.patch(
            "autonomy.cli.helpers.registry.get_ipfs_node_multiaddr",
            new=lambda: IPFS_REGISTRY,
        ), cd(
            service_dir
        ):
            result = self.cli_runner.invoke(cli, ["publish", "--remote"])

            assert result.exit_code == 0, result.output
            assert expected_hash in result.output

        with mock.patch(
            "autonomy.cli.helpers.registry.get_default_remote_registry",
            new=lambda: "http",
        ), cd(service_dir):
            result = self.run_cli(("--remote", expected_hash))
            assert result.exit_code == 1, result.output
            assert "HTTP registry not supported." in result.output, result.output

        with mock.patch(
            "autonomy.cli.helpers.registry.get_default_remote_registry",
            new=lambda: "ipfs",
        ), mock.patch(
            "autonomy.cli.helpers.registry.get_ipfs_node_multiaddr",
            new=lambda: IPFS_REGISTRY,
        ), cd(
            service_dir
        ):
            result = self.run_cli(("--remote", expected_hash))
            assert result.exit_code == 0, result.output
            assert service_dir.exists()

        alias = "some_service"

        with mock.patch(
            "autonomy.cli.helpers.registry.get_default_remote_registry",
            new=lambda: "ipfs",
        ), mock.patch(
            "autonomy.cli.helpers.registry.get_ipfs_node_multiaddr",
            new=lambda: IPFS_REGISTRY,
        ), cd(
            service_dir.parent
        ):
            result = self.run_cli(("--remote", "--alias", alias, expected_hash))
            assert result.exit_code == 0, result.output
            assert (service_dir.parent / alias).exists()

        shutil.rmtree(service_dir)

    def test_fetch_service_mixed(
        self,
    ) -> None:
        """Test fetch service in mixed mode."""
        with mock.patch(
            "autonomy.cli.helpers.registry.fetch_service_local",
            side_effect=Exception("expected"),
        ) as fetch_local_mock, mock.patch(
            "autonomy.cli.helpers.registry.fetch_service_ipfs"
        ) as fetch_remote_mock:
            result = self.run_cli(("--mixed", "valory/counter"))

        assert result.exit_code == 0, result.output
        fetch_local_mock.assert_called_once()
        fetch_remote_mock.assert_called_once()

    def test_not_a_service_package(
        self,
    ) -> None:
        """Test fetch service."""
        with mock.patch(
            "autonomy.cli.helpers.registry.get_default_remote_registry",
            new=lambda: "ipfs",
        ), mock.patch(
            "autonomy.cli.helpers.registry.get_ipfs_node_multiaddr",
            new=lambda: IPFS_REGISTRY,
        ), mock.patch.object(
            IPFSTool, "download", return_value=self.t
        ):
            result = self.run_cli(
                (
                    "--remote",
                    "bafybeicqvwvogloyw2ujhedbwv4opn2ngus6dh7ocxg7umhhawcnzpibrq",
                )
            )
            assert result.exit_code == 1, result.output
            assert (
                "Downloaded packages is not a service package, "
                "if you intend to download an agent please use "
                "`--agent` flag or check the hash"
            ) in result.output
