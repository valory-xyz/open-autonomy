# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021 Valory AG
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
import traceback
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Tuple

from flask import Flask, Response, jsonify, request
from tendermint import TendermintNode, TendermintParams
from werkzeug.exceptions import InternalServerError, NotFound


ENCODING = "utf-8"
DEFAULT_LOG_FILE = "log.log"
TMHOME = Path(os.environ.get("TMHOME", "~/.tendermint")).resolve()
logging.basicConfig(
    filename=os.environ.get("FLASK_LOG_FILE", DEFAULT_LOG_FILE),
    level=logging.DEBUG,
    format=f"%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s",  # noqa : W1309
)


class PeriodDumper:
    """Dumper for tendermint data."""

    resets: int
    dump_dir: Path
    logger: logging.Logger

    def __init__(self, logger: logging.Logger, dump_dir: Optional[Path] = None) -> None:
        """Initialize object."""

        self.resets = 0
        self.logger = logger
        self.dump_dir = Path("/logs/dump") if dump_dir is None else dump_dir

        if self.dump_dir.is_dir():
            shutil.rmtree(str(self.dump_dir), onerror=self.readonly_handler)
        self.dump_dir.mkdir()

    @staticmethod
    def readonly_handler(func: Callable, path: str, execinfo: Any) -> None:
        """If permission is readonly, we change and retry."""
        os.chmod(path, stat.S_IWRITE)
        func(path)

    def dump_period(
        self,
    ) -> None:
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


CONFIG_OVERRIDE = [
    ("fast_sync = true", "fast_sync = false"),
    ("max_num_outbound_peers = 10", "max_num_outbound_peers = 0"),
]


def update_sync_method() -> None:
    """Update sync method."""

    config_path = str(Path(os.environ["TMHOME"]) / "config" / "config.toml")
    with open(config_path, "r", encoding="UTF8") as fp:
        config = fp.read()

    for old, new in CONFIG_OVERRIDE:
        config = config.replace(old, new)

    with open(config_path, "w+", encoding="UTF8") as fp:
        fp.write(config)


update_sync_method()
tendermint_params = TendermintParams(
    proxy_app=os.environ["PROXY_APP"],
    consensus_create_empty_blocks=os.environ["CREATE_EMPTY_BLOCKS"] == "true",
    home=os.environ["TMHOME"],
)

app = Flask(__name__)
period_dumper = PeriodDumper(logger=app.logger)

tendermint_node = TendermintNode(tendermint_params, logger=app.logger)


@app.route("/start")
def start() -> Response:
    """Start Tendermint node"""
    try:
        tendermint_node.start()
        return jsonify(response="Tendermint node started", status=200)
    except Exception:  # pylint: disable=broad-except
        return jsonify(response=traceback.format_exc(), status=400)


@app.get("/params")
def get_params() -> Dict:
    """Get tendermint params."""
    try:
        priv_key_file = TMHOME / "config" / "priv_validator_key.json"
        priv_key_data = json.loads(priv_key_file.read_text(encoding="utf-8"))
        del priv_key_data["priv_key"]
        return {"params": priv_key_data, "status": True, "error": None}
    except (FileNotFoundError, json.JSONDecodeError):
        return {"params": {}, "status": False, "error": traceback.format_exc()}


@app.post("/params")
def update_params() -> Dict:
    """Update validator params."""

    try:
        data = request.get_json()
        genesis_file = TMHOME / "config" / "genesis.json"
        genesis_data = {}
        genesis_data["genesis_time"] = data["genesis_config"]["genesis_time"]
        genesis_data["chain_id"] = data["genesis_config"]["chain_id"]
        genesis_data["consensus_params"] = data["genesis_config"]["consensus_params"]
        genesis_data["initial_height"] = "0"
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
        genesis_file.write_text(json.dumps(genesis_data, indent=2), encoding="utf-8")

        return {"status": True, "error": None}
    except (FileNotFoundError, json.JSONDecodeError, PermissionError):
        return {"status": False, "error": traceback.format_exc()}


@app.route("/gentle_reset")
def gentle_reset() -> Tuple[Any, int]:
    """Reset the tendermint node gently."""
    try:
        tendermint_node.stop()
        tendermint_node.start()
        return jsonify({"message": "Reset successful.", "status": True}), 200
    except Exception as e:  # pylint: disable=W0703
        return (
            jsonify(
                {"message": f"Reset failed with error : f{str(e)}", "status": False}
            ),
            200,
        )


@app.route("/hard_reset")
def hard_reset() -> Tuple[Any, int]:
    """Reset the node forcefully, and prune the blocks"""
    try:
        tendermint_node.stop()
        if os.environ.get("DEV_MODE", "0") == "1":
            period_dumper.dump_period()
        tendermint_node.prune_blocks()
        tendermint_node.start()
        return jsonify({"message": "Reset successful.", "status": True}), 200
    except Exception as e:  # pylint: disable=W0703
        return (
            jsonify(
                {"message": f"Reset failed with error : f{str(e)}", "status": False}
            ),
            200,
        )


@app.errorhandler(404)  # type: ignore
def handle_notfound(e: NotFound) -> Response:
    """Handle server error."""
    app.logger.info(e)
    return Response("Not Found", status=404, mimetype="application/json")


@app.errorhandler(500)  # type: ignore
def handle_server_error(e: InternalServerError) -> Response:
    """Handle server error."""
    app.logger.info(e)  # pylint: disable=E
    return Response("Error Closing Node", status=500, mimetype="application/json")


if __name__ == "__main__":
    app.run(port=8080)
