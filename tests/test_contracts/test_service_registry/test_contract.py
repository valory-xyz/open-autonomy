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

# To test locally, run a hardhat node:


import logging
from typing import Dict, List, Tuple, Any, cast
from pathlib import Path

from aea_ledger_ethereum import EthereumCrypto

from packages.valory.contracts.component_registry.contract import (
    PUBLIC_ID as COMPONENT_REGISTRY_PUBLIC_ID,
    ComponentRegistryContract,
)

from packages.valory.contracts.agent_registry.contract import (
    PUBLIC_ID as AGENT_REGISTRY_PUBLIC_ID,
    AgentRegistryContract,
)

from packages.valory.contracts.service_registry.contract import (
    PUBLIC_ID,
    ServiceRegistryContract,
)
from unittest import mock
from tests.conftest import ROOT_DIR
# from tests.helpers.contracts import get_register_contract
from web3 import Web3
# from aea_ledger_ethereum import EthereumApi
from tests.test_contracts.base import BaseContractTest, BaseGanacheContractTest
from tests.helpers.contracts import get_register_contract

Address = hex
ConfigHash = Tuple[bytes, int, int]
AgentParams = Tuple[int, int]

DEPLOYER_ADDRESS = "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266"
CONTRACT_ADDRESS = "0x5FbDB2315678afecb367f032d93F642f64180aa3"
AGENT_REGISTRY = "0xe7f1725E7734CE288F8367e1Bb143E90bb3F0512"
COMPONENT_REGISTRY = "0x9fE46736679d2D9a65F0992F2272dE9f3c7fa6e0"
# REGISTRIES_MANAGER = "0x9fE46736679d2D9a65F0992F2272dE9f3c7fa6e0"
# OWNER_COMPONENTS_AND_AGENTS = "0x8626f6940E2eb28930eFb4CeF49B2d1F2C9C1199"

ADDRESS_ONE = "0x70997970c51812dc3a010c7d01b50e0d17dc79c8"
ADDRESS_TWO = "0x3c44cdddb6a900fa2b585dd299e03d12fa4293bc"
ADDRESS_THREE = "0x90f79bf6eb2c4f870365e785982e1f101e93b906"
ADDRESS_FOUR = "0x15d34AAf54267DB7D7c367839AAf71A00a2C6A65"

NONCE = 0
CHAIN_ID = 31337


class BaseComponentRegistryTest(BaseContractTest):
    """"""
    contract: AgentRegistryContract
    ledger_identifier = EthereumCrypto.identifier
    contract_address = AGENT_REGISTRY
    contract_directory = Path(
        ROOT_DIR, "packages", COMPONENT_REGISTRY_PUBLIC_ID.author, "contracts", "component_registry"
    )

    GAS: int = 10 ** 10
    DEFAULT_MAX_FEE_PER_GAS: int = 10 ** 10
    DEFAULT_MAX_PRIORITY_FEE_PER_GAS: int = 10 ** 10

    @classmethod
    def deployment_kwargs(cls) -> Dict[str, Any]:
        """Contract deployment kwargs"""

        _name: str = "TestComponentRegistry"
        _symbol: str = "OLA"
        _bURI: str = "bURI"

        return dict(
            _name=_name,
            _symbol=_symbol,
            _bURI=_bURI,
            gas=cls.GAS,
        )


class BaseAgentRegistryTest(BaseContractTest):
    """"""
    contract: AgentRegistryContract
    ledger_identifier = EthereumCrypto.identifier
    contract_address = AGENT_REGISTRY
    contract_directory = Path(
        ROOT_DIR, "packages", AGENT_REGISTRY_PUBLIC_ID.author, "contracts", "agent_registry"
    )

    GAS: int = 10 ** 10
    DEFAULT_MAX_FEE_PER_GAS: int = 10 ** 10
    DEFAULT_MAX_PRIORITY_FEE_PER_GAS: int = 10 ** 10

    @classmethod
    def deployment_kwargs(cls) -> Dict[str, Any]:
        """Contract deployment kwargs"""

        _name: str = "TestAgentRegistry"
        _symbol: str = "OLA"
        _bURI: str = "bURI"
        _componentRegistry: Address = Web3.toChecksumAddress(COMPONENT_REGISTRY)

        return dict(
            _name=_name,
            _symbol=_symbol,
            _bURI=_bURI,
            _componentRegistry=_componentRegistry,
            gas=cls.GAS,
        )


class BaseServiceRegistryContractTest(BaseGanacheContractTest):

    contract: ServiceRegistryContract
    ledger_identifier = EthereumCrypto.identifier
    contract_address = CONTRACT_ADDRESS
    contract_directory = Path(
        ROOT_DIR, "packages", PUBLIC_ID.author, "contracts", PUBLIC_ID.name
    )

    GAS: int = 10 ** 10
    DEFAULT_MAX_FEE_PER_GAS: int = 10 ** 10
    DEFAULT_MAX_PRIORITY_FEE_PER_GAS: int = 10 ** 10

    @classmethod
    def setup_class(cls) -> None:
        super().setup_class()

        # deploy agent registry contract
        contract = get_register_contract(BaseAgentRegistryTest.contract_directory)
        tx = contract.get_deploy_transaction(
            ledger_api=cls.ledger_api,
            deployer_address=str(cls.deployer_crypto.address),
            **BaseAgentRegistryTest.deployment_kwargs(),
        )
        contract_address = tx.pop("contract_address", None)
        tx_signed = cls.deployer_crypto.sign_transaction(tx)
        tx_hash = cls.ledger_api.send_signed_transaction(tx_signed)
        import time
        time.sleep(0.5)  # give it time to mine the block
        tx_receipt = cls.ledger_api.get_transaction_receipt(tx_hash)
        contract_address = (
            cast(Dict, tx_receipt)["contractAddress"]
            if contract_address is None
            else contract_address
        )
        assert contract_address == AGENT_REGISTRY

        # deploy component registry contract
        contract = get_register_contract(BaseComponentRegistryTest.contract_directory)
        tx = contract.get_deploy_transaction(
            ledger_api=cls.ledger_api,
            deployer_address=str(cls.deployer_crypto.address),
            **BaseComponentRegistryTest.deployment_kwargs(),
        )
        contract_address = tx.pop("contract_address", None)
        tx_signed = cls.deployer_crypto.sign_transaction(tx)
        tx_hash = cls.ledger_api.send_signed_transaction(tx_signed)
        import time
        time.sleep(0.5)  # give it time to mine the block
        tx_receipt = cls.ledger_api.get_transaction_receipt(tx_hash)
        contract_address = (
            cast(Dict, tx_receipt)["contractAddress"]
            if contract_address is None
            else contract_address
        )
        assert contract_address == COMPONENT_REGISTRY

    @classmethod
    def deployment_kwargs(cls) -> Dict[str, Any]:
        """Contract deployment kwargs"""

        _name: str = "TestServiceRegistry"
        _symbol: str = "OLA"
        _agentRegistry: Address = Web3.toChecksumAddress(AGENT_REGISTRY)

        return dict(
            _name=_name,
            _symbol=_symbol,
            _agentRegistry=_agentRegistry,
            gas=cls.GAS,
        )

    def create_dummy_service(self) -> bool:
        """Create dummy service"""

        owner: Address = self.key_pairs()[0][0]
        name: str = "dummy_service"
        description: str = "description"
        config_hash: ConfigHash = (b"config_hash", 8, 8)
        agent_ids: List[int] = [1, ]
        agent_params: List[AgentParams] = [(256, 256), ]
        threshold: int = 0

        kwargs = dict(
            owner=owner,
            name=name,
            description=description,
            configHash=config_hash,
            agentIds=agent_ids,
            agentParams=agent_params,
            threshold=threshold,
        )

        success = self.contract.contract_method_call(
            self.ledger_api, "createService", **kwargs
        )

        return cast(bool, success)


class TestServiceRegistryContract(BaseServiceRegistryContractTest):
    """Test Service Registry Contract"""

    def test_deployment(self) -> None:
        """Test deployment"""

        expected_keys = {'gas', 'chainId', 'value', 'nonce', 'maxFeePerGas', 'maxPriorityFeePerGas', 'data', 'from'}

        tx = self.contract.get_deploy_transaction(
            ledger_api=self.ledger_api,
            deployer_address=str(self.deployer_crypto.address),
            **self.deployment_kwargs(),
        )

        assert isinstance(tx, dict)
        assert len(tx) == 8
        assert not expected_keys.symmetric_difference(tx)
        assert tx['data'].startswith("0x")

    def test_verify_contract(self) -> None:
        """Run verify test. If abi file is updated tests need updating"""

        assert self.contract_address is not None
        result = self.contract.verify_contract(
            ledger_api=self.ledger_api,
            contract_address=self.contract_address,
        )

        assert result["verified"]

    def test_get_service_info(self) -> None:
        """Test service info retrieval"""

        service_id: int = 1  # contract counter increments before assignment

        assert self.contract_address is not None
        assert self.create_dummy_service()

        service_info = self.contract.get_service_info(
            ledger_api=self.ledger_api,
            contract_address=self.contract_address,
            service_id=service_id,
        )

        assert service_info['service_id'] == service_id

    # def test_get_service_info(self) -> None:
    #
    #     owner: Address = self.key_pairs()[0][0]
    #     name: str = "dummy_service"
    #     description: str = "description"
    #     config_hash: ConfigHash = (b"config_hash", 8, 8)
    #     threshold: int = 0
    #     num_agent_ids: int = 1
    #     agent_ids: List[int] = [1, ]
    #     agent_params: List = [(256, 256), ]
    #     num_agent_instances: int = 1
    #     agent_instances: List[Address] = [ADDRESS_ONE, ]
    #     address: Address = ADDRESS_ONE
    #
    #     result = dict(
    #         owner=owner,
    #         name=name,
    #         description=description,
    #         config_hash=config_hash,
    #         threshold=threshold,
    #         num_agent_ids=num_agent_ids,
    #         agent_ids=agent_ids,
    #         agent_params=agent_params,
    #         num_agent_instances=num_agent_instances,
    #         agent_instances=agent_instances,
    #         address=address,
    #     )
    #
    #     with mock.patch.object(
    #             self.ledger_api.api.manager, "request_blocking", return_value=CHAIN_ID
    #     ):
    #         with mock.patch.object(
    #                 self.ledger_api.api.manager, "call_contract_function", return_value=result
    #         ):
    #             service_info = self.contract.get_service_info(
    #                 ledger_api=self.ledger_api,
    #                 contract_address=self.contract_address,
    #                 service_id=1,
    #             )
    #
    #     logging.error(service_info)


