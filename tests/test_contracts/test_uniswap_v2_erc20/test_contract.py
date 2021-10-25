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

from aea.common import JSONLike
from aea.test_tools.test_contract import BaseContractTestCase

from packages.valory.contracts.uniswap_v2_erc20.contract import UniswapV2ERC20Contract

from tests.conftest import ROOT_DIR


class TestUniswapV2ERC20(BaseContractTestCase):
    """Test deployment of the proxy to Ganache."""

    contract_directory = Path(
        ROOT_DIR, "packages", "valory", "contracts", "uniswap_v2_erc20"
    )
    contract: UniswapV2ERC20Contract
    owner_address = ""
    spender_address = ""

    def test_aprove(self) -> None:
        """Test approve."""
        result = self.contract.approve(
            self.ledger_api,
            self.contract_address,
            self.owner_address,
            self.spender_address,
            100,
        )
        assert type(result) == JSONLike

    def test_transfer(self) -> None:
        """Test transfer."""
        result = self.contract.transfer(
            self.ledger_api,
            self.contract_address,
            self.owner_address,
            self.spender_address,
            100,
        )
        assert type(result) == JSONLike

    def test_transfer_from(self) -> None:
        """Test transfer_from."""
        result = self.contract.transfer_from(
            self.ledger_api,
            self.contract_address,
            self.owner_address,
            self.spender_address,
            100,
        )
        assert type(result) == JSONLike

    def test_permit(self) -> None:
        """Test permit."""
        result = self.contract.permit(
            self.ledger_api,
            self.contract_address,
            self.owner_address,
            self.spender_address,
            100,
            # deadline,
            # v,
            # r,
            # s,
        )
        assert type(result) == JSONLike

    def test_allowance(self) -> None:
        """Test allowance."""
        result = self.contract.allowance(
            self.ledger_api,
            self.contract_address,
            self.owner_address,
            self.spender_address,
        )
        assert type(result) == JSONLike

    def test_balance_of(self) -> None:
        """Test balance_of."""
        result = self.contract.balance_of(
            self.ledger_api, self.contract_address, self.owner_address
        )
        assert type(result) == JSONLike
