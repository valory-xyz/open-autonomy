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
import inspect
import logging
import os
import socket
import time
from functools import wraps
from pathlib import Path
from types import FunctionType, MethodType
from typing import (
    Any,
    AsyncGenerator,
    Callable,
    Dict,
    Generator,
    Iterator,
    List,
    Optional,
    Sequence,
    Tuple,
    Union,
    cast,
)
from unittest.mock import MagicMock

import docker
import pytest
from aea.configurations.base import ConnectionConfig, PublicId
from aea.configurations.constants import DEFAULT_LEDGER
from aea.connections.base import Connection
from aea.contracts.base import Contract
from aea.crypto.base import Crypto
from aea.crypto.ledger_apis import DEFAULT_LEDGER_CONFIGS, LedgerApi
from aea.crypto.registries import ledger_apis_registry, make_crypto
from aea.crypto.wallet import CryptoStore
from aea.helpers.base import CertRequest, SimpleId
from aea.identity.base import Identity
from aea_cli_ipfs.ipfs_utils import IPFSDaemon
from aea_ledger_ethereum import (
    DEFAULT_EIP1559_STRATEGY,
    DEFAULT_GAS_STATION_STRATEGY,
    EthereumCrypto,
)
from web3 import Web3

from packages.open_aea.connections.p2p_libp2p.check_dependencies import build_node
from packages.open_aea.connections.p2p_libp2p.connection import (
    LIBP2P_NODE_MODULE_NAME,
    MultiAddr,
    P2PLibp2pConnection,
    POR_DEFAULT_SERVICE_ID,
)
from packages.open_aea.connections.p2p_libp2p_client.connection import (
    P2PLibp2pClientConnection,
)
from packages.open_aea.connections.p2p_libp2p_mailbox.connection import (
    P2PLibp2pMailboxConnection,
)

from tests.helpers.constants import KEY_PAIRS
from tests.helpers.constants import ROOT_DIR as _ROOT_DIR
from tests.helpers.contracts import get_register_contract
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
    DEFAULT_ABCI_HOST,
    DEFAULT_ABCI_PORT,
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

NB_OWNERS = 4
THRESHOLD = 1

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


# ported from open-aea for ACN testing purposes
PUBLIC_DHT_P2P_MADDR_1 = "/dns4/acn.fetch.ai/tcp/9000/p2p/16Uiu2HAkw1ypeQYQbRFV5hKUxGRHocwU5ohmVmCnyJNg36tnPFdx"
PUBLIC_DHT_P2P_MADDR_2 = "/dns4/acn.fetch.ai/tcp/9001/p2p/16Uiu2HAmVWnopQAqq4pniYLw44VRvYxBUoRHqjz1Hh2SoCyjbyRW"
PUBLIC_DHT_DELEGATE_URI_1 = "acn.fetch.ai:11000"
PUBLIC_DHT_DELEGATE_URI_2 = "acn.fetch.ai:11001"
PUBLIC_DHT_P2P_PUBLIC_KEY_1 = (
    "0217a59bd805c310aca4febe0e99ce22ee3712ae085dc1e5630430b1e15a584bb7"
)
PUBLIC_DHT_P2P_PUBLIC_KEY_2 = (
    "03fa7cfae1037cba5218f0f5743802eced8de3247c55ecebaae46c7d3679e3f91d"
)
PUBLIC_STAGING_DHT_P2P_MADDR_1 = "/dns4/acn.fetch-ai.com/tcp/9003/p2p/16Uiu2HAmQo6EHbmwhkMJkyhjz1DCxE8Ahsy5zFZtw97tWCFckLUp"
PUBLIC_STAGING_DHT_P2P_MADDR_2 = "/dns4/acn.fetch-ai.com/tcp/9004/p2p/16Uiu2HAmEvey5siPHzdEb5QcTYCkh16squbeFHYHvRCWP9Jzp4bV"
PUBLIC_STAGING_DHT_DELEGATE_URI_1 = "acn.fetch-ai.com:11003"
PUBLIC_STAGING_DHT_DELEGATE_URI_2 = "acn.fetch-ai.com:11004"
PUBLIC_STAGING_DHT_P2P_PUBLIC_KEY_1 = (
    "03b45f898bde437ace4728b3ba097988306930b1600b7991d384e6d08452e340e1"
)
PUBLIC_STAGING_DHT_P2P_PUBLIC_KEY_2 = (
    "0321bac023b7f7cf655cf5e0f988a4c1cf758f7b530528362c4ba8d563f7b090c4"
)
# TODO: temporary overwriting of addresses, URIs and public keys
#  used in test_p2p_libp2p/test_public_dht.py
PUBLIC_DHT_P2P_MADDR_1 = PUBLIC_STAGING_DHT_P2P_MADDR_1
PUBLIC_DHT_P2P_MADDR_2 = PUBLIC_STAGING_DHT_P2P_MADDR_2
PUBLIC_DHT_DELEGATE_URI_1 = PUBLIC_STAGING_DHT_DELEGATE_URI_1
PUBLIC_DHT_DELEGATE_URI_2 = PUBLIC_STAGING_DHT_DELEGATE_URI_2
PUBLIC_DHT_P2P_PUBLIC_KEY_1 = PUBLIC_STAGING_DHT_P2P_PUBLIC_KEY_1
PUBLIC_DHT_P2P_PUBLIC_KEY_2 = PUBLIC_STAGING_DHT_P2P_PUBLIC_KEY_2

DEFAULT_LEDGER_LIBP2P_NODE = "cosmos"  # Secp256k1 keys
MAX_FLAKY_RERUNS_INTEGRATION = 1


@pytest.fixture()
def tendermint_port() -> int:
    """Get the Tendermint port"""
    return DEFAULT_TENDERMINT_PORT


@pytest.fixture(scope="function")
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
    daemon = IPFSDaemon(offline=True)
    daemon.start()
    yield daemon.is_started()
    print("Tearing down IPFS daemon...")
    daemon.stop()


def _process_cert(key: Crypto, cert: CertRequest, path_prefix: str):
    # must match aea/cli/issue_certificates.py:_process_certificate
    assert cert.public_key is not None
    message = cert.get_message(cert.public_key)
    signature = key.sign_message(message).encode("ascii").hex()
    Path(cert.get_absolute_save_path(path_prefix)).write_bytes(
        signature.encode("ascii")
    )


def _make_libp2p_connection(
    data_dir: str,
    port: int = 10234,
    host: str = "127.0.0.1",
    relay: bool = True,
    delegate: bool = False,
    mailbox: bool = False,
    entry_peers: Optional[Sequence[MultiAddr]] = None,
    delegate_port: int = 11234,
    delegate_host: str = "127.0.0.1",
    mailbox_port: int = 8888,
    mailbox_host: str = "127.0.0.1",
    node_key_file: Optional[str] = None,
    agent_key: Optional[Crypto] = None,
    build_directory: Optional[str] = None,
    peer_registration_delay: str = "0.0",
) -> P2PLibp2pConnection:
    if not os.path.isdir(data_dir) or not os.path.exists(data_dir):
        raise ValueError("Data dir must be directory and exist!")
    log_file = os.path.join(data_dir, "libp2p_node_{}.log".format(port))
    if os.path.exists(log_file):
        os.remove(log_file)
    key = agent_key
    if key is None:
        key = make_crypto(DEFAULT_LEDGER)
    identity = Identity(
        "identity",
        address=key.address,
        public_key=key.public_key,
        default_address_key=key.identifier,
    )
    conn_crypto_store = None
    if node_key_file is not None:
        conn_crypto_store = CryptoStore({DEFAULT_LEDGER_LIBP2P_NODE: node_key_file})
    else:
        node_key = make_crypto(DEFAULT_LEDGER_LIBP2P_NODE)
        node_key_path = os.path.join(data_dir, f"{node_key.public_key}.txt")
        node_key.dump(node_key_path)
        conn_crypto_store = CryptoStore({node_key.identifier: node_key_path})
    cert_request = CertRequest(
        conn_crypto_store.public_keys[DEFAULT_LEDGER_LIBP2P_NODE],
        POR_DEFAULT_SERVICE_ID,
        key.identifier,
        "2021-01-01",
        "2021-01-02",
        "{public_key}",
        f"./{key.address}_cert.txt",
    )
    _process_cert(key, cert_request, path_prefix=data_dir)
    if not build_directory:
        build_directory = os.getcwd()
    config = {"ledger_id": node_key.identifier}
    if relay and delegate:
        configuration = ConnectionConfig(
            node_key_file=node_key_file,
            local_uri="{}:{}".format(host, port),
            public_uri="{}:{}".format(host, port),
            entry_peers=entry_peers,
            log_file=log_file,
            delegate_uri="{}:{}".format(delegate_host, delegate_port),
            peer_registration_delay=peer_registration_delay,
            connection_id=P2PLibp2pConnection.connection_id,
            build_directory=build_directory,
            cert_requests=[cert_request],
            **config,  # type: ignore
        )
    elif relay and not delegate:
        configuration = ConnectionConfig(
            node_key_file=node_key_file,
            local_uri="{}:{}".format(host, port),
            public_uri="{}:{}".format(host, port),
            entry_peers=entry_peers,
            log_file=log_file,
            peer_registration_delay=peer_registration_delay,
            connection_id=P2PLibp2pConnection.connection_id,
            build_directory=build_directory,
            cert_requests=[cert_request],
            **config,  # type: ignore
        )
    else:
        configuration = ConnectionConfig(
            node_key_file=node_key_file,
            local_uri="{}:{}".format(host, port),
            entry_peers=entry_peers,
            log_file=log_file,
            peer_registration_delay=peer_registration_delay,
            connection_id=P2PLibp2pConnection.connection_id,
            build_directory=build_directory,
            cert_requests=[cert_request],
            **config,  # type: ignore
        )

    if mailbox:
        configuration.config["mailbox_uri"] = f"{mailbox_host}:{mailbox_port}"
    else:
        configuration.config["mailbox_uri"] = ""

    if not os.path.exists(os.path.join(build_directory, LIBP2P_NODE_MODULE_NAME)):
        build_node(build_directory)
    connection = P2PLibp2pConnection(
        configuration=configuration,
        data_dir=data_dir,
        identity=identity,
        crypto_store=conn_crypto_store,
    )
    return connection


def _make_libp2p_client_connection(
    peer_public_key: str,
    data_dir: str,
    node_port: int = 11234,
    node_host: str = "127.0.0.1",
    uri: Optional[str] = None,
    ledger_api_id: Union[SimpleId, str] = DEFAULT_LEDGER,
) -> P2PLibp2pClientConnection:
    if not os.path.isdir(data_dir) or not os.path.exists(data_dir):
        raise ValueError("Data dir must be directory and exist!")
    crypto = make_crypto(ledger_api_id)
    identity = Identity(
        "identity",
        address=crypto.address,
        public_key=crypto.public_key,
        default_address_key=crypto.identifier,
    )
    cert_request = CertRequest(
        peer_public_key,
        POR_DEFAULT_SERVICE_ID,
        ledger_api_id,
        "2021-01-01",
        "2021-01-02",
        "{public_key}",
        f"./{crypto.address}_cert.txt",
    )
    _process_cert(crypto, cert_request, path_prefix=data_dir)
    config = {"ledger_id": crypto.identifier}
    configuration = ConnectionConfig(
        tcp_key_file=None,
        nodes=[
            {
                "uri": str(uri)
                if uri is not None
                else "{}:{}".format(node_host, node_port),
                "public_key": peer_public_key,
            },
        ],
        connection_id=P2PLibp2pClientConnection.connection_id,
        cert_requests=[cert_request],
        **config,  # type: ignore
    )
    return P2PLibp2pClientConnection(
        configuration=configuration, data_dir=data_dir, identity=identity
    )


def _make_libp2p_mailbox_connection(
    peer_public_key: str,
    data_dir: str,
    node_port: int = 8888,
    node_host: str = "127.0.0.1",
    uri: Optional[str] = None,
    ledger_api_id: Union[SimpleId, str] = DEFAULT_LEDGER,
) -> P2PLibp2pMailboxConnection:
    """Get a libp2p mailbox connection."""
    if not os.path.isdir(data_dir) or not os.path.exists(data_dir):
        raise ValueError("Data dir must be directory and exist!")
    crypto = make_crypto(ledger_api_id)
    identity = Identity(
        "identity",
        address=crypto.address,
        public_key=crypto.public_key,
        default_address_key=crypto.identifier,
    )
    cert_request = CertRequest(
        peer_public_key,
        POR_DEFAULT_SERVICE_ID,
        ledger_api_id,
        "2021-01-01",
        "2021-01-02",
        "{public_key}",
        f"./{crypto.address}_cert.txt",
    )
    _process_cert(crypto, cert_request, path_prefix=data_dir)
    config = {"ledger_id": crypto.identifier}
    configuration = ConnectionConfig(
        tcp_key_file=None,
        nodes=[
            {
                "uri": str(uri)
                if uri is not None
                else "{}:{}".format(node_host, node_port),
                "public_key": peer_public_key,
            },
        ],
        connection_id=P2PLibp2pMailboxConnection.connection_id,
        cert_requests=[cert_request],
        **config,  # type: ignore
    )
    return P2PLibp2pMailboxConnection(
        configuration=configuration, data_dir=data_dir, identity=identity
    )


def libp2p_log_on_failure(fn: Callable) -> Callable:
    """
    Decorate a pytest method running a libp2p node to print its logs in case test fails.

    :return: decorated method.
    """

    # for pydcostyle
    @wraps(fn)
    def wrapper(self, *args, **kwargs):
        try:
            return fn(self, *args, **kwargs)
        except Exception:
            for log_file in self.log_files:
                print("libp2p log file ======================= {}".format(log_file))
                try:
                    with open(log_file, "r") as f:
                        print(f.read())
                except FileNotFoundError:
                    pass
                print("=======================================")
            raise

    return wrapper


def libp2p_log_on_failure_all(cls):
    """
    Decorate every method of a class with `libp2p_log_on_failure`.

    :return: class with decorated methods.
    """
    for name, fn in inspect.getmembers(cls):
        if isinstance(fn, FunctionType):
            setattr(cls, name, libp2p_log_on_failure(fn))
        continue
        if isinstance(fn, MethodType):
            if fn.im_self is None:
                wrapped_fn = libp2p_log_on_failure(fn.im_func)
                method = MethodType(wrapped_fn, None, cls)
                setattr(cls, name, method)
            else:
                wrapped_fn = libp2p_log_on_failure(fn.im_func)
                clsmethod = MethodType(wrapped_fn, cls, type)
                setattr(cls, name, clsmethod)
    return cls
