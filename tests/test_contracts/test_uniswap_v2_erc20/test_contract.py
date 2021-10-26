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

"""Tests for valory/uniswap_v2_erc20 contract."""

from pathlib import Path
from typing import Dict
from unittest import mock

from aea.common import JSONLike
from aea.test_tools.test_contract import BaseContractTestCase

from packages.valory.contracts.uniswap_v2_erc20.contract import UniswapV2ERC20Contract

from tests.conftest import ROOT_DIR


CONTRACT_ADDRESS = "0xa6B71E26C5e0845f74c812102Ca7114b6a896AB2"
ADDRESS_ONE = "0x46F415F7BF30f4227F98def9d2B22ff62738fD68"
ADDRESS_TWO = "0x7A1236d5195e31f1F573AD618b2b6FEFC85C5Ce6"
ADDRESS_THREE = "0x7A1236d5195e31f1F573AD618b2b6FEFC85C5Ce6"
NONCE = 0
CHAIN_ID = 1


class TestUniswapV2ERC20Contract(BaseContractTestCase):
    """Test TestUniswapV2ERC20Contract."""

    path_to_contract = Path(
        ROOT_DIR, "packages", "valory", "contracts", "uniswap_v2_erc20"
    )
    ledger_identifier = "ethereum"
    contract: UniswapV2ERC20Contract
    owner_address = ADDRESS_ONE
    sender_address = ADDRESS_TWO
    gas_price = 100

    @classmethod
    def finish_contract_deployment(cls) -> str:
        """Finish the contract deployment."""
        contract_address = CONTRACT_ADDRESS
        return contract_address

    @classmethod
    def _deploy_contract(cls, contract, ledger_api, deployer_crypto, gas) -> Dict:
        return {}

    def test_aprove(self) -> None:
        """Test approve."""
        eth_value = 0
        gas = 100
        spender_address = ADDRESS_THREE
        approval_value = 100
        with mock.patch.object(
            self.ledger_api.api.eth, "getTransactionCount", return_value=NONCE
        ):
            with mock.patch.object(
                self.ledger_api.api.manager, "request_blocking", return_value=CHAIN_ID
            ):
                result = self.contract.approve(
                    self.ledger_api,
                    self.contract_address,
                    self.sender_address,
                    gas,
                    self.gas_price,
                    spender_address,
                    approval_value,
                )
        assert result == {
            "chainId": CHAIN_ID,
            "data": "0x095ea7b30000000000000000000000007a1236d5195e31f1f573ad618b2b6fefc85c5ce60000000000000000000000000000000000000000000000000000000000000064",
            "gas": gas,
            "gasPrice": self.gas_price,
            "nonce": NONCE,
            "to": CONTRACT_ADDRESS,
            "value": eth_value,
        }

    def test_transfer(self) -> None:
        """Test transfer."""
        gas = 100
        spender_address = "0x1"
        value = 100
        result = self.contract.transfer(
            self.ledger_api,
            self.contract_address,
            self.sender_address,
            gas,
            self.gas_price,
            spender_address,
            value,
        )
        assert type(result) == JSONLike

    def test_transfer_from(self) -> None:
        """Test transfer_from."""
        gas = 100
        from_address = "0x1"
        to_address = "0x2"
        value = 100
        result = self.contract.transfer_from(
            self.ledger_api,
            self.contract_address,
            self.sender_address,
            gas,
            self.gas_price,
            from_address,
            to_address,
            value,
        )
        assert type(result) == JSONLike

    def test_permit(self) -> None:
        """Test permit."""
        gas = 100
        owner_address = "0x1"
        spender_address = "0x2"
        value = 100
        deadline = 10
        v = 10
        r = b""
        s = b""
        result = self.contract.permit(
            self.ledger_api,
            self.contract_address,
            self.sender_address,
            gas,
            self.gas_price,
            owner_address,
            spender_address,
            value,
            deadline,
            v,
            r,
            s,
        )
        assert type(result) == JSONLike

    def test_allowance(self) -> None:
        """Test allowance."""
        owner_address = "0x1"
        spender_address = "0x2"
        result = self.contract.allowance(
            self.ledger_api,
            self.contract_address,
            owner_address,
            spender_address,
        )
        assert type(result) == JSONLike

    def test_balance_of(self) -> None:
        """Test balance_of."""
        owner_address = "0x1"
        result = self.contract.balance_of(
            self.ledger_api, self.contract_address, owner_address
        )
        assert type(result) == JSONLike
