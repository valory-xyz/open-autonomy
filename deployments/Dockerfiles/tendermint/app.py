# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2022 Valory AG
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
import re
import shutil
import stat
import traceback
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, cast

import requests
from flask import Flask, Response, jsonify, request
from werkzeug.exceptions import InternalServerError, NotFound


try:
    from .tendermint import TendermintNode, TendermintParams  # type: ignore
except ImportError:
    from tendermint import TendermintNode, TendermintParams

ENCODING = "utf-8"
DEFAULT_LOG_FILE = "log.log"
IS_DEV_MODE = os.environ.get("DEV_MODE", "0") == "1"
CONFIG_OVERRIDE = [
    ("fast_sync = true", "fast_sync = false"),
    ("max_num_outbound_peers = 10", "max_num_outbound_peers = 0"),
    ("pex = true", "pex = false"),
]
DOCKER_INTERNAL_HOST = "host.docker.internal"
TM_STATUS_ENDPOINT = "http://localhost:26657/status"

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
    logging.info(config_path)
    with open(config_path, "r", encoding=ENCODING) as fp:
        config = fp.read()

    for old, new in CONFIG_OVERRIDE:
        config = config.replace(old, new)

    with open(config_path, "w+", encoding=ENCODING) as fp:
        fp.write(config)


def update_peers(validators: List[Dict], config_path: Path) -> None:
    """Fix peers."""

    config_text = config_path.read_text(encoding="utf-8")

    new_peer_string = 'persistent_peers = "'
    for peer in validators:
        hostname = peer["hostname"]
        if hostname in ("localhost", "0.0.0.0"):
            # This (tendermint) node will be running in a docker container and no other node
            # will be running in the same container. If we receive either localhost or 0.0.0.0,
            # we make an assumption that the address belongs to a node running on the
            # same machine with a different docker container and different p2p port so,
            # we replace the hostname with the docker's internal host url.
            hostname = DOCKER_INTERNAL_HOST
        new_peer_string += (
            peer["peer_id"] + "@" + hostname + ":" + str(peer["p2p_port"]) + ","
        )
    new_peer_string = new_peer_string[:-1] + '"\n'

    updated_config = re.sub('persistent_peers = ".*\n', new_peer_string, config_text)
    config_path.write_text(updated_config, encoding="utf-8")


def update_genesis_config(data: Dict) -> None:
    """Update genesis.json file for the tendermint node."""

    genesis_file = Path(os.environ["TMHOME"]) / "config" / "genesis.json"
    genesis_data = {}
    genesis_data["genesis_time"] = data["genesis_config"]["genesis_time"]
    genesis_data["chain_id"] = data["genesis_config"]["chain_id"]
    genesis_data["initial_height"] = "0"
    genesis_data["consensus_params"] = data["genesis_config"]["consensus_params"]
    genesis_data["validators"] = [
        {
            "address": validator["address"],
            "pub_key": validator["pub_key"],
            "power": validator["power"],
            "name": validator["name"],
        }
        for validator in data["validators"]
    ]
    genesis_data["app_hash"] = ""
    genesis_file.write_text(json.dumps(genesis_data, indent=2), encoding=ENCODING)


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
        except OSError as e:
            self.logger.info(
                f"Error occurred while dumping data for period {self.resets}: {e}"
            )
        self.resets += 1


def create_app(
    dump_dir: Optional[Path] = None,
    perform_monitoring: bool = True,
    debug: bool = False,
) -> Tuple[Flask, TendermintNode]:
    """Create the Tendermint server app"""

    tendermint_params = TendermintParams(
        proxy_app=os.environ["PROXY_APP"],
        consensus_create_empty_blocks=os.environ["CREATE_EMPTY_BLOCKS"] == "true",
        home=os.environ["TMHOME"],
        use_grpc=os.environ["USE_GRPC"] == "true",
    )

    app = Flask(__name__)
    period_dumper = PeriodDumper(logger=app.logger, dump_dir=dump_dir)
    tendermint_node = TendermintNode(tendermint_params, logger=app.logger)
    tendermint_node.init()

    override_config_toml()

    tendermint_node.start(start_monitoring=perform_monitoring, debug=debug)

    @app.get("/params")
    def get_params() -> Dict:
        """Get tendermint params."""
        try:
            priv_key_file = (
                Path(os.environ["TMHOME"]) / "config" / "priv_validator_key.json"
            )
            priv_key_data = json.loads(priv_key_file.read_text(encoding=ENCODING))
            del priv_key_data["priv_key"]
            status = requests.get(TM_STATUS_ENDPOINT).json()
            priv_key_data["peer_id"] = status["result"]["node_info"]["id"]
            return {
                "params": priv_key_data,
                "status": True,
                "error": None,
            }
        except (FileNotFoundError, json.JSONDecodeError):
            return {"params": {}, "status": False, "error": traceback.format_exc()}

    @app.post("/params")
    def update_params() -> Dict:
        """Update validator params."""

        try:
            data: Dict = json.loads(request.get_data().decode(ENCODING))
            cast(logging.Logger, app.logger).debug(  # pylint: disable=no-member
                f"Data update requested with data={data}"
            )

            cast(logging.Logger, app.logger).info(  # pylint: disable=no-member
                "Updating genesis config."
            )
            update_genesis_config(data=data)

            cast(logging.Logger, app.logger).info(  # pylint: disable=no-member
                "Updating peristent peers."
            )
            update_peers(
                validators=data["validators"],
                config_path=Path(os.environ["TMHOME"]) / "config" / "config.toml",
            )

            return {"status": True, "error": None}
        except (FileNotFoundError, json.JSONDecodeError, PermissionError):
            return {"status": False, "error": traceback.format_exc()}

    @app.route("/gentle_reset")
    def gentle_reset() -> Tuple[Any, int]:
        """Reset the tendermint node gently."""
        try:
            tendermint_node.stop()
            tendermint_node.start(start_monitoring=perform_monitoring)
            return jsonify({"message": "Reset successful.", "status": True}), 200
        except Exception as e:  # pylint: disable=W0703
            return jsonify({"message": f"Reset failed: {e}", "status": False}), 200

    @app.route("/app_hash")
    def app_hash() -> Tuple[Any, int]:
        """Get the app hash."""
        try:
            non_routable, loopback = "0.0.0.0", "127.0.0.1"
            endpoint = f"{tendermint_params.rpc_laddr.replace('tcp', 'http').replace(non_routable, loopback)}/block"
            height = request.args.get("height")
            params = {"height": height} if height is not None else None
            res = requests.get(endpoint, params)
            app_hash_ = res.json()["result"]["block"]["header"]["app_hash"]
            return jsonify({"app_hash": app_hash_}), res.status_code
        except Exception as e:  # pylint: disable=W0703
            return (
                jsonify({"error": f"Could not get the app hash: {str(e)}"}),
                200,
            )

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
            )
            tendermint_node.start(start_monitoring=perform_monitoring)
            return jsonify({"message": "Reset successful.", "status": True}), 200
        except Exception as e:  # pylint: disable=W0703
            return jsonify({"message": f"Reset failed: {e}", "status": False}), 200

    @app.errorhandler(404)  # type: ignore
    def handle_notfound(e: NotFound) -> Response:
        """Handle server error."""
        cast(logging.Logger, app.logger).info(e)  # pylint: disable=E
        return Response("Not Found", status=404, mimetype="application/json")

    @app.errorhandler(500)  # type: ignore
    def handle_server_error(e: InternalServerError) -> Response:
        """Handle server error."""
        cast(logging.Logger, app.logger).info(e)  # pylint: disable=E
        return Response("Error Closing Node", status=500, mimetype="application/json")

    return app, tendermint_node


def create_server() -> Any:
    """Function to retrieve just the app to be used by flask entry point."""
    flask_app, _ = create_app()
    return flask_app
