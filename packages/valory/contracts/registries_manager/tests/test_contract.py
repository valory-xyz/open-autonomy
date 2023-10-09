# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2023 Valory AG
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

"""Test for contract module."""

from pathlib import Path

from aea_test_autonomy.base_test_classes.contracts import BaseRegistriesContractsTest
from aea_test_autonomy.docker.base import skip_docker_tests
from aea_test_autonomy.docker.registries import REGISTRIES_MANAGER

from packages.valory.contracts.registries_manager.contract import (
    RegistriesManagerContract,
)


PACKAGE_DIR = Path(__file__).parent.parent

METADATA_HASH = "0xaaca27f6156089376fd85900d511c7570b6c9b0f6afc64576aac5aa0da8de92d"


@skip_docker_tests
class TestRegistriesManager(BaseRegistriesContractsTest):
    """Test registries manager."""

    contract: RegistriesManagerContract
    contract_address = REGISTRIES_MANAGER
    contract_directory = PACKAGE_DIR

    def test_get_create_transaction(self) -> None:
        """Test `get_create_transaction` method."""

        tx = self.contract.get_create_transaction(
            ledger_api=self.ledger_api,
            contract_address=self.contract_address,
            metadata_hash=METADATA_HASH,
            component_type=RegistriesManagerContract.UnitType.COMPONENT,
            owner=self.deployer_crypto.address,
            sender=self.deployer_crypto.address,
        )

        assert all(
            [
                key
                in [
                    "chainId",
                    "nonce",
                    "value",
                    "gas",
                    "maxFeePerGas",
                    "maxPriorityFeePerGas",
                    "to",
                    "data",
                ]
                for key in tx.keys()
            ]
        )

    def test_get_update_hash_transaction(self) -> None:
        """Test `get_update_hash_transaction` method."""

        tx = self.contract.get_update_hash_transaction(
            ledger_api=self.ledger_api,
            contract_address=self.contract_address,
            metadata_hash=METADATA_HASH,
            component_type=RegistriesManagerContract.UnitType.COMPONENT,
            unit_id=3,
            sender=self.deployer_crypto.address,
        )

        assert all(
            [
                key
                in [
                    "chainId",
                    "nonce",
                    "value",
                    "gas",
                    "maxFeePerGas",
                    "maxPriorityFeePerGas",
                    "to",
                    "data",
                ]
                for key in tx.keys()
            ]
        )
