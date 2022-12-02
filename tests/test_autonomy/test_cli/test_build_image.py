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

"""Test build image."""

import json
import os
import shutil
from pathlib import Path
from random import choices
from string import ascii_letters
from typing import Any, Tuple

import docker
from aea.configurations.constants import PACKAGES

from tests.conftest import ROOT_DIR, skip_docker_tests
from tests.test_autonomy.test_cli.base import BaseCliTest


@skip_docker_tests
class TestBuildImage(BaseCliTest):
    """Test build image command."""

    cli_options: Tuple[str, ...] = ("build-image",)
    docker_api: docker.APIClient
    build_dir: Path
    hash_: str

    def setup(self) -> None:
        """Setup class."""
        super().setup()

        self.docker_api = docker.APIClient()

        with open(ROOT_DIR / PACKAGES / "packages.json") as json_data:
            d = json.load(json_data)
            self.hash_ = d["dev"]["agent/valory/hello_world/0.1.0"]
            json_data.close()
        shutil.copytree(
            ROOT_DIR / PACKAGES / "valory" / "services" / "hello_world",
            self.t / "hello_world",
        )
        os.chdir(self.t / "hello_world")

    def test_build_prod(
        self,
    ) -> None:
        """Test prod build."""

        result = self.run_cli()

        assert result.exit_code == 0, result.output
        assert (
            len(self.docker_api.images(name=f"valory/oar-hello_world:{self.hash_}"))
            == 1
        )

    def test_build_dev(
        self,
    ) -> None:
        """Test prod build."""

        result = self.run_cli(("--dev",))

        assert result.exit_code == 0, result.output
        assert len(self.docker_api.images(name="valory/oar-hello_world:dev")) == 1

    def test_build_version(
        self,
    ) -> None:
        """Test prod build."""

        test_version = "".join(choices(ascii_letters, k=6))
        result = self.run_cli(("--version", test_version))

        assert result.exit_code == 0, result.output
        assert (
            len(self.docker_api.images(name=f"valory/oar-hello_world:{test_version}"))
            == 1
        )


class TestBuildImageFailures(BaseCliTest):
    """Test build image command."""

    cli_options: Tuple[str, ...] = ("build-image",)
    docker_api: docker.APIClient
    build_dir: Path
    hash_: str

    def test_service_file_missing(
        self,
    ) -> None:
        """Test prod build."""

        result = self.run_cli()

        assert result.exit_code == 1, result.output
        assert "Service configuration not found the current directory" in result.output

    def test_image_build_fail(self, capsys: Any) -> None:
        """Test prod build."""

        result = self.run_cli(
            commands=(
                "valory/agent:bafybeihyasfforsfualp6jnhh2jj7nreqmws2ygyfnh4p3idmfkm5yxu11",
            )
        )

        out, err = capsys.readouterr()
        assert result.exit_code == 1, out
        assert "Error occured while downloading agent" in out
        assert "Image build failed with error" in err
