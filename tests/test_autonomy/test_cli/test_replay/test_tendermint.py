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

"""Test agent runner."""


import json
import os
from pathlib import Path
from typing import Any, Tuple
from unittest import mock

import flask

from autonomy.cli import cli
from autonomy.deploy.constants import (
    DEFAULT_ABCI_BUILD_DIR,
    PERSISTENT_DATA_DIR,
    TM_STATE_DIR,
)
from autonomy.replay.tendermint import TendermintNetwork
from autonomy.test_tools.docker.base import skip_docker_tests

from tests.conftest import ROOT_DIR
from tests.test_autonomy.test_cli.base import BaseCliTest


ADDRBOOK_DATA = {
    "key": "53f91939db980b06e7cfb145",
    "addrs": [
        {
            "addr": {
                "id": "4fa21e46ad7cdfa028761f13e460de2dd6eb93c8",
                "ip": "192.167.11.3",
                "port": 26656,
            },
        },
        {
            "addr": {
                "id": "3d495cf3bf345b7e04a849e6e70900f5d2cbfcd3",
                "ip": "192.167.11.4",
                "port": 26656,
            },
        },
        {
            "addr": {
                "id": "cf52b0f56ad58f5aa400f813f16f35cf726ff3e4",
                "ip": "192.167.11.5",
                "port": 26656,
            },
        },
    ],
}


def ctrl_c(*args: Any, **kwargs: Any) -> None:
    """Send control C."""

    raise KeyboardInterrupt()


@skip_docker_tests
class TestTendermintRunner(BaseCliTest):
    """Test agent runner tool."""

    cli_options: Tuple[str, ...] = ("replay", "tendermint")
    packages_dir: Path = ROOT_DIR / "packages"
    output_dir: Path = ROOT_DIR
    keys_path: Path = ROOT_DIR / "deployments" / "keys" / "hardhat_keys.json"

    @classmethod
    def setup(cls) -> None:
        """Setup."""
        super().setup()
        os.chdir(cls.t)

    def test_run(self) -> None:
        """Test run."""
        result = self.cli_runner.invoke(
            cli,
            (
                "deploy",
                "build",
                "deployment",
                "valory/oracle_hardhat",
                str(self.keys_path),
                "--packages-dir",
                str(self.packages_dir),
                "--force",
                "--o",
                str(self.t),
                "--local",
            ),
        )

        assert result.exit_code == 0, result.output

        addrbook_file = (
            (
                self.t
                / DEFAULT_ABCI_BUILD_DIR
                / PERSISTENT_DATA_DIR
                / TM_STATE_DIR
                / "addrbook.json"
            )
            .resolve()
            .absolute()
        )
        addrbook_file.write_text(json.dumps(ADDRBOOK_DATA))

        config_toml = (
            (
                self.t
                / DEFAULT_ABCI_BUILD_DIR
                / PERSISTENT_DATA_DIR
                / TM_STATE_DIR
                / "config.toml"
            )
            .resolve()
            .absolute()
        )
        config_toml.write_text("""persistent_peers = peers""")

        with mock.patch.object(TendermintNetwork, "init"), mock.patch.object(
            TendermintNetwork, "start"
        ), mock.patch.object(TendermintNetwork, "stop") as stop_mock, mock.patch.object(
            flask.Flask, "run", new=ctrl_c
        ):

            result = self.run_cli(("--build", str(self.t / DEFAULT_ABCI_BUILD_DIR)))
            assert result.exit_code == 0, result.output
            stop_mock.assert_any_call()

            addrbook_data = json.loads(addrbook_file.read_text())
            for i, addr in enumerate(addrbook_data["addrs"]):
                assert addr["addr"]["ip"] == "127.0.0.1"
                assert addr["addr"]["port"] == (26630 + i)

            assert "# persistent_peers" in config_toml.read_text()
