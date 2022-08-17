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

"""Test `run` command."""


import os
from unittest import mock

from tests.test_autonomy.test_cli.base import BaseCliTest


class TestRun(BaseCliTest):
    """Test `run` command."""

    cli_options = ("deploy", "run")

    @classmethod
    def setup(cls) -> None:
        """Setup test."""

        super().setup()
        os.chdir(cls.t)

    def test_run(
        self,
    ) -> None:
        """Run test."""

        with mock.patch(
            "autonomy.cli.deploy.docker_compose.project_from_options"
        ), mock.patch("autonomy.cli.deploy.docker_compose.TopLevelCommand"):
            result = self.run_cli()
            assert result.exit_code == 0, result.output
            assert "Running build @" in result.output
