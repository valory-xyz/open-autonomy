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
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, Generator, Iterator, List, Tuple, cast
from unittest.mock import MagicMock

import docker
import pytest
from aea.configurations.base import PublicId
from aea.configurations.constants import DEFAULT_LEDGER
from aea.connections.base import Connection
from aea.contracts.base import Contract
from aea.crypto.ledger_apis import DEFAULT_LEDGER_CONFIGS, LedgerApi
from aea.crypto.registries import ledger_apis_registry, make_crypto
from aea.crypto.wallet import CryptoStore
from aea.identity.base import Identity
from aea_cli_ipfs.ipfs_utils import IPFSDaemon
from aea_ledger_ethereum import (
    DEFAULT_EIP1559_STRATEGY,
    DEFAULT_GAS_STATION_STRATEGY,
    EthereumCrypto,
)
from web3 import Web3

from tests.helpers.constants import KEY_PAIRS
from tests.helpers.constants import ROOT_DIR as _ROOT_DIR
from tests.helpers.contracts import get_register_contract
from tests.helpers.docker.acn_node import ACNNodeDockerImage, DEFAULT_ACN_CONFIG
from tests.helpers.docker.base import launch_image, launch_many_containers
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
    DEFAULT_ABCI_HOST,
    DEFAULT_ABCI_PORT,
    DEFAULT_TENDERMINT_PORT,
    FlaskTendermintDockerImage,
    TendermintDockerImage,
)


def get_key(key_path: Path) -> str:
    """Returns key value from file.""" ""
    return key_path.read_bytes().strip().decode()


ROOT_DIR = _ROOT_DIR
DATA_PATH = _ROOT_DIR / "tests" / "data"
DEFAULT_AMOUNT = 1000000000000000000000
UNKNOWN_PROTOCOL_PUBLIC_ID = PublicId("unused", "unused", "1.0.0")

NB_OWNERS = 4
THRESHOLD = 1

ETHEREUM_KEY_DEPLOYER = DATA_PATH / "ethereum_key_deployer.txt"
ETHEREUM_KEY_PATH_1 = DATA_PATH / "ethereum_key_1.txt"
ETHEREUM_KEY_PATH_2 = DATA_PATH / "ethereum_key_2.txt"
ETHEREUM_KEY_PATH_3 = DATA_PATH / "ethereum_key_3.txt"
ETHEREUM_KEY_PATH_4 = DATA_PATH / "ethereum_key_4.txt"

ETHEREUM_ENCRYPTED_KEYS = DATA_PATH / "encrypted_keys.json"
ETHEREUM_ENCRYPTION_PASSWORD = "much-secure"  # nosec

GANACHE_CONFIGURATION = dict(
    accounts_balances=[
        (get_key(ETHEREUM_KEY_DEPLOYER), DEFAULT_AMOUNT),
        (get_key(ETHEREUM_KEY_PATH_1), DEFAULT_AMOUNT),
        (get_key(ETHEREUM_KEY_PATH_2), DEFAULT_AMOUNT),
        (get_key(ETHEREUM_KEY_PATH_3), DEFAULT_AMOUNT),
        (get_key(ETHEREUM_KEY_PATH_4), DEFAULT_AMOUNT),
    ],
)
ETHEREUM_DEFAULT_LEDGER_CONFIG = {
    "address": f"{DEFAULT_GANACHE_ADDR}:{DEFAULT_GANACHE_PORT}",
    "chain_id": DEFAULT_GANACHE_CHAIN_ID,
    # "denom": ETHEREUM_DEFAULT_CURRENCY_DENOM, # noqa: E800
    # "gas_price_api_key": GAS_PRICE_API_KEY, # noqa: E800
    "default_gas_price_strategy": "eip1559",
    "gas_price_strategies": {
        "gas_station": DEFAULT_GAS_STATION_STRATEGY,
        "eip1559": DEFAULT_EIP1559_STRATEGY,
    },
}

ANY_ADDRESS = "0.0.0.0"  # nosec


@pytest.fixture(scope="session")
def tendermint_port() -> int:
    """Get the Tendermint port"""
    return DEFAULT_TENDERMINT_PORT


@pytest.fixture(scope="class")
def tendermint(
    tendermint_port: Any,
    abci_host: str = DEFAULT_ABCI_HOST,
    abci_port: int = DEFAULT_ABCI_PORT,
    timeout: float = 2.0,
    max_attempts: int = 10,
) -> Generator:
    """Launch the Ganache image."""
    client = docker.from_env()
    logging.info(f"Launching Tendermint at port {tendermint_port}")
    image = TendermintDockerImage(client, abci_host, abci_port, tendermint_port)
    yield from launch_image(image, timeout=timeout, max_attempts=max_attempts)


@pytest.fixture
def nb_nodes(request: Any) -> int:
    """Get a parametrized number of nodes."""
    return request.param


@pytest.fixture
def flask_tendermint(
    tendermint_port: Any,
    nb_nodes: int,
    abci_host: str = DEFAULT_ABCI_HOST,
    abci_port: int = DEFAULT_ABCI_PORT,
    timeout: float = 2.0,
    max_attempts: int = 10,
) -> Generator[FlaskTendermintDockerImage, None, None]:
    """Launch the Flask server with Tendermint container."""
    client = docker.from_env()
    logging.info(
        f"Launching Tendermint nodes at ports {[tendermint_port + i * 10 for i in range(nb_nodes)]}"
    )
    image = FlaskTendermintDockerImage(client, abci_host, abci_port, tendermint_port)
    yield from cast(
        Generator[FlaskTendermintDockerImage, None, None],
        launch_many_containers(image, nb_nodes, timeout, max_attempts),
    )


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


@pytest.fixture()
def owners(key_pairs: List[Tuple[str, str]]) -> List[str]:
    """Get the owners."""
    return [Web3.toChecksumAddress(t[0]) for t in key_pairs[:NB_OWNERS]]


@pytest.fixture()
def threshold() -> int:
    """Returns the amount of threshold."""
    return THRESHOLD


@pytest.fixture(scope="function")
def gnosis_safe_hardhat_scope_function(
    hardhat_addr: Any,
    hardhat_port: Any,
    timeout: float = 3.0,
    max_attempts: int = 40,
) -> Generator:
    """Launch the HardHat node with Gnosis Safe contracts deployed. This fixture is scoped to a function which means it will destroyed at the end of the test."""
    client = docker.from_env()
    logging.info(f"Launching Hardhat at port {hardhat_port}")
    image = GnosisSafeNetDockerImage(client, hardhat_addr, hardhat_port)
    yield from launch_image(image, timeout=timeout, max_attempts=max_attempts)


@pytest.fixture(scope="class")
def gnosis_safe_hardhat_scope_class(
    timeout: float = 3.0,
    max_attempts: int = 40,
) -> Generator:
    """Launch the HardHat node with Gnosis Safe contracts deployed.This fixture is scoped to a class which means it will destroyed after running every test in a class."""
    client = docker.from_env()
    logging.info(f"Launching Hardhat at port {DEFAULT_HARDHAT_PORT}")
    image = GnosisSafeNetDockerImage(client, DEFAULT_HARDHAT_ADDR, DEFAULT_HARDHAT_PORT)
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


@pytest.fixture(scope="function")
def ganache_scope_function(
    ganache_configuration: Any,
    ganache_addr: Any,
    ganache_port: Any,
    timeout: float = 2.0,
    max_attempts: int = 10,
) -> Generator:
    """Launch the Ganache image. This fixture is scoped to a function which means it will destroyed at the end of the test."""
    client = docker.from_env()
    image = GanacheDockerImage(
        client, ganache_addr, ganache_port, config=ganache_configuration
    )
    yield from launch_image(image, timeout=timeout, max_attempts=max_attempts)


@pytest.fixture(scope="class")
def ganache_scope_class(
    ganache_configuration: Any,
    ganache_addr: Any,
    ganache_port: Any,
    timeout: float = 2.0,
    max_attempts: int = 10,
) -> Generator:
    """Launch the Ganache image. This fixture is scoped to a class which means it will destroyed after running every test in a class."""
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
    new_config = ETHEREUM_DEFAULT_LEDGER_CONFIG
    new_config["address"] = new_uri
    return new_config


@pytest.fixture()
def ledger_api(
    ethereum_testnet_config: Dict,
) -> Generator[LedgerApi, None, None]:
    """Ledger api fixture."""
    ledger_id, config = EthereumCrypto.identifier, ethereum_testnet_config
    api = ledger_apis_registry.make(ledger_id, **config)
    yield api


@pytest.fixture(scope="function")
def update_default_ethereum_ledger_api(ethereum_testnet_config: Dict) -> Generator:
    """Change temporarily default Ethereum ledger api configurations to interact with local Ganache."""
    old_config = DEFAULT_LEDGER_CONFIGS.pop(EthereumCrypto.identifier)
    DEFAULT_LEDGER_CONFIGS[EthereumCrypto.identifier] = ethereum_testnet_config
    yield
    DEFAULT_LEDGER_CONFIGS.pop(EthereumCrypto.identifier)
    DEFAULT_LEDGER_CONFIGS[EthereumCrypto.identifier] = old_config


def make_ledger_api_connection(
    ethereum_testnet_config: Dict = ETHEREUM_DEFAULT_LEDGER_CONFIG,
) -> Connection:
    """Make a connection."""
    crypto = make_crypto(DEFAULT_LEDGER)
    identity = Identity("name", crypto.address, crypto.public_key)
    crypto_store = CryptoStore()
    directory = Path(ROOT_DIR, "packages", "valory", "connections", "ledger")
    connection = Connection.from_dir(
        str(directory),
        data_dir=MagicMock(),
        identity=identity,
        crypto_store=crypto_store,
    )
    connection = cast(Connection, connection)
    connection._logger = logging.getLogger("packages.valory.connections.ledger")

    # use testnet config
    connection.configuration.config.get("ledger_apis", {})[
        "ethereum"
    ] = ethereum_testnet_config

    connection.request_retry_attempts = 1  # type: ignore
    connection.request_retry_attempts = 2  # type: ignore
    return connection


@pytest.fixture()
async def ledger_apis_connection(
    request: Any, ethereum_testnet_config: Dict
) -> AsyncGenerator:
    """Make a connection."""
    connection = make_ledger_api_connection(ethereum_testnet_config)
    await connection.connect()
    yield connection
    await connection.disconnect()


@pytest.fixture()
def gnosis_safe_contract(
    ledger_api: LedgerApi, owners: List[str], threshold: int
) -> Generator[Tuple[Contract, str], None, None]:
    """
    Instantiate an Gnosis Safe contract instance.

    As a side effect, register it to the registry, if not already registered.

    :param ledger_api: ledger_api fixture
    :param owners: onwers fixture
    :param threshold: threshold fixture
    :yield: contract and contract_address
    """
    directory = Path(
        ROOT_DIR, "packages", "valory", "contracts", "gnosis_safe_proxy_factory"
    )
    _ = get_register_contract(
        directory
    )  # we need to load this too as it's a dependency of the gnosis_safe
    directory = Path(ROOT_DIR, "packages", "valory", "contracts", "gnosis_safe")
    contract = get_register_contract(directory)
    crypto = make_crypto(
        EthereumCrypto.identifier, private_key_path=ETHEREUM_KEY_DEPLOYER
    )
    tx = contract.get_deploy_transaction(
        ledger_api=ledger_api,
        deployer_address=crypto.address,
        gas=5000000,
        owners=owners,
        threshold=threshold,
    )
    assert tx is not None
    contract_address = tx.pop("contract_address")  # hack
    assert isinstance(contract_address, str)
    gas = ledger_api.api.eth.estimate_gas(transaction=tx)
    tx["gas"] = gas
    tx_signed = crypto.sign_transaction(tx)
    tx_digest = ledger_api.send_signed_transaction(tx_signed)
    assert tx_digest is not None
    time.sleep(0.5)
    receipt = ledger_api.get_transaction_receipt(tx_digest)
    assert receipt is not None
    # contract_address = ledger_api.get_contract_address(receipt)  # noqa: E800 won't work as it's a proxy
    yield contract, contract_address


@pytest.fixture(scope="module")
def ipfs_daemon() -> Iterator[bool]:
    """Starts an IPFS daemon for the tests."""
    print("Starting IPFS daemon...")
    daemon = IPFSDaemon()
    daemon.start()
    yield daemon.is_started()
    print("Tearing down IPFS daemon...")
    daemon.stop()


@pytest.fixture(scope="function")
def acn_node(
    config: Dict = None,
    timeout: float = 2.0,
    max_attempts: int = 10,
) -> Generator:
    """Launch the Ganache image."""
    client = docker.from_env()
    config = config or DEFAULT_ACN_CONFIG
    logging.info(f"Launching ACNNode with the following config: {config}")
    image = ACNNodeDockerImage(client, config)
    yield from launch_image(image, timeout=timeout, max_attempts=max_attempts)
