import os, click
from pathlib import Path
import shutil
import signal
import subprocess
import time
from typing import List, Optional
from flask import Flask, jsonify


TENDERMINT_BIN = shutil.which("tendermint")
BUILD_DIR = Path("deployments/build/").absolute()


class TendermintRunner:
    """Run tednermint using the dump."""

    node_id: int
    process: Optional[subprocess.Popen]
    period: int = 0

    def __init__(self, node_id: int, dump_dir: Path) -> None:
        """Initialize object."""

        self.period = 0
        self.process = None
        self.dump_dir = dump_dir
        self.node_id = node_id

    def update_period(
        self,
    ) -> None:
        """Update period."""
        self.stop()
        self.period += 1
        self.start()

    def start(
        self,
    ) -> None:
        """Start tendermint process."""
        self.process = subprocess.Popen(
            [
                TENDERMINT_BIN,
                "node",
                f"--p2p.laddr=tcp://127.0.0.1:2663{self.node_id}",
                f"--rpc.laddr=tcp://localhost:2664{self.node_id}",
                f"--proxy_app=tcp://localhost:2665{self.node_id}",
                "--consensus.create_empty_blocks=true",
                "--home",
                str(self.dump_dir / f"period_{self.period}" / f"node{self.node_id}"),
            ],
            # stdout=subprocess.PIPE,
        )

    def stop(
        self,
    ) -> None:
        """Stop tendermint process."""
        if self.process is None:
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

    def __init__(self, dump_dir: Path, number_of_nodes: int = 4) -> None:
        """Initialize object."""

        self.dump_dir = dump_dir
        self.number_of_nodes = number_of_nodes
        self.nodes = []

    def build(
        self,
    ) -> None:
        """Build tendermint nodes."""
        for node_id in range(self.number_of_nodes):
            self.nodes.append(TendermintRunner(node_id, self.dump_dir))

    def update_period(self, node_id: int) -> None:
        """Update period for nth node."""
        self.nodes[node_id].update_period()

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
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()


tendermint_network: TendermintNetwork

app = Flask(__name__)


@app.route("/<int:node_id>/hard_reset")
def hard_reset(node_id: int):
    """Reset tendermint node."""
    global tendermint_network
    tendermint_network.update_period(node_id)
    app.logger.info(f"Restarted node {node_id}")
    return jsonify({"message": "Reset successful.", "status": True}), 200


@app.get("/status")
def status():
    return jsonify(
        {"result": {"sync_info": {"latest_block_height": 0}}, "is_replay": True}
    )


@app.get("/broadcast_tx_sync")
def broadcast_tx_sync():
    return jsonify({"result": {"hash": "", "code": 0}})


@app.get("/tx")
def tx():
    return jsonify({"result": {"tx_result": {"code": 0}}})


@click.command()
@click.option(
    "--build",
    "build_dir",
    type=click.Path(dir_okay=True, exists=True),
    default=BUILD_DIR,
)
def main(build_dir: Path):
    """Main function."""

    build_dir = Path(build_dir).absolute()
    dump_dir = build_dir / "logs" / "dump"

    global tendermint_network
    tendermint_network = TendermintNetwork(dump_dir)
    tendermint_network.build()
    tendermint_network.start()
    app.run(host="localhost", port=8080)


if __name__ == "__main__":
    main()
