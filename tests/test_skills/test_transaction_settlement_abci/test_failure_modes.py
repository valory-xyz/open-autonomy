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

"""Integration tests for various transaction settlement skill's failure modes."""

from unittest import mock

import pytest
from aea_ledger_ethereum import EthereumApi
from web3.types import RPCEndpoint

from tests.test_skills.integration.test_transaction_settlement import (
    TransactionSettlementIntegrationBaseCase,
)


class TestRepricing(TransactionSettlementIntegrationBaseCase):
    """Test failure modes related to repricing."""

    @pytest.mark.parametrize("should_mock_ledger_pricing_mechanism", (True, False))
    def test_same_keeper(
        self,
        should_mock_ledger_pricing_mechanism: bool,
    ) -> None:
        """Test repricing with and without mocking ledger's `try_get_gas_pricing` method."""

        try:
            if should_mock_ledger_pricing_mechanism:
                with mock.patch.object(
                    EthereumApi,
                    "try_get_gas_pricing",
                    new_callable=TransactionSettlementIntegrationBaseCase.dummy_try_get_gas_pricing_wrapper,
                ):
                    self._test_same_keeper()
            else:
                self._test_same_keeper()

        finally:
            # clear all unmined txs. Mined txs will not be cleared, but this is not a problem
            for tx in self.tx_settlement_period_state.tx_hashes_history:
                self.hardhat_provider.make_request(
                    RPCEndpoint("hardhat_dropTransaction"), (tx,)
                )

    def _test_same_keeper(self) -> None:
        """
        Test repricing after the first failure.

        Test that we are using the same keeper to reprice when we fail or timeout for the first time.
        Also, test that we are adjusting the gas correctly when repricing.
        """

        # deploy the oracle
        self.deploy_oracle()
        # generate tx hash
        self.gen_safe_tx_hash()
        # sign tx
        self.sign_tx()
        # stop HardHat's automatic mining
        assert self.hardhat_provider.make_request(
            RPCEndpoint("evm_setAutomine"), [False]
        ), "Disabling auto-mining failed!"
        # send tx first time, we expect it to be pending until we enable the mining back
        self.send_tx()
        # re-enable HardHat's automatic mining so that the second tx replaces the first, pending one
        assert self.hardhat_provider.make_request(
            RPCEndpoint("evm_setIntervalMining"), [1000]
        ), "Re-enabling auto-mining failed!"
        # send tx second time
        self.send_tx()
        # validate the tx
        self.validate_tx()
