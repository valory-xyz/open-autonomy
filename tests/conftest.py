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

"""Conftest module for Pytest."""
import logging
from pathlib import Path
from typing import List, Tuple

import docker
import pytest

from tests.helpers.constants import KEY_PAIRS
from tests.helpers.constants import ROOT_DIR as _ROOT_DIR
from tests.helpers.docker.base import launch_image
from tests.helpers.docker.ganache import (
    DEFAULT_GANACHE_ADDR,
    DEFAULT_GANACHE_PORT,
    GanacheDockerImage,
)
from tests.helpers.docker.gnosis_safe_net import (
    DEFAULT_HARDHAT_PORT,
    GnosisSafeNetDockerImage,
)
from tests.helpers.docker.tendermint import (
    DEFAULT_PROXY_APP,
    DEFAULT_TENDERMINT_PORT,
    TendermintDockerImage,
)


ROOT_DIR = _ROOT_DIR
DATA_PATH = _ROOT_DIR / "tests" / "data"
DEFAULT_AMOUNT = 1000000000000000000000

ETHEREUM_KEY_DEPLOYER = DATA_PATH / "ethereum_key_deployer.txt"
ETHEREUM_KEY_PATH_1 = DATA_PATH / "ethereum_key_1.txt"
ETHEREUM_KEY_PATH_2 = DATA_PATH / "ethereum_key_2.txt"
ETHEREUM_KEY_PATH_3 = DATA_PATH / "ethereum_key_3.txt"
ETHEREUM_KEY_PATH_4 = DATA_PATH / "ethereum_key_4.txt"


def get_key(key_path: Path) -> str:
    """Returns key value from file.""" ""
    return key_path.read_bytes().strip().decode()


@pytest.fixture()
def tendermint_port() -> int:
    """Get the Tendermint port"""
    return DEFAULT_TENDERMINT_PORT


@pytest.mark.integration
@pytest.mark.ledger
@pytest.fixture(scope="function")
def tendermint(
    tendermint_port,
    proxy_app: str = DEFAULT_PROXY_APP,
    timeout: float = 2.0,
    max_attempts: int = 10,
):
    """Launch the Ganache image."""
    client = docker.from_env()
    logging.info(f"Launching Tendermint at port {tendermint_port}")
    image = TendermintDockerImage(client, tendermint_port, proxy_app)
    yield from launch_image(image, timeout=timeout, max_attempts=max_attempts)


@pytest.fixture()
def hardhat_port() -> int:
    """Get the Tendermint port"""
    return DEFAULT_HARDHAT_PORT


@pytest.fixture()
def key_pairs() -> List[Tuple[str, str]]:
    """Get the default key paris for hardhat."""
    return KEY_PAIRS


@pytest.mark.integration
@pytest.mark.ledger
@pytest.fixture(scope="function")
def gnosis_safe_hardhat(
    hardhat_port,
    timeout: float = 3.0,
    max_attempts: int = 30,
):
    """Launch the HardHat node with Gnosis Safe contracts deployed."""
    client = docker.from_env()
    logging.info(f"Launching Hardhat at port {hardhat_port}")
    image = GnosisSafeNetDockerImage(client, hardhat_port)
    yield from launch_image(image, timeout=timeout, max_attempts=max_attempts)


@pytest.fixture(scope="session")
def ganache_addr() -> str:
    """HTTP address to the Ganache node."""
    return DEFAULT_GANACHE_ADDR


@pytest.fixture(scope="session")
def ganache_port() -> int:
    """Port of the connection to the Ganache Node to use during the tests."""
    return DEFAULT_GANACHE_PORT


@pytest.fixture(scope="session")
def ganache_configuration():
    """Get the Ganache configuration for testing purposes."""
    return dict(
        accounts_balances=[
            (get_key(ETHEREUM_KEY_DEPLOYER), DEFAULT_AMOUNT),
            (get_key(ETHEREUM_KEY_PATH_1), DEFAULT_AMOUNT),
            (get_key(ETHEREUM_KEY_PATH_2), DEFAULT_AMOUNT),
            (get_key(ETHEREUM_KEY_PATH_3), DEFAULT_AMOUNT),
            (get_key(ETHEREUM_KEY_PATH_4), DEFAULT_AMOUNT),
        ],
    )


@pytest.mark.integration
@pytest.mark.ledger
@pytest.fixture(scope="function")
def ganache(
    ganache_configuration,
    ganache_addr,
    ganache_port,
    timeout: float = 2.0,
    max_attempts: int = 10,
):
    """Launch the Ganache image."""
    client = docker.from_env()
    image = GanacheDockerImage(
        client, ganache_addr, ganache_port, config=ganache_configuration
    )
    yield from launch_image(image, timeout=timeout, max_attempts=max_attempts)
