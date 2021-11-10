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
import socket
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, Generator, List, Tuple, cast
from unittest.mock import MagicMock

import docker
import pytest
from aea.configurations.base import PublicId
from aea.configurations.constants import DEFAULT_LEDGER
from aea.connections.base import Connection
from aea.crypto.ledger_apis import DEFAULT_LEDGER_CONFIGS
from aea.crypto.registries import make_crypto
from aea.crypto.wallet import CryptoStore
from aea.identity.base import Identity
from aea_ledger_ethereum import EthereumCrypto

from tests.helpers.constants import KEY_PAIRS
from tests.helpers.constants import ROOT_DIR as _ROOT_DIR
from tests.helpers.docker.base import launch_image
from tests.helpers.docker.ganache import (
    DEFAULT_GANACHE_ADDR,
    DEFAULT_GANACHE_CHAIN_ID,
    DEFAULT_GANACHE_PORT,
    GanacheDockerImage,
)
from tests.helpers.docker.gnosis_safe_net import (
    DEFAULT_HARDHAT_ADDR,
    DEFAULT_HARDHAT_PORT,
    GnosisSafeNetDockerImage,
)
from tests.helpers.docker.tendermint import (
    DEFAULT_PROXY_APP,
    DEFAULT_TENDERMINT_PORT,
    TendermintDockerImage,
)


def get_key(key_path: Path) -> str:
    """Returns key value from file.""" ""
    return key_path.read_bytes().strip().decode()


ROOT_DIR = _ROOT_DIR
DATA_PATH = _ROOT_DIR / "tests" / "data"
DEFAULT_AMOUNT = 1000000000000000000000
UNKNOWN_PROTOCOL_PUBLIC_ID = PublicId("unused", "unused", "1.0.0")

ETHEREUM_KEY_DEPLOYER = DATA_PATH / "ethereum_key_deployer.txt"
ETHEREUM_KEY_PATH_1 = DATA_PATH / "ethereum_key_1.txt"
ETHEREUM_KEY_PATH_2 = DATA_PATH / "ethereum_key_2.txt"
ETHEREUM_KEY_PATH_3 = DATA_PATH / "ethereum_key_3.txt"
ETHEREUM_KEY_PATH_4 = DATA_PATH / "ethereum_key_4.txt"
GANACHE_CONFIGURATION = dict(
    accounts_balances=[
        (get_key(ETHEREUM_KEY_DEPLOYER), DEFAULT_AMOUNT),
        (get_key(ETHEREUM_KEY_PATH_1), DEFAULT_AMOUNT),
        (get_key(ETHEREUM_KEY_PATH_2), DEFAULT_AMOUNT),
        (get_key(ETHEREUM_KEY_PATH_3), DEFAULT_AMOUNT),
        (get_key(ETHEREUM_KEY_PATH_4), DEFAULT_AMOUNT),
    ],
)


@pytest.fixture()
def tendermint_port() -> int:
    """Get the Tendermint port"""
    return DEFAULT_TENDERMINT_PORT


@pytest.mark.integration
@pytest.mark.ledger
@pytest.fixture(scope="function")
def tendermint(
    tendermint_port: Any,
    proxy_app: str = DEFAULT_PROXY_APP,
    timeout: float = 2.0,
    max_attempts: int = 10,
) -> Generator:
    """Launch the Ganache image."""
    client = docker.from_env()
    logging.info(f"Launching Tendermint at port {tendermint_port}")
    image = TendermintDockerImage(client, tendermint_port, proxy_app)
    yield from launch_image(image, timeout=timeout, max_attempts=max_attempts)


@pytest.fixture()
def hardhat_addr() -> str:
    """Get the hardhat addr"""
    return DEFAULT_HARDHAT_ADDR


@pytest.fixture()
def hardhat_port() -> int:
    """Get the hardhat port"""
    return DEFAULT_HARDHAT_PORT


@pytest.fixture()
def key_pairs() -> List[Tuple[str, str]]:
    """Get the default key paris for hardhat."""
    return KEY_PAIRS


@pytest.mark.integration
@pytest.mark.ledger
@pytest.fixture(scope="function")
def gnosis_safe_hardhat(
    hardhat_addr: Any,
    hardhat_port: Any,
    timeout: float = 3.0,
    max_attempts: int = 40,
) -> Generator:
    """Launch the HardHat node with Gnosis Safe contracts deployed."""
    client = docker.from_env()
    logging.info(f"Launching Hardhat at port {hardhat_port}")
    image = GnosisSafeNetDockerImage(client, hardhat_addr, hardhat_port)
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
def ganache_configuration() -> Dict:
    """Get the Ganache configuration for testing purposes."""
    return GANACHE_CONFIGURATION


@pytest.mark.integration
@pytest.mark.ledger
@pytest.fixture(scope="function")
def ganache(
    ganache_configuration: Any,
    ganache_addr: Any,
    ganache_port: Any,
    timeout: float = 2.0,
    max_attempts: int = 10,
) -> Generator:
    """Launch the Ganache image."""
    client = docker.from_env()
    image = GanacheDockerImage(
        client, ganache_addr, ganache_port, config=ganache_configuration
    )
    yield from launch_image(image, timeout=timeout, max_attempts=max_attempts)


def get_unused_tcp_port() -> int:
    """Get an unused TCP port."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    s.listen(1)
    port = s.getsockname()[1]
    s.close()
    return port


def get_host() -> str:
    """Get the host."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(("10.255.255.255", 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = "127.0.0.1"
    finally:
        s.close()
    return IP


@pytest.fixture(scope="session")
def ethereum_testnet_config(ganache_addr: str, ganache_port: int) -> Dict:
    """Get Ethereum ledger api configurations using Ganache."""
    new_uri = f"{ganache_addr}:{ganache_port}"
    new_config = {
        "address": new_uri,
        "chain_id": DEFAULT_GANACHE_CHAIN_ID,
        # "denom": ETHEREUM_DEFAULT_CURRENCY_DENOM, # noqa: E800
        # "gas_price_api_key": GAS_PRICE_API_KEY, # noqa: E800
    }
    return new_config


@pytest.fixture(scope="function")
def update_default_ethereum_ledger_api(ethereum_testnet_config: Dict) -> Generator:
    """Change temporarily default Ethereum ledger api configurations to interact with local Ganache."""
    old_config = DEFAULT_LEDGER_CONFIGS.pop(EthereumCrypto.identifier, None)
    DEFAULT_LEDGER_CONFIGS[EthereumCrypto.identifier] = ethereum_testnet_config
    yield
    DEFAULT_LEDGER_CONFIGS.pop(EthereumCrypto.identifier)
    DEFAULT_LEDGER_CONFIGS[EthereumCrypto.identifier] = old_config


@pytest.fixture()
async def ledger_apis_connection(
    request: Any, ethereum_testnet_config: Dict
) -> AsyncGenerator:
    """Make a connection."""
    crypto = make_crypto(DEFAULT_LEDGER)
    identity = Identity("name", crypto.address, crypto.public_key)
    crypto_store = CryptoStore()
    directory = Path(ROOT_DIR, "packages", "valory", "connections", "ledger")
    connection = Connection.from_dir(
        directory, data_dir=MagicMock(), identity=identity, crypto_store=crypto_store
    )
    connection = cast(Connection, connection)
    connection._logger = logging.getLogger("packages.valory.connections.ledger")

    # use testnet config
    connection.configuration.config.get("ledger_apis", {})[
        "ethereum"
    ] = ethereum_testnet_config

    await connection.connect()
    yield connection
    await connection.disconnect()
