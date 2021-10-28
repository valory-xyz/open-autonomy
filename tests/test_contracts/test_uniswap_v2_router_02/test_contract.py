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

"""Tests for valory/uniswap_v2_router02 contract."""

from pathlib import Path
from typing import Dict
from unittest import mock

from aea.test_tools.test_contract import BaseContractTestCase

from packages.valory.contracts.uniswap_v2_router_02.contract import (
    UniswapV2Router02Contract,
)

from tests.conftest import ROOT_DIR


CONTRACT_ADDRESS = "0xa6B71E26C5e0845f74c812102Ca7114b6a896AB2"
ADDRESS_ONE = "0x46F415F7BF30f4227F98def9d2B22ff62738fD68"
ADDRESS_TWO = "0x7A1236d5195e31f1F573AD618b2b6FEFC85C5Ce6"
ADDRESS_THREE = "0x7A1236d5195e31f1F573AD618b2b6FEFC85C5Ce6"
ADDRESS_FTM = "0x4E15361FD6b4BB609Fa63C81A2be19d873717870"
ADDRESS_BOO = "0x841FAD6EAe12c286d1Fd18d1d525DFfA75C7EFFE"
NONCE = 0
CHAIN_ID = 1


class TestUniswapV2Router02Contract(BaseContractTestCase):
    """Test TestUniswapV2Router02Contract."""

    path_to_contract = Path(
        ROOT_DIR, "packages", "valory", "contracts", "uniswap_v2_router_02"
    )
    ledger_identifier = "ethereum"
    contract: UniswapV2Router02Contract
    sender_address = ADDRESS_TWO
    to_address = ADDRESS_THREE
    gas_price = 100
    deadline = 10

    # Add TokenA - token B
    token_a = ADDRESS_FTM
    token_b = ADDRESS_BOO
    amount_a_desired = 10
    amount_b_desired = 10
    amount_a_min = 10
    amount_b_min = 10

    # Add Token - ETH
    token = ADDRESS_FTM
    amount_token_desired = 10
    amount_token_min = 10
    amount_ETH_min = 10

    # Remove liquidity
    liquidity = 10

    # Permit
    approve_max = False
    v = 0
    r = bytes(0)
    s = bytes(0)

    # Swap
    path = []
    amount_in = 10
    amount_out_min = 10
    amount_out = 10
    amount_in_max = 10

    # Quote
    amount_a = 10
    reserve_a = 10
    reserve_b = 10

    # Get amount
    reserve_in = 10
    reserve_out = 10

    @classmethod
    def finish_contract_deployment(cls) -> str:
        """Finish the contract deployment."""
        contract_address = CONTRACT_ADDRESS
        return contract_address

    @classmethod
    def _deploy_contract(cls, contract, ledger_api, deployer_crypto, gas) -> Dict:
        return {}

    def test_add_liquidity(self) -> None:
        """Test add_liquidity."""
        eth_value = 0
        gas = 100
        data = self.contract.get_instance(
            self.ledger_api, self.contract_address
        ).encodeABI(
            fn_name="addLiquidity",
            args= [
                self.token_a,
                self.token_b,
                self.amount_a_desired,
                self.amount_b_desired,
                self.amount_a_min,
                self.amount_b_min,
                self.to_address,
                self.deadline
            ]
        )
        with mock.patch.object(
            self.ledger_api.api.eth, "getTransactionCount", return_value=NONCE
        ):
            with mock.patch.object(
                self.ledger_api.api.manager, "request_blocking", return_value=CHAIN_ID
            ):
                result = self.contract.add_liquidity(
                    self.ledger_api,
                    self.contract_address,
                    self.sender_address,
                    gas,
                    self.gas_price,
                    self.token_a,
                    self.token_b,
                    self.amount_a_desired,
                    self.amount_b_desired,
                    self.amount_a_min,
                    self.amount_b_min,
                    self.to_address,
                    self.deadline,
                )
        assert result == {
            "chainId": CHAIN_ID,
            "data": data,
            "gas": gas,
            "gasPrice": self.gas_price,
            "nonce": NONCE,
            "to": CONTRACT_ADDRESS,
            "value": eth_value,
        }

    def test_add_liquidity_ETH(self) -> None:
        """Test add_liquidity_ETH."""
        eth_value = 0
        gas = 100
        data = self.contract.get_instance(
            self.ledger_api, self.contract_address
        ).encodeABI(
            fn_name="addLiquidityETH",
            args= [
                self.token,
                self.amount_token_desired,
                self.amount_token_min,
                self.amount_ETH_min,
                self.to_address,
                self.deadline
            ]
        )
        with mock.patch.object(
            self.ledger_api.api.eth, "getTransactionCount", return_value=NONCE
        ):
            with mock.patch.object(
                self.ledger_api.api.manager, "request_blocking", return_value=CHAIN_ID
            ):
                result = self.contract.add_liquidity_ETH(
                    self.ledger_api,
                    self.contract_address,
                    self.sender_address,
                    gas,
                    self.gas_price,
                    self.token,
                    self.amount_token_desired,
                    self.amount_token_min,
                    self.amount_ETH_min,
                    self.to_address,
                    self.deadline,
                )
        assert result == {
            "chainId": CHAIN_ID,
            "data": data,
            "gas": gas,
            "gasPrice": self.gas_price,
            "nonce": NONCE,
            "to": CONTRACT_ADDRESS,
            "value": eth_value,
        }

    def test_remove_liquidity(self) -> None:
        """Test remove_liquidity."""
        eth_value = 0
        gas = 100
        data = self.contract.get_instance(
            self.ledger_api, self.contract_address
        ).encodeABI(
            fn_name="removeLiquidity",
            args= [
                self.token_a,
                self.token_b,
                self.liquidity,
                self.amount_a_min,
                self.amount_b_min,
                self.to_address,
                self.deadline
            ]
        )
        with mock.patch.object(
            self.ledger_api.api.eth, "getTransactionCount", return_value=NONCE
        ):
            with mock.patch.object(
                self.ledger_api.api.manager, "request_blocking", return_value=CHAIN_ID
            ):
                result = self.contract.remove_liquidity(
                    self.ledger_api,
                    self.contract_address,
                    self.sender_address,
                    gas,
                    self.gas_price,
                    self.token_a,
                    self.token_b,
                    self.liquidity,
                    self.amount_a_min,
                    self.amount_b_min,
                    self.to_address,
                    self.deadline,
                )
        assert result == {
            "chainId": CHAIN_ID,
            "data": data,
            "gas": gas,
            "gasPrice": self.gas_price,
            "nonce": NONCE,
            "to": CONTRACT_ADDRESS,
            "value": eth_value,
        }

    def test_remove_liquidity_ETH(self) -> None:
        """Test remove_liquidity_ETH."""
        eth_value = 0
        gas = 100
        data = self.contract.get_instance(
            self.ledger_api, self.contract_address
        ).encodeABI(
            fn_name="removeLiquidityETH",
            args= [
                self.token,
                self.liquidity,
                self.amount_token_min,
                self.amount_ETH_min,
                self.to_address,
                self.deadline
            ]
        )
        with mock.patch.object(
            self.ledger_api.api.eth, "getTransactionCount", return_value=NONCE
        ):
            with mock.patch.object(
                self.ledger_api.api.manager, "request_blocking", return_value=CHAIN_ID
            ):
                result = self.contract.remove_liquidity_ETH(
                    self.ledger_api,
                    self.contract_address,
                    self.sender_address,
                    gas,
                    self.gas_price,
                    self.token,
                    self.liquidity,
                    self.amount_token_min,
                    self.amount_ETH_min,
                    self.to_address,
                    self.deadline,
                )
        assert result == {
            "chainId": CHAIN_ID,
            "data": data,
            "gas": gas,
            "gasPrice": self.gas_price,
            "nonce": NONCE,
            "to": CONTRACT_ADDRESS,
            "value": eth_value,
        }

    def test_remove_liquidity_with_permit(self) -> None:
        """Test remove_liquidity_with_permit."""
        eth_value = 0
        gas = 100
        data = self.contract.get_instance(
            self.ledger_api, self.contract_address
        ).encodeABI(
            fn_name="removeLiquidityWithPermit",
            args= [
                self.token_a,
                self.token_b,
                self.liquidity,
                self.amount_a_min,
                self.amount_b_min,
                self.to_address,
                self.deadline,
                self.approve_max,
                self.v,
                self.r,
                self.s
            ]
        )
        with mock.patch.object(
            self.ledger_api.api.eth, "getTransactionCount", return_value=NONCE
        ):
            with mock.patch.object(
                self.ledger_api.api.manager, "request_blocking", return_value=CHAIN_ID
            ):
                result = self.contract.remove_liquidity_with_permit(
                    self.ledger_api,
                    self.contract_address,
                    self.sender_address,
                    gas,
                    self.gas_price,
                    self.token_a,
                    self.token_b,
                    self.liquidity,
                    self.amount_a_min,
                    self.amount_b_min,
                    self.to_address,
                    self.deadline,
                    self.approve_max,
                    self.v,
                    self.r,
                    self.s,
        )
        assert result == {
            "chainId": CHAIN_ID,
            "data": data,
            "gas": gas,
            "gasPrice": self.gas_price,
            "nonce": NONCE,
            "to": CONTRACT_ADDRESS,
            "value": eth_value,
        }

    def test_remove_liquidity_ETH_with_permit(self) -> None:
        """Test remove_liquidity_ETH_with_permit."""
        eth_value = 0
        gas = 100
        data = self.contract.get_instance(
            self.ledger_api, self.contract_address
        ).encodeABI(
            fn_name="removeLiquidityETHWithPermit",
            args= [
                self.token,
                self.liquidity,
                self.amount_token_min,
                self.amount_ETH_min,
                self.to_address,
                self.deadline,
                self.approve_max,
                self.v,
                self.r,
                self.s
            ]
        )
        with mock.patch.object(
            self.ledger_api.api.eth, "getTransactionCount", return_value=NONCE
        ):
            with mock.patch.object(
                self.ledger_api.api.manager, "request_blocking", return_value=CHAIN_ID
            ):
                result = self.contract.remove_liquidity_ETH_with_permit(
                    self.ledger_api,
                    self.contract_address,
                    self.sender_address,
                    gas,
                    self.gas_price,
                    self.token,
                    self.liquidity,
                    self.amount_token_min,
                    self.amount_ETH_min,
                    self.to_address,
                    self.deadline,
                    self.approve_max,
                    self.v,
                    self.r,
                    self.s,
                )
        assert result == {
            "chainId": CHAIN_ID,
            "data": data,
            "gas": gas,
            "gasPrice": self.gas_price,
            "nonce": NONCE,
            "to": CONTRACT_ADDRESS,
            "value": eth_value,
        }

    def test_remove_liquidity_ETH_Supporting_fee_on_transfer_tokens(self) -> None:
        """Test remove_liquidity_ETH_Supporting_fee_on_transfer_tokens."""
        eth_value = 0
        gas = 100
        data = self.contract.get_instance(
            self.ledger_api, self.contract_address
        ).encodeABI(
            fn_name="removeLiquidityETHSupportingFeeOnTransferTokens",
            args= [
                self.token,
                self.liquidity,
                self.amount_token_min,
                self.amount_ETH_min,
                self.to_address,
                self.deadline
            ]
        )
        with mock.patch.object(
            self.ledger_api.api.eth, "getTransactionCount", return_value=NONCE
        ):
            with mock.patch.object(
                self.ledger_api.api.manager, "request_blocking", return_value=CHAIN_ID
            ):
                result = self.contract.remove_liquidity_ETH_Supporting_fee_on_transfer_tokens(
                    self.ledger_api,
                    self.contract_address,
                    self.sender_address,
                    gas,
                    self.gas_price,
                    self.token,
                    self.liquidity,
                    self.amount_token_min,
                    self.amount_ETH_min,
                    self.to_address,
                    self.deadline,
                )
        assert result == {
            "chainId": CHAIN_ID,
            "data": data,
            "gas": gas,
            "gasPrice": self.gas_price,
            "nonce": NONCE,
            "to": CONTRACT_ADDRESS,
            "value": eth_value,
        }

    def test_remove_liquidity_ETH_with_permit_supporting_fee_on_transfer_tokens(
        self,
    ) -> None:
        """Test remove_liquidity_ETH_with_permit_supporting_fee_on_transfer_tokens."""
        eth_value = 0
        gas = 100
        data = self.contract.get_instance(
            self.ledger_api, self.contract_address
        ).encodeABI(
            fn_name="removeLiquidityETHWithPermitSupportingFeeOnTransferTokens",
            args= [
                self.token,
                self.liquidity,
                self.amount_token_min,
                self.amount_ETH_min,
                self.to_address,
                self.deadline,
                self.approve_max,
                self.v,
                self.r,
                self.s
            ]
        )
        with mock.patch.object(
            self.ledger_api.api.eth, "getTransactionCount", return_value=NONCE
        ):
            with mock.patch.object(
                self.ledger_api.api.manager, "request_blocking", return_value=CHAIN_ID
            ):
                result = self.contract.remove_liquidity_ETH_with_permit_supporting_fee_on_transfer_tokens(
                    self.ledger_api,
                    self.contract_address,
                    self.sender_address,
                    gas,
                    self.gas_price,
                    self.token,
                    self.liquidity,
                    self.amount_token_min,
                    self.amount_ETH_min,
                    self.to_address,
                    self.deadline,
                    self.approve_max,
                    self.v,
                    self.r,
                    self.s,
                )
        assert result == {
            "chainId": CHAIN_ID,
            "data": data,
            "gas": gas,
            "gasPrice": self.gas_price,
            "nonce": NONCE,
            "to": CONTRACT_ADDRESS,
            "value": eth_value,
        }

    def test_swap_exact_tokens_for_tokens(self) -> None:
        """Test swap_exact_tokens_for_tokens."""
        eth_value = 0
        gas = 100
        data = self.contract.get_instance(
            self.ledger_api, self.contract_address
        ).encodeABI(
            fn_name="swapExactTokensForTokens",
            args= [
                self.amount_in,
                self.amount_out_min,
                self.path,
                self.to_address,
                self.deadline
            ]
        )
        with mock.patch.object(
            self.ledger_api.api.eth, "getTransactionCount", return_value=NONCE
        ):
            with mock.patch.object(
                self.ledger_api.api.manager, "request_blocking", return_value=CHAIN_ID
            ):
                result = self.contract.swap_exact_tokens_for_tokens(
                    self.ledger_api,
                    self.contract_address,
                    self.sender_address,
                    gas,
                    self.gas_price,
                    self.amount_in,
                    self.amount_out_min,
                    self.path,
                    self.to_address,
                    self.deadline,
                )
        assert result == {
            "chainId": CHAIN_ID,
            "data": data,
            "gas": gas,
            "gasPrice": self.gas_price,
            "nonce": NONCE,
            "to": CONTRACT_ADDRESS,
            "value": eth_value,
        }

    def test_swap_tokens_for_exact_tokens(self) -> None:
        """Test swap_tokens_for_exact_tokens."""
        eth_value = 0
        gas = 100
        data = self.contract.get_instance(
            self.ledger_api, self.contract_address
        ).encodeABI(
            fn_name="swapTokensForExactTokens",
            args= [
                self.amount_out,
                self.amount_in_max,
                self.path,
                self.to_address,
                self.deadline
            ]
        )
        with mock.patch.object(
            self.ledger_api.api.eth, "getTransactionCount", return_value=NONCE
        ):
            with mock.patch.object(
                self.ledger_api.api.manager, "request_blocking", return_value=CHAIN_ID
            ):
                result = self.contract.swap_tokens_for_exact_tokens(
                    self.ledger_api,
                    self.contract_address,
                    self.sender_address,
                    gas,
                    self.gas_price,
                    self.amount_out,
                    self.amount_in_max,
                    self.path,
                    self.to_address,
                    self.deadline,
                )
        assert result == {
            "chainId": CHAIN_ID,
            "data": data,
            "gas": gas,
            "gasPrice": self.gas_price,
            "nonce": NONCE,
            "to": CONTRACT_ADDRESS,
            "value": eth_value,
        }

    def test_swap_exact_ETH_for_tokens(self) -> None:
        """Test swap_exact_ETH_for_tokens."""
        eth_value = 0
        gas = 100
        data = self.contract.get_instance(
            self.ledger_api, self.contract_address
        ).encodeABI(
            fn_name="swapExactETHForTokens",
            args= [
                self.amount_out_min,
                self.path,
                self.to_address,
                self.deadline
            ]
        )
        with mock.patch.object(
            self.ledger_api.api.eth, "getTransactionCount", return_value=NONCE
        ):
            with mock.patch.object(
                self.ledger_api.api.manager, "request_blocking", return_value=CHAIN_ID
            ):
                result = self.contract.swap_exact_ETH_for_tokens(
                    self.ledger_api,
                    self.contract_address,
                    self.sender_address,
                    gas,
                    self.gas_price,
                    self.amount_out_min,
                    self.path,
                    self.to_address,
                    self.deadline,
                )
        assert result == {
            "chainId": CHAIN_ID,
            "data": data,
            "gas": gas,
            "gasPrice": self.gas_price,
            "nonce": NONCE,
            "to": CONTRACT_ADDRESS,
            "value": eth_value,
        }

    def test_swap_tokens_for_exact_ETH(self) -> None:
        """Test swap_tokens_for_exact_ETH."""
        eth_value = 0
        gas = 100
        data = self.contract.get_instance(
            self.ledger_api, self.contract_address
        ).encodeABI(
            fn_name="swapTokensForExactETH",
            args= [
                self.amount_out,
                self.amount_in_max,
                self.path,
                self.to_address,
                self.deadline
            ]
        )
        with mock.patch.object(
            self.ledger_api.api.eth, "getTransactionCount", return_value=NONCE
        ):
            with mock.patch.object(
                self.ledger_api.api.manager, "request_blocking", return_value=CHAIN_ID
            ):
                result = self.contract.swap_tokens_for_exact_ETH(
                    self.ledger_api,
                    self.contract_address,
                    self.sender_address,
                    gas,
                    self.gas_price,
                    self.amount_out,
                    self.amount_in_max,
                    self.path,
                    self.to_address,
                    self.deadline,
                )
        assert result == {
            "chainId": CHAIN_ID,
            "data": data,
            "gas": gas,
            "gasPrice": self.gas_price,
            "nonce": NONCE,
            "to": CONTRACT_ADDRESS,
            "value": eth_value,
        }

    def test_swap_exact_tokens_for_ETH(self) -> None:
        """Test swap_exact_tokens_for_ETH."""
        eth_value = 0
        gas = 100
        data = self.contract.get_instance(
            self.ledger_api, self.contract_address
        ).encodeABI(
            fn_name="swapExactTokensForETH",
            args= [
                self.amount_in,
                self.amount_out_min,
                self.path,
                self.to_address,
                self.deadline
            ]
        )
        with mock.patch.object(
            self.ledger_api.api.eth, "getTransactionCount", return_value=NONCE
        ):
            with mock.patch.object(
                self.ledger_api.api.manager, "request_blocking", return_value=CHAIN_ID
            ):
                result = self.contract.swap_exact_tokens_for_ETH(
                    self.ledger_api,
                    self.contract_address,
                    self.sender_address,
                    gas,
                    self.gas_price,
                    self.amount_in,
                    self.amount_out_min,
                    self.path,
                    self.to_address,
                    self.deadline,
                )
        assert result == {
            "chainId": CHAIN_ID,
            "data": data,
            "gas": gas,
            "gasPrice": self.gas_price,
            "nonce": NONCE,
            "to": CONTRACT_ADDRESS,
            "value": eth_value,
        }

    def test_swap_ETH_for_exact_tokens(self) -> None:
        """Test swap_ETH_for_exact_tokens."""
        eth_value = 0
        gas = 100
        data = self.contract.get_instance(
            self.ledger_api, self.contract_address
        ).encodeABI(
            fn_name="swapETHForExactTokens",
            args= [
                self.amount_out,
                self.path,
                self.to_address,
                self.deadline
            ]
        )
        with mock.patch.object(
            self.ledger_api.api.eth, "getTransactionCount", return_value=NONCE
        ):
            with mock.patch.object(
                self.ledger_api.api.manager, "request_blocking", return_value=CHAIN_ID
            ):
                result = self.contract.swap_ETH_for_exact_tokens(
                    self.ledger_api,
                    self.contract_address,
                    self.sender_address,
                    gas,
                    self.gas_price,
                    self.amount_out,
                    self.path,
                    self.to_address,
                    self.deadline,
                )
        assert result == {
            "chainId": CHAIN_ID,
            "data": data,
            "gas": gas,
            "gasPrice": self.gas_price,
            "nonce": NONCE,
            "to": CONTRACT_ADDRESS,
            "value": eth_value,
        }

    def test_swap_exact_tokens_for_tokens_supporting_fee_on_transfer_tokens(
        self,
    ) -> None:
        """Test swap_exact_tokens_for_tokens_supporting_fee_on_transfer_tokens."""
        eth_value = 0
        gas = 100
        data = self.contract.get_instance(
            self.ledger_api, self.contract_address
        ).encodeABI(
            fn_name="swapExactTokensForTokensSupportingFeeOnTransferTokens",
            args= [
                self.amount_in,
                self.amount_out_min,
                self.path,
                self.to_address,
                self.deadline
            ]
        )
        with mock.patch.object(
            self.ledger_api.api.eth, "getTransactionCount", return_value=NONCE
        ):
            with mock.patch.object(
                self.ledger_api.api.manager, "request_blocking", return_value=CHAIN_ID
            ):
                result = self.contract.swap_exact_tokens_for_tokens_supporting_fee_on_transfer_tokens(
                    self.ledger_api,
                    self.contract_address,
                    self.sender_address,
                    gas,
                    self.gas_price,
                    self.amount_in,
                    self.amount_out_min,
                    self.path,
                    self.to_address,
                    self.deadline,
                )
        assert result == {
            "chainId": CHAIN_ID,
            "data": data,
            "gas": gas,
            "gasPrice": self.gas_price,
            "nonce": NONCE,
            "to": CONTRACT_ADDRESS,
            "value": eth_value,
        }

    def test_swap_exact_ETH_for_tokens_supporting_fee_on_transfer_tokens(self) -> None:
        """Test swap_exact_ETH_for_tokens_supporting_fee_on_transfer_tokens."""
        eth_value = 0
        gas = 100
        data = self.contract.get_instance(
            self.ledger_api, self.contract_address
        ).encodeABI(
            fn_name="swapExactETHForTokensSupportingFeeOnTransferTokens",
            args= [
                self.amount_out_min,
                self.path,
                self.to_address,
                self.deadline
            ]
        )
        with mock.patch.object(
            self.ledger_api.api.eth, "getTransactionCount", return_value=NONCE
        ):
            with mock.patch.object(
                self.ledger_api.api.manager, "request_blocking", return_value=CHAIN_ID
            ):
                result = self.contract.swap_exact_ETH_for_tokens_supporting_fee_on_transfer_tokens(
                    self.ledger_api,
                    self.contract_address,
                    self.sender_address,
                    gas,
                    self.gas_price,
                    self.amount_out_min,
                    self.path,
                    self.to_address,
                    self.deadline
                )
        assert result == {
            "chainId": CHAIN_ID,
            "data": data,
            "gas": gas,
            "gasPrice": self.gas_price,
            "nonce": NONCE,
            "to": CONTRACT_ADDRESS,
            "value": eth_value,
        }

    def test_swap_exact_tokens_for_ETH_supporting_fee_on_transfer_tokens(self) -> None:
        """Test swap_exact_tokens_for_ETH_supporting_fee_on_transfer_tokens."""
        eth_value = 0
        gas = 100
        data = self.contract.get_instance(
            self.ledger_api, self.contract_address
        ).encodeABI(
            fn_name="swapExactTokensForETHSupportingFeeOnTransferTokens",
            args= [
                    self.amount_in,
                    self.amount_out_min,
                    self.path,
                    self.to_address,
                    self.deadline
            ]
        )
        with mock.patch.object(
            self.ledger_api.api.eth, "getTransactionCount", return_value=NONCE
        ):
            with mock.patch.object(
                self.ledger_api.api.manager, "request_blocking", return_value=CHAIN_ID
            ):
                result = self.contract.swap_exact_tokens_for_ETH_supporting_fee_on_transfer_tokens(
                    self.ledger_api,
                    self.contract_address,
                    self.sender_address,
                    gas,
                    self.gas_price,
                    self.amount_in,
                    self.amount_out_min,
                    self.path,
                    self.to_address,
                    self.deadline
                )
        assert result == {
            "chainId": CHAIN_ID,
            "data": data,
            "gas": gas,
            "gasPrice": self.gas_price,
            "nonce": NONCE,
            "to": CONTRACT_ADDRESS,
            "value": eth_value
        }

    def test_quote(self) -> None:
        """Test quote."""
        eth_value = 0
        gas = 100
        data = self.contract.get_instance(
            self.ledger_api, self.contract_address
        ).encodeABI(
            fn_name="quote",
            args= [
                self.amount_a,
                self.reserve_a,
                self.reserve_b
            ]
        )
        with mock.patch.object(
            self.ledger_api.api.eth, "getTransactionCount", return_value=NONCE
        ):
            with mock.patch.object(
                self.ledger_api.api.manager, "request_blocking", return_value=CHAIN_ID
            ):
                result = self.contract.quote(
                    self.ledger_api,
                    self.contract_address,
                    self.amount_a,
                    self.reserve_a,
                    self.reserve_b
                )
        assert result == {
            "chainId": CHAIN_ID,
            "data": data,
            "gas": gas,
            "gasPrice": self.gas_price,
            "nonce": NONCE,
            "to": CONTRACT_ADDRESS,
            "value": eth_value
        }

    def test_get_amount_out(self) -> None:
        """Test get_amount_out."""
        eth_value = 0
        gas = 100
        data = self.contract.get_instance(
            self.ledger_api, self.contract_address
        ).encodeABI(
            fn_name="getAmountOut",
            args= [
                self.amount_in,
                self.reserve_in,
                self.reserve_out
            ]
        )
        with mock.patch.object(
            self.ledger_api.api.eth, "getTransactionCount", return_value=NONCE
        ):
            with mock.patch.object(
                self.ledger_api.api.manager, "request_blocking", return_value=CHAIN_ID
            ):
                result = self.contract.get_amount_out(
                    self.ledger_api,
                    self.contract_address,
                    self.amount_in,
                    self.reserve_in,
                    self.reserve_out
                )
        assert result == {
            "chainId": CHAIN_ID,
            "data": data,
            "gas": gas,
            "gasPrice": self.gas_price,
            "nonce": NONCE,
            "to": CONTRACT_ADDRESS,
            "value": eth_value
        }

    def test_get_amount_in(self) -> None:
        """Test get_amount_in."""
        eth_value = 0
        gas = 100
        data = self.contract.get_instance(
            self.ledger_api, self.contract_address
        ).encodeABI(
            fn_name="getAmountIn",
            args= [
                self.amount_out,
                self.reserve_in,
                self.reserve_out
            ]
        )
        with mock.patch.object(
            self.ledger_api.api.eth, "getTransactionCount", return_value=NONCE
        ):
            with mock.patch.object(
                self.ledger_api.api.manager, "request_blocking", return_value=CHAIN_ID
            ):
                result = self.contract.get_amount_in(
                    self.ledger_api,
                    self.contract_address,
                    self.amount_out,
                    self.reserve_in,
                    self.reserve_out
                )
        assert result == {
            "chainId": CHAIN_ID,
            "data": data,
            "gas": gas,
            "gasPrice": self.gas_price,
            "nonce": NONCE,
            "to": CONTRACT_ADDRESS,
            "value": eth_value
        }

    def test_get_amounts_out(self) -> None:
        """Test get_amounts_out."""
        eth_value = 0
        gas = 100
        data = self.contract.get_instance(
            self.ledger_api, self.contract_address
        ).encodeABI(
            fn_name="getAmountsOut",
            args= [self.amount_in, self.path]
        )
        with mock.patch.object(
            self.ledger_api.api.eth, "getTransactionCount", return_value=NONCE
        ):
            with mock.patch.object(
                self.ledger_api.api.manager, "request_blocking", return_value=CHAIN_ID
            ):
                result = self.contract.get_amounts_out(
                    self.ledger_api, self.contract_address, self.amount_in, self.path
                )
        assert result == {
            "chainId": CHAIN_ID,
            "data": data,
            "gas": gas,
            "gasPrice": self.gas_price,
            "nonce": NONCE,
            "to": CONTRACT_ADDRESS,
            "value": eth_value
        }

    def test_get_amounts_in(self) -> None:
        """Test get_amounts_in."""
        eth_value = 0
        gas = 100
        data = self.contract.get_instance(
            self.ledger_api, self.contract_address
        ).encodeABI(
            fn_name="getAmountsIn",
            args= [self.amount_out, self.path]
        )
        with mock.patch.object(
            self.ledger_api.api.eth, "getTransactionCount", return_value=NONCE
        ):
            with mock.patch.object(
                self.ledger_api.api.manager, "request_blocking", return_value=CHAIN_ID
            ):
                result = self.contract.get_amounts_in(
                    self.ledger_api, self.contract_address, self.amount_out, self.path
                )
        assert result == {
            "chainId": CHAIN_ID,
            "data": data,
            "gas": gas,
            "gasPrice": self.gas_price,
            "nonce": NONCE,
            "to": CONTRACT_ADDRESS,
            "value": eth_value
        }
