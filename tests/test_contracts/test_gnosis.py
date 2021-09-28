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

from tests.fixture_helpers import UseGnosisSafeHardHatNet
from tests.helpers.docker.gnosis_safe_net import DEFAULT_HARDHAT_PORT


class BaseContractTest(UseGnosisSafeHardHatNet):
    """Base test case for GnosisSafeContract"""

    contract: GnosisSafeContract
    ledger_api: LedgerApi
    aea_ledger_ethereum: Crypto

    def setup(self, ):
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
            EthereumCrypto.identifier, address=f"http://localhost:{self.hardhat_port}"
        )
        self.aea_ledger_ethereum = crypto_registry.make(EthereumCrypto.identifier)

    @abstractmethod
    def test_run(
        self,
    ):
        """Run tests."""


class TestNoneImplementedMethods(BaseContractTest):
    """Test methods which are yet to implement."""

    def test_run(
        self,
    ):
        """Run tests."""

        with pytest.raises(NotImplementedError):
            self.contract.get_raw_message(None, None)

        with pytest.raises(NotImplementedError):
            self.contract.get_raw_message(None, None)

        with pytest.raises(NotImplementedError):
            self.contract.get_state(None, None)


class TestDeployTransection(BaseContractTest):
    """Test `get_deploy_transection` method."""

    def test_run(self):
        """Run tests."""


class TestRawSafeTransectionHash(BaseContractTest):
    """Test `get_raw_safe_transaction_hash` method."""

    def test_run(self):
        """Run tests."""


class TestRawSafeTransaction(BaseContractTest):
    """Test `get_raw_safe_transection`"""

    def test_run(self):
        """Run tests."""


if __name__ == "__main__":
    test = TestDeployTransection()
    test.setup()
    test.test_run()
