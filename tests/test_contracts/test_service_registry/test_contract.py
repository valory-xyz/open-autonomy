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
from typing import Dict, List, Tuple, Any
from pathlib import Path

from aea_ledger_ethereum import EthereumCrypto

from packages.valory.contracts.service_registry.contract import (
    PUBLIC_ID,
    ServiceRegistryContract,
)
from unittest import mock
from web3 import Web3
import pytest
from tests.conftest import ROOT_DIR
from tests.test_contracts.base import BaseGanacheContractTest

Address = hex
ConfigHash = Tuple[bytes, int, int]
AgentParams = Tuple[int, int]

ADDRESS_ZERO = "0x0000000000000000000000000000000000000000"
COMPONENT_REGISTRY = "0x5FbDB2315678afecb367f032d93F642f64180aa3"
AGENT_REGISTRY = "0xe7f1725E7734CE288F8367e1Bb143E90bb3F0512"
REGISTRIES_MANAGER = "0x9fE46736679d2D9a65F0992F2272dE9f3c7fa6e0"
OWNER = "0x8626f6940E2eb28930eFb4CeF49B2d1F2C9C1199"
SERVICE_REGISTRY = "0xA51c1fc2f0D1a1b8494Ed1FE312d7C3a78Ed91C0"
SERVICE_MANAGER = "0x0DCd1Bf9A1b36cE34237eEaFef220932846BCD82"

ADDRESS_ONE = "0x70997970c51812dc3a010c7d01b50e0d17dc79c8"
ADDRESS_TWO = "0x3c44cdddb6a900fa2b585dd299e03d12fa4293bc"
ADDRESS_THREE = "0x90f79bf6eb2c4f870365e785982e1f101e93b906"
ADDRESS_FOUR = "0x15d34AAf54267DB7D7c367839AAf71A00a2C6A65"

NONCE = 0
CHAIN_ID = 31337


class BaseServiceRegistryContractTest(BaseGanacheContractTest):

    contract: ServiceRegistryContract
    ledger_identifier = EthereumCrypto.identifier
    contract_address = SERVICE_REGISTRY
    contract_directory = Path(
        ROOT_DIR, "packages", PUBLIC_ID.author, "contracts", PUBLIC_ID.name
    )

    GAS: int = 10 ** 10
    DEFAULT_MAX_FEE_PER_GAS: int = 10 ** 10
    DEFAULT_MAX_PRIORITY_FEE_PER_GAS: int = 10 ** 10
    eth_value: int = 0

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

    def get_dummy_service_args(self) -> List:
        """Create dummy service"""

        owner: Address = OWNER
        name: str = "service name"
        description: str = "service description"
        config_hash: ConfigHash = (
            b'UUUUUUUUUUUUUUUUUUUUUUUUUUUUUUU"',
            int("0x12", 16),
            int("0x20", 16),
        )
        agent_ids: List[int] = [1, 2]
        agent_params: List[AgentParams] = [(3, 1000), (4, 1000)]
        threshold: int = 0

        return [
            owner,
            name,
            description,
            config_hash,
            agent_ids,
            agent_params,
            threshold,
        ]


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
        assert tx['data'].startswith("0x") and len(tx['data']) > 2

    def test_verify_contract(self) -> None:
        """Run verify test. If abi file is updated tests + addresses need updating"""

        assert self.contract_address is not None
        result = self.contract.verify_contract(
            ledger_api=self.ledger_api,
            contract_address=self.contract_address,
        )

        assert result["verified"] is True

    def test_change_manager(self):
        """Test change manager"""

        new_manager: Address = Web3.toChecksumAddress(ADDRESS_TWO)
        data = self.contract.get_instance(
            self.ledger_api, self.contract_address
        ).encodeABI(fn_name="changeManager", args=[new_manager])

        with mock.patch.object(
            self.ledger_api.api.eth, "get_transaction_count", return_value=NONCE
        ):
            with mock.patch.object(
                self.ledger_api.api.manager, "request_blocking", return_value=CHAIN_ID
            ):
                result = self.contract.change_service_manager(
                    self.ledger_api,
                    self.contract_address,
                    new_manager=new_manager,
                    sender_address=Web3.toChecksumAddress(ADDRESS_ONE),
                    gas=self.GAS,
                    gasPrice=self.DEFAULT_MAX_FEE_PER_GAS,
                )

        assert data.startswith("0x") and len(data) > 2
        assert result["chainId"] == CHAIN_ID
        assert result["nonce"] == NONCE
        assert result["to"] == COMPONENT_REGISTRY
        assert result["data"] == data
        assert result["value"] == self.eth_value

    @pytest.mark.parametrize("service_id, expected", [(0, False), (1, True)])
    def test_exists(self, service_id: int, expected: int):
        """Test whether service id exists"""

        hex_str = "0x" + "0" * 63 + str(int(expected))

        with mock.patch.object(
            self.ledger_api.api.manager, "request_blocking", return_value=hex_str
        ):
            exists = self.contract.exists(
                self.ledger_api,
                self.contract_address,
                service_id,
            )

        assert exists is expected

    def test_create_service(self):
        """Test service creation"""

        data = self.contract.get_instance(
            self.ledger_api, self.contract_address
        ).encodeABI(fn_name="createService", args=self.get_dummy_service_args())

        with mock.patch.object(
            self.ledger_api.api.eth, "get_transaction_count", return_value=NONCE + 1
        ):
            with mock.patch.object(
                self.ledger_api.api.manager, "request_blocking", return_value=CHAIN_ID
            ):
                result = self.contract.create_service(
                    self.ledger_api,
                    self.contract_address,
                    *self.get_dummy_service_args(),
                    sender_address=Web3.toChecksumAddress(ADDRESS_ONE),
                    gas=self.GAS,
                    gasPrice=self.DEFAULT_MAX_FEE_PER_GAS,
                )

            assert data.startswith("0x") and len(data) > 2
            assert result["chainId"] == CHAIN_ID
            assert result["nonce"] == NONCE + 1
            assert result["to"] == COMPONENT_REGISTRY
            assert result["data"] == data
            assert result["value"] == self.eth_value

    def test_get_service_info(self):
        """Test service info retrieval"""

        return_value = [
            OWNER,
            'service name',
            'service description',
            (b'UUUUUUUUUUUUUUUUUUUUUUUUUUUUUUU"', 18, 32),
            7,
            2,
            [1, 2],
            [(3, 1000), (4, 1000)],
            0,
            [],
            ADDRESS_ZERO,
        ]

        data = self.contract.get_instance(
            self.ledger_api, self.contract_address
        ).encodeABI(fn_name="getServiceInfo", args=[1])

        with mock.patch.object(
            self.ledger_api.api.manager, "request_blocking", return_value=return_value
        ):
            service_info = self.contract.get_service_info(
                ledger_api=self.ledger_api,
                contract_address=self.contract_address,
                service_id=1,
            )

        assert service_info == return_value


def _test_service_info():
    # docker run -p 8545:8545 -it valory/onchain-protocol:main
    abi = [{'inputs': [{'internalType': 'string', 'name': '_name', 'type': 'string'}, {'internalType': 'string', 'name': '_symbol', 'type': 'string'}, {'internalType': 'address', 'name': '_agentRegistry', 'type': 'address'}], 'stateMutability': 'nonpayable', 'type': 'constructor'}, {'inputs': [{'internalType': 'address', 'name': 'operator', 'type': 'address'}], 'name': 'AgentInstanceRegistered', 'type': 'error'}, {'inputs': [{'internalType': 'uint256', 'name': 'serviceId', 'type': 'uint256'}], 'name': 'AgentInstancesSlotsFilled', 'type': 'error'}, {'inputs': [{'internalType': 'uint256', 'name': 'actual', 'type': 'uint256'}, {'internalType': 'uint256', 'name': 'maxNumAgentInstances', 'type': 'uint256'}, {'internalType': 'uint256', 'name': 'serviceId', 'type': 'uint256'}], 'name': 'AgentInstancesSlotsNotFilled', 'type': 'error'}, {'inputs': [{'internalType': 'uint256', 'name': 'agentId', 'type': 'uint256'}], 'name': 'AgentNotFound', 'type': 'error'}, {'inputs': [{'internalType': 'uint256', 'name': 'agentId', 'type': 'uint256'}, {'internalType': 'uint256', 'name': 'serviceId', 'type': 'uint256'}], 'name': 'AgentNotInService', 'type': 'error'}, {'inputs': [{'internalType': 'uint256', 'name': 'provided', 'type': 'uint256'}, {'internalType': 'uint256', 'name': 'expected', 'type': 'uint256'}], 'name': 'AmountLowerThan', 'type': 'error'}, {'inputs': [{'internalType': 'uint256', 'name': 'componentId', 'type': 'uint256'}], 'name': 'ComponentNotFound', 'type': 'error'}, {'inputs': [], 'name': 'EmptyString', 'type': 'error'}, {'inputs': [], 'name': 'HashExists', 'type': 'error'}, {'inputs': [{'internalType': 'uint256', 'name': 'sent', 'type': 'uint256'}, {'internalType': 'uint256', 'name': 'expected', 'type': 'uint256'}, {'internalType': 'uint256', 'name': 'serviceId', 'type': 'uint256'}], 'name': 'IncorrectAgentBondingValue', 'type': 'error'}, {'inputs': [{'internalType': 'uint256', 'name': 'sent', 'type': 'uint256'}, {'internalType': 'uint256', 'name': 'expected', 'type': 'uint256'}, {'internalType': 'uint256', 'name': 'serviceId', 'type': 'uint256'}], 'name': 'IncorrectRegistrationDepositValue', 'type': 'error'}, {'inputs': [{'internalType': 'address', 'name': 'addr', 'type': 'address'}, {'internalType': 'uint256', 'name': 'deadline', 'type': 'uint256'}, {'internalType': 'uint256', 'name': 'curTime', 'type': 'uint256'}], 'name': 'LockExpired', 'type': 'error'}, {'inputs': [{'internalType': 'address', 'name': 'addr', 'type': 'address'}, {'internalType': 'uint256', 'name': 'deadline', 'type': 'uint256'}, {'internalType': 'uint256', 'name': 'curTime', 'type': 'uint256'}], 'name': 'LockNotExpired', 'type': 'error'}, {'inputs': [{'internalType': 'address', 'name': 'addr', 'type': 'address'}, {'internalType': 'int128', 'name': 'amount', 'type': 'int128'}], 'name': 'LockedValueNotZero', 'type': 'error'}, {'inputs': [{'internalType': 'address', 'name': 'sender', 'type': 'address'}, {'internalType': 'address', 'name': 'manager', 'type': 'address'}], 'name': 'ManagerOnly', 'type': 'error'}, {'inputs': [{'internalType': 'address', 'name': 'addr', 'type': 'address'}, {'internalType': 'uint256', 'name': 'maxUnlockTime', 'type': 'uint256'}, {'internalType': 'uint256', 'name': 'providedUnlockTime', 'type': 'uint256'}], 'name': 'MaxUnlockTimeReached', 'type': 'error'}, {'inputs': [{'internalType': 'address', 'name': 'addr', 'type': 'address'}], 'name': 'NoValueLocked', 'type': 'error'}, {'inputs': [], 'name': 'NonZeroValue', 'type': 'error'}, {'inputs': [{'internalType': 'address', 'name': 'provided', 'type': 'address'}, {'internalType': 'address', 'name': 'expected', 'type': 'address'}, {'internalType': 'uint256', 'name': 'serviceId', 'type': 'uint256'}], 'name': 'OnlyOwnServiceMultisig', 'type': 'error'}, {'inputs': [{'internalType': 'address', 'name': 'operator', 'type': 'address'}, {'internalType': 'uint256', 'name': 'serviceId', 'type': 'uint256'}], 'name': 'OperatorHasNoInstances', 'type': 'error'}, {'inputs': [{'internalType': 'address', 'name': 'tokenAddress', 'type': 'address'}, {'internalType': 'uint256', 'name': 'productId', 'type': 'uint256'}, {'internalType': 'uint256', 'name': 'deadline', 'type': 'uint256'}, {'internalType': 'uint256', 'name': 'curTime', 'type': 'uint256'}], 'name': 'ProductExpired', 'type': 'error'}, {'inputs': [{'internalType': 'address', 'name': 'tokenAddress', 'type': 'address'}, {'internalType': 'uint256', 'name': 'productId', 'type': 'uint256'}, {'internalType': 'uint256', 'name': 'requested', 'type': 'uint256'}, {'internalType': 'uint256', 'name': 'actual', 'type': 'uint256'}], 'name': 'ProductSupplyLow', 'type': 'error'}, {'inputs': [{'internalType': 'uint256', 'name': 'serviceId', 'type': 'uint256'}], 'name': 'ServiceDoesNotExist', 'type': 'error'}, {'inputs': [{'internalType': 'uint256', 'name': 'serviceId', 'type': 'uint256'}], 'name': 'ServiceMustBeActive', 'type': 'error'}, {'inputs': [{'internalType': 'uint256', 'name': 'serviceId', 'type': 'uint256'}], 'name': 'ServiceMustBeInactive', 'type': 'error'}, {'inputs': [{'internalType': 'uint256', 'name': 'serviceId', 'type': 'uint256'}], 'name': 'ServiceNotFound', 'type': 'error'}, {'inputs': [{'internalType': 'uint256', 'name': 'teminationBlock', 'type': 'uint256'}, {'internalType': 'uint256', 'name': 'curBlock', 'type': 'uint256'}, {'internalType': 'uint256', 'name': 'serviceId', 'type': 'uint256'}], 'name': 'ServiceTerminated', 'type': 'error'}, {'inputs': [{'internalType': 'address', 'name': 'token', 'type': 'address'}, {'internalType': 'address', 'name': 'from', 'type': 'address'}, {'internalType': 'address', 'name': 'to', 'type': 'address'}, {'internalType': 'uint256', 'name': 'value', 'type': 'uint256'}], 'name': 'TransferFailed', 'type': 'error'}, {'inputs': [{'internalType': 'address', 'name': 'tokenAddress', 'type': 'address'}], 'name': 'UnauthorizedToken', 'type': 'error'}, {'inputs': [{'internalType': 'address', 'name': 'addr', 'type': 'address'}, {'internalType': 'uint256', 'name': 'minUnlockTime', 'type': 'uint256'}, {'internalType': 'uint256', 'name': 'providedUnlockTime', 'type': 'uint256'}], 'name': 'UnlockTimeIncorrect', 'type': 'error'}, {'inputs': [{'internalType': 'uint256', 'name': 'agentId', 'type': 'uint256'}], 'name': 'WrongAgentId', 'type': 'error'}, {'inputs': [{'internalType': 'uint256', 'name': 'numAgentIds', 'type': 'uint256'}, {'internalType': 'uint256', 'name': 'numAgentSlots', 'type': 'uint256'}], 'name': 'WrongAgentsData', 'type': 'error'}, {'inputs': [{'internalType': 'uint256', 'name': 'providedBlockNumber', 'type': 'uint256'}, {'internalType': 'uint256', 'name': 'actualBlockNumber', 'type': 'uint256'}], 'name': 'WrongBlockNumber', 'type': 'error'}, {'inputs': [{'internalType': 'uint256', 'name': 'componentId', 'type': 'uint256'}], 'name': 'WrongComponentId', 'type': 'error'}, {'inputs': [], 'name': 'WrongFunction', 'type': 'error'}, {'inputs': [{'internalType': 'uint8', 'name': 'hashFunctionProvided', 'type': 'uint8'}, {'internalType': 'uint8', 'name': 'hashFunctionNeeded', 'type': 'uint8'}, {'internalType': 'uint8', 'name': 'sizeProvided', 'type': 'uint8'}, {'internalType': 'uint8', 'name': 'sizeNeeded', 'type': 'uint8'}], 'name': 'WrongHash', 'type': 'error'}, {'inputs': [{'internalType': 'uint256', 'name': 'serviceId', 'type': 'uint256'}], 'name': 'WrongOperator', 'type': 'error'}, {'inputs': [{'internalType': 'uint256', 'name': 'state', 'type': 'uint256'}, {'internalType': 'uint256', 'name': 'serviceId', 'type': 'uint256'}], 'name': 'WrongServiceState', 'type': 'error'}, {'inputs': [{'internalType': 'uint256', 'name': 'currentThreshold', 'type': 'uint256'}, {'internalType': 'uint256', 'name': 'minThreshold', 'type': 'uint256'}, {'internalType': 'uint256', 'name': 'maxThreshold', 'type': 'uint256'}], 'name': 'WrongThreshold', 'type': 'error'}, {'inputs': [{'internalType': 'address', 'name': 'provided', 'type': 'address'}, {'internalType': 'address', 'name': 'expected', 'type': 'address'}], 'name': 'WrongTokenAddress', 'type': 'error'}, {'inputs': [], 'name': 'ZeroAddress', 'type': 'error'}, {'inputs': [], 'name': 'ZeroValue', 'type': 'error'}, {'anonymous': False, 'inputs': [{'indexed': False, 'internalType': 'address', 'name': 'owner', 'type': 'address'}, {'indexed': False, 'internalType': 'uint256', 'name': 'serviceId', 'type': 'uint256'}], 'name': 'ActivateRegistration', 'type': 'event'}, {'anonymous': False, 'inputs': [{'indexed': True, 'internalType': 'address', 'name': 'owner', 'type': 'address'}, {'indexed': True, 'internalType': 'address', 'name': 'approved', 'type': 'address'}, {'indexed': True, 'internalType': 'uint256', 'name': 'tokenId', 'type': 'uint256'}], 'name': 'Approval', 'type': 'event'}, {'anonymous': False, 'inputs': [{'indexed': True, 'internalType': 'address', 'name': 'owner', 'type': 'address'}, {'indexed': True, 'internalType': 'address', 'name': 'operator', 'type': 'address'}, {'indexed': False, 'internalType': 'bool', 'name': 'approved', 'type': 'bool'}], 'name': 'ApprovalForAll', 'type': 'event'}, {'anonymous': False, 'inputs': [{'indexed': False, 'internalType': 'uint256', 'name': 'serviceId', 'type': 'uint256'}, {'indexed': False, 'internalType': 'address', 'name': 'multisig', 'type': 'address'}, {'indexed': False, 'internalType': 'address[]', 'name': 'agentInstances', 'type': 'address[]'}, {'indexed': False, 'internalType': 'uint256', 'name': 'threshold', 'type': 'uint256'}], 'name': 'CreateMultisigWithAgents', 'type': 'event'}, {'anonymous': False, 'inputs': [{'indexed': False, 'internalType': 'address', 'name': 'owner', 'type': 'address'}, {'indexed': False, 'internalType': 'string', 'name': 'name', 'type': 'string'}, {'indexed': False, 'internalType': 'uint256', 'name': 'threshold', 'type': 'uint256'}, {'indexed': False, 'internalType': 'uint256', 'name': 'serviceId', 'type': 'uint256'}], 'name': 'CreateService', 'type': 'event'}, {'anonymous': False, 'inputs': [{'indexed': False, 'internalType': 'address', 'name': 'owner', 'type': 'address'}, {'indexed': False, 'internalType': 'uint256', 'name': 'serviceId', 'type': 'uint256'}], 'name': 'DeployService', 'type': 'event'}, {'anonymous': False, 'inputs': [{'indexed': False, 'internalType': 'address', 'name': 'sender', 'type': 'address'}, {'indexed': False, 'internalType': 'uint256', 'name': 'amount', 'type': 'uint256'}], 'name': 'Deposit', 'type': 'event'}, {'anonymous': False, 'inputs': [{'indexed': False, 'internalType': 'address', 'name': 'owner', 'type': 'address'}, {'indexed': False, 'internalType': 'uint256', 'name': 'serviceId', 'type': 'uint256'}], 'name': 'DestroyService', 'type': 'event'}, {'anonymous': False, 'inputs': [{'indexed': False, 'internalType': 'uint256', 'name': 'amount', 'type': 'uint256'}, {'indexed': False, 'internalType': 'address', 'name': 'operator', 'type': 'address'}, {'indexed': False, 'internalType': 'uint256', 'name': 'serviceId', 'type': 'uint256'}], 'name': 'OperatorSlashed', 'type': 'event'}, {'anonymous': False, 'inputs': [{'indexed': False, 'internalType': 'address', 'name': 'operator', 'type': 'address'}, {'indexed': False, 'internalType': 'uint256', 'name': 'serviceId', 'type': 'uint256'}], 'name': 'OperatorUnbond', 'type': 'event'}, {'anonymous': False, 'inputs': [{'indexed': True, 'internalType': 'address', 'name': 'previousOwner', 'type': 'address'}, {'indexed': True, 'internalType': 'address', 'name': 'newOwner', 'type': 'address'}], 'name': 'OwnershipTransferred', 'type': 'event'}, {'anonymous': False, 'inputs': [{'indexed': False, 'internalType': 'address', 'name': 'sendee', 'type': 'address'}, {'indexed': False, 'internalType': 'uint256', 'name': 'amount', 'type': 'uint256'}], 'name': 'Refund', 'type': 'event'}, {'anonymous': False, 'inputs': [{'indexed': False, 'internalType': 'address', 'name': 'operator', 'type': 'address'}, {'indexed': False, 'internalType': 'uint256', 'name': 'serviceId', 'type': 'uint256'}, {'indexed': False, 'internalType': 'address', 'name': 'agent', 'type': 'address'}, {'indexed': False, 'internalType': 'uint256', 'name': 'agentId', 'type': 'uint256'}], 'name': 'RegisterInstance', 'type': 'event'}, {'anonymous': False, 'inputs': [{'indexed': False, 'internalType': 'uint256', 'name': 'serviceId', 'type': 'uint256'}, {'indexed': False, 'internalType': 'uint256', 'name': 'amount', 'type': 'uint256'}], 'name': 'RewardService', 'type': 'event'}, {'anonymous': False, 'inputs': [{'indexed': False, 'internalType': 'address', 'name': 'manager', 'type': 'address'}], 'name': 'ServiceRegistryManagerUpdated', 'type': 'event'}, {'anonymous': False, 'inputs': [{'indexed': False, 'internalType': 'address', 'name': 'owner', 'type': 'address'}, {'indexed': False, 'internalType': 'uint256', 'name': 'serviceId', 'type': 'uint256'}], 'name': 'TerminateService', 'type': 'event'}, {'anonymous': False, 'inputs': [{'indexed': True, 'internalType': 'address', 'name': 'from', 'type': 'address'}, {'indexed': True, 'internalType': 'address', 'name': 'to', 'type': 'address'}, {'indexed': True, 'internalType': 'uint256', 'name': 'tokenId', 'type': 'uint256'}], 'name': 'Transfer', 'type': 'event'}, {'anonymous': False, 'inputs': [{'indexed': False, 'internalType': 'address', 'name': 'owner', 'type': 'address'}, {'indexed': False, 'internalType': 'string', 'name': 'name', 'type': 'string'}, {'indexed': False, 'internalType': 'uint256', 'name': 'threshold', 'type': 'uint256'}, {'indexed': False, 'internalType': 'uint256', 'name': 'serviceId', 'type': 'uint256'}], 'name': 'UpdateService', 'type': 'event'}, {'stateMutability': 'payable', 'type': 'fallback'}, {'inputs': [{'internalType': 'address', 'name': 'owner', 'type': 'address'}, {'internalType': 'uint256', 'name': 'serviceId', 'type': 'uint256'}], 'name': 'activateRegistration', 'outputs': [{'internalType': 'bool', 'name': 'success', 'type': 'bool'}], 'stateMutability': 'payable', 'type': 'function'}, {'inputs': [], 'name': 'agentRegistry', 'outputs': [{'internalType': 'address', 'name': '', 'type': 'address'}], 'stateMutability': 'view', 'type': 'function'}, {'inputs': [{'internalType': 'address', 'name': 'to', 'type': 'address'}, {'internalType': 'uint256', 'name': 'tokenId', 'type': 'uint256'}], 'name': 'approve', 'outputs': [], 'stateMutability': 'nonpayable', 'type': 'function'}, {'inputs': [{'internalType': 'address', 'name': 'owner', 'type': 'address'}], 'name': 'balanceOf', 'outputs': [{'internalType': 'uint256', 'name': '', 'type': 'uint256'}], 'stateMutability': 'view', 'type': 'function'}, {'inputs': [{'internalType': 'address', 'name': 'newManager', 'type': 'address'}], 'name': 'changeManager', 'outputs': [], 'stateMutability': 'nonpayable', 'type': 'function'}, {'inputs': [{'internalType': 'address', 'name': 'owner', 'type': 'address'}, {'internalType': 'string', 'name': 'name', 'type': 'string'}, {'internalType': 'string', 'name': 'description', 'type': 'string'}, {'components': [{'internalType': 'bytes32', 'name': 'hash', 'type': 'bytes32'}, {'internalType': 'uint8', 'name': 'hashFunction', 'type': 'uint8'}, {'internalType': 'uint8', 'name': 'size', 'type': 'uint8'}], 'internalType': 'struct IStructs.Multihash', 'name': 'configHash', 'type': 'tuple'}, {'internalType': 'uint256[]', 'name': 'agentIds', 'type': 'uint256[]'}, {'components': [{'internalType': 'uint256', 'name': 'slots', 'type': 'uint256'}, {'internalType': 'uint256', 'name': 'bond', 'type': 'uint256'}], 'internalType': 'struct IStructs.AgentParams[]', 'name': 'agentParams', 'type': 'tuple[]'}, {'internalType': 'uint256', 'name': 'threshold', 'type': 'uint256'}], 'name': 'createService', 'outputs': [{'internalType': 'uint256', 'name': 'serviceId', 'type': 'uint256'}], 'stateMutability': 'nonpayable', 'type': 'function'}, {'inputs': [{'internalType': 'address', 'name': 'owner', 'type': 'address'}, {'internalType': 'uint256', 'name': 'serviceId', 'type': 'uint256'}, {'internalType': 'address', 'name': 'multisigImplementation', 'type': 'address'}, {'internalType': 'bytes', 'name': 'data', 'type': 'bytes'}], 'name': 'deploy', 'outputs': [{'internalType': 'address', 'name': 'multisig', 'type': 'address'}], 'stateMutability': 'nonpayable', 'type': 'function'}, {'inputs': [{'internalType': 'address', 'name': 'owner', 'type': 'address'}, {'internalType': 'uint256', 'name': 'serviceId', 'type': 'uint256'}], 'name': 'destroy', 'outputs': [{'internalType': 'bool', 'name': 'success', 'type': 'bool'}], 'stateMutability': 'nonpayable', 'type': 'function'}, {'inputs': [{'internalType': 'uint256', 'name': 'serviceId', 'type': 'uint256'}], 'name': 'exists', 'outputs': [{'internalType': 'bool', 'name': '', 'type': 'bool'}], 'stateMutability': 'view', 'type': 'function'}, {'inputs': [{'internalType': 'uint256', 'name': 'tokenId', 'type': 'uint256'}], 'name': 'getApproved', 'outputs': [{'internalType': 'address', 'name': '', 'type': 'address'}], 'stateMutability': 'view', 'type': 'function'}, {'inputs': [{'internalType': 'uint256', 'name': 'serviceId', 'type': 'uint256'}], 'name': 'getConfigHashes', 'outputs': [{'internalType': 'uint256', 'name': 'numHashes', 'type': 'uint256'}, {'components': [{'internalType': 'bytes32', 'name': 'hash', 'type': 'bytes32'}, {'internalType': 'uint8', 'name': 'hashFunction', 'type': 'uint8'}, {'internalType': 'uint8', 'name': 'size', 'type': 'uint8'}], 'internalType': 'struct IStructs.Multihash[]', 'name': 'configHashes', 'type': 'tuple[]'}], 'stateMutability': 'view', 'type': 'function'}, {'inputs': [{'internalType': 'uint256', 'name': 'serviceId', 'type': 'uint256'}, {'internalType': 'uint256', 'name': 'agentId', 'type': 'uint256'}], 'name': 'getInstancesForAgentId', 'outputs': [{'internalType': 'uint256', 'name': 'numAgentInstances', 'type': 'uint256'}, {'internalType': 'address[]', 'name': 'agentInstances', 'type': 'address[]'}], 'stateMutability': 'view', 'type': 'function'}, {'inputs': [{'internalType': 'address', 'name': 'operator', 'type': 'address'}, {'internalType': 'uint256', 'name': 'serviceId', 'type': 'uint256'}], 'name': 'getOperatorBalance', 'outputs': [{'internalType': 'uint256', 'name': 'balance', 'type': 'uint256'}], 'stateMutability': 'view', 'type': 'function'}, {'inputs': [{'internalType': 'uint256', 'name': 'agentId', 'type': 'uint256'}], 'name': 'getServiceIdsCreatedWithAgentId', 'outputs': [{'internalType': 'uint256', 'name': 'numServiceIds', 'type': 'uint256'}, {'internalType': 'uint256[]', 'name': 'serviceIds', 'type': 'uint256[]'}], 'stateMutability': 'view', 'type': 'function'}, {'inputs': [{'internalType': 'uint256', 'name': 'componentId', 'type': 'uint256'}], 'name': 'getServiceIdsCreatedWithComponentId', 'outputs': [{'internalType': 'uint256', 'name': 'numServiceIds', 'type': 'uint256'}, {'internalType': 'uint256[]', 'name': 'serviceIds', 'type': 'uint256[]'}], 'stateMutability': 'view', 'type': 'function'}, {'inputs': [{'internalType': 'uint256', 'name': 'serviceId', 'type': 'uint256'}], 'name': 'getServiceInfo', 'outputs': [{'internalType': 'address', 'name': 'owner', 'type': 'address'}, {'internalType': 'string', 'name': 'name', 'type': 'string'}, {'internalType': 'string', 'name': 'description', 'type': 'string'}, {'components': [{'internalType': 'bytes32', 'name': 'hash', 'type': 'bytes32'}, {'internalType': 'uint8', 'name': 'hashFunction', 'type': 'uint8'}, {'internalType': 'uint8', 'name': 'size', 'type': 'uint8'}], 'internalType': 'struct IStructs.Multihash', 'name': 'configHash', 'type': 'tuple'}, {'internalType': 'uint256', 'name': 'threshold', 'type': 'uint256'}, {'internalType': 'uint256', 'name': 'numAgentIds', 'type': 'uint256'}, {'internalType': 'uint256[]', 'name': 'agentIds', 'type': 'uint256[]'}, {'components': [{'internalType': 'uint256', 'name': 'slots', 'type': 'uint256'}, {'internalType': 'uint256', 'name': 'bond', 'type': 'uint256'}], 'internalType': 'struct IStructs.AgentParams[]', 'name': 'agentParams', 'type': 'tuple[]'}, {'internalType': 'uint256', 'name': 'numAgentInstances', 'type': 'uint256'}, {'internalType': 'address[]', 'name': 'agentInstances', 'type': 'address[]'}, {'internalType': 'address', 'name': 'multisig', 'type': 'address'}], 'stateMutability': 'view', 'type': 'function'}, {'inputs': [{'internalType': 'uint256', 'name': 'serviceId', 'type': 'uint256'}], 'name': 'getServiceState', 'outputs': [{'internalType': 'enum ServiceRegistry.ServiceState', 'name': 'state', 'type': 'uint8'}], 'stateMutability': 'view', 'type': 'function'}, {'inputs': [{'internalType': 'address', 'name': 'owner', 'type': 'address'}, {'internalType': 'address', 'name': 'operator', 'type': 'address'}], 'name': 'isApprovedForAll', 'outputs': [{'internalType': 'bool', 'name': '', 'type': 'bool'}], 'stateMutability': 'view', 'type': 'function'}, {'inputs': [], 'name': 'name', 'outputs': [{'internalType': 'string', 'name': '', 'type': 'string'}], 'stateMutability': 'view', 'type': 'function'}, {'inputs': [], 'name': 'owner', 'outputs': [{'internalType': 'address', 'name': '', 'type': 'address'}], 'stateMutability': 'view', 'type': 'function'}, {'inputs': [{'internalType': 'uint256', 'name': 'tokenId', 'type': 'uint256'}], 'name': 'ownerOf', 'outputs': [{'internalType': 'address', 'name': '', 'type': 'address'}], 'stateMutability': 'view', 'type': 'function'}, {'inputs': [{'internalType': 'address', 'name': 'operator', 'type': 'address'}, {'internalType': 'uint256', 'name': 'serviceId', 'type': 'uint256'}, {'internalType': 'address[]', 'name': 'agentInstances', 'type': 'address[]'}, {'internalType': 'uint256[]', 'name': 'agentIds', 'type': 'uint256[]'}], 'name': 'registerAgents', 'outputs': [{'internalType': 'bool', 'name': 'success', 'type': 'bool'}], 'stateMutability': 'payable', 'type': 'function'}, {'inputs': [], 'name': 'renounceOwnership', 'outputs': [], 'stateMutability': 'nonpayable', 'type': 'function'}, {'inputs': [{'internalType': 'uint256', 'name': 'serviceId', 'type': 'uint256'}], 'name': 'reward', 'outputs': [{'internalType': 'uint256', 'name': 'rewardBalance', 'type': 'uint256'}], 'stateMutability': 'payable', 'type': 'function'}, {'inputs': [{'internalType': 'address', 'name': 'from', 'type': 'address'}, {'internalType': 'address', 'name': 'to', 'type': 'address'}, {'internalType': 'uint256', 'name': 'tokenId', 'type': 'uint256'}], 'name': 'safeTransferFrom', 'outputs': [], 'stateMutability': 'nonpayable', 'type': 'function'}, {'inputs': [{'internalType': 'address', 'name': 'from', 'type': 'address'}, {'internalType': 'address', 'name': 'to', 'type': 'address'}, {'internalType': 'uint256', 'name': 'tokenId', 'type': 'uint256'}, {'internalType': 'bytes', 'name': '_data', 'type': 'bytes'}], 'name': 'safeTransferFrom', 'outputs': [], 'stateMutability': 'nonpayable', 'type': 'function'}, {'inputs': [{'internalType': 'address', 'name': 'operator', 'type': 'address'}, {'internalType': 'bool', 'name': 'approved', 'type': 'bool'}], 'name': 'setApprovalForAll', 'outputs': [], 'stateMutability': 'nonpayable', 'type': 'function'}, {'inputs': [{'internalType': 'address[]', 'name': 'agentInstances', 'type': 'address[]'}, {'internalType': 'uint256[]', 'name': 'amounts', 'type': 'uint256[]'}, {'internalType': 'uint256', 'name': 'serviceId', 'type': 'uint256'}], 'name': 'slash', 'outputs': [{'internalType': 'bool', 'name': 'success', 'type': 'bool'}], 'stateMutability': 'nonpayable', 'type': 'function'}, {'inputs': [], 'name': 'slashedFunds', 'outputs': [{'internalType': 'uint256', 'name': '', 'type': 'uint256'}], 'stateMutability': 'view', 'type': 'function'}, {'inputs': [{'internalType': 'bytes4', 'name': 'interfaceId', 'type': 'bytes4'}], 'name': 'supportsInterface', 'outputs': [{'internalType': 'bool', 'name': '', 'type': 'bool'}], 'stateMutability': 'view', 'type': 'function'}, {'inputs': [], 'name': 'symbol', 'outputs': [{'internalType': 'string', 'name': '', 'type': 'string'}], 'stateMutability': 'view', 'type': 'function'}, {'inputs': [{'internalType': 'address', 'name': 'owner', 'type': 'address'}, {'internalType': 'uint256', 'name': 'serviceId', 'type': 'uint256'}], 'name': 'terminate', 'outputs': [{'internalType': 'bool', 'name': 'success', 'type': 'bool'}, {'internalType': 'uint256', 'name': 'refund', 'type': 'uint256'}], 'stateMutability': 'nonpayable', 'type': 'function'}, {'inputs': [{'internalType': 'uint256', 'name': 'index', 'type': 'uint256'}], 'name': 'tokenByIndex', 'outputs': [{'internalType': 'uint256', 'name': '', 'type': 'uint256'}], 'stateMutability': 'view', 'type': 'function'}, {'inputs': [{'internalType': 'address', 'name': 'owner', 'type': 'address'}, {'internalType': 'uint256', 'name': 'index', 'type': 'uint256'}], 'name': 'tokenOfOwnerByIndex', 'outputs': [{'internalType': 'uint256', 'name': '', 'type': 'uint256'}], 'stateMutability': 'view', 'type': 'function'}, {'inputs': [{'internalType': 'uint256', 'name': 'tokenId', 'type': 'uint256'}], 'name': 'tokenURI', 'outputs': [{'internalType': 'string', 'name': '', 'type': 'string'}], 'stateMutability': 'view', 'type': 'function'}, {'inputs': [], 'name': 'totalSupply', 'outputs': [{'internalType': 'uint256', 'name': '', 'type': 'uint256'}], 'stateMutability': 'view', 'type': 'function'}, {'inputs': [{'internalType': 'address', 'name': 'from', 'type': 'address'}, {'internalType': 'address', 'name': 'to', 'type': 'address'}, {'internalType': 'uint256', 'name': 'tokenId', 'type': 'uint256'}], 'name': 'transferFrom', 'outputs': [], 'stateMutability': 'nonpayable', 'type': 'function'}, {'inputs': [{'internalType': 'address', 'name': 'newOwner', 'type': 'address'}], 'name': 'transferOwnership', 'outputs': [], 'stateMutability': 'nonpayable', 'type': 'function'}, {'inputs': [{'internalType': 'address', 'name': 'operator', 'type': 'address'}, {'internalType': 'uint256', 'name': 'serviceId', 'type': 'uint256'}], 'name': 'unbond', 'outputs': [{'internalType': 'bool', 'name': 'success', 'type': 'bool'}, {'internalType': 'uint256', 'name': 'refund', 'type': 'uint256'}], 'stateMutability': 'nonpayable', 'type': 'function'}, {'inputs': [{'internalType': 'address', 'name': 'owner', 'type': 'address'}, {'internalType': 'string', 'name': 'name', 'type': 'string'}, {'internalType': 'string', 'name': 'description', 'type': 'string'}, {'components': [{'internalType': 'bytes32', 'name': 'hash', 'type': 'bytes32'}, {'internalType': 'uint8', 'name': 'hashFunction', 'type': 'uint8'}, {'internalType': 'uint8', 'name': 'size', 'type': 'uint8'}], 'internalType': 'struct IStructs.Multihash', 'name': 'configHash', 'type': 'tuple'}, {'internalType': 'uint256[]', 'name': 'agentIds', 'type': 'uint256[]'}, {'components': [{'internalType': 'uint256', 'name': 'slots', 'type': 'uint256'}, {'internalType': 'uint256', 'name': 'bond', 'type': 'uint256'}], 'internalType': 'struct IStructs.AgentParams[]', 'name': 'agentParams', 'type': 'tuple[]'}, {'internalType': 'uint256', 'name': 'threshold', 'type': 'uint256'}, {'internalType': 'uint256', 'name': 'serviceId', 'type': 'uint256'}], 'name': 'update', 'outputs': [{'internalType': 'bool', 'name': 'success', 'type': 'bool'}], 'stateMutability': 'nonpayable', 'type': 'function'}, {'stateMutability': 'payable', 'type': 'receive'}]
    w3 = Web3(Web3.HTTPProvider('http://127.0.0.1:8545'))
    contract_instance = w3.eth.contract(address=SERVICE_REGISTRY, abi=abi)
    x = contract_instance.functions.getServiceInfo(1).call()
    logging.error(x)
