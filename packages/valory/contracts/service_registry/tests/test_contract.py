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
from typing import Any, List, Optional, Set
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


def event_filter_patch(event: str, return_value: Any) -> mock._patch:
    """Returns an event filter patch for the given event name."""
    return mock.patch.object(
        ServiceRegistryContract,
        "get_instance",
        return_value=mock.MagicMock(
            events=mock.MagicMock(
                **{
                    event: mock.MagicMock(
                        createFilter=lambda **_: mock.MagicMock(
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
            "agentInstances": [
                "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266",
                "0x70997970C51812dc3A010C7d01b50e0d17dc79C8",
                "0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC",
                "0x90F79bf6EB2c4f870365E785982E1f101E93b906",
            ],
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
        service_owner = "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266"
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
        assert multisig_address == "0xD8dE647170163a981bb3Fdb2063583eAcF7D55AC"
        assert ipfs_hash_for_config == b"UUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUU"
        assert threshold == 3
        assert max_number_of_agent_instances == 4
        assert number_of_agent_instances == 4
        assert service_state == 4
        assert list_of_cannonical_agents == [1]

    @pytest.mark.parametrize(
        ("return_value", "assert_value"),
        (
            ([], None),
            (
                [
                    {
                        "args": {
                            "serviceId": 1,
                        }
                    }
                ],
                1,
            ),
        ),
    )
    def test_filter_token_id_from_emitted_events(
        self, return_value: List, assert_value: Optional[int]
    ) -> None:
        """Test `filter_token_id_from_emitted_events` method"""

        with event_filter_patch(event="CreateService", return_value=return_value):
            token_id = self.contract.filter_token_id_from_emitted_events(
                ledger_api=self.ledger_api,
                contract_address=self.contract_address,
            )

            if assert_value is None:
                assert token_id is None
            else:
                assert token_id == 1

    @pytest.mark.parametrize(
        ("return_value", "assert_value"),
        (
            ([], False),
            (
                [
                    {
                        "args": {
                            "serviceId": 0,
                        }
                    }
                ],
                True,
            ),
        ),
    )
    def test_verify_service_has_been_activated(
        self, return_value: List, assert_value: bool
    ) -> None:
        """Test `verify_service_has_been_activated` method."""

        with event_filter_patch(
            event="ActivateRegistration", return_value=return_value
        ):
            success = self.contract.verify_service_has_been_activated(
                ledger_api=self.ledger_api,
                contract_address=self.contract_address,
                service_id=0,
            )

            assert success is assert_value

    @pytest.mark.parametrize(
        ("return_value", "assert_value"),
        (
            ([], set()),
            (
                [{"args": {"serviceId": 0, "agentInstance": "0x"}}],
                {"0x"},
            ),
        ),
    )
    def test_verify_agent_instance_registration(
        self, return_value: List, assert_value: Set[str]
    ) -> None:
        """Test `verify_agent_instance_registration` method."""

        with event_filter_patch(event="RegisterInstance", return_value=return_value):
            successful = self.contract.verify_agent_instance_registration(
                ledger_api=self.ledger_api,
                contract_address=self.contract_address,
                service_id=0,
                instance_check={"0x"},
            )

            assert successful == assert_value

    @pytest.mark.parametrize(
        ("return_value", "assert_value"),
        (
            ([], False),
            (
                [
                    {
                        "args": {
                            "serviceId": 0,
                        }
                    }
                ],
                True,
            ),
        ),
    )
    def test_verify_service_has_been_deployed(
        self, return_value: List, assert_value: bool
    ) -> None:
        """Test `verify_service_has_been_deployed` method."""

        with event_filter_patch(event="DeployService", return_value=return_value):
            success = self.contract.verify_service_has_been_deployed(
                ledger_api=self.ledger_api,
                contract_address=self.contract_address,
                service_id=0,
            )

            assert success is assert_value
