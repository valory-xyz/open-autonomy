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
from typing import Any, Dict

from packages.valory.contracts.uniswap_v2_erc20.contract import SAFE_CONTRACT

from tests.conftest import ROOT_DIR
from tests.test_contracts.base import BaseGanacheContractTest


class TestGnosisSafeProxyFactory(BaseGanacheContractTest):
    """Test deployment of the proxy to Ganache."""

    contract_directory = Path(
        ROOT_DIR, "packages", "valory", "contracts", "gnosis_safe_proxy_factory"
    )
    contract: GnosisSafeProxyFactoryContract

    @classmethod
    def deployment_kwargs(cls) -> Dict[str, Any]:
        """Get deployment kwargs."""
        return dict(gas=10000000, gasPrice=10000000)

    def test_deploy(self) -> None:
        """Test deployment results."""
        assert (
            self.contract_address != PROXY_FACTORY_CONTRACT
        ), "Contract addresses should differ as we don't use deterministic deployment here."
