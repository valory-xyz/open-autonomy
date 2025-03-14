# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2023 Valory AG
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

"""Tests for valory/multicall2 contract."""
from pathlib import Path
from typing import Any, Dict, cast

from aea_test_autonomy.base_test_classes.contracts import BaseGanacheContractTest
from aea_test_autonomy.configurations import DEFAULT_AMOUNT as DEFAULT_ETH_BALANCE
from aea_test_autonomy.docker.base import skip_docker_tests

from packages.valory.contracts.multicall2.contract import Multicall2Contract


DEFAULT_GAS = 10000000


@skip_docker_tests
class TestTokenSettingsFactory(BaseGanacheContractTest):
    """Test deployment of Token Settings to Ganache."""

    contract_directory = Path(__file__).parent.parent
    contract: Multicall2Contract

    @classmethod
    def deployment_kwargs(cls) -> Dict[str, Any]:
        """Get deployment kwargs."""
        return dict(
            gas=DEFAULT_GAS,
        )

    def test_aggregate(self) -> None:
        """Test aggregate."""
        address, _pk = self.key_pairs()[1]
        expected_funds = DEFAULT_ETH_BALANCE
        multicall_instance = Multicall2Contract.get_instance(
            self.ledger_api, self.contract_address
        )
        call = self.contract.encode_function_call(
            self.ledger_api,
            multicall_instance,
            fn_name="getEthBalance",
            args=[address],
        )
        # make the same call 3 times
        calls = [call, call, call]
        contract_address = cast(str, self.contract_address)
        results = self.contract.aggregate_and_decode(
            self.ledger_api, contract_address, calls
        )

        assert isinstance(results, tuple)
        assert len(results) == 2

        block_number, responses = results
        assert isinstance(block_number, int)
        assert isinstance(responses, list)
        assert len(responses) == len(calls)
        for response in responses:
            # the response always is Tuple
            assert isinstance(response, tuple)
            assert isinstance(response[0], int)
            actual_funds = response[0]
            assert actual_funds == expected_funds
