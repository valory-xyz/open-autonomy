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

"""Script to build and run tendermint nodes from data dumps."""

import json
import os
import shutil
import signal
import subprocess  # nosec
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from flask import Flask


# TODO: extract constants


class RanOutOfDumpsToReplay(Exception):
    """Error to raise when we run out of dumps to replay."""


class TendermintRunner:
    """Run tednermint using the dump."""

    node_id: int
    process: Optional[subprocess.Popen]  # nosec
    period: int = 0
    n_periods: int

    def __init__(self, node_id: int, dump_dir: Path, n_periods: int) -> None:
        """Initialize object."""

        self.period = 0
        self.process = None
        self.dump_dir = dump_dir
        self.node_id = node_id
        self.n_periods = n_periods

    def update_period(
        self,
    ) -> None:
        """Update period."""
        self.stop()
        self.period += 1
        if self.period >= self.n_periods:
            raise RanOutOfDumpsToReplay()
        self.start()

    def get_last_block_height(
        self,
    ) -> int:
        """Returns the last block height before dumping."""
        state_file = (
            self.dump_dir
            / f"period_{self.period}"
            / f"node{self.node_id}"
            / "data"
            / "priv_validator_state.json"
        )
        state_data = json.loads(state_file.read_text())
        return int(state_data.get("height", 0))

    def start(
        self,
    ) -> None:
        """Start tendermint process."""

        tendermint_bin = shutil.which("tendermint")
        if tendermint_bin is None:
            raise ValueError("Cannot find tendermint installation.")

        self.process = subprocess.Popen(  # nosec  # pylint: disable=subprocess-run-check,consider-using-with
            [
                str(tendermint_bin),
                "node",
                f"--p2p.laddr=tcp://127.0.0.1:2663{self.node_id}",
                f"--rpc.laddr=tcp://localhost:2664{self.node_id}",
                f"--proxy_app=tcp://localhost:2665{self.node_id}",
                "--consensus.create_empty_blocks=true",
                "--home",
                str(self.dump_dir / f"period_{self.period}" / f"node{self.node_id}"),
            ],
        )

    def stop(
        self,
    ) -> None:
        """Stop tendermint process."""
        if self.process is None:  # pragma: nocover
            return

        self.process.poll()
        if self.process.returncode is None:  # stop only pending processes
            os.kill(self.process.pid, signal.SIGTERM)

        self.process.wait(timeout=5)
        self.process.terminate()
        self.process = None


class TendermintNetwork:
    """Tendermint network."""

    dump_dir: Path
    number_of_nodes: int
    nodes: List[TendermintRunner]
    reset_periods: int

    _recent_reset: bool

    def init(self, dump_dir: Path) -> None:
        """Initialize object."""

        self.dump_dir = dump_dir
        self.reset_periods = len(list(dump_dir.glob("period_*")))
        if self.reset_periods == 0:
            raise FileNotFoundError(f"Can't find period dumps in {dump_dir}")

        self.number_of_nodes = len(list((dump_dir / "period_0").iterdir()))
        if self.number_of_nodes == 0:
            raise FileNotFoundError("Can't find dumped nodes.")

        self.nodes = []
        self._recent_reset = True
        for node_id in range(self.number_of_nodes):
            self.nodes.append(
                TendermintRunner(node_id, self.dump_dir, self.reset_periods)
            )

    def update_period(self, node_id: int) -> None:
        """Update period for nth node."""
        self.nodes[node_id].update_period()
        self._recent_reset = True

    def get_last_block_height(self, node_id: int) -> int:
        """Returns last block height before dumping for `node_id`"""
        if self._recent_reset:
            self._recent_reset = False
            return 0

        return self.nodes[node_id].get_last_block_height() - 1

    def stop_node(self, node_id: int) -> None:
        """Stop a specific node."""
        self.nodes[node_id].stop()

    def start(
        self,
    ) -> None:
        """Start networks."""
        for node in self.nodes:
            node.start()

    def stop(
        self,
    ) -> None:
        """Stop network."""

        for node in self.nodes:
            node.stop()

    def run_until_interruption(
        self,
    ) -> None:
        """Run network until interruption."""

        try:
            self.start()
            while True:  # pragma: nocover
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()


def build_tendermint_apps() -> Tuple[Flask, TendermintNetwork]:
    """Build flask app and tendermint network."""
    app = Flask(__name__)
    tendermint_network = TendermintNetwork()

    @app.route("/<int:node_id>/hard_reset")
    def hard_reset(node_id: int) -> Dict:
        """Reset tendermint node."""

        try:
            tendermint_network.update_period(node_id)
            return {"message": "Reset successful.", "status": True, "is_replay": True}

        except RanOutOfDumpsToReplay:
            tendermint_network.stop_node(node_id)
            return {
                "message": "Ran out of dumps to replay, You can stop the agent replay now.",
                "status": False,
                "is_replay": True,
            }

    @app.get("/<int:node_id>/status")
    def status(node_id: int) -> Dict:
        """
        Status

        This endpoint will imitate the tendermint RPC server's /status so the ABCI
        app doesn't get blocked in replay mode.

        :param node_id: node id
        :return: response
        """

        return {
            "result": {
                "sync_info": {
                    "latest_block_height": tendermint_network.get_last_block_height(
                        node_id
                    )
                }
            }
        }

    @app.get("/<int:node_id>/broadcast_tx_sync")
    def broadcast_tx_sync(node_id: int) -> Dict:  # pylint: disable=unused-argument
        """Similar as /status"""
        return {"result": {"hash": "", "code": 0}}

    @app.get("/<int:node_id>/tx")
    def tx(node_id: int) -> Dict:  # pylint: disable=unused-argument
        """Similar as /status"""
        return {"result": {"tx_result": {"code": 0}}}

    return app, tendermint_network
