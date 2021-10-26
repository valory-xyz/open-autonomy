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

from aea.common import JSONLike
from aea.test_tools.test_contract import BaseContractTestCase

from packages.valory.contracts.uniswap_v2_router_02.contract import (
    UniswapV2Router02Contract,
)

from tests.conftest import ROOT_DIR


class TestUniswapV2Router02Contract(BaseContractTestCase):
    """Test TestUniswapV2Router02Contract."""

    contract_directory = Path(
        ROOT_DIR, "packages", "valory", "contracts", "gnosis_safe_proxy_factory"
    )
    contract: UniswapV2Router02Contract
    owner_address = ""
    to_address = ""
    deadline = 10

    # Add TokenA - token B
    token_a = ""
    token_b = ""
    amount_a_desired = 10
    amount_b_desired = 10
    amount_a_min = 10
    amount_b_min = 10

    # Add Token - ETH
    token = ""
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

    def test_add_liquidity(self) -> None:
        """Test add_liquidity."""
        result = self.contract.add_liquidity(
            self.ledger_api,
            self.contract_address,
            self.owner_address,
            self.token_a,
            self.token_b,
            self.amount_a_desired,
            self.amount_b_desired,
            self.amount_a_min,
            self.amount_b_min,
            self.to_address,
            self.deadline,
        )
        assert type(result) == JSONLike

    def test_add_liquidity_ETH(self) -> None:
        """Test add_liquidity_ETH."""
        result = self.contract.add_liquidity_ETH(
            self.ledger_api,
            self.contract_address,
            self.owner_address,
            self.token,
            self.amount_token_desired,
            self.amount_token_min,
            self.amount_ETH_min,
            self.to_address,
            self.deadline,
        )
        assert type(result) == JSONLike

    def test_remove_liquidity(self) -> None:
        """Test remove_liquidity."""
        result = self.contract.remove_liquidity(
            self.ledger_api,
            self.contract_address,
            self.owner_address,
            self.token_a,
            self.token_b,
            self.liquidity,
            self.amount_a_min,
            self.amount_b_min,
            self.to_address,
            self.deadline,
        )
        assert type(result) == JSONLike

    def test_remove_liquidity_ETH(self) -> None:
        """Test remove_liquidity_ETH."""
        result = self.contract.remove_liquidity_ETH(
            self.ledger_api,
            self.contract_address,
            self.owner_address,
            self.token,
            self.liquidity,
            self.amount_token_min,
            self.amount_ETH_min,
            self.to_address,
            self.deadline,
        )
        assert type(result) == JSONLike

    def test_remove_liquidity_with_permit(self) -> None:
        """Test remove_liquidity_with_permit."""
        result = self.contract.remove_liquidity_with_permit(
            self.ledger_api,
            self.contract_address,
            self.owner_address,
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
        assert type(result) == JSONLike

    def test_remove_liquidity_ETH_with_permit(self) -> None:
        """Test remove_liquidity_ETH_with_permit."""
        result = self.contract.remove_liquidity_ETH_with_permit(
            self.ledger_api,
            self.contract_address,
            self.owner_address,
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
        assert type(result) == JSONLike

    def test_remove_liquidity_ETH_Supporting_fee_on_transfer_tokens(self) -> None:
        """Test remove_liquidity_ETH_Supporting_fee_on_transfer_tokens."""
        result = self.contract.remove_liquidity_ETH_Supporting_fee_on_transfer_tokens(
            self.ledger_api,
            self.contract_address,
            self.owner_address,
            self.token,
            self.liquidity,
            self.amount_token_min,
            self.amount_ETH_min,
            self.to_address,
            self.deadline,
        )
        assert type(result) == JSONLike

    def test_remove_liquidity_ETH_with_permit_supporting_fee_on_transfer_tokens(
        self,
    ) -> None:
        """Test remove_liquidity_ETH_with_permit_supporting_fee_on_transfer_tokens."""
        result = self.contract.remove_liquidity_ETH_with_permit_supporting_fee_on_transfer_tokens(
            self.ledger_api,
            self.contract_address,
            self.owner_address,
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
        assert type(result) == JSONLike

    def test_swap_exact_tokens_for_tokens(self) -> None:
        """Test swap_exact_tokens_for_tokens."""
        result = self.contract.swap_exact_tokens_for_tokens(
            self.ledger_api,
            self.contract_address,
            self.owner_address,
            self.amount_in,
            self.amount_out_min,
            self.path,
            self.to_address,
            self.deadline,
        )
        assert type(result) == JSONLike

    def test_swap_tokens_for_exact_tokens(self) -> None:
        """Test swap_tokens_for_exact_tokens."""
        result = self.contract.swap_tokens_for_exact_tokens(
            self.ledger_api,
            self.contract_address,
            self.owner_address,
            self.amount_out,
            self.amount_in_max,
            self.path,
            self.to_address,
            self.deadline,
        )
        assert type(result) == JSONLike

    def test_swap_exact_ETH_for_tokens(self) -> None:
        """Test swap_exact_ETH_for_tokens."""
        result = self.contract.swap_exact_ETH_for_tokens(
            self.ledger_api,
            self.contract_address,
            self.owner_address,
            self.amount_out_min,
            self.path,
            self.to_address,
            self.deadline,
        )
        assert type(result) == JSONLike

    def test_swap_tokens_for_exact_ETH(self) -> None:
        """Test swap_tokens_for_exact_ETH."""
        result = self.contract.swap_tokens_for_exact_ETH(
            self.ledger_api,
            self.contract_address,
            self.owner_address,
            self.amount_out,
            self.amount_in_max,
            self.path,
            self.to_address,
            self.deadline,
        )
        assert type(result) == JSONLike

    def test_swap_exact_tokens_for_ETH(self) -> None:
        """Test swap_exact_tokens_for_ETH."""
        result = self.contract.swap_exact_tokens_for_ETH(
            self.ledger_api,
            self.contract_address,
            self.owner_address,
            self.amount_in,
            self.amount_out_min,
            self.path,
            self.to_address,
            self.deadline,
        )
        assert type(result) == JSONLike

    def test_swap_ETH_for_exact_tokens(self) -> None:
        """Test swap_ETH_for_exact_tokens."""
        result = self.contract.swap_ETH_for_exact_tokens(
            self.ledger_api,
            self.contract_address,
            self.owner_address,
            self.amount_out,
            self.path,
            self.to_address,
            self.deadline,
        )
        assert type(result) == JSONLike

    def test_swap_exact_tokens_for_tokens_supporting_fee_on_transfer_tokens(
        self,
    ) -> None:
        """Test swap_exact_tokens_for_tokens_supporting_fee_on_transfer_tokens."""
        result = self.contract.swap_exact_tokens_for_tokens_supporting_fee_on_transfer_tokens(
            self.ledger_api,
            self.contract_address,
            self.owner_address,
            self.amount_in,
            self.amount_out_min,
            self.path,
            self.to_address,
            self.deadline,
        )
        assert type(result) == JSONLike

    def test_swap_exact_ETH_for_tokens_supporting_fee_on_transfer_tokens(self) -> None:
        """Test swap_exact_ETH_for_tokens_supporting_fee_on_transfer_tokens."""
        result = (
            self.contract.swap_exact_ETH_for_tokens_supporting_fee_on_transfer_tokens(
                self.ledger_api,
                self.contract_address,
                self.owner_address,
                self.amount_out_min,
                self.path,
                self.to_address,
                self.deadline,
            )
        )
        assert type(result) == JSONLike

    def test_swap_exact_tokens_for_ETH_supporting_fee_on_transfer_tokens(self) -> None:
        """Test swap_exact_tokens_for_ETH_supporting_fee_on_transfer_tokens."""
        result = (
            self.contract.swap_exact_tokens_for_ETH_supporting_fee_on_transfer_tokens(
                self.ledger_api,
                self.contract_address,
                self.owner_address,
                self.amount_in,
                self.amount_out_min,
                self.path,
                self.to_address,
                self.deadline,
            )
        )
        assert type(result) == JSONLike

    def test_quote(self) -> None:
        """Test quote."""
        result = self.contract.quote(
            self.ledger_api,
            self.contract_address,
            self.amount_a,
            self.reserve_a,
            self.reserve_b,
        )
        assert type(result) == JSONLike

    def test_get_amount_out(self) -> None:
        """Test get_amount_out."""
        result = self.contract.get_amount_out(
            self.ledger_api,
            self.contract_address,
            self.amount_in,
            self.reserve_in,
            self.reserve_out,
        )
        assert type(result) == JSONLike

    def test_get_amount_in(self) -> None:
        """Test get_amount_in."""
        result = self.contract.get_amount_in(
            self.ledger_api,
            self.contract_address,
            self.amount_out,
            self.reserve_in,
            self.reserve_out,
        )
        assert type(result) == JSONLike

    def test_get_amounts_out(self) -> None:
        """Test get_amounts_out."""
        result = self.contract.get_amounts_out(
            self.ledger_api, self.contract_address, self.amount_in, self.path
        )
        assert type(result) == JSONLike

    def test_get_amounts_in(self) -> None:
        """Test get_amounts_in."""
        result = self.contract.get_amounts_in(
            self.ledger_api, self.contract_address, self.amount_out, self.path
        )
        assert type(result) == JSONLike
