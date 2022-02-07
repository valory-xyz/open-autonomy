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

from http import HTTPStatus
from datetime import datetime
from queue import Queue

from threading import Thread, Event

from flask import Flask, request, render_template
from flask_socketio import SocketIO
from flask_cors import CORS

from packages.valory.skills.abstract_round_abci.serializer import (
    DictProtobufStructSerializer,
)

thread = Thread()
thread_stop_event = Event()

app = Flask(__name__)
app.config['SECRET_KEY'] = "💩"
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

PORT = 9999  # must match skill.yaml file specification
period_data = {}
data_sources = {}
last_period_count: int = 0
queue = Queue()


dummy_period_data = {
    -1: {
        "0x_address_agent1": {
            "estimate": 6.66,
            "observations": {
                "0x_address_agent1": 0.0,
                "0x_address_agent2": 1.14,
                "0x_address_agent3": 5.5,
                "0x_address_agent4": 20.0,
            },
            "signature": "tx_hash",
            "time_stamp": "2022-02-03T10:54:35.233373",
            "data_source": "coinmarketcap",
            "unit": "BTC:USD",
        },
        "0x_address_agent2": {},
        "0x_address_agent3": {},
        "0x_address_agent4": {},
    }
}


@app.route("/data")
def data():
    """API endpoint for GET requests"""
    return period_data if period_data else dummy_period_data


@app.route("/deposit", methods=['POST'])
def deposit() -> int:
    """Receive agent http POST request data from oracle service"""
    global last_period_count
    global queue
    raw_data = request.get_data()
    oracle_data = DictProtobufStructSerializer.decode(raw_data)
    try:
        period_count = oracle_data.pop("period_count")
        agent_address = oracle_data.pop("agent_address")
        if period_count > last_period_count:
            queue.put(period_data[last_period_count], block=True, timeout=None)
            last_period_count = period_count
        oracle_data['time_stamp'] = datetime.now().isoformat()
        period_data.setdefault(period_count, {})[agent_address] = oracle_data
        return HTTPStatus.CREATED  # this is not correct yet
    except Exception as e:
        print(e)
        return HTTPStatus.BAD_REQUEST


def generate_random_period_data():
    global last_period_count
    global queue
    import time
    import copy
    time.sleep(2)
    new_period_data = copy.deepcopy(dummy_period_data)
    period_data[last_period_count] = new_period_data[-1]
    queue.put(period_data[last_period_count], block=True, timeout=2)
    last_period_count += 1


def emit_last_period_data():
    """Emit an event to the client"""
    while not thread_stop_event.is_set():
        # generate_random_period_data()  # sleep, q.put, period_ctr += 1
        if not queue.empty():
            data_to_emit = queue.get(block=True, timeout=None)
            socketio.emit('new_data', {'period': data_to_emit}, namespace='/test')


@app.route('/')
def index():
    return render_template('index.html')  # async_mode=socketio.async_mode


@socketio.on('connect', namespace='/test')
def test_connect():
    global thread  # need visibility of the global thread object
    if not thread.is_alive():
        thread = socketio.start_background_task(emit_last_period_data)


@socketio.on('disconnect', namespace='/test')
def test_disconnect():
    print('Client disconnected')


if __name__ == '__main__':
    host = "0.0.0.0"
    app.run(host=host, port=PORT, debug=True)
