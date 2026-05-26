# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022-2026 Valory AG
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

import json
import shutil
import subprocess  # nosec
import tempfile
from pathlib import Path
from typing import cast
from unittest import mock

import pytest

from autonomy.deploy.base import TENDERMINT_COM_URL_PARAM, TENDERMINT_URL_PARAM
from autonomy.deploy.constants import PERSISTENT_DATA_DIR, TM_STATE_DIR
from autonomy.replay.agent import AgentRunner
from autonomy.replay.tendermint import (
    RanOutOfDumpsToReplay,
    TendermintRunner,
    build_tendermint_apps,
)
from autonomy.replay.utils import fix_address_books

from tests.conftest import ROOT_DIR

TENDERMINT_BIN = shutil.which("tendermint")
AGENT_DATA = {
    "mem_limit": "1024m",
    "mem_reservation": "256M",
    "cpus": 1,
    "container_name": "abci0",
    "image": "valory/open-autonomy-open-aea:hello-world-0.1.0",
    "environment": [
        "LOG_FILE=/logs/aea_0.txt",
        "ID=0",
        "AEA_AGENT=valory/offend_slash:0.1.0:bafybeideb6b5k4i6z7bm3p53eydxgknmwdefo2oshcnlxthjc6oxeox7ua",
        "ABCI_HOST=abci0",
        f"SKILL_ORACLE_ABCI_MODELS_PARAMS_ARGS_{TENDERMINT_URL_PARAM.upper()}=http://node0:26657",
        f"SKILL_ORACLE_ABCI_MODELS_PARAMS_ARGS_{TENDERMINT_COM_URL_PARAM.upper()}=http://node0:8080",
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


def _addrbook_at(dump_root: Path, node_id: int, payload: dict) -> Path:
    """Write a synthetic ``addrbook.json`` under the expected glob path."""
    node_dir = dump_root / PERSISTENT_DATA_DIR / TM_STATE_DIR / f"node{node_id}"
    node_dir.mkdir(parents=True, exist_ok=True)
    addr_file = node_dir / "addrbook.json"
    addr_file.write_text(json.dumps(payload))
    return addr_file


@pytest.mark.parametrize(
    "addr_payload, expect_mutation",
    (
        # Missing "addr" key — entry must be skipped, file rewritten unchanged.
        ({"addrs": [{"ip": "1.2.3.4"}]}, False),
        # Non-dotted IP — entry must be skipped.
        ({"addrs": [{"addr": {"ip": "not-an-ip"}}]}, False),
        # Non-numeric trailing octet — entry must be skipped.
        ({"addrs": [{"addr": {"ip": "1.2.3.abc"}}]}, False),
        # Healthy entry — must be rewritten with replay-local ip/port.
        (
            {"addrs": [{"addr": {"ip": "10.0.0.6", "port": 26656}}]},
            True,
        ),
    ),
)
def test_fix_address_books_skips_malformed_entries(
    addr_payload: dict, expect_mutation: bool
) -> None:
    """Malformed peer entries are skipped without aborting the whole sweep."""
    with tempfile.TemporaryDirectory() as temp_dir:
        build_dir = Path(temp_dir)
        addr_file = _addrbook_at(build_dir, 0, addr_payload)
        fix_address_books(build_dir)
        result = json.loads(addr_file.read_text())
        if expect_mutation:
            assert result["addrs"][0]["addr"]["ip"] == "127.0.0.1"
            assert (
                result["addrs"][0]["addr"]["port"]
                != addr_payload["addrs"][0]["addr"]["port"]
            )
        else:
            assert result == addr_payload, (
                "malformed entry must be preserved unchanged so the addrbook "
                "is not left half-rewritten"
            )


def test_fix_address_books_continues_past_malformed_peer_to_subsequent_files() -> None:
    """A malformed peer in one addrbook does not stop processing the next file."""
    with tempfile.TemporaryDirectory() as temp_dir:
        build_dir = Path(temp_dir)
        bad = _addrbook_at(build_dir, 0, {"addrs": [{"ip": "1.2.3.4"}]})
        good_payload = {"addrs": [{"addr": {"ip": "10.0.0.7", "port": 26656}}]}
        good = _addrbook_at(build_dir, 1, good_payload)

        fix_address_books(build_dir)

        # First file untouched (entry was malformed, skipped).
        assert json.loads(bad.read_text()) == {"addrs": [{"ip": "1.2.3.4"}]}
        # Second file rewritten with replay-local values — proves the sweep did not abort.
        result = json.loads(good.read_text())
        assert result["addrs"][0]["addr"]["ip"] == "127.0.0.1"
