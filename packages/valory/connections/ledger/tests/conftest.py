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
"""Test confiugurations for the package."""

# pylint: skip-file

import logging
import time
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, Generator, List, Tuple, cast
from unittest.mock import MagicMock

import pytest
from aea.configurations.constants import DEFAULT_LEDGER
from aea.connections.base import Connection
from aea.contracts.base import Contract
from aea.crypto.ledger_apis import DEFAULT_LEDGER_CONFIGS, LedgerApi
from aea.crypto.registries import ledger_apis_registry, make_crypto
from aea.crypto.wallet import CryptoStore
from aea.identity.base import Identity
from aea_ledger_ethereum import EthereumCrypto
from aea_ledger_ethereum.test_tools.constants import (
    ETHEREUM_TESTNET_CONFIG as _DEFAULT_ETHEREUM_TESTNET_CONFIG,
)
from aea_test_autonomy.configurations import ETHEREUM_KEY_DEPLOYER, KEY_PAIRS
from aea_test_autonomy.docker.ganache import DEFAULT_GANACHE_ADDR, DEFAULT_GANACHE_PORT
from aea_test_autonomy.fixture_helpers import (  # noqa: F401  # pylint: disable=unused-import
    tendermint,
)
from aea_test_autonomy.helpers.contracts import get_register_contract
from web3 import Web3


NB_OWNERS = 4
THRESHOLD = 1

PACKAGE_DIR = Path(__file__).parent.parent

DEFAULT_ETHEREUM_TESTNET_CONFIG = {
    **_DEFAULT_ETHEREUM_TESTNET_CONFIG,
    "default_gas_price_strategy": "eip1559",
}


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


@pytest.fixture()
def ganache_addr() -> str:
    """Get the ganache addr"""
    return DEFAULT_GANACHE_ADDR


@pytest.fixture()
def ganache_port() -> int:
    """Get the ganache port"""
    return DEFAULT_GANACHE_PORT


@pytest.fixture(scope="function")
def ethereum_testnet_config(ganache_addr: str, ganache_port: int) -> Dict:
    """Get Ethereum ledger api configurations using Ganache."""
    new_uri = f"{ganache_addr}:{ganache_port}"
    new_config = DEFAULT_ETHEREUM_TESTNET_CONFIG.copy()
    new_config["address"] = new_uri
    return new_config


@pytest.fixture(scope="function")
def update_default_ethereum_ledger_api(ethereum_testnet_config: Dict) -> Generator:
    """Change temporarily default Ethereum ledger api configurations to interact with local Ganache."""
    old_config = DEFAULT_LEDGER_CONFIGS.pop(EthereumCrypto.identifier)
    DEFAULT_LEDGER_CONFIGS[EthereumCrypto.identifier] = ethereum_testnet_config
    yield
    DEFAULT_LEDGER_CONFIGS.pop(EthereumCrypto.identifier)
    DEFAULT_LEDGER_CONFIGS[EthereumCrypto.identifier] = old_config


def make_ledger_api_connection(
    ethereum_testnet_config: Dict = DEFAULT_ETHEREUM_TESTNET_CONFIG,
) -> Connection:
    """Make a connection."""
    crypto = make_crypto(DEFAULT_LEDGER)
    identity = Identity("name", crypto.address, crypto.public_key)
    crypto_store = CryptoStore()
    directory = PACKAGE_DIR
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
def ledger_api(
    ethereum_testnet_config: Dict,
) -> Generator[LedgerApi, None, None]:
    """Ledger api fixture."""
    ledger_id, config = EthereumCrypto.identifier, ethereum_testnet_config
    api = ledger_apis_registry.make(ledger_id, **config)
    yield api


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
        PACKAGE_DIR.parent.parent, "contracts", "gnosis_safe_proxy_factory"
    )
    _ = get_register_contract(
        directory
    )  # we need to load this too as it's a dependency of the gnosis_safe
    directory = Path(PACKAGE_DIR.parent.parent, "contracts", "gnosis_safe")
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
