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

"""Test fetch command."""

import os
import shutil
from pathlib import Path
from unittest import mock

from tests.conftest import ROOT_DIR
from tests.test_autonomy.test_cli.base import BaseCliTest


IPFS_REGISTRY = "/dns/registry.autonolas.tech/tcp/443/https"


class TestFetchCommand(BaseCliTest):
    """Test fetch command."""

    packages_dir: Path

    @classmethod
    def setup(cls) -> None:
        """Setup class."""

        super().setup()

        cls.packages_dir = cls.t / "packages"
        cls.cli_options = (
            "--registry-path",
            str(cls.packages_dir),
            "fetch",
            "--service",
        )

        shutil.copytree(ROOT_DIR / "packages", cls.packages_dir)
        os.chdir(cls.t)

    def get_service_hash(
        self,
    ) -> str:
        """Load hashes from CSV file."""

        hashes_file = self.packages_dir / "hashes.csv"
        with open(str(hashes_file), "r") as file:
            content = file.read().strip()
        hashes = dict([line.split(",") for line in content.split("\n") if "," in line])  # type: ignore
        return hashes["valory/services/counter"]

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

    def test_fetch_service_ipfs(
        self,
    ) -> None:
        """Test fetch service."""

        service = self.t / "counter"
        service_hash = self.get_service_hash()

        with mock.patch(
            "autonomy.cli.fetch.get_default_remote_registry", new=lambda: "http"
        ):
            result = self.run_cli(("--remote", service_hash))
            assert result.exit_code == 1, result.output
            assert "HTTP registry not supported." in result.output, result.output

        with mock.patch(
            "autonomy.cli.fetch.get_default_remote_registry", new=lambda: "ipfs"
        ), mock.patch(
            "autonomy.cli.fetch.get_ipfs_node_multiaddr", new=lambda: IPFS_REGISTRY
        ):
            result = self.run_cli(("--remote", service_hash))

        assert result.exit_code == 0, result.output
        assert service.exists()

        shutil.rmtree(service)
