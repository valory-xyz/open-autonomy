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

from pathlib import Path
from typing import Any, Dict, Optional, cast

from aea.contracts.base import Contract
from aea.crypto.base import Crypto, LedgerApi
from aea.crypto.registries import crypto_registry, ledger_apis_registry
from aea_ledger_ethereum import EthereumCrypto

from packages.valory.contracts.gnosis_safe.contract import SAFE_CONTRACT
from packages.valory.contracts.gnosis_safe_proxy_factory.contract import (
    PROXY_FACTORY_CONTRACT,
)

from tests.conftest import ETHEREUM_KEY_DEPLOYER, ROOT_DIR
from tests.fixture_helpers import UseGanache
from tests.helpers.contracts import get_register_contract
from tests.helpers.docker.ganache import DEFAULT_GANACHE_PORT


class BaseContractTest(UseGanache):
    """Base test case for GnosisSafeContract"""

    directory: Path
    contract: Contract
    ledger_api: LedgerApi
    deployer_crypto: Crypto
    contract_address: Optional[str] = None

    def setup(
        self,
    ):
        """Setup test."""
        self.contract = get_register_contract(self.directory)
        self.ledger_api = ledger_apis_registry.make(
            EthereumCrypto.identifier,
            address=f"http://localhost:{DEFAULT_GANACHE_PORT}",
        )
        self.deployer_crypto = crypto_registry.make(
            EthereumCrypto.identifier, private_key_path=ETHEREUM_KEY_DEPLOYER
        )
        self.deploy()

    def deploy(self, **kwargs: Any):
        """Deploy the contract."""
        tx = self.contract.get_deploy_transaction(
            ledger_api=self.ledger_api,
            deployer_address=str(self.deployer_crypto.address),
            **kwargs,
        )
        if tx is None:
            return None
        tx_signed = self.deployer_crypto.sign_transaction(tx)
        tx_hash = self.ledger_api.send_signed_transaction(tx_signed)
        if tx_hash is None:
            return None
        tx_receipt = self.ledger_api.get_transaction_receipt(tx_hash)
        if tx_receipt is None:
            return None
        contract_address = cast(Dict, tx_receipt)["contractAddress"]
        self.contract_address = contract_address


class TestDeployTransactionGanache(BaseContractTest):
    """Test deployment of the proxy to Ganache."""

    directory = Path(
        ROOT_DIR, "packages", "valory", "contracts", "gnosis_safe_proxy_factory"
    )

    def deploy(self):
        """Deploy the contract."""
        super().deploy(
            gas=10000000,
            gasPrice=10000000,
        )

    def test_build_tx_deploy_proxy_contract_with_nonce(self):
        """Test build_tx_deploy_proxy_contract_with_nonce method."""
        assert self.contract_address is not None, "Contract not deployed."
        assert (
            self.contract_address != PROXY_FACTORY_CONTRACT
        ), "Contract addresses should differ as we don't use deterministic deployment here."
        result = self.contract.build_tx_deploy_proxy_contract_with_nonce(
            self.ledger_api,
            self.contract_address,
            SAFE_CONTRACT,
            self.deployer_crypto.address,
            b"",
            1,
            gas=1000,
            gas_price=1000,
            nonce=1,
        )
        assert len(result) == 2
        assert len(result[0]) == 8
        assert all(
            [
                key
                in [
                    "value",
                    "gas",
                    "gasPrice",
                    "chainId",
                    "from",
                    "to",
                    "data",
                    "nonce",
                ]
                for key in result[0].keys()
            ]
        )
