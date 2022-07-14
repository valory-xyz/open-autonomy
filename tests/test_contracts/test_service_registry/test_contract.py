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
import hashlib
from pathlib import Path
from typing import Dict, cast
from unittest import mock
from unittest.mock import MagicMock

import pytest
from aea.test_tools.test_contract import BaseContractTestCase
from aea_ledger_ethereum import EthereumCrypto

from packages.valory.contracts.service_registry.contract import (
    DEPLOYED_BYTECODE_MD5_HASH,
    PUBLIC_ID,
    ServiceRegistryContract,
)

from tests.conftest import ROOT_DIR
from tests.helpers.docker.base import skip_docker_tests


SERVICE_REGISTRY = "0x0DCd1Bf9A1b36cE34237eEaFef220932846BCD82"
SERVICE_REGISTRY_INVALID = "0x5aAeb6053F3E94C9b9A09f33669435E7Ef1BeAed"
VALID_SERVICE_ID = 1
INVALID_SERVICE_ID = 0


class BaseServiceRegistryContractTest(BaseContractTestCase):
    """Base class for Service Registry contract tests"""

    contract_address = SERVICE_REGISTRY
    invalid_contract_address = SERVICE_REGISTRY_INVALID
    path_to_contract = Path(
        ROOT_DIR, "packages", PUBLIC_ID.author, "contracts", PUBLIC_ID.name
    )
    ledger_identifier = EthereumCrypto.identifier

    @classmethod
    def finish_contract_deployment(cls) -> str:
        """Finish the contract deployment."""
        return cls.contract_address

    @classmethod
    def _deploy_contract(cls, contract, ledger_api, deployer_crypto, gas) -> Dict:  # type: ignore
        """Deploy contract."""
        return {}

    @property
    def contract(self) -> ServiceRegistryContract:
        """Get the contract."""
        return cast(ServiceRegistryContract, super().contract)


@skip_docker_tests
class TestServiceRegistryContract(BaseServiceRegistryContractTest):
    """Test Service Registry Contract"""

    @pytest.mark.parametrize("valid_address", (True, False))
    def test_verify_contract(self, valid_address: bool) -> None:
        """Run verify test. If abi file is updated tests + addresses need updating"""
        if valid_address:
            contract_address = self.contract_address
            bytecode = DEPLOYED_BYTECODE_MD5_HASH
        else:
            contract_address = self.invalid_contract_address
            bytecode = DEPLOYED_BYTECODE_MD5_HASH + "invalid"

        with mock.patch.object(
            self.ledger_api.api.manager, "request_blocking", return_value=0
        ), mock.patch.object(
            hashlib, "sha512", return_value=MagicMock(hexdigest=lambda: bytecode)
        ):
            result = self.contract.verify_contract(
                self.ledger_api,
                contract_address,
            )

        assert result["verified"] is valid_address, result

    @pytest.mark.parametrize(
        "service_id, expected", [(INVALID_SERVICE_ID, False), (VALID_SERVICE_ID, True)]
    )
    def test_exists(self, service_id: int, expected: int) -> None:
        """Test whether service id exists"""

        with mock.patch.object(
            self.ledger_api,
            "contract_method_call",
            return_value=expected,
        ):
            exists = self.contract.exists(
                self.ledger_api,
                self.contract_address,
                service_id,
            )

        assert exists is expected

    def test_get_agent_instances(self) -> None:
        """Test agent instances retrieval"""

        return_value = dict(
            numAgentInstances=0,
            agentInstances=[],
        )

        assert self.contract_address is not None

        with mock.patch.object(
            self.ledger_api,
            "contract_method_call",
            return_value=list(return_value.values()),
        ):
            result = self.contract.get_agent_instances(
                self.ledger_api,
                self.contract_address,
                VALID_SERVICE_ID,
            )

        assert result == return_value
