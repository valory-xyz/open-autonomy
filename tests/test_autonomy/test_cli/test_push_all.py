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

from tests.conftest import ROOT_DIR
from tests.test_autonomy.test_cli.base import BaseCliTest


class TestPushAll(BaseCliTest):
    """Test `push-all` command."""

    cli_options: Tuple[str, ...] = ("push-all", "--remote")
    packages_dir: Path

    @classmethod
    def setup(cls) -> None:
        """Setup class."""

        super().setup()

        cls.packages_dir = cls.t / "packages"
        shutil.copytree(ROOT_DIR / "packages", cls.packages_dir)
        os.chdir(cls.t)

    def test_run(
        self,
    ) -> None:
        """Test run."""

        packages = set([file.parent for file in self.t.glob("**/*yaml")])
        published_packages = []

        def _push_patch(_: Any, public_id: Any) -> None:
            published_packages.append(public_id)

        with mock.patch(
            "aea.cli.push_all.get_default_remote_registry", new=lambda: REMOTE_IPFS
        ), mock.patch("aea.cli.push_all.push_item_ipfs", new=_push_patch):
            result = self.run_cli()

        assert result.exit_code == 0, result.output
        assert len(published_packages) == len(packages)
