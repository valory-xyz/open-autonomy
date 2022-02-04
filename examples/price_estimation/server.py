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

"""Server for testing"""

from typing import Optional
from http import HTTPStatus
from datetime import datetime
import json
import asyncio
import websockets
from flask import Flask, request, jsonify
from packages.valory.skills.abstract_round_abci.serializer import (
    DictProtobufStructSerializer,
)

app = Flask(__name__)

PORT = 9999  # must match skill.yaml file specification
period_data = {}
data_sources = {}
last_period_count: Optional[int] = None


dummy_period_data = {
    "-1":
        {
            "estimate": 6.66,
            "observations": {
                "agent1": 0.0,
                "agent2": 1.14,
                "agent3": 5.5,
                "agent4": 20.0,
            },
            "signature": "tx_hash",
            "time_stamp": "2022-02-03T10:54:35.233373",
            "unit": "BTC:USD",
        },
}

dummy_data_sources = {
    "agent1": "coingecko",
    "agent2": "coinmarketcap",
    "agent3": "coinbase",
    "agent4": "binance",
}


@app.route("/data")
def data():
    """API endpoint for GET requests"""
    return period_data if period_data else dummy_period_data


@app.route("/sources")
def sources():
    """API endpoint for GET requests"""
    return data_sources if data_sources else dummy_data_sources


@app.route("/deposit", methods=['POST'])
def deposit() -> int:
    """Receive agent http POST request data from oracle service"""
    raw_data = request.get_data()
    oracle_data = DictProtobufStructSerializer.decode(raw_data)
    try:
        period_count = oracle_data.pop("period_count")
        agent_address = oracle_data.pop("agent_address")
        oracle_data['time_stamp'] = datetime.now().isoformat()
        period_data.setdefault(period_count, {})[agent_address] = oracle_data
        return HTTPStatus.CREATED
    except Exception as e:
        print(e)
        return HTTPStatus.BAD_REQUEST


if __name__ == '__main__':
    host = "0.0.0.0"
    app.run(host=host, port=PORT, debug=True)
