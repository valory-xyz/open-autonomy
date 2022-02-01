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

"""HTTP server to control the tendermint execution environment."""
import os

from flask import Flask, Response, jsonify
from tendermint import TendermintNode, TendermintParams
from werkzeug.exceptions import InternalServerError, NotFound


tendermint_params = TendermintParams(
    proxy_app=os.environ["PROXY_APP"],
    consensus_create_empty_blocks=os.environ["CREATE_EMPTY_BLOCKS"] == "true",
    home=os.environ["TMHOME"],
)
tendermint_node = TendermintNode(tendermint_params)
tendermint_node.start()

app = Flask(__name__)


@app.route("/gentle_reset")
def gentle_reset():
    try:
        tendermint_node.stop()
        tendermint_node.start()
        return jsonify({"message": "Reset successful.", "status": True}), 200
    except Exception as e:
        return (
            jsonify(
                {"message": f"Reset failed with error : f{str(e)}", "status": False}
            ),
            200,
        )


@app.route("/hard_reset")
def hard_reset():
    try:
        tendermint_node.stop()
        tendermint_node.prune_blocks()
        tendermint_node.start()
        return jsonify({"message": "Reset successful.", "status": True}), 200
    except Exception as e:
        return (
            jsonify(
                {"message": f"Reset failed with error : f{str(e)}", "status": False}
            ),
            200,
        )


@app.errorhandler(404)
def handle_notfound(e: NotFound):
    return Response("Not Found", status=404, mimetype="application/json")


@app.errorhandler(500)
def handle_server_error(e: InternalServerError):
    return Response("Error Closing Node", status=500, mimetype="application/json")


if __name__ == "__main__":
    app.run()
