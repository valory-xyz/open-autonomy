# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
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

"""Tests for valory/service_registry contract."""
import logging
from typing import Dict
from pathlib import Path
from aea.test_tools.test_contract import BaseContractTestCase
from aea_ledger_ethereum import EthereumCrypto
from packages.valory.contracts.service_registry.contract import (
    PUBLIC_ID,
    ServiceRegistryContract,
)
from unittest import mock
from tests.conftest import ROOT_DIR


CONTRACT_ADDRESS = "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266"
COMPONENT_REGISTRY = "0x5FbDB2315678afecb367f032d93F642f64180aa3"
AGENT_REGISTRY = "0xe7f1725E7734CE288F8367e1Bb143E90bb3F0512"
REGISTRIES_MANAGER = "0x9fE46736679d2D9a65F0992F2272dE9f3c7fa6e0"
OWNER_COMPONENTS_AND_AGENTS = "0x8626f6940E2eb28930eFb4CeF49B2d1F2C9C1199"

ADDRESS_ONE = "0x70997970c51812dc3a010c7d01b50e0d17dc79c8"
ADDRESS_TWO = "0x3c44cdddb6a900fa2b585dd299e03d12fa4293bc"
ADDRESS_THREE = "0x90f79bf6eb2c4f870365e785982e1f101e93b906"


class TestServiceRegistryContract(BaseContractTestCase):
    """Test Service Registry Contract"""

    contract: ServiceRegistryContract
    ledger_identifier = EthereumCrypto.identifier
    contract_address = CONTRACT_ADDRESS
    path_to_contract = Path(
        ROOT_DIR, "packages", PUBLIC_ID.author, "contracts", PUBLIC_ID.name
    )

    @classmethod
    def finish_contract_deployment(cls) -> str:
        return CONTRACT_ADDRESS

    @classmethod
    def _deploy_contract(cls, contract, ledger_api, deployer_crypto, gas) -> Dict:  # type: ignore
        """Deploy contract."""
        return {}



    def test_get_service_info(self):
        assert self.contract_address is not None

        with mock.path.object(
            self.ledger_api
        ):

            result = self.contract.get_service_info(
                ledger_api=self.ledger_api,
                contract_address=self.contract_address,
                service_id=1,
            )
            logging.error(str(result))
            assert result


    # def test_verify(self) -> None:
    #     """Run verify test."""
    #     assert self.contract_address is not None
    #     result = self.contract.verify_contract(
    #         ledger_api=self.ledger_api,
    #         contract_address=self.contract_address,
    #     )
    #     assert result["verified"], "Contract not verified."
