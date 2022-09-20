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

"""Tests for valory/uniswap_v2_router02 contract."""

from pathlib import Path
from typing import Any, Dict, Optional, cast
from unittest import mock

from aea.test_tools.test_contract import BaseContractTestCase
from aea_test_autonomy.base_test_classes.contracts import BaseHardhatAMMContractTest
from aea_test_autonomy.docker.base import skip_docker_tests

from packages.valory.contracts.uniswap_v2_router_02.contract import (
    UniswapV2Router02Contract,
)


PACKAGE_DIR = Path(__file__).parent.parent

CONTRACT_ADDRESS = "0xa6B71E26C5e0845f74c812102Ca7114b6a896AB2"
ADDRESS_ONE = "0x46F415F7BF30f4227F98def9d2B22ff62738fD68"
ADDRESS_TWO = "0x7A1236d5195e31f1F573AD618b2b6FEFC85C5Ce6"
ADDRESS_THREE = "0x7A1236d5195e31f1F573AD618b2b6FEFC85C5Ce6"
ADDRESS_FTM = "0x4E15361FD6b4BB609Fa63C81A2be19d873717870"
ADDRESS_BOO = "0x841FAD6EAe12c286d1Fd18d1d525DFfA75C7EFFE"
NONCE = 0
CHAIN_ID = 31337
DEFAULT_GAS = 1000000
DEFAULT_GAS_PRICE = 1000000


class TestUniswapV2Router02Contract(BaseContractTestCase):
    """Test TestUniswapV2Router02Contract."""

    path_to_contract = PACKAGE_DIR
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
    path = [ADDRESS_ONE, ADDRESS_TWO, ADDRESS_THREE]
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
    def _deploy_contract(cls, contract, ledger_api, deployer_crypto, gas) -> Dict:  # type: ignore
        """Deploy contract."""
        return {}

    def test_get_method_data(
        self,
    ) -> None:
        """Test get_method_data."""

        result = self.contract.get_method_data(
            self.ledger_api,
            self.contract_address,
            method_name="add_liquidity",
            tokenA=self.token_a,
            tokenB=self.token_b,
            amountADesired=self.amount_a_desired,
            amountBDesired=self.amount_b_desired,
            amountAMin=self.amount_a_min,
            amountBMin=self.amount_b_min,
            to=self.to_address,
            deadline=self.deadline,
        )

        assert result == {
            "data": b"\xe8\xe37\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
            b"\x00\x00\x00N\x156\x1f\xd6\xb4\xbb`\x9f\xa6<\x81\xa2\xbe"
            b"\x19\xd8sqxp\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
            b"\x00\x84\x1f\xadn\xae\x12\xc2\x86\xd1\xfd\x18\xd1\xd5%\xdf"
            b"\xfau\xc7\xef\xfe\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
            b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
            b"\x00\x00\x00\x00\x00\x00\x00\n\x00\x00\x00\x00\x00\x00\x00"
            b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
            b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\n\x00\x00\x00\x00"
            b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
            b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\n"
            b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
            b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
            b"\x00\x00\x00\n\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
            b"\x00\x00z\x126\xd5\x19^1\xf1\xf5s\xada\x8b+o\xef\xc8\\\\"
            b"\xe6\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
            b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
            b"\x00\x00\x00\x00\n"
        }

    def test_add_liquidity(self) -> None:
        """Test add_liquidity."""
        eth_value = 0
        gas = 100
        data = self.contract.get_instance(
            self.ledger_api, self.contract_address
        ).encodeABI(
            fn_name="addLiquidity",
            args=[
                self.token_a,
                self.token_b,
                self.amount_a_desired,
                self.amount_b_desired,
                self.amount_a_min,
                self.amount_b_min,
                self.to_address,
                self.deadline,
            ],
        )
        with mock.patch.object(
            self.ledger_api.api.eth, "get_transaction_count", return_value=NONCE
        ):
            with mock.patch.object(
                self.ledger_api.api.manager, "request_blocking", return_value=CHAIN_ID
            ):
                result = self.contract.add_liquidity(
                    self.ledger_api,
                    self.contract_address,
                    self.token_a,
                    self.token_b,
                    self.amount_a_desired,
                    self.amount_b_desired,
                    self.amount_a_min,
                    self.amount_b_min,
                    self.to_address,
                    self.deadline,
                    sender_address=self.sender_address,
                    gas=gas,
                    gasPrice=self.gas_price,
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
            args=[
                self.token,
                self.amount_token_desired,
                self.amount_token_min,
                self.amount_ETH_min,
                self.to_address,
                self.deadline,
            ],
        )
        with mock.patch.object(
            self.ledger_api.api.eth, "get_transaction_count", return_value=NONCE
        ):
            with mock.patch.object(
                self.ledger_api.api.manager, "request_blocking", return_value=CHAIN_ID
            ):
                result = self.contract.add_liquidity_ETH(
                    self.ledger_api,
                    self.contract_address,
                    self.token,
                    self.amount_token_desired,
                    self.amount_token_min,
                    self.amount_ETH_min,
                    self.to_address,
                    self.deadline,
                    sender_address=self.sender_address,
                    gas=gas,
                    gasPrice=self.gas_price,
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
            args=[
                self.token_a,
                self.token_b,
                self.liquidity,
                self.amount_a_min,
                self.amount_b_min,
                self.to_address,
                self.deadline,
            ],
        )
        with mock.patch.object(
            self.ledger_api.api.eth, "get_transaction_count", return_value=NONCE
        ):
            with mock.patch.object(
                self.ledger_api.api.manager, "request_blocking", return_value=CHAIN_ID
            ):
                result = self.contract.remove_liquidity(
                    self.ledger_api,
                    self.contract_address,
                    self.token_a,
                    self.token_b,
                    self.liquidity,
                    self.amount_a_min,
                    self.amount_b_min,
                    self.to_address,
                    self.deadline,
                    sender_address=self.sender_address,
                    gas=gas,
                    gasPrice=self.gas_price,
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
            args=[
                self.token,
                self.liquidity,
                self.amount_token_min,
                self.amount_ETH_min,
                self.to_address,
                self.deadline,
            ],
        )
        with mock.patch.object(
            self.ledger_api.api.eth, "get_transaction_count", return_value=NONCE
        ):
            with mock.patch.object(
                self.ledger_api.api.manager, "request_blocking", return_value=CHAIN_ID
            ):
                result = self.contract.remove_liquidity_ETH(
                    self.ledger_api,
                    self.contract_address,
                    self.token,
                    self.liquidity,
                    self.amount_token_min,
                    self.amount_ETH_min,
                    self.to_address,
                    self.deadline,
                    sender_address=self.sender_address,
                    gas=gas,
                    gasPrice=self.gas_price,
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
            args=[
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
            ],
        )
        with mock.patch.object(
            self.ledger_api.api.eth, "get_transaction_count", return_value=NONCE
        ):
            with mock.patch.object(
                self.ledger_api.api.manager, "request_blocking", return_value=CHAIN_ID
            ):
                result = self.contract.remove_liquidity_with_permit(
                    self.ledger_api,
                    self.contract_address,
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
                    sender_address=self.sender_address,
                    gas=gas,
                    gasPrice=self.gas_price,
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
            args=[
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
            ],
        )
        with mock.patch.object(
            self.ledger_api.api.eth, "get_transaction_count", return_value=NONCE
        ):
            with mock.patch.object(
                self.ledger_api.api.manager, "request_blocking", return_value=CHAIN_ID
            ):
                result = self.contract.remove_liquidity_ETH_with_permit(
                    self.ledger_api,
                    self.contract_address,
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
                    sender_address=self.sender_address,
                    gas=gas,
                    gasPrice=self.gas_price,
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
            args=[
                self.token,
                self.liquidity,
                self.amount_token_min,
                self.amount_ETH_min,
                self.to_address,
                self.deadline,
            ],
        )
        with mock.patch.object(
            self.ledger_api.api.eth, "get_transaction_count", return_value=NONCE
        ):
            with mock.patch.object(
                self.ledger_api.api.manager, "request_blocking", return_value=CHAIN_ID
            ):
                result = self.contract.remove_liquidity_ETH_Supporting_fee_on_transfer_tokens(
                    self.ledger_api,
                    self.contract_address,
                    self.token,
                    self.liquidity,
                    self.amount_token_min,
                    self.amount_ETH_min,
                    self.to_address,
                    self.deadline,
                    sender_address=self.sender_address,
                    gas=gas,
                    gasPrice=self.gas_price,
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
            args=[
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
            ],
        )
        with mock.patch.object(
            self.ledger_api.api.eth, "get_transaction_count", return_value=NONCE
        ):
            with mock.patch.object(
                self.ledger_api.api.manager, "request_blocking", return_value=CHAIN_ID
            ):
                result = self.contract.remove_liquidity_ETH_with_permit_supporting_fee_on_transfer_tokens(
                    self.ledger_api,
                    self.contract_address,
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
                    sender_address=self.sender_address,
                    gas=gas,
                    gasPrice=self.gas_price,
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
            args=[
                self.amount_in,
                self.amount_out_min,
                self.path,
                self.to_address,
                self.deadline,
            ],
        )
        with mock.patch.object(
            self.ledger_api.api.eth, "get_transaction_count", return_value=NONCE
        ):
            with mock.patch.object(
                self.ledger_api.api.manager, "request_blocking", return_value=CHAIN_ID
            ):
                result = self.contract.swap_exact_tokens_for_tokens(
                    self.ledger_api,
                    self.contract_address,
                    self.amount_in,
                    self.amount_out_min,
                    self.path,
                    self.to_address,
                    self.deadline,
                    sender_address=self.sender_address,
                    gas=gas,
                    gasPrice=self.gas_price,
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
            args=[
                self.amount_out,
                self.amount_in_max,
                self.path,
                self.to_address,
                self.deadline,
            ],
        )
        with mock.patch.object(
            self.ledger_api.api.eth, "get_transaction_count", return_value=NONCE
        ):
            with mock.patch.object(
                self.ledger_api.api.manager, "request_blocking", return_value=CHAIN_ID
            ):
                result = self.contract.swap_tokens_for_exact_tokens(
                    self.ledger_api,
                    self.contract_address,
                    self.amount_out,
                    self.amount_in_max,
                    self.path,
                    self.to_address,
                    self.deadline,
                    sender_address=self.sender_address,
                    gas=gas,
                    gasPrice=self.gas_price,
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
            args=[self.amount_out_min, self.path, self.to_address, self.deadline],
        )
        with mock.patch.object(
            self.ledger_api.api.eth, "get_transaction_count", return_value=NONCE
        ):
            with mock.patch.object(
                self.ledger_api.api.manager, "request_blocking", return_value=CHAIN_ID
            ):
                result = self.contract.swap_exact_ETH_for_tokens(
                    self.ledger_api,
                    self.contract_address,
                    self.amount_out_min,
                    self.path,
                    self.to_address,
                    self.deadline,
                    sender_address=self.sender_address,
                    gas=gas,
                    gasPrice=self.gas_price,
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
            args=[
                self.amount_out,
                self.amount_in_max,
                self.path,
                self.to_address,
                self.deadline,
            ],
        )
        with mock.patch.object(
            self.ledger_api.api.eth, "get_transaction_count", return_value=NONCE
        ):
            with mock.patch.object(
                self.ledger_api.api.manager, "request_blocking", return_value=CHAIN_ID
            ):
                result = self.contract.swap_tokens_for_exact_ETH(
                    self.ledger_api,
                    self.contract_address,
                    self.amount_out,
                    self.amount_in_max,
                    self.path,
                    self.to_address,
                    self.deadline,
                    sender_address=self.sender_address,
                    gas=gas,
                    gasPrice=self.gas_price,
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
            args=[
                self.amount_in,
                self.amount_out_min,
                self.path,
                self.to_address,
                self.deadline,
            ],
        )
        with mock.patch.object(
            self.ledger_api.api.eth, "get_transaction_count", return_value=NONCE
        ):
            with mock.patch.object(
                self.ledger_api.api.manager, "request_blocking", return_value=CHAIN_ID
            ):
                result = self.contract.swap_exact_tokens_for_ETH(
                    self.ledger_api,
                    self.contract_address,
                    self.amount_in,
                    self.amount_out_min,
                    self.path,
                    self.to_address,
                    self.deadline,
                    sender_address=self.sender_address,
                    gas=gas,
                    gasPrice=self.gas_price,
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
            args=[self.amount_out, self.path, self.to_address, self.deadline],
        )
        with mock.patch.object(
            self.ledger_api.api.eth, "get_transaction_count", return_value=NONCE
        ):
            with mock.patch.object(
                self.ledger_api.api.manager, "request_blocking", return_value=CHAIN_ID
            ):
                result = self.contract.swap_ETH_for_exact_tokens(
                    self.ledger_api,
                    self.contract_address,
                    self.amount_out,
                    self.path,
                    self.to_address,
                    self.deadline,
                    sender_address=self.sender_address,
                    gas=gas,
                    gasPrice=self.gas_price,
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
            args=[
                self.amount_in,
                self.amount_out_min,
                self.path,
                self.to_address,
                self.deadline,
            ],
        )
        with mock.patch.object(
            self.ledger_api.api.eth, "get_transaction_count", return_value=NONCE
        ):
            with mock.patch.object(
                self.ledger_api.api.manager, "request_blocking", return_value=CHAIN_ID
            ):
                result = self.contract.swap_exact_tokens_for_tokens_supporting_fee_on_transfer_tokens(
                    self.ledger_api,
                    self.contract_address,
                    self.amount_in,
                    self.amount_out_min,
                    self.path,
                    self.to_address,
                    self.deadline,
                    sender_address=self.sender_address,
                    gas=gas,
                    gasPrice=self.gas_price,
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
            args=[self.amount_out_min, self.path, self.to_address, self.deadline],
        )
        with mock.patch.object(
            self.ledger_api.api.eth, "get_transaction_count", return_value=NONCE
        ):
            with mock.patch.object(
                self.ledger_api.api.manager, "request_blocking", return_value=CHAIN_ID
            ):
                result = self.contract.swap_exact_ETH_for_tokens_supporting_fee_on_transfer_tokens(
                    self.ledger_api,
                    self.contract_address,
                    self.amount_out_min,
                    self.path,
                    self.to_address,
                    self.deadline,
                    sender_address=self.sender_address,
                    gas=gas,
                    gasPrice=self.gas_price,
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
            args=[
                self.amount_in,
                self.amount_out_min,
                self.path,
                self.to_address,
                self.deadline,
            ],
        )
        with mock.patch.object(
            self.ledger_api.api.eth, "get_transaction_count", return_value=NONCE
        ):
            with mock.patch.object(
                self.ledger_api.api.manager, "request_blocking", return_value=CHAIN_ID
            ):
                result = self.contract.swap_exact_tokens_for_ETH_supporting_fee_on_transfer_tokens(
                    self.ledger_api,
                    self.contract_address,
                    self.amount_in,
                    self.amount_out_min,
                    self.path,
                    self.to_address,
                    self.deadline,
                    sender_address=self.sender_address,
                    gas=gas,
                    gasPrice=self.gas_price,
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

    def test_quote(self) -> None:
        """Test quote."""
        with mock.patch.object(
            self.ledger_api.api.manager,
            "request_blocking",
            return_value="0x0000000000000000000000000000000000000000000000000000000000000000",
        ):
            result = self.contract.quote(
                self.ledger_api,
                self.contract_address,
                self.amount_a,
                self.reserve_a,
                self.reserve_b,
            )
        assert result == 0

    def test_get_amount_out(self) -> None:
        """Test get_amount_out."""
        with mock.patch.object(
            self.ledger_api.api.manager,
            "request_blocking",
            return_value="0x0000000000000000000000000000000000000000000000000000000000000000",
        ):
            result = self.contract.get_amount_out(
                self.ledger_api,
                self.contract_address,
                self.amount_in,
                self.reserve_in,
                self.reserve_out,
            )
        assert result == 0

    def test_get_amount_in(self) -> None:
        """Test get_amount_in."""
        with mock.patch.object(
            self.ledger_api.api.manager,
            "request_blocking",
            return_value="0x0000000000000000000000000000000000000000000000000000000000000000",
        ):
            result = self.contract.get_amount_in(
                self.ledger_api,
                self.contract_address,
                self.amount_out,
                self.reserve_in,
                self.reserve_out,
            )
        assert result == 0

    def test_get_amounts_out(self) -> None:
        """Test get_amounts_out."""
        with mock.patch.object(
            self.ledger_api.api.manager,
            "request_blocking",
            return_value="0x0000000000000000000000000000000000000000000000000000000000000000",
        ):
            result = self.contract.get_amounts_out(
                self.ledger_api, self.contract_address, self.amount_in, self.path
            )
        assert result == []

    def test_get_amounts_in(self) -> None:
        """Test get_amounts_in."""
        with mock.patch.object(
            self.ledger_api.api.manager,
            "request_blocking",
            return_value="0x0000000000000000000000000000000000000000000000000000000000000000",
        ):
            result = self.contract.get_amounts_in(
                self.ledger_api, self.contract_address, self.amount_out, self.path
            )
        assert result == []


class BaseContractTestHardHatAMMNet(BaseHardhatAMMContractTest):
    """Base test case for AMM contracts"""

    NB_OWNERS: int = 4
    THRESHOLD: int = 1
    SALT_NONCE: Optional[int] = None
    contract_directory = PACKAGE_DIR
    sanitize_from_deploy_tx = ["contract_address"]
    contract: UniswapV2Router02Contract

    contract_address = "0xA51c1fc2f0D1a1b8494Ed1FE312d7C3a78Ed91C0"
    weth_address = "0xDc64a140Aa3E981100a9becA4E685f962f0cF6C9"
    tokenA_address = "0x0DCd1Bf9A1b36cE34237eEaFef220932846BCD82"
    tokenB_address = "0x9A676e781A523b5d0C0e43731313A708CB607508"
    account_1_address = "0xBcd4042DE499D14e55001CcbB24a551F3b954096"
    account_2_address = "0x71bE63f3384f5fb98995898A86B02Fb2426c5788"

    @classmethod
    def deployment_kwargs(cls) -> Dict[str, Any]:
        """Get deployment kwargs."""
        return {}

    @classmethod
    def deploy(cls, **kwargs: Any) -> None:
        """Dummy method."""


@skip_docker_tests
class TestSwapHardhat(BaseContractTestHardHatAMMNet):
    """Test."""

    amount_out_min = 10
    path = [ADDRESS_FTM, ADDRESS_BOO]
    to_address = ADDRESS_ONE
    deadline = 300

    def test_swap_exact_ETH_for_tokens(self) -> None:
        """Test swap_exact_ETH_for_tokens."""
        assert self.contract_address is not None
        eth_value = 0
        gas = 100

        data = self.contract.get_method_data(
            self.ledger_api,
            self.contract_address,
            "swapExactETHForTokens",
            amount_out_min=self.amount_out_min,
            path=self.path,
            to=self.to_address,
            deadline=self.deadline,
        )
        assert data is not None
        data_ = "0x" + cast(bytes, data["data"]).hex()

        result = self.contract.swap_exact_ETH_for_tokens(
            self.ledger_api,
            self.contract_address,
            self.amount_out_min,
            self.path,
            self.to_address,
            self.deadline,
            sender_address=ADDRESS_ONE,
            gas=gas,
            gasPrice=DEFAULT_GAS_PRICE,
        )
        assert result == {
            "chainId": CHAIN_ID,
            "data": data_,
            "gas": gas,
            "gasPrice": DEFAULT_GAS_PRICE,
            "nonce": NONCE,
            "to": self.contract_address,
            "value": eth_value,
        }

    def test_quote(self) -> None:
        """Test quote."""
        assert self.contract_address is not None
        amount_a = 10 * 10
        reserve_a = 10 * 10
        reserve_b = 10 * 10
        quote = self.contract.quote(
            self.ledger_api,
            self.contract_address,
            amount_a,
            reserve_a,
            reserve_b,
        )
        assert quote is not None
