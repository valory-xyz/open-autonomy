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

from pathlib import Path
from typing import Any, Dict, List, Tuple
from unittest import mock

import pytest
from aea_ledger_ethereum import EthereumCrypto
from web3 import Web3

from packages.valory.contracts.service_registry.contract import (
    PUBLIC_ID,
    ServiceRegistryContract,
)

from tests.conftest import ROOT_DIR
from tests.test_contracts.base import BaseGanacheContractTest


Address = str  # hex
ConfigHash = Tuple[bytes, int, int]
AgentParams = Tuple[int, int]

ADDRESS_ZERO = "0x0000000000000000000000000000000000000000"
AGENT_REGISTRY = "0xe7f1725E7734CE288F8367e1Bb143E90bb3F0512"
OWNER = "0x8626f6940E2eb28930eFb4CeF49B2d1F2C9C1199"
SERVICE_REGISTRY = "0xA51c1fc2f0D1a1b8494Ed1FE312d7C3a78Ed91C0"

NONCE = 0
CHAIN_ID = 31337


class BaseServiceRegistryContractTest(BaseGanacheContractTest):
    """Base class for Service Registry contract tests"""

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

        expected_keys = {
            "gas",
            "chainId",
            "value",
            "nonce",
            "maxFeePerGas",
            "maxPriorityFeePerGas",
            "data",
            "from",
        }

        tx = self.contract.get_deploy_transaction(
            ledger_api=self.ledger_api,
            deployer_address=str(self.deployer_crypto.address),
            **self.deployment_kwargs(),
        )

        assert isinstance(tx, dict)
        assert len(tx) == 8
        assert not expected_keys.symmetric_difference(tx)
        assert tx["data"].startswith("0x") and len(tx["data"]) > 2

    def test_verify_contract(self) -> None:
        """Run verify test. If abi file is updated tests + addresses need updating"""

        assert self.contract_address is not None
        result = self.contract.verify_contract(
            ledger_api=self.ledger_api,
            contract_address=self.contract_address,
        )

        assert result["verified"] is True

    @pytest.mark.parametrize("service_id, expected", [(0, False), (1, True)])
    def test_exists(self, service_id: int, expected: int) -> None:
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

    def test_get_service_info(self) -> None:
        """Test service info retrieval"""

        return_value = dict(
            owner=OWNER,
            name="service name",
            description="service description",
            config_hash=(b'UUUUUUUUUUUUUUUUUUUUUUUUUUUUUUU"', 18, 32),
            threshold=7,
            num_agent_ids=2,
            agent_ids=[1, 2],
            agent_params=[(3, 1000), (4, 1000)],
            num_agent_instances=0,
            agent_instances=[],
            multisig=ADDRESS_ZERO,
        )

        assert self.contract_address is not None

        with mock.patch.object(
            self.ledger_api,
            "contract_method_call",
            return_value=list(return_value.values()),
        ):
            result = self.contract.get_service_info(
                ledger_api=self.ledger_api,
                contract_address=self.contract_address,
                service_id=1,
            )

        assert result == return_value
