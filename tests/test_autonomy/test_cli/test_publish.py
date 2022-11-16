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

"""Test hash command group."""


import os
import shutil
from pathlib import Path
from typing import Tuple
from unittest import mock

from autonomy.cli.helpers.registry import IPFSTool, REMOTE_IPFS, to_v1

from tests.conftest import ROOT_DIR
from tests.test_autonomy.test_cli.base import BaseCliTest


class TestPublish(BaseCliTest):
    """Test `publish` command."""

    packages_dir: Path
    agent_dir: Path
    service_dir: Path
    temp_local_registry: Path

    cli_options: Tuple[str, ...] = ("publish",)

    def setup(self) -> None:
        """Setup class."""

        super().setup()

        self.packages_dir = self.t / "packages"
        self.service_dir = self.t / "packages" / "valory" / "services" / "counter"
        self.temp_local_registry = self.t / "temp_reg"
        self.temp_local_registry.mkdir()
        self.cli_options = (
            "--registry-path",
            str(self.temp_local_registry),
            "publish",
        )

        shutil.copytree(ROOT_DIR / "packages", self.packages_dir)
        os.chdir(self.service_dir)

    def test_local(
        self,
    ) -> None:
        """Test publish service locally."""
        result = self.run_cli(("--local",))

        assert result.exit_code == 0, result.output
        assert (
            'Service "counter" successfully published on the local packages directory.'
            in result.output
        )

    def test_ipfs(
        self,
    ) -> None:
        """Test publish service on IPFS registry."""

        dummy_hash_v0 = "QmeU1Cz796TBihCT426pA3HAYC7LhaawsXgGmy1hpyZXj9"
        dummy_hash_v1 = to_v1("QmeU1Cz796TBihCT426pA3HAYC7LhaawsXgGmy1hpyZXj9")

        with mock.patch(
            "autonomy.cli.helpers.registry.get_default_remote_registry",
            new=lambda: REMOTE_IPFS,
        ), mock.patch.object(
            IPFSTool,
            "add",
            new=lambda *_: (
                None,
                dummy_hash_v0,
                None,
            ),
        ):
            result = self.run_cli(("--remote",))

        msg_check = f"""Service "counter" successfully published on the IPFS registry.\n\tPublicId: valory/counter:0.1.0\n\tPackage hash: {dummy_hash_v1}"""
        assert result.exit_code == 0, result.output
        assert msg_check in result.output, result.output
