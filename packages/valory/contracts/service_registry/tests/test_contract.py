# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022-2023 Valory AG
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
from typing import Any
from unittest import mock

import pytest
from aea_ledger_ethereum import EthereumCrypto
from aea_test_autonomy.base_test_classes.contracts import BaseRegistriesContractsTest
from aea_test_autonomy.docker.base import skip_docker_tests

from packages.valory.contracts.service_registry.contract import (
    DEPLOYED_BYTECODE_MD5_HASH_BY_CHAIN_ID,
    EXPECTED_CONTRACT_ADDRESS_BY_CHAIN_ID,
    ServiceRegistryContract,
)


PACKAGE_DIR = Path(__file__).parent.parent

SERVICE_REGISTRY_INVALID = "0x5aAeb6053F3E94C9b9A09f33669435E7Ef1BeAed"
VALID_SERVICE_ID = 1
INVALID_SERVICE_ID = 0
CHAIN_ID = 31337
AGENT_INSTANCES = [
    "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266",
    "0x70997970C51812dc3A010C7d01b50e0d17dc79C8",
    "0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC",
    "0x90F79bf6EB2c4f870365E785982E1f101E93b906",
]
OPERATOR = "0xBcd4042DE499D14e55001CcbB24a551F3b954096"
OPERATORS_MAPPING = dict.fromkeys(AGENT_INSTANCES, OPERATOR)


def event_filter_patch(event: str, return_value: Any) -> mock._patch:
    """Returns an event filter patch for the given event name."""
    return mock.patch.object(
        ServiceRegistryContract,
        "get_instance",
        return_value=mock.MagicMock(
            events=mock.MagicMock(
                **{
                    event: mock.MagicMock(
                        create_filter=lambda **_: mock.MagicMock(
                            get_all_entries=lambda *_: return_value
                        )
                    )
                }
            )
        ),
    )


class BaseServiceRegistryContractTest(BaseRegistriesContractsTest):
    """Base class for Service Registry contract tests"""

    contract: ServiceRegistryContract
    contract_address = EXPECTED_CONTRACT_ADDRESS_BY_CHAIN_ID[CHAIN_ID]
    invalid_contract_address = SERVICE_REGISTRY_INVALID
    path_to_contract = PACKAGE_DIR
    ledger_identifier = EthereumCrypto.identifier
    contract_directory = PACKAGE_DIR


@skip_docker_tests
class TestServiceRegistryContract(BaseServiceRegistryContractTest):
    """Test Service Registry Contract"""

    @pytest.mark.parametrize("valid_address", (True, False))
    def test_verify_contract(self, valid_address: bool) -> None:
        """Run verify test. If abi file is updated tests + addresses need updating"""
        bytecode = DEPLOYED_BYTECODE_MD5_HASH_BY_CHAIN_ID[CHAIN_ID]

        if valid_address:
            contract_address = self.contract_address
        else:
            contract_address = self.invalid_contract_address
            bytecode += "invalid"

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
        exists = self.contract.exists(
            self.ledger_api,
            self.contract_address,
            service_id,
        )

        assert exists is expected

    def test_get_agent_instances(self) -> None:
        """Test agent instances retrieval"""

        return_value = {
            "numAgentInstances": 4,
            "agentInstances": AGENT_INSTANCES,
        }

        assert self.contract_address is not None

        result = self.contract.get_agent_instances(
            self.ledger_api,
            self.contract_address,
            VALID_SERVICE_ID,
        )

        assert result == return_value

    def test_get_service_owner(self) -> None:
        """Test service owner retrieval."""
        service_owner = AGENT_INSTANCES[0]
        assert self.contract_address is not None

        actual = self.contract.get_service_owner(
            self.ledger_api,
            self.contract_address,
            VALID_SERVICE_ID,
        )

        expected = dict(service_owner=service_owner)
        assert expected == actual

    def test_get_token_uri(self) -> None:
        """Test `get_token_uri` method."""

        token_uri = self.contract.get_token_uri(
            self.ledger_api,
            self.contract_address,
            VALID_SERVICE_ID,
        )

        assert (
            token_uri
            == "https://gateway.autonolas.tech/ipfs/f017012205555555555555555555555555555555555555555555555555555555555555555"  # nosec
        )

    def test_get_service_information(self) -> None:
        """Test `test_get_service_information` method."""

        (
            security_deposit,
            multisig_address,
            ipfs_hash_for_config,
            threshold,
            max_number_of_agent_instances,
            number_of_agent_instances,
            service_state,
            list_of_cannonical_agents,
        ) = self.contract.get_service_information(
            self.ledger_api,
            self.contract_address,
            VALID_SERVICE_ID,
        )

        assert security_deposit == 10000000000000000
        assert multisig_address == "0x77b783e911F4398D75908Cc60C7138Bd1eFe35Fd"
        assert ipfs_hash_for_config == b"UUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUU"
        assert threshold == 3
        assert max_number_of_agent_instances == 4
        assert number_of_agent_instances == 4
        assert service_state == 4
        assert list_of_cannonical_agents == [1]

    def test_get_slash_data(self) -> None:
        """Test the `get_slash_data`."""
        result = self.contract.get_slash_data(
            self.ledger_api,
            self.contract_address,
            AGENT_INSTANCES,
            [0, 0, 0, 1],
            service_id=1,
        )

        assert result.get("data", b"") == (
            b"s\xb8\xb6\xa2\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
            b"\x00\x00\x00\x00\x00\x00\x00\x00`\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
            b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
            b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00"
            b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x04"
            b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xf3\x9f\xd6\xe5\x1a\xad\x88\xf6\xf4\xcej\xb8\x82ry\xcf"
            b'\xff\xb9"f\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00p\x99yp\xc5\x18\x12\xdc:\x01\x0c}\x01\xb5\x0e\r'
            b"\x17\xdcy\xc8\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00<D\xcd\xdd\xb6\xa9\x00\xfa+X]\xd2\x99\xe0="
            b"\x12\xfaB\x93\xbc\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x90\xf7\x9b\xf6\xeb,O\x87\x03e\xe7\x85"
            b"\x98.\x1f\x10\x1e\x93\xb9\x06\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
            b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x04\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
            b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
            b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
            b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
            b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
            b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01"
        ), "Contract did not return the expected data."

    def test_get_operator(self) -> None:
        """Test `get_operator` method."""
        for agent_instance, expected_operator in OPERATORS_MAPPING.items():
            actual_operator = (
                self.contract._get_operator(  # pylint: disable=protected-access
                    self.ledger_api,
                    self.contract_address,
                    agent_instance,
                )
            )
            assert actual_operator == expected_operator

    def test_get_operators_mapping(self) -> None:
        """Test `get_operator` method."""
        actual_mapping = self.contract.get_operators_mapping(
            self.ledger_api,
            self.contract_address,
            frozenset(OPERATORS_MAPPING.keys()),
        )
        assert actual_mapping == OPERATORS_MAPPING
