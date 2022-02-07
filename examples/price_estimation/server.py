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

import random
import time

from threading import Thread, Event

from flask import Flask, request, jsonify, render_template
from flask_socketio import SocketIO, emit, send
from flask_cors import CORS

from packages.valory.skills.abstract_round_abci.serializer import (
    DictProtobufStructSerializer,
)

# setup
app = Flask(__name__)
# app.config['SECRET_KEY'] = 'private_key'
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# constants and storage
PORT = 9999  # must match skill.yaml file specification
period_data = {}
data_sources = {}
last_period_count: Optional[int] = None


dummy_period_data = {
    "-1": {
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


thread = Thread()
thread_stop_event = Event()


def generate_random_number():
    while not thread_stop_event.is_set():
        number = round(random.random(), 3)
        socketio.emit('newnumber', {'number': number}, namespace='/test')
        socketio.sleep(5)


def generate_random_period_data():
    while not thread_stop_event.is_set():
        dummy_period_data["-1"]["0x_address_agent1"]["estimate"] = random.random()
        socketio.emit('new_data', {'period': dummy_period_data}, namespace='/test')
        socketio.sleep(5)


@app.route('/')
def index():
    return render_template('index.html')


@socketio.on('connect', namespace='/test')
def test_connect():
    global thread  # need visibility of the global thread object
    if not thread.is_alive():
        thread = socketio.start_background_task(generate_random_period_data)


@socketio.on('disconnect', namespace='/test')
def test_disconnect():
    print('Client disconnected')


# @socketio.on('message')
# def handle_message(message):
#     send(message, broadcast=True)
#
#
# @socketio.on('json')
# def handle_json(json):
#     send(json, json=True)

# import random, time
# thread = Thread()
# thread_stop_event = Event()
#
#
# def randomNumberGenerator():
#     """
#     Generate a random number every 1 second and emit to a socketio instance (broadcast)
#     Ideally to be run in a separate thread?
#     """
#     #infinite loop of magical random numbers
#     print("Making random numbers")
#     while not thread_stop_event.isSet():
#         number = round(random.random()*10, 3)
#         print(number)
#         socketio.emit('newnumber', {'number': number}, namespace='/test')
#         socketio.sleep(5)
#
#
# @app.route('/')
# def index():
#     #only by sending this page first will the client be connected to the socketio instance
#     return render_template('index.html')
#
#
# @socketio.on('connect', namespace='/test')
# def test_connect():
#     # need visibility of the global thread object
#     global thread
#     print('Client connected')
#     if not thread.isAlive():
#         print("Starting Thread")
#         thread = socketio.start_background_task(randomNumberGenerator)
#
#
# @socketio.on('disconnect', namespace='/test')
# def test_disconnect():
#     print('Client disconnected')


# class RandomThread(Thread):
#
#     def __init__(self):
#         super(RandomThread, self).__init__()
#
#     def randomNumberGenerator(self):
#         """
#         Generate a random number every 1 second and emit to a socketio instance (broadcast)
#         Ideally to be run in a separate thread?
#         """
#         #infinite loop of magical random numbers
#         print("Making random numbers")
#         while not thread_stop_event.isSet():
#             number = round(random.random()*10, 3)
#             print(number)
#             socketio.emit('newnumber', {'number': number}, namespace='/test')
#             time.sleep(1)
#
#     def run(self):
#         self.randomNumberGenerator()
#
#
# @app.route('/')
# def index():
#     # only by sending this page first will the client be connected to the socketio instance
#     import os
#     return render_template('index.html')
#
#
# @socketio.on('connect', namespace='/test')
# def test_connect():
#     # need visibility of the global thread object
#     global thread
#     print('Client connected')
#     if not thread.is_alive():
#         print("Starting Thread")
#         thread = RandomThread()
#         thread.start()
#
#
# @socketio.on('disconnect', namespace='/test')
# def test_disconnect():
#     print('Client disconnected')




# @socketio.on('connect')
# def test_connect():
#     emit('responseMessage', {'data': 'Connected! ayy'})
    # need visibility of the global thread object
    # global thread
    # if not thread.isAlive():
    #     print("Starting Thread")
    #     thread = DataThread()
    #     thread.start()

# @socketio.on('message')
# def handle_message(msg):
#     pass



# @app.route("/pulse", methods=['GET', 'POST'])
# def pulse():
#     """API endpoint for POST requests"""
#
#     import time
#     import requests
#
#     url = 'https://1359-62-131-191-3.ngrok.io/test'
#     headers = {'Content-type': 'text/html; charset=UTF-8'}
#     response = requests.post(url, data=data, headers=headers)
#     # wait for the response. it should not be higher
#     # than keep alive time for TCP connection
#
#     # render template or redirect to some url:
#     # return redirect("some_url")
#     # return render_template("some_page.html", message=str(response.text)) # or response.json()
#
#     i = 0
#     while True:
#         i += 1
#         time.sleep(3)
#         return i
#     # return "Content not supported"




if __name__ == '__main__':
    host = "0.0.0.0"
    app.run(host=host, port=PORT, debug=True)

