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

import os
from abc import ABC
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Dict, List, Optional, Tuple, cast

from aea.contracts.base import Contract
from aea.crypto.base import Crypto, LedgerApi
from aea.crypto.registries import crypto_registry, ledger_apis_registry
from aea_ledger_ethereum import EthereumCrypto

from tests.fixture_helpers import GanacheBaseTest, HardHatBaseTest
from tests.helpers.contracts import get_register_contract


class BaseContractTest(ABC):
    """Base test class for contract tests."""

    contract_directory: Path
    contract: Contract
    ledger_api: LedgerApi
    identifier: str = EthereumCrypto.identifier
    deployer_crypto: Crypto
    contract_address: Optional[str] = None

    @classmethod
    def _setup_class(cls, **kwargs):
        """Setup test."""
        key_pairs: List[Tuple[str, str]] = kwargs.pop("key_pairs")
        url: str = kwargs.pop("url")
        cls.contract = get_register_contract(cls.contract_directory)
        cls.ledger_api = ledger_apis_registry.make(
            cls.identifier,
            address=url,
        )
        with TemporaryDirectory() as temp_dir:
            output_file = Path(os.path.join(temp_dir, "key_file"))
            with open(output_file, "w") as text_file:
                text_file.write(key_pairs[0][1])
            cls.deployer_crypto = crypto_registry.make(
                cls.identifier, private_key_path=output_file
            )
        cls.deploy(**cls.deployment_kwargs())
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
        contract_address = tx.pop("contract_address", None)
        tx_signed = cls.deployer_crypto.sign_transaction(tx)
        tx_hash = cls.ledger_api.send_signed_transaction(tx_signed)
        if tx_hash is None:
            return None
        tx_receipt = cls.ledger_api.get_transaction_receipt(tx_hash)
        if tx_receipt is None:
            return None
        contract_address = (
            cast(Dict, tx_receipt)["contractAddress"]
            if contract_address is None
            else contract_address
        )
        cls.contract_address = cast(str, contract_address)

    @classmethod
    def deployment_kwargs(cls) -> Dict[str, Any]:
        """Get deployment kwargs."""
        raise NotImplementedError


class BaseGanacheContractTest(BaseContractTest, GanacheBaseTest):
    """Base test case for testing contracts on Ganache."""


class BaseHardhatContractTest(BaseContractTest, HardHatBaseTest):
    """Base test case for testing contracts on Ganache."""
