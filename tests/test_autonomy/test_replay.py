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

"""Test replay tools."""

import shutil
import subprocess  # nosec
import tempfile
from pathlib import Path
from typing import cast
from unittest import mock

import pytest

from autonomy.deploy.constants import TM_STATE_DIR
from autonomy.replay.agent import AgentRunner
from autonomy.replay.tendermint import (
    RanOutOfDumpsToReplay,
    TendermintRunner,
    build_tendermint_apps,
)

from tests.conftest import ROOT_DIR


TENDERMINT_BIN = shutil.which("tendermint")
AGENT_DATA = {
    "mem_limit": "1024m",
    "mem_reservation": "256M",
    "cpus": 1,
    "container_name": "abci0",
    "image": "valory/open-autonomy-open-aea:oracle-0.1.0",
    "environment": [
        "LOG_FILE=/logs/aea_0.txt",
        "ID=0",
        "VALORY_APPLICATION=valory/oracle:0.1.0:QmUTuBXUbgBjBbiLR3kmBxZXQowseu2mc6xR5MVuX8UyXJ",
        "ABCI_HOST=abci0",
        "MAX_PARTICIPANTS=4",
        "TENDERMINT_URL=http://node0:26657",
        "TENDERMINT_COM_URL=http://node0:8080",
        "SKILL_ORACLE_ABCI_MODELS_PRICE_API_ARGS_URL=https://api.coingecko.com/api/v3/simple/price",
        "SKILL_ORACLE_ABCI_MODELS_PRICE_API_ARGS_API_ID=coingecko",
        'SKILL_ORACLE_ABCI_MODELS_PRICE_API_ARGS_PARAMETERS=[["ids", "bitcoin"], ["vs_currencies", "usd"]]',
        "SKILL_ORACLE_ABCI_MODELS_PRICE_API_ARGS_RESPONSE_KEY=bitcoin:usd",
        "SKILL_ORACLE_ABCI_MODELS_PRICE_API_ARGS_HEADERS=None",
        "SKILL_ORACLE_ABCI_MODELS_RANDOMNESS_API_ARGS_URL=https://drand.cloudflare.com/public/latest",
        "SKILL_ORACLE_ABCI_MODELS_RANDOMNESS_API_ARGS_API_ID=cloudflare",
        "SKILL_ORACLE_ABCI_MODELS_PARAMS_ARGS_OBSERVATION_INTERVAL=30",
        "SKILL_ORACLE_ABCI_MODELS_PARAMS_ARGS_BROADCAST_TO_SERVER=False",
        "SKILL_ORACLE_ABCI_MODELS_PARAMS_ARGS_SERVICE_REGISTRY_ADDRESS=0x0DCd1Bf9A1b36cE34237eEaFef220932846BCD82",
        "SKILL_ORACLE_ABCI_MODELS_PARAMS_ARGS_ON_CHAIN_SERVICE_ID=1",
        "SKILL_ORACLE_ABCI_MODELS_SERVER_API_ARGS_URL=https://staging.oracle-server.autonolas.tech/deposit",
        "SKILL_ORACLE_ABCI_MODELS_BENCHMARK_TOOL_ARGS_LOG_DIR=/benchmarks",
        "LEDGER_ADDRESS=http://143.110.184.220:8545",
        "LEDGER_CHAIN_ID=31337",
        "AEA_KEY=0x874741e86698d72ce5a579386ab6f3e006426e4959662736aa3132b83911130a",
    ],
    "networks": {"localnet": {"ipv4_address": "192.167.11.7"}},
    "volumes": ["./persistent_data/logs:/logs:Z", "./agent_keys/agent_0:/agent_key:Z"],
}


def ctrl_c() -> None:
    """Generate keyboard inturrupt."""
    raise KeyboardInterrupt()


def init_tendermint(home: Path) -> None:
    """Initialize tendermint home."""
    result = subprocess.run(  # nosec
        [cast(str, TENDERMINT_BIN), "init", "--home", str(home)]
    )
    assert result.returncode == 0, result.stdout


def test_tendermint_runner() -> None:
    """Test `TendermintRunner` class."""

    number_of_periods = 2
    node_id = 0

    with tempfile.TemporaryDirectory() as temp_dir:
        dump_dir = Path(temp_dir, TM_STATE_DIR)
        dump_dir.mkdir()

        for p in range(number_of_periods):
            tm_home = dump_dir / f"period_{p}" / f"node{node_id}"
            init_tendermint(tm_home)

        runner = TendermintRunner(
            node_id=node_id,
            dump_dir=dump_dir,
            n_periods=number_of_periods,
        )

        assert runner.get_last_block_height() == 0

        with pytest.raises(ValueError, match="Cannot find tendermint installation."):
            with mock.patch("shutil.which", new=lambda _: None):
                runner.start()

        runner.start()
        assert isinstance(runner.process, subprocess.Popen)

        runner.stop()
        assert runner.process is None

        runner.update_period()
        assert runner.period == 1

        with pytest.raises(RanOutOfDumpsToReplay):
            runner.update_period()


def test_tendermint_network() -> None:
    """Test tendermint network."""

    periods = 2
    nodes = 2
    app, tendermint_network = build_tendermint_apps()

    with tempfile.TemporaryDirectory() as temp_dir:
        dump_dir = Path(temp_dir, TM_STATE_DIR)

        with pytest.raises(FileNotFoundError, match="Can't find period dumps in"):
            tendermint_network.init(dump_dir=dump_dir)

        dump_dir.mkdir()
        for p in range(periods):
            (dump_dir / f"period_{p}").mkdir()

        with pytest.raises(FileNotFoundError, match="Can't find dumped nodes"):
            tendermint_network.init(dump_dir=dump_dir)

        for p in range(periods):
            period_dir = dump_dir / f"period_{p}"
            for n in range(nodes):
                node_dir = period_dir / f"node{n}"
                init_tendermint(node_dir)

        tendermint_network.init(dump_dir=dump_dir)
        assert tendermint_network.get_last_block_height(0) == 0

        tendermint_network.start()
        for node in tendermint_network.nodes:
            assert isinstance(node.process, subprocess.Popen)

        tendermint_network.stop()
        for node in tendermint_network.nodes:
            assert node.process is None

        with mock.patch.object(tendermint_network, "start", ctrl_c):
            tendermint_network.run_until_interruption()

        with app.test_client() as client:

            response = client.get("/0/tx")
            response_data = response.get_json()
            assert response_data["result"]["tx_result"]["code"] == 0

            response = client.get("/0/broadcast_tx_sync")
            response_data = response.get_json()
            assert response_data["result"]["code"] == 0
            assert response_data["result"]["hash"] == ""

            response = client.get("/0/status")
            response_data = response.get_json()
            assert response_data["result"]["sync_info"]["latest_block_height"] == -1

            response = client.get("/0/hard_reset")
            response_data = response.get_json()
            assert response_data["status"] is True
            assert response_data["is_replay"] is True

            response = client.get("/0/hard_reset")
            response_data = response.get_json()
            assert response_data["status"] is False
            assert (
                response_data["message"]
                == "Ran out of dumps to replay, You can stop the agent replay now."
            )
            assert response_data["is_replay"] is True


def test_agent_runner() -> None:
    """Test agent runner."""

    agent_runner = AgentRunner(
        0,
        AGENT_DATA,
        ROOT_DIR / "packages",
    )

    agent_runner.start()
    assert isinstance(agent_runner.process, subprocess.Popen)
    assert (
        len(
            {
                "vendor",
                "ethereum_private_key.txt",
                "aea-config.yaml",
                "README.md",
            }.difference(
                set(
                    map(
                        lambda x: x.name,
                        Path(agent_runner.agent_dir.name, "agent").iterdir(),
                    )
                )
            )
        )
        == 0
    )

    agent_runner.stop()
    assert agent_runner.process is None
