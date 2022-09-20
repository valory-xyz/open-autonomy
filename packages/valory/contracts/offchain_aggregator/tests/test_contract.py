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

"""Tests for valory/offchain_aggregator contract."""

import time
from pathlib import Path
from typing import Any, Dict, List, Tuple, cast

import pytest
from aea.crypto.registries import crypto_registry
from aea_ledger_ethereum import EthereumCrypto
from aea_test_autonomy.base_test_classes.contracts import BaseGanacheContractTest
from aea_test_autonomy.configurations import ETHEREUM_KEY_PATH_1
from aea_test_autonomy.docker.base import skip_docker_tests
from web3 import Web3

from packages.valory.contracts.offchain_aggregator.contract import (
    OffchainAggregatorContract,
)


PACKAGE_DIR = Path(__file__).parent.parent


class BaseContractTest(BaseGanacheContractTest):
    """Base test case for OffchainAggregatorContract"""

    MIN_ANSWER: int = 10 ** 18
    MAX_ANSWER: int = 10 ** 24
    DECIMALS: int = 18
    DESCRIPTION: str = "BTC"
    NB_TRANSMITTERS: int = 1
    GAS: int = 10 ** 10
    DEFAULT_MAX_FEE_PER_GAS: int = 10 ** 10
    DEFAULT_MAX_PRIORITY_FEE_PER_GAS: int = 10 ** 10
    contract_directory = PACKAGE_DIR
    contract: OffchainAggregatorContract

    @classmethod
    def deployment_kwargs(cls) -> Dict[str, Any]:
        """Get deployment kwargs."""
        return dict(
            _minAnswer=cls.MIN_ANSWER,
            _maxAnswer=cls.MAX_ANSWER,
            _decimals=cls.DECIMALS,
            _description=cls.DESCRIPTION,
            _transmitters=cls.transmitters(),
            gas=cls.GAS,
        )

    @classmethod
    def transmitters(cls) -> List[str]:
        """Get the owners."""
        return [
            Web3.toChecksumAddress(t[0])
            for t in cls.key_pairs()[1 : cls.NB_TRANSMITTERS + 1]
        ]

    @classmethod
    def deployer(cls) -> Tuple[str, str]:
        """Get the key pair of the deployer."""
        # for simplicity, get the first owner
        return cls.key_pairs()[0]


@skip_docker_tests
class TestDeployTransaction(BaseContractTest):
    """Test."""

    def test_deployed(self) -> None:
        """Run tests."""
        result = self.contract.get_deploy_transaction(
            ledger_api=self.ledger_api,
            deployer_address=str(self.deployer_crypto.address),
            **self.deployment_kwargs()
        )
        assert isinstance(result, dict)
        assert len(result) == 8
        data = result.pop("data")
        assert isinstance(data, str)
        assert len(data) > 0 and data.startswith("0x")
        assert all(
            [
                key in result
                for key in [
                    "value",
                    "from",
                    "gas",
                    "maxFeePerGas",
                    "maxPriorityFeePerGas",
                    "nonce",
                ]
            ]
        ), "Error, found: {}".format(result)

    def test_non_implemented_methods(
        self,
    ) -> None:
        """Test not implemented methods."""
        with pytest.raises(NotImplementedError):
            self.contract.get_raw_transaction(self.ledger_api, "")

        with pytest.raises(NotImplementedError):
            self.contract.get_raw_message(self.ledger_api, "")

        with pytest.raises(NotImplementedError):
            self.contract.get_state(self.ledger_api, "")

    def test_get_transmit_data(self) -> None:
        """Run test_get_transmit_data test."""
        assert self.contract_address is not None
        result = self.contract.get_transmit_data(
            ledger_api=self.ledger_api,
            contract_address=self.contract_address,
            epoch_=1,
            round_=1,
            amount_=10 ** 19,
        )
        assert result["data"], "Contract did not return data."

    def test_get_latest_transmission_details(self) -> None:
        """Run get_latest_transmission_details test."""
        assert self.contract_address is not None
        result = self.contract.get_latest_transmission_details(
            ledger_api=self.ledger_api,
            contract_address=self.contract_address,
        )
        assert all(key in ["epoch_", "round_"] for key in result.keys())

    def test_verify(self) -> None:
        """Run verify test."""
        assert self.contract_address is not None
        result = self.contract.verify_contract(
            ledger_api=self.ledger_api,
            contract_address=self.contract_address,
        )
        assert result["verified"], "Contract not verified."

    def test_transmit_and_get_latest_round_data(self) -> None:
        """Run transmit test."""
        assert self.contract_address is not None
        epoch_ = 1
        round_ = 2
        amount_ = 10 ** 19
        result = self.contract.transmit(
            ledger_api=self.ledger_api,
            contract_address=self.contract_address,
            epoch_=epoch_,
            round_=round_,
            amount_=amount_,
            sender_address=self.transmitters()[0],
            gas=self.GAS,
        )
        assert result is not None, "Tx generation failed"
        assert len(result) == 8
        sender = crypto_registry.make(
            EthereumCrypto.identifier, private_key_path=ETHEREUM_KEY_PATH_1
        )
        assert sender.address == self.transmitters()[0]
        tx_signed = sender.sign_transaction(result)
        tx_hash = self.ledger_api.send_signed_transaction(tx_signed)
        assert tx_hash is not None, "Tx hash is none"
        time.sleep(1)
        tx_receipt = self.ledger_api.get_transaction_receipt(tx_hash)
        assert tx_receipt is not None, "Tx receipt is none"
        result_ = cast(
            List,
            self.contract.latest_round_data(
                ledger_api=self.ledger_api,
                contract_address=self.contract_address,
            ),
        )
        assert isinstance(result_, list), "Call failed"
        assert result_[0] == epoch_
        assert result_[1] == amount_
        assert result_[4] == epoch_
