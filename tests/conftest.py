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
import secrets
from typing import List, Optional, Tuple, cast

import docker
import pytest
from eth_account import Account
from eth_account.signers.local import LocalAccount
from eth_typing import URI
from gnosis.eth import EthereumClient
from gnosis.eth.constants import NULL_ADDRESS
from gnosis.eth.contracts import get_safe_V1_3_0_contract
from gnosis.safe import ProxyFactory
from hexbytes import HexBytes

from tests.helpers.constants import HTTP_LOCALHOST, KEY_PAIRS
from tests.helpers.constants import ROOT_DIR as _ROOT_DIR
from tests.helpers.docker.base import launch_image
from tests.helpers.docker.gnosis_safe_net import (
    DEFAULT_CALLBACK_HANDLER,
    DEFAULT_HARDHAT_PORT,
    GnosisSafeNetDockerImage,
    PROXY_FACTORY_CONTRACT,
    SAFE_CONTRACT,
)
from tests.helpers.docker.tendermint import (
    DEFAULT_PROXY_APP,
    DEFAULT_TENDERMINT_PORT,
    TendermintDockerImage,
)


ROOT_DIR = _ROOT_DIR


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
    image = TendermintDockerImage(client, tendermint_port, proxy_app)
    yield from launch_image(image, timeout=timeout, max_attempts=max_attempts)


@pytest.mark.integration
class UseTendermint:
    """Inherit from this class to use Tendermint."""

    @pytest.fixture(autouse=True)
    def _start_tendermint(self, tendermint, tendermint_port):
        """Start a Tendermint image."""
        self.tendermint_port = tendermint_port


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
    timeout: float = 2.0,
    max_attempts: int = 10,
):
    """Launch the HardHat node with Gnosis Safe contracts deployed."""
    client = docker.from_env()
    image = GnosisSafeNetDockerImage(client, hardhat_port)
    yield from launch_image(image, timeout=timeout, max_attempts=max_attempts)


@pytest.mark.integration
class UseGnosisSafeHardHatNet:
    """Inherit from this class to use HardHat local net with Gnosis-Safe deployed."""

    NB_OWNERS: int = 4
    THRESHOLD: int = 1
    SALT_NONCE: Optional[int] = None

    hardhat_port: int
    hardhat_key_pairs: List[Tuple[str, str]]
    proxy_contract_address: str

    @classmethod
    @pytest.fixture(autouse=True)
    def _start_hardhat(cls, gnosis_safe_hardhat, hardhat_port, key_pairs) -> None:
        """Start an HardHat instance."""
        cls.hardhat_port = hardhat_port
        cls.hardhat_key_pairs = key_pairs

    @classmethod
    def owners(cls) -> List[Tuple[str, str]]:
        """Get the owners."""
        return cls.hardhat_key_pairs[: cls.NB_OWNERS]

    @classmethod
    def deployer(cls) -> Tuple[str, str]:
        """Get the key pair of the deployer."""
        # for simplicity, get the first owner
        return cls.owners()[0]

    @classmethod
    def setup_class(cls) -> None:
        """
        Set up the test class.

        Deploy a new Safe contract.
        """
        cls.deploy_gnosis_safe()

    @classmethod
    def get_nonce(cls) -> int:
        """Get the nonce."""
        if cls.SALT_NONCE is not None:
            return cls.SALT_NONCE
        return secrets.SystemRandom().randint(0, 2 ** 256 - 1)

    @classmethod
    def deploy_gnosis_safe(cls) -> None:
        """
        Do the deployment of the new Safe.

        Taken from:
            https://github.com/gnosis/safe-cli/blob/contracts_v1.3.0/safe_creator.py
        """
        node_url: URI = URI(HTTP_LOCALHOST + ":" + str(cls.hardhat_port))
        public_key_deployer, private_key_deployer = cls.deployer()
        account: LocalAccount = Account.from_key(private_key_deployer)
        owners: List[str] = [pair[0] for pair in cls.owners()]
        threshold: int = cls.THRESHOLD
        salt_nonce: int = cls.get_nonce()
        to = NULL_ADDRESS
        data = b""
        payment_token = NULL_ADDRESS
        payment = 0
        payment_receiver = NULL_ADDRESS

        if len(owners) < threshold:
            pytest.fail("Threshold cannot be bigger than the number of unique owners")

        safe_contract_address = SAFE_CONTRACT
        proxy_factory_address = PROXY_FACTORY_CONTRACT
        fallback_handler = DEFAULT_CALLBACK_HANDLER
        ethereum_client = EthereumClient(node_url)

        account_balance: int = ethereum_client.get_balance(account.address)
        if not account_balance:
            pytest.fail("Client does not have any funds")
        else:
            ether_account_balance = round(
                ethereum_client.w3.fromWei(account_balance, "ether"), 6
            )
            logging.info(
                f"Network {ethereum_client.get_network().name} - Sender {account.address} - "
                f"Balance: {ether_account_balance}Ξ"
            )

        if not ethereum_client.w3.eth.getCode(
            safe_contract_address
        ) or not ethereum_client.w3.eth.getCode(proxy_factory_address):
            pytest.fail("Network not supported")

        logging.info(
            f"Creating new Safe with owners={owners} threshold={threshold} "
            f"fallback-handler={fallback_handler} salt-nonce={salt_nonce}"
        )
        safe_contract = get_safe_V1_3_0_contract(
            ethereum_client.w3, safe_contract_address
        )
        safe_creation_tx_data = HexBytes(
            safe_contract.functions.setup(
                owners,
                threshold,
                to,
                data,
                fallback_handler,
                payment_token,
                payment,
                payment_receiver,
            ).buildTransaction(  # type: ignore
                {"gas": 1, "gasPrice": 1}  # type: ignore
            )[
                "data"
            ]
        )

        proxy_factory = ProxyFactory(proxy_factory_address, ethereum_client)
        ethereum_tx_sent = proxy_factory.deploy_proxy_contract_with_nonce(
            account, safe_contract_address, safe_creation_tx_data, salt_nonce
        )
        logging.info(
            f"Tx with tx-hash={ethereum_tx_sent.tx_hash.hex()} "
            f"will create safe={ethereum_tx_sent.contract_address}"
        )
        logging.info(f"Tx parameters={ethereum_tx_sent.tx}")

        cls.proxy_contract_address = cast(str, ethereum_tx_sent.contract_address)
