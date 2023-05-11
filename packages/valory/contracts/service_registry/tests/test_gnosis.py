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

"""Tests for valory/service_registry contract on Gnosis."""

from pathlib import Path
from typing import List, Optional, Set

import pytest
from aea.crypto.registries import ledger_apis_registry
from aea_ledger_ethereum import (
    DEFAULT_CURRENCY_DENOM,
    DEFAULT_EIP1559_STRATEGY,
    DEFAULT_GAS_STATION_STRATEGY,
    EIP1559,
)
from aea_test_autonomy.base_test_classes.contracts import BaseContractTest
from web3.exceptions import ContractLogicError

from packages.valory.contracts.service_registry.contract import (
    EXPECTED_CONTRACT_ADDRESS_BY_CHAIN_ID,
    ServiceRegistryContract,
)


PACKAGE_DIR = Path(__file__).parents[1]
GNOSIS_PUBLIC_RPC = "https://rpc.gnosis.gateway.fm"
GNOSIS_CHAIN_ID = 100
GNOSIS_REGISTRY_ADDRESS = EXPECTED_CONTRACT_ADDRESS_BY_CHAIN_ID[GNOSIS_CHAIN_ID]


class TestServiceRegistryContract(BaseContractTest):
    """Test Service Registry Contract"""

    deploy_contract: bool = False
    contract: ServiceRegistryContract
    contract_address: str = EXPECTED_CONTRACT_ADDRESS_BY_CHAIN_ID[GNOSIS_CHAIN_ID]
    contract_directory: Path = PACKAGE_DIR

    @classmethod
    def setup_class(
        cls,
    ) -> None:
        """Setup test class."""
        dummy_pkey = (
            "0x47e179ec197488593b187f80a00eb0da91f1b9d0b13f8733639f19c30a32926a"
        )
        cls._setup_class(key_pairs=[["", dummy_pkey]], url="")

        gnosis_config = {
            # public RPC
            "address": GNOSIS_PUBLIC_RPC,
            "chain_id": GNOSIS_CHAIN_ID,
            "denom": DEFAULT_CURRENCY_DENOM,
            "default_gas_price_strategy": EIP1559,
            "gas_price_strategies": {
                "gas_station": DEFAULT_GAS_STATION_STRATEGY,
                "eip1559": DEFAULT_EIP1559_STRATEGY,
            },
        }

        cls.ledger_api = ledger_apis_registry.make(
            cls.identifier,
            **gnosis_config,
        )

    def test_verify_contract(self) -> None:
        """Run verification test."""

        result = self.contract.verify_contract(
            self.ledger_api,
            GNOSIS_REGISTRY_ADDRESS,
        )

        assert result["verified"] is True

    @pytest.mark.parametrize("service_id, exists", ((0, False), (1, False)))
    def test_exists(self, service_id: int, exists: bool) -> None:
        """Test exists."""

        result = self.contract.exists(
            self.ledger_api, GNOSIS_REGISTRY_ADDRESS, service_id
        )

        assert result is exists

    @pytest.mark.parametrize("service_id, agent_instances", ((0, []), (1, [])))
    def test_get_agent_instances(self, service_id: int, agent_instances: List) -> None:
        """Test `get_agent_instances`."""

        result = self.contract.get_agent_instances(
            self.ledger_api, GNOSIS_REGISTRY_ADDRESS, service_id
        )

        assert result == {
            "numAgentInstances": len(agent_instances),
            "agentInstances": agent_instances,
        }

    @pytest.mark.parametrize("service_id, owner", ((0, None), (1, None)))
    def test_get_service_owner(self, service_id: int, owner: Optional[str]) -> None:
        """Test `get_service_owner`."""

        if owner is not None:
            result = self.contract.get_service_owner(
                self.ledger_api, GNOSIS_REGISTRY_ADDRESS, service_id
            )

            assert result == {"service_owner": owner}
            return

        with pytest.raises(ContractLogicError):
            self.contract.get_service_owner(
                self.ledger_api, GNOSIS_REGISTRY_ADDRESS, service_id
            )

    @pytest.mark.parametrize(
        "service_id, info",
        (
            (
                0,
                (
                    0,
                    "0x0000000000000000000000000000000000000000",
                    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
                    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00",
                    0,
                    0,
                    0,
                    0,
                    [],
                ),
            ),
            (
                1,
                (
                    0,
                    "0x0000000000000000000000000000000000000000",
                    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
                    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00",
                    0,
                    0,
                    0,
                    0,
                    [],
                ),
            ),
        ),
    )
    def test_get_service_information(self, service_id: int, info: List) -> None:
        """Test `get_service_information`."""

        result = self.contract.get_service_information(
            self.ledger_api, GNOSIS_REGISTRY_ADDRESS, service_id
        )

        assert result == info

    @pytest.mark.parametrize(
        "service_id, uri",
        (
            (
                0,
                "https://gateway.autonolas.tech/ipfs/"
                "f017012200000000000000000000000000000000000000000000000000000000000000000",
            ),
            (
                1,
                "https://gateway.autonolas.tech/ipfs/"
                "f017012200000000000000000000000000000000000000000000000000000000000000000",
            ),
        ),
    )
    def test_get_get_token_uri(self, service_id: int, uri: str) -> None:
        """Test `get_token_uri`."""

        result = self.contract.get_token_uri(
            self.ledger_api, GNOSIS_REGISTRY_ADDRESS, service_id
        )

        assert result == uri

    @pytest.mark.skip(
        "Getting `The method eth_newFilter does not exist/is not available`."
    )
    def test_filter_token_id_from_emitted_events(self) -> None:
        """Test filter_token_id_from_emitted_events."""

        result = self.contract.filter_token_id_from_emitted_events(
            self.ledger_api, GNOSIS_REGISTRY_ADDRESS
        )

        assert result == 0

    @pytest.mark.parametrize("service_id, activated", ((0, False), (1, False)))
    @pytest.mark.skip(
        "Getting `The method eth_newFilter does not exist/is not available`."
    )
    def test_verify_service_has_been_activated(
        self, service_id: int, activated: bool
    ) -> None:
        """Test verify_service_has_been_activated."""

        result = self.contract.verify_service_has_been_activated(
            self.ledger_api, GNOSIS_REGISTRY_ADDRESS, service_id
        )

        assert result is activated

    @pytest.mark.parametrize("service_id, instance_check", ((0, {}),))
    @pytest.mark.skip(
        "No instances to check. "
        "Moreover, the issue with `eth_newFilter` would occur because of using `createFilter`:"
        "`The method eth_newFilter does not exist/is not available`"
    )
    def test_verify_agent_instance_registration(
        self, service_id: int, instance_check: Set
    ) -> None:
        """Test verify_agent_instance_registration."""

        result = self.contract.verify_agent_instance_registration(
            self.ledger_api, GNOSIS_REGISTRY_ADDRESS, service_id, instance_check
        )

        assert result is instance_check

    @pytest.mark.parametrize("service_id, deployed", ((0, False), (1, False)))
    @pytest.mark.skip(
        "Getting `The method eth_newFilter does not exist/is not available`."
    )
    def test_verify_service_has_been_deployed(
        self, service_id: int, deployed: bool
    ) -> None:
        """Test verify_service_has_been_deployed."""

        result = self.contract.verify_service_has_been_deployed(
            self.ledger_api, GNOSIS_REGISTRY_ADDRESS, service_id
        )

        assert result is deployed
