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

from packages.valory.contracts.uniswap_v2_erc20.contract import UniswapV2ERC20Contract

from tests.conftest import ROOT_DIR
from tests.test_contracts.base import BaseGanacheContractTest


class TestUniswapV2ERC20(BaseGanacheContractTest):
    """Test deployment of the proxy to Ganache."""

    contract_directory = Path(
        ROOT_DIR, "packages", "valory", "contracts", "uniswap_v2_erc20"
    )
    contract: UniswapV2ERC20Contract

    @classmethod
    def setup_class(
        cls,
    ) -> None:
        """Setup test."""
        super().setup_class()

    def test_aprove(self) -> None:
        """Test approve."""
        # check tx fields
        # check allowance increase
        pass

    def test_transfer(self) -> None:
        """Test transfer."""
        # check tx fields
        # check new balances from from and to addresses
        pass

    def test_transfer_from(self) -> None:
        """Test transfer_from."""
        # check tx fields
        # check new balances from from and to addresses
        pass

    def test_permit(self) -> None:
        """Test permit."""
        # check tx fields
        # check allowance increase
        pass
