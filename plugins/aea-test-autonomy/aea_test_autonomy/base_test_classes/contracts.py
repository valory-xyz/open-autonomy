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

"""Base test classes."""

import os
import time
from abc import ABC
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Dict, List, Optional, Tuple, cast

from aea.contracts.base import Contract
from aea.crypto.base import Crypto, LedgerApi
from aea.crypto.registries import crypto_registry, ledger_apis_registry
from aea_ledger_ethereum import (
    DEFAULT_CHAIN_ID,
    DEFAULT_CURRENCY_DENOM,
    DEFAULT_EIP1559_STRATEGY,
    DEFAULT_GAS_STATION_STRATEGY,
    EthereumCrypto,
)
from aea_test_autonomy.fixture_helpers import (
    GanacheBaseTest,
    HardHatAMMBaseTest,
    HardHatGnosisBaseTest,
    RegistriesBaseTest,
)
from aea_test_autonomy.helpers.contracts import get_register_contract


class BaseContractTest(ABC):
    """Base test class for contract tests."""

    contract_directory: Path
    contract: Contract
    ledger_api: LedgerApi
    identifier: str = EthereumCrypto.identifier
    deployer_crypto: Crypto
    contract_address: Optional[str] = None
    deploy_contract: bool = True

    @classmethod
    def _setup_class(cls, **kwargs: Any) -> None:
        """Setup test."""
        key_pairs: List[Tuple[str, str]] = kwargs.pop("key_pairs")
        url: str = kwargs.pop("url")
        new_config = {
            "address": url,
            "chain_id": DEFAULT_CHAIN_ID,
            "denom": DEFAULT_CURRENCY_DENOM,
            "default_gas_price_strategy": "eip1559",
            "gas_price_strategies": {
                "gas_station": DEFAULT_GAS_STATION_STRATEGY,
                "eip1559": DEFAULT_EIP1559_STRATEGY,
            },
        }
        cls.contract = get_register_contract(cls.contract_directory)
        cls.ledger_api = ledger_apis_registry.make(
            cls.identifier,
            **new_config,
        )
        with TemporaryDirectory() as temp_dir:
            output_file = Path(os.path.join(temp_dir, "key_file"))
            with open(  # pylint: disable=unspecified-encoding
                output_file, "w"
            ) as text_file:
                text_file.write(key_pairs[0][1])
            cls.deployer_crypto = crypto_registry.make(
                cls.identifier, private_key_path=output_file
            )

        if cls.deploy_contract:
            cls.deploy(**cls.deployment_kwargs())
            assert cls.contract_address is not None, "Contract not deployed."  # nosec

    @classmethod
    def deploy(cls, **kwargs: Any) -> None:
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
        time.sleep(0.5)  # give it time to mine the block
        tx_receipt = cls.ledger_api.get_transaction_receipt(tx_hash)
        if tx_receipt is None:
            return None
        contract_address = (
            cast(Dict, tx_receipt)["contractAddress"]
            if contract_address is None
            else contract_address
        )
        cls.contract_address = cast(str, contract_address)
        return None

    @classmethod
    def deployment_kwargs(cls) -> Dict[str, Any]:
        """Get deployment kwargs."""
        raise NotImplementedError


class BaseGanacheContractTest(BaseContractTest, GanacheBaseTest):
    """Base test case for testing contracts on Ganache."""


class BaseHardhatGnosisContractTest(BaseContractTest, HardHatGnosisBaseTest):
    """Base test case for testing contracts on Hardhat with Gnosis."""


class BaseHardhatAMMContractTest(BaseContractTest, HardHatAMMBaseTest):
    """Base test case for testing AMM contracts on Hardhat."""


class BaseRegistriesContractsTest(BaseContractTest, RegistriesBaseTest):
    """Base test case for the registries contract."""

    deploy_contract: bool = False


class BaseContractWithDependencyTest(BaseContractTest):
    """Base test contract with contract dependencies"""

    dependencies: List[Tuple[str, Path, Any]] = []
    dependency_info: Dict[str, Tuple[str, Contract]] = {}

    @classmethod
    def _deploy_dependencies(cls) -> None:
        """Deploy the dependencies"""

        original_contract_directory = cls.contract_directory
        original_contract = cls.contract

        for dependency in cls.dependencies:
            label, path, kwargs = dependency
            cls.contract_directory = path
            cls.contract = get_register_contract(cls.contract_directory)

            deps = kwargs.pop("deps", {})  # dependencies this contract has

            for dep_name, dep in deps.items():
                dep_address, _ = cls.dependency_info[dep]
                kwargs[dep_name] = dep_address

            cls.deploy(**kwargs)

            cls.dependency_info[label] = (str(cls.contract_address), cls.contract)

        # reset class vars to their initial state
        cls.contract_directory = original_contract_directory
        cls.contract = original_contract
        cls.contract_address = None

    @classmethod
    def _setup_class(cls, **kwargs: Any) -> None:
        """Deploy the dependencies then setups the contract"""
        key_pairs: List[Tuple[str, str]] = kwargs.pop("key_pairs")
        url: str = kwargs.pop("url")
        new_config = {
            "address": url,
            "chain_id": DEFAULT_CHAIN_ID,
            "denom": DEFAULT_CURRENCY_DENOM,
            "default_gas_price_strategy": "eip1559",
            "gas_price_strategies": {
                "gas_station": DEFAULT_GAS_STATION_STRATEGY,
                "eip1559": DEFAULT_EIP1559_STRATEGY,
            },
        }
        cls.contract = get_register_contract(cls.contract_directory)
        cls.ledger_api = ledger_apis_registry.make(
            cls.identifier,
            **new_config,
        )
        with TemporaryDirectory() as temp_dir:
            output_file = Path(os.path.join(temp_dir, "key_file"))
            with open(  # pylint: disable=unspecified-encoding
                output_file, "w"
            ) as text_file:
                text_file.write(key_pairs[0][1])
            cls.deployer_crypto = crypto_registry.make(
                cls.identifier, private_key_path=output_file
            )

        cls._deploy_dependencies()

        cls.deploy(**cls.deployment_kwargs())
        assert cls.contract_address is not None, "Contract not deployed."  # nosec


class BaseGanacheContractWithDependencyTest(
    BaseContractWithDependencyTest, GanacheBaseTest
):
    """Base test case for testing contracts with dependencies on Ganache."""


class BaseHardhatGnosisContractWithDependencyTest(
    BaseContractWithDependencyTest, HardHatGnosisBaseTest
):
    """Base test case for testing contracts with dependencies on Hardhat with Gnosis."""


class BaseHardhatAMMContractWithDependencyTest(
    BaseContractWithDependencyTest, HardHatAMMBaseTest
):
    """Base test case for testing AMM contracts with dependencies on Hardhat."""
