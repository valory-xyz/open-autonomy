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

import pytest
from aea.configurations.base import ContractConfig
from aea.crypto.base import Crypto, LedgerApi
from aea.crypto.registries import crypto_registry, ledger_apis_registry
from aea_ledger_ethereum import EthereumCrypto

from packages.valory.contracts.gnosis_safe.contract import GnosisSafeContract

from tests.conftest import (
    ETHEREUM_KEY_DEPLOYER,
    ETHEREUM_KEY_PATH_1,
    ETHEREUM_KEY_PATH_2,
)
from tests.fixture_helpers import UseGanache
from tests.helpers.docker.ganache import DEFAULT_GANACHE_PORT


class BaseContractTest(UseGanache):
    """Base test case for GnosisSafeContract"""

    contract: GnosisSafeContract
    ledger_api: LedgerApi
    ethereum_crypto: Crypto

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
            address=f"http://localhost:{DEFAULT_GANACHE_PORT}",
        )

        self.ethereum_crypto = crypto_registry.make(
            EthereumCrypto.identifier, private_key_path=ETHEREUM_KEY_DEPLOYER
        )

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

        assert len(result) == 6
        data = result.pop("data")
        assert len(data) > 0 and data.startswith("0x")
        assert all(
            [key in result for key in ["value", "from", "gas", "gasPrice", "nonce"]]
        ), "Error, found: {}".format(result)

    def test_exceptions(
        self,
    ):
        """Test exceptions."""

        with pytest.raises(ValueError):
            # Tests for `ValueError("Threshold cannot be bigger than the number of unique owners")`.`
            self.contract.get_deploy_transaction(
                ledger_api=self.ledger_api,
                deployer_address=str(self.ethereum_crypto.address),
                owners=[],
                threshold=1,
            )

        with pytest.raises(ValueError):
            # Tests for  `ValueError("Client does not have any funds")`.
            self.contract.get_deploy_transaction(
                ledger_api=self.ledger_api,
                deployer_address=crypto_registry.make(EthereumCrypto.identifier),
                owners=list(map(str, self.owners)),
                threshold=int(self.threshold),
            )


class TestRawSafeTransaction(BaseContractTest):
    """Test `get_raw_safe_transection`"""

    def test_run(self):
        """Run tests."""
        sender = crypto_registry.make(
            EthereumCrypto.identifier, private_key_path=ETHEREUM_KEY_PATH_1
        )
        receiver = crypto_registry.make(
            EthereumCrypto.identifier, private_key_path=ETHEREUM_KEY_PATH_2
        )

        self.contract.get_raw_safe_transaction(
            self.ledger_api,
            self.ethereum_crypto.address,
            sender.address,
            self.owners,
            receiver.address,
            10,
            b"",
            {},
        )


class TestRawSafeTransectionHash(BaseContractTest):
    """Test `get_raw_safe_transaction_hash` method."""

    def test_run(self):
        """Run tests."""
        receiver = crypto_registry.make(
            EthereumCrypto.identifier, private_key_path=ETHEREUM_KEY_PATH_1
        )

        self.contract.get_raw_safe_transaction_hash(
            self.ledger_api, self.ethereum_crypto.address, receiver.address, 10, b""
        )


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
