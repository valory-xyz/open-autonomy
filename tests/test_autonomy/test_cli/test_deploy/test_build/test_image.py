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

import os
import random
import string
from pathlib import Path
from typing import Tuple

import docker

from autonomy.constants import DEFAULT_BUILD_FOLDER

from tests.conftest import ROOT_DIR
from tests.helpers.docker.base import skip_docker_tests
from tests.test_autonomy.test_cli.base import BaseCliTest, cli


@skip_docker_tests
class TestBuildImage(BaseCliTest):
    """Test build image command."""

    cli_options: Tuple[str, ...] = ("deploy", "build", "image")
    service_id: str = "valory/oracle_hardhat"
    docker_api: docker.APIClient
    build_dir: Path

    @classmethod
    def setup(cls) -> None:
        """Setup class."""
        super().setup()

        cls.docker_api = docker.APIClient()
        os.chdir(cls.t)

        result = cls.cli_runner.invoke(
            cli,
            (
                "deploy",
                "build",
                "deployment",
                "valory/oracle_hardhat",
                str(ROOT_DIR / "deployments" / "keys" / "hardhat_keys.json"),
                "--packages-dir",
                str(ROOT_DIR / "packages"),
                "--force",
                "--local",
                "--skip-images",
                "--o",
                str(cls.t),
            ),
        )

        assert result.exit_code == 0, result.output
        cls.build_dir = cls.t / DEFAULT_BUILD_FOLDER
        os.chdir(cls.build_dir)

    @staticmethod
    def generate_random_tag(length: int = 16) -> str:
        """Generate random version tag."""

        return "".join(
            [random.choice(string.ascii_lowercase) for _ in range(length)]  # nosec
        )

    def test_build_prod(
        self,
    ) -> None:
        """Test prod build."""

        version = self.generate_random_tag()
        result = self.run_cli(("--version", version))

        assert result.exit_code == 0, f"{result.stdout_bytes}\n{result.stderr_bytes}"
        assert (
            len(
                self.docker_api.images(
                    name=f"valory/open-autonomy-open-aea:oracle-{version}"
                )
            )
            == 1
        )

    def test_dev(
        self,
    ) -> None:
        """Test prod build."""

        result = self.run_cli(("--dev",))
        assert result.exit_code == 0, f"{result.stdout_bytes}\n{result.stderr_bytes}"
        assert (
            len(self.docker_api.images(name="valory/open-autonomy-open-aea:oracle-dev"))
            == 1
        )

    def test_cluster(
        self,
    ) -> None:
        """Test prod build."""

        result = self.run_cli(("--cluster",))

        assert result.exit_code == 1, f"{result.stdout_bytes}\n{result.stderr_bytes}"
        assert (
            "Please setup kubernetes environment variables." in result.stdout
        ), f"{result.stdout_bytes}\n{result.stderr_bytes}"

    def test_build_dependencies(
        self,
    ) -> None:
        """Test prod build."""

        version = self.generate_random_tag()
        result = self.run_cli(("--dependencies", "--version", version))

        assert result.exit_code == 0, f"{result.stdout_bytes}\n{result.stderr_bytes}"
        assert (
            len(
                self.docker_api.images(
                    name=f"valory/open-autonomy-tendermint:{version}"
                )
            )
            == 1
        )
        assert (
            len(self.docker_api.images(name=f"valory/open-autonomy-hardhat:{version}"))
            == 1
        )

    @classmethod
    def teardown(cls) -> None:
        """Teardown."""

        os.chdir(cls.cwd)
        super().teardown()
