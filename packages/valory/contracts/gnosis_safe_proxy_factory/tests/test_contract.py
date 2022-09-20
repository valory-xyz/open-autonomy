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

"""Tests for valory/gnosis contract."""

from pathlib import Path
from typing import Any, Dict

from aea_test_autonomy.base_test_classes.contracts import BaseGanacheContractTest
from aea_test_autonomy.docker.base import skip_docker_tests

from packages.valory.contracts.gnosis_safe_proxy_factory.contract import (
    GnosisSafeProxyFactoryContract,
    PROXY_FACTORY_CONTRACT,
)


PACKAGE_DIR = Path(__file__).parent.parent

DEFAULT_GAS = 1000000
DEFAULT_MAX_FEE_PER_GAS = 10 ** 10
DEFAULT_MAX_PRIORITY_FEE_PER_GAS = 10 ** 10
SAFE_CONTRACT = "0xd9Db270c1B5E3Bd161E8c8503c55cEABeE709552"


@skip_docker_tests
class TestGnosisSafeProxyFactory(BaseGanacheContractTest):
    """Test deployment of the proxy to Ganache."""

    contract_directory = PACKAGE_DIR
    contract: GnosisSafeProxyFactoryContract

    @classmethod
    def deployment_kwargs(cls) -> Dict[str, Any]:
        """Get deployment kwargs."""
        return dict(
            gas=DEFAULT_GAS,
        )

    def test_deploy(self) -> None:
        """Test deployment results."""
        assert (
            self.contract_address != PROXY_FACTORY_CONTRACT
        ), "Contract addresses should differ as we don't use deterministic deployment here."

    def test_build_tx_deploy_proxy_contract_with_nonce(self) -> None:
        """Test build_tx_deploy_proxy_contract_with_nonce method."""
        assert self.contract_address is not None
        result = self.contract.build_tx_deploy_proxy_contract_with_nonce(
            self.ledger_api,
            self.contract_address,
            SAFE_CONTRACT,
            self.deployer_crypto.address,
            b"",
            1,
            gas=DEFAULT_GAS,
            nonce=1,
        )
        assert len(result) == 2
        assert len(result[0]) == 9
        assert all(
            [
                key
                in [
                    "value",
                    "gas",
                    "maxFeePerGas",
                    "maxPriorityFeePerGas",
                    "chainId",
                    "from",
                    "to",
                    "data",
                    "nonce",
                ]
                for key in result[0].keys()
            ]
        )

    def test_verify(self) -> None:
        """Test verification of deployed contract results."""
        assert self.contract_address is not None
        result = self.contract.verify_contract(
            ledger_api=self.ledger_api,
            contract_address=self.contract_address,
        )

        assert result["verified"], "Contract not verified."
