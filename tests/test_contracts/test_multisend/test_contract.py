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

"""Tests for valory/gnosis contract."""

from pathlib import Path
from typing import Dict
from unittest import mock

import pytest
from aea.crypto.registries import crypto_registry
from aea.test_tools.test_contract import BaseContractTestCase
from aea_ledger_ethereum import EthereumCrypto
from hexbytes import HexBytes

from packages.valory.contracts.multisend.contract import (
    MultiSendContract,
    MultiSendOperation,
    PUBLIC_ID,
)

from tests.conftest import ROOT_DIR


CONTRACT_ADDRESS = "0xa6B71E26C5e0845f74c812102Ca7114b6a896AB2"
CHAIN_ID = 1


class TestMultisendContract(BaseContractTestCase):
    """Base test case for GnosisSafeContract"""

    path_to_contract = Path(
        ROOT_DIR, "packages", PUBLIC_ID.author, "contracts", PUBLIC_ID.name
    )
    ledger_identifier = EthereumCrypto.identifier
    contract: MultiSendContract
    tx_list = [
        {
            "operation": MultiSendOperation.CALL,
            "to": crypto_registry.make(EthereumCrypto.identifier).address,
            "value": 1,
            "data": HexBytes("0x123456789a"),
        },
        {
            "operation": MultiSendOperation.DELEGATE_CALL,
            "to": crypto_registry.make(EthereumCrypto.identifier).address,
            "value": 796,
            "data": HexBytes("0x123456789a"),
        },
    ]

    @classmethod
    def finish_contract_deployment(cls) -> str:
        """Finish the contract deployment."""
        contract_address = CONTRACT_ADDRESS
        return contract_address

    @classmethod
    def _deploy_contract(cls, contract, ledger_api, deployer_crypto, gas) -> Dict:  # type: ignore
        """Deploy contract."""
        return {}

    def test_non_implemented_methods(
        self,
    ) -> None:
        """Test not implemented methods."""
        with pytest.raises(NotImplementedError):
            self.contract.get_raw_transaction(self.ledger_api, "")

        with pytest.raises(NotImplementedError):
            self.contract.get_raw_message(self.ledger_api, "")

        with pytest.raises(NotImplementedError):
            self.contract.get_state(self.ledger_api, "")

        with pytest.raises(NotImplementedError):
            self.contract.get_deploy_transaction(self.ledger_api, "")

    def test_get_tx_data_get_tx_list(self) -> None:
        """Run end-to-end data conversion test."""
        assert self.contract_address is not None
        with mock.patch.object(
            self.ledger_api.api.manager, "request_blocking", return_value=CHAIN_ID
        ):
            result = self.contract.get_tx_data(
                ledger_api=self.ledger_api,
                contract_address=self.contract_address,
                multi_send_txs=self.tx_list,
            )
        assert isinstance(result, dict)
        assert "data" in result
        data = result["data"]
        assert isinstance(data, str)
        assert len(data) > 0, "No data."
        with mock.patch.object(
            self.ledger_api.api.manager, "request_blocking", return_value=CHAIN_ID
        ):
            result = self.contract.get_tx_list(
                ledger_api=self.ledger_api,
                contract_address=self.contract_address,
                multi_send_data=data,
            )
        assert isinstance(result, dict)
        assert "tx_list" in result
        assert self.tx_list == result["tx_list"], "Not same."
