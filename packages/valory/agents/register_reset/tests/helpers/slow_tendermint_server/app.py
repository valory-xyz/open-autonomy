# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2023 Valory AG
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

"""HTTP server to control the tendermint execution environment."""
import json
import logging
import os
import shutil
import stat
import time
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Tuple

from flask import Flask, Response, jsonify, request
from werkzeug.exceptions import InternalServerError, NotFound

from packages.valory.agents.register_reset.tests.helpers.slow_tendermint_server.tendermint import (
    TendermintNode,
    TendermintParams,
)


ENCODING = "utf-8"
DEFAULT_LOG_FILE = "log.log"
IS_DEV_MODE = os.environ.get("DEV_MODE", "0") == "1"
CONFIG_OVERRIDE = [
    ("fast_sync = true", "fast_sync = false"),
    ("max_num_outbound_peers = 10", "max_num_outbound_peers = 0"),
    ("pex = true", "pex = false"),
]

logging.basicConfig(
    filename=os.environ.get("LOG_FILE", DEFAULT_LOG_FILE),
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s",  # noqa : W1309
)


def load_genesis() -> Any:
    """Load genesis file."""
    return json.loads(
        Path(os.environ["TMHOME"], "config", "genesis.json").read_text(
            encoding=ENCODING
        )
    )


def get_defaults() -> Dict[str, str]:
    """Get defaults from genesis file."""
    genesis = load_genesis()
    return dict(genesis_time=genesis.get("genesis_time"))


def override_config_toml() -> None:
    """Update sync method."""

    config_path = str(Path(os.environ["TMHOME"]) / "config" / "config.toml")
    with open(config_path, "r", encoding=ENCODING) as fp:
        config = fp.read()

    for old, new in CONFIG_OVERRIDE:
        config = config.replace(old, new)

    with open(config_path, "w+", encoding=ENCODING) as fp:
        fp.write(config)


class PeriodDumper:
    """Dumper for tendermint data."""

    resets: int
    dump_dir: Path
    logger: logging.Logger

    def __init__(self, logger: logging.Logger, dump_dir: Optional[Path] = None) -> None:
        """Initialize object."""

        self.resets = 0
        self.logger = logger
        self.dump_dir = dump_dir or Path("/tm_state")

        if self.dump_dir.is_dir():
            shutil.rmtree(str(self.dump_dir), onerror=self.readonly_handler)
        self.dump_dir.mkdir(exist_ok=True)

    @staticmethod
    def readonly_handler(
        func: Callable, path: str, execinfo: Any  # pylint: disable=unused-argument
    ) -> None:
        """If permission is readonly, we change and retry."""
        try:
            os.chmod(path, stat.S_IWRITE)
            func(path)
        except (FileNotFoundError, OSError):
            return

    def dump_period(self) -> None:
        """Dump tendermint run data for replay"""
        store_dir = self.dump_dir / f"period_{self.resets}"
        store_dir.mkdir(exist_ok=True)
        try:
            shutil.copytree(
                os.environ["TMHOME"], str(store_dir / ("node" + os.environ["ID"]))
            )
            self.logger.info(f"Dumped data for period {self.resets}")
        except OSError:
            self.logger.info(
                f"Error occurred while dumping data for period {self.resets}"
            )
        self.resets += 1


def create_app(
    dump_dir: Optional[Path] = None,
    perform_monitoring: bool = True,
    debug: bool = False,
) -> Tuple[Flask, TendermintNode]:
    """
    Create a tendermint server app that is slow to respond to /hard_reset response.

    This implementation was copied over from deployments/tendermint.
    THIS IMPLEMENTATION SHOULD NOT BE USED IN TESTS WHERE NORMAL OPERATION OF THE TENDERMINT SERVER APP IS REQUIRED!
    """

    override_config_toml()
    tendermint_params = TendermintParams(
        proxy_app=os.environ["PROXY_APP"],
        consensus_create_empty_blocks=os.environ["CREATE_EMPTY_BLOCKS"] == "true",
        home=os.environ["TMHOME"],
    )

    app = Flask(__name__)
    period_dumper = PeriodDumper(logger=app.logger, dump_dir=dump_dir)

    tendermint_node = TendermintNode(tendermint_params, logger=app.logger)
    tendermint_node.start(start_monitoring=perform_monitoring, debug=debug)

    @app.route("/hard_reset")
    def hard_reset() -> Tuple[Any, int]:
        """Reset the node forcefully, and prune the blocks"""
        try:
            tendermint_node.stop()
            if IS_DEV_MODE:
                period_dumper.dump_period()

            return_code = tendermint_node.prune_blocks()
            if return_code:
                tendermint_node.start(start_monitoring=perform_monitoring)
                raise RuntimeError("Could not perform `unsafe-reset-all` successfully!")
            defaults = get_defaults()
            tendermint_node.reset_genesis_file(
                request.args.get("genesis_time", defaults["genesis_time"]),
                # default should be 1: https://github.com/tendermint/tendermint/pull/5191/files
                request.args.get("initial_height", "1"),
                request.args.get("period_count", "0"),
            )
            tendermint_node.start(start_monitoring=perform_monitoring)
            # we assume we have a 5 seconds delay between the time the tendermint node starts
            # and when the agent receiving a response, 5 seconds should be enough for
            # tendermint to start and perform a Handshake Info request, where the agent
            # would respond with a non-zero height, because the agent has not wiped its
            # local blockchain. Checkout https://docs.tendermint.com/v0.33/app-dev/app-development.html#handshake
            delay = 5
            time.sleep(delay)
            return jsonify({"message": "Reset successful.", "status": True}), 200
        except Exception as e:  # pylint: disable=W0703
            return jsonify({"message": f"Reset failed: {e}", "status": False}), 200

    @app.errorhandler(404)
    def handle_notfound(e: NotFound) -> Response:
        """Handle server error."""
        app.logger.info(e)  # pylint: disable=E
        return Response("Not Found", status=404, mimetype="application/json")

    @app.errorhandler(500)
    def handle_server_error(e: InternalServerError) -> Response:
        """Handle server error."""
        app.logger.info(e)  # pylint: disable=E
        return Response("Error Closing Node", status=500, mimetype="application/json")

    return app, tendermint_node


def create_server() -> Any:
    """Function to retrieve just the app to be used by flask entry point."""
    flask_app, _ = create_app()
    return flask_app
