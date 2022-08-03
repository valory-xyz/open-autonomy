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

"""Conftest module for Pytest."""
import logging
import socket
import time
import urllib
from typing import Generator

import pytest
import requests

from autonomy.data.Dockerfiles.tendermint.tendermint import (  # type: ignore
    DEFAULT_RPC_LISTEN_ADDRESS,
)


__parse_result = urllib.parse.urlparse(DEFAULT_RPC_LISTEN_ADDRESS)  # type: ignore
__IP, __RPC_PORT = __parse_result.hostname, __parse_result.port


@pytest.fixture(scope="session")
def http_() -> str:
    """The http prefix."""
    return "http://"


@pytest.fixture(scope="session")
def loopback() -> str:
    """The loopback address."""
    return "127.0.0.1"


@pytest.fixture(scope="session")
def rpc_port() -> int:
    """The Tendermint RPC port."""
    return __RPC_PORT


def __port_is_open(ip: str, port: int) -> bool:
    """Assess whether a port is open"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    is_open = sock.connect_ex((ip, port)) == 0
    sock.close()
    return is_open


@pytest.fixture
def wait_for_node(
    http_: str, loopback: str, rpc_port: int
) -> Generator[None, None, None]:
    """Wait for Tendermint node to run."""
    i, max_retries = 0, 5
    while not __port_is_open(loopback, rpc_port) and i < max_retries:
        logging.debug(f"waiting for node... t={i}")
        i += 1
        time.sleep(1)
    response = requests.get(f"{http_}{loopback}:{rpc_port}/status")
    success = response.status_code == 200
    assert success, "Tendermint node not running"
    yield
