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

"""Test `run` command."""


import os
from unittest import mock

from autonomy.constants import DOCKER_COMPOSE_YAML

from tests.test_autonomy.test_cli.base import BaseCliTest


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
