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

"""Test push-all command group."""


import os
import shutil
from pathlib import Path
from typing import Any, Tuple
from unittest import mock

import _strptime  # noqa  # pylint: disable=unsed-import
from aea.cli.registry.settings import REMOTE_IPFS
from aea.configurations.constants import PACKAGES
from aea.package_manager.v1 import PackageManagerV1

from tests.conftest import ROOT_DIR
from tests.test_autonomy.test_cli.base import BaseCliTest


class TestPushAll(BaseCliTest):
    """Test `push-all` command."""

    cli_options: Tuple[str, ...] = ("push-all", "--remote")
    packages_dir: Path

    def setup(self) -> None:
        """Setup test method."""

        super().setup()

        self.packages_dir = self.t / PACKAGES
        shutil.copytree(ROOT_DIR / PACKAGES, self.packages_dir)
        os.chdir(self.t)

    def test_run(
        self,
    ) -> None:
        """Test run."""

        # packages/<author>/<component>/<name>/<config>.yaml
        available_packages = len(
            PackageManagerV1.from_dir(ROOT_DIR / PACKAGES).dev_packages
        )
        published_packages = []

        def _push_patch(_: Any, public_id: Any) -> None:
            published_packages.append(public_id)

        with mock.patch(
            "aea.cli.push_all.get_default_remote_registry", new=lambda: REMOTE_IPFS
        ), mock.patch("aea.cli.push_all.push_item_ipfs", new=_push_patch):
            result = self.run_cli()

        assert result.exit_code == 0, result.output
        assert len(published_packages) == available_packages
