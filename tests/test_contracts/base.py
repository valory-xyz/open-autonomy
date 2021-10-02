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

"""Base test classes."""

from pathlib import Path
from typing import Any, Dict, Optional, cast

from aea.contracts.base import Contract
from aea.crypto.base import Crypto, LedgerApi
from aea.crypto.registries import crypto_registry, ledger_apis_registry
from aea_ledger_ethereum import EthereumCrypto

from tests.conftest import ETHEREUM_KEY_DEPLOYER
from tests.fixture_helpers import GanacheBaseTest
from tests.helpers.contracts import get_register_contract
from tests.helpers.docker.ganache import DEFAULT_GANACHE_PORT


class BaseGanacheContractTest(GanacheBaseTest):
    """Base test case for testing contracts on Ganache."""

    directory: Path
    contract: Contract
    ledger_api: LedgerApi
    deployer_crypto: Crypto
    contract_address: Optional[str] = None
    deployment_kwargs: Dict[str, Any] = {}

    @classmethod
    def setup_class(
        cls,
    ):
        """Setup test."""
        super().setup_class()
        cls.contract = get_register_contract(cls.directory)
        cls.ledger_api = ledger_apis_registry.make(
            EthereumCrypto.identifier,
            address=f"http://localhost:{DEFAULT_GANACHE_PORT}",
        )
        cls.deployer_crypto = crypto_registry.make(
            EthereumCrypto.identifier, private_key_path=ETHEREUM_KEY_DEPLOYER
        )
        cls.deploy(**cls.deployment_kwargs)
        assert cls.contract_address is not None, "Contract not deployed."

    @classmethod
    def deploy(cls, **kwargs: Any):
        """Deploy the contract."""
        tx = cls.contract.get_deploy_transaction(
            ledger_api=cls.ledger_api,
            deployer_address=str(cls.deployer_crypto.address),
            **kwargs,
        )
        if tx is None:
            return None
        tx_signed = cls.deployer_crypto.sign_transaction(tx)
        tx_hash = cls.ledger_api.send_signed_transaction(tx_signed)
        if tx_hash is None:
            return None
        tx_receipt = cls.ledger_api.get_transaction_receipt(tx_hash)
        if tx_receipt is None:
            return None
        contract_address = cast(Dict, tx_receipt)["contractAddress"]
        cls.contract_address = contract_address
