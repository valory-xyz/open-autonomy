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

import os
import tempfile
from abc import abstractmethod
from pathlib import Path

import pytest
from aea.crypto.base import Crypto, LedgerApi
from aea.crypto.registries import crypto_registry, ledger_apis_registry
from aea_ledger_ethereum import EthereumCrypto

from packages.valory.contracts.gnosis_safe.contract import GnosisSafeContract

from tests.conftest import (
    ETHEREUM_KEY_DEPLOYER,
    ETHEREUM_KEY_PATH_1,
    ETHEREUM_KEY_PATH_2,
    ROOT_DIR,
)
from tests.fixture_helpers import UseGanache, UseGnosisSafeHardHatNet
from tests.helpers.contracts import get_register_contract
from tests.helpers.docker.ganache import DEFAULT_GANACHE_PORT
from tests.helpers.docker.gnosis_safe_net import DEFAULT_HARDHAT_PORT


class BaseContractTest(UseGanache):
    """Base test case for GnosisSafeContract"""

    contract: GnosisSafeContract
    ledger_api: LedgerApi
    ethereum_crypto: Crypto

    def setup(
        self,
    ):
        """Setup test."""
        directory = Path(ROOT_DIR, "packages", "valory", "contracts", "gnosis_safe")
        self.contract = get_register_contract(directory)
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


class BaseContractTestHardHatSafeNet(UseGnosisSafeHardHatNet):
    """Base test case for GnosisSafeContract"""

    contract: GnosisSafeContract
    ledger_api: LedgerApi
    ethereum_crypto: Crypto

    def setup(
        self,
    ):
        """Setup test."""
        directory = Path(ROOT_DIR, "packages", "valory", "contracts", "gnosis_safe")
        self.contract = get_register_contract(directory)
        self.ledger_api = ledger_apis_registry.make(
            EthereumCrypto.identifier,
            address=f"http://localhost:{DEFAULT_HARDHAT_PORT}",
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            output_file = Path(os.path.join(temp_dir, "key_file"))
            with open(output_file, "w") as text_file:
                text_file.write(self.hardhat_key_pairs[0][1])
            self.ethereum_crypto = crypto_registry.make(
                EthereumCrypto.identifier, private_key_path=output_file
            )

    @abstractmethod
    def test_run(
        self,
    ):
        """Run tests."""


class TestDeployTransactionGanache(BaseContractTest):
    """Test."""

    def test_run(self):
        """Run tests."""

        with pytest.raises(ValueError, match="Network not supported"):
            self.contract.get_deploy_transaction(
                ledger_api=self.ledger_api,
                deployer_address=str(self.ethereum_crypto.address),
                owners=self.owners,
                threshold=int(self.threshold),
            )
        # TOFIX: predeploy gnosis safe factory

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
                deployer_address=crypto_registry.make(
                    EthereumCrypto.identifier
                ).address,
                owners=self.owners,
                threshold=int(self.threshold),
            )


class TestDeployTransactionHardhat(BaseContractTestHardHatSafeNet):
    """Test."""

    def test_run(self):
        """Run tests."""

        result = self.contract.get_deploy_transaction(
            ledger_api=self.ledger_api,
            deployer_address=str(self.ethereum_crypto.address),
            owners=self.owners,
            threshold=int(self.threshold),
        )

        assert len(result) == 9
        data = result.pop("data")
        assert len(data) > 0 and data.startswith("0x")
        assert all(
            [
                key in result
                for key in [
                    "value",
                    "from",
                    "gas",
                    "gasPrice",
                    "chainId",
                    "nonce",
                    "to",
                    "contract_address",
                ]
            ]
        ), "Error, found: {}".format(result)


@pytest.mark.skip
class TestRawSafeTransaction(BaseContractTest):
    """Test `get_raw_safe_transaction`"""

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


@pytest.mark.skip
class TestRawSafeTransactionHash(BaseContractTest):
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
