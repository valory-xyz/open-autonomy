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

"""Test `from-token` command."""


import os
from unittest import mock

from tests.conftest import ROOT_DIR
from tests.test_autonomy.test_cli.base import BaseCliTest


class TestFromToken(BaseCliTest):
    """Test `from-token` command."""

    cli_options = ("deploy", "from-token")
    keys_file = ROOT_DIR / "deployments" / "hardhat_keys.json"
    token = 2
    chain = "staging"

    @classmethod
    def setup(cls) -> None:
        """Setup test."""

        super().setup()
        os.chdir(cls.t)

    def test_from_token(
        self,
    ) -> None:
        """Run test."""

        with mock.patch("autonomy.cli.deploy.run_deployment"), mock.patch(
            "autonomy.cli.deploy.build_image"
        ), mock.patch("autonomy.cli.deploy.build_deployment"), mock.patch(
            "click.echo"
        ) as click_mock:
            result = self.run_cli(
                (str(self.token), str(self.keys_file), f"--use-{self.chain}")
            )

            assert result.exit_code == 0, result.output
            assert (
                "Building service deployment using token ID: 2"
                in click_mock.call_args_list[0][0][0]
            )
            assert "Service name: Hello World" in click_mock.call_args_list[1][0][0]
            assert (
                "Downloaded service package valory/hello_world:0.1.0"
                in click_mock.call_args_list[2][0][0]
            )
            assert "Service build successful." in click_mock.call_args_list[3][0][0]
