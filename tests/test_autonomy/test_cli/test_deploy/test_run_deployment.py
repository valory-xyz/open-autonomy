# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022-2025 Valory AG
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

"""Test `run` command."""


import json
import os
import shutil
from unittest import mock

from aea.configurations.constants import DEFAULT_AEA_CONFIG_FILE, PACKAGES

from autonomy.constants import DEFAULT_BUILD_FOLDER, DOCKER_COMPOSE_YAML, VALORY
from autonomy.deploy.base import ServiceBuilder
from autonomy.deploy.constants import (
    AGENT_VARS_CONFIG_FILE,
    TENDERMINT_VARS_CONFIG_FILE,
)

from tests.conftest import ROOT_DIR
from tests.test_autonomy.test_cli.base import BaseCliTest
from tests.test_autonomy.test_cli.test_deploy.test_build.test_deployment import (
    OS_ENV_PATCH,
)


class TestRun(BaseCliTest):
    """Test `run` command."""

    cli_options = ("deploy", "run")

    def setup(self) -> None:
        """Setup test method."""

        super().setup()
        os.chdir(self.t)

    def test_run(
        self,
    ) -> None:
        """Run test."""
        (self.t / DOCKER_COMPOSE_YAML).touch()
        with mock.patch(
            "autonomy.cli.helpers.deployment.docker_compose.project_from_options"
        ), mock.patch("autonomy.cli.helpers.deployment.docker_compose.TopLevelCommand"):
            result = self.run_cli(("--detach",))
            assert result.exit_code == 0, result.output
            assert "Running build @" in result.output

    def test_run_local(self) -> None:
        """Test that `deploy run` works on localhost."""
        super().setup()

        # setup the service keys and packages
        self.keys_file = self.t / "keys.json"
        shutil.copytree(ROOT_DIR / PACKAGES, self.t / PACKAGES)
        shutil.copy(
            ROOT_DIR / "deployments" / "keys" / "hardhat_keys.json", self.keys_file
        )
        shutil.copytree(
            self.t / PACKAGES / "valory" / "services" / "register_reset",
            self.t / "register_reset",
        )
        with OS_ENV_PATCH:
            self.spec = ServiceBuilder.from_dir(
                self.t / "register_reset",
                self.keys_file,
            )
        os.chdir(self.t / "register_reset")

        # setup aea-config.yaml
        shutil.copy(
            ROOT_DIR
            / PACKAGES
            / VALORY
            / "agents"
            / "register_reset"
            / DEFAULT_AEA_CONFIG_FILE,
            self.t / "register_reset",
        )

        # setup agent.json and tendermint.json
        os.mkdir(build_path := self.t / "register_reset" / DEFAULT_BUILD_FOLDER)
        with open(build_path / TENDERMINT_VARS_CONFIG_FILE, "w") as fp:
            json.dump({}, fp)
        with open(build_path / AGENT_VARS_CONFIG_FILE, "w") as fp:
            json.dump({}, fp)
        with mock.patch("autonomy.cli.helpers.deployment.subprocess.run"), mock.patch(
            "autonomy.cli.helpers.deployment.subprocess.Popen"
        ), mock.patch("autonomy.cli.helpers.deployment.check_tendermint_version"):
            result = self.run_cli(("--localhost", "--build-dir", build_path.as_posix()))
            assert result.exit_code == 0, result.output
            assert "Running build @" in result.output

    def test_missing_config_file(
        self,
    ) -> None:
        """Run test."""
        result = self.run_cli()
        assert result.exit_code == 1, result.output
        assert "Deployment configuration does not exist" in result.output


class TestStop(BaseCliTest):
    """Test `stop` command."""

    cli_options = ("deploy", "stop")

    def setup(self) -> None:
        """Setup test method."""
        super().setup()
        os.chdir(self.t)

    def test_run(
        self,
    ) -> None:
        """Run test."""
        (self.t / DOCKER_COMPOSE_YAML).touch()
        with mock.patch(
            "autonomy.cli.helpers.deployment.docker_compose.project_from_options"
        ), mock.patch("autonomy.cli.helpers.deployment.docker_compose.TopLevelCommand"):
            result = self.run_cli()
            assert result.exit_code == 0, result.output
            assert "Don't cancel while stopping services..." in result.output

    def test_missing_config_file(
        self,
    ) -> None:
        """Run test."""
        result = self.run_cli()
        assert result.exit_code == 1, result.output
        assert "Deployment configuration does not exist" in result.output
