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

"""Tests for valory/gnosis contract."""

from abc import abstractmethod
from typing import List, Tuple

import pytest
from aea.configurations.base import ContractConfig
from aea.crypto.base import Crypto, LedgerApi
from aea.crypto.registries import crypto_registry, ledger_apis_registry
from aea_ledger_ethereum import EthereumCrypto
from eth_account.account import Account
from eth_keys import keys
from web3 import Web3

from packages.valory.contracts.gnosis_safe.contract import GnosisSafeContract

from tests.fixture_helpers import UseGanache, UseGnosisSafeHardHatNet
from tests.helpers.constants import KEY_PAIRS
from tests.helpers.docker.gnosis_safe_net import DEFAULT_HARDHAT_PORT


class BaseContractTest(UseGnosisSafeHardHatNet):
    """Base test case for GnosisSafeContract"""

    contract: GnosisSafeContract
    ledger_api: LedgerApi
    receiver: Crypto

    owners: Tuple[Tuple[str, str]]
    threshold: int

    def setup(
        self,
    ):
        """Setup test."""
        self.contract = GnosisSafeContract(
            ContractConfig(
                "gnosis_safe",
                "valory",
                "0.1.0",
                "Apache-2.0",
                ">=1.0.0, <2.0.0",
                "",
                [],
            )
        )
        self.ledger_api = ledger_apis_registry.make(
            EthereumCrypto.identifier,
            address=f"http://localhost:{DEFAULT_HARDHAT_PORT}",
        )

        self.owners = [key for _, key in KEY_PAIRS[:4]]
        self.threshold = 1
        self.ethereum_crypto = self.generate_account(KEY_PAIRS[0][1])

    def generate_account(self, key: str) -> EthereumCrypto:
        crypto = crypto_registry.make(EthereumCrypto.identifier)
        crypto._entity = Account.from_key(private_key=key)
        bytes_representation = Web3.toBytes(hexstr=crypto.entity.key.hex())
        crypto._public_key = str(keys.PrivateKey(bytes_representation).public_key)
        crypto._address = str(crypto.entity.address)
        return crypto

    @abstractmethod
    def test_run(
        self,
    ):
        """Run tests."""


class TestDeployTransection(BaseContractTest):
    """Test `get_deploy_transection` method."""

    def test_run(self):
        """Run tests."""

        result = self.contract.get_deploy_transaction(
            ledger_api=self.ledger_api,
            deployer_address=str(self.ethereum_crypto.address),
            owners=list(map(str, self.owners)),
            threshold=int(self.threshold),
        )
        print(result)


class TestRawSafeTransectionHash(BaseContractTest):
    """Test `get_raw_safe_transaction_hash` method."""

    def test_run(self):
        """Run tests."""


class TestRawSafeTransaction(BaseContractTest):
    """Test `get_raw_safe_transection`"""

    def test_run(self):
        """Run tests."""


class TestNoneImplementedMethods(BaseContractTest):
    """Test methods which are yet to implement."""

    def test_run(
        self,
    ):
        """Run tests."""

        with pytest.raises(NotImplementedError):
            self.contract.get_raw_transaction(None, None)

        with pytest.raises(NotImplementedError):
            self.contract.get_raw_message(None, None)

        with pytest.raises(NotImplementedError):
            self.contract.get_state(None, None)
