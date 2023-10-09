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
from unittest import mock

from aea_test_autonomy.base_test_classes.contracts import BaseRegistriesContractsTest
from aea_test_autonomy.docker.base import skip_docker_tests
from aea_test_autonomy.docker.registries import SERVICE_MANAGER

from packages.valory.contracts.service_manager.contract import (
    JSONLike,
    ServiceManagerContract,
)


PACKAGE_DIR = Path(__file__).parent.parent

METADATA_HASH = "0xaaca27f6156089376fd85900d511c7570b6c9b0f6afc64576aac5aa0da8de92d"
AGENT_ID = 1
NUMBER_OF_SLOTS = 1
COST_OF_BOND = 1000
THRESHOLD = 3


@skip_docker_tests
class TestServiceManager(BaseRegistriesContractsTest):
    """Test service manager."""

    contract: ServiceManagerContract
    contract_address = SERVICE_MANAGER
    contract_directory = PACKAGE_DIR

    def make_transaction(self, tx: JSONLike) -> JSONLike:
        """Make transaction."""
        tx_signed = self.deployer_crypto.sign_transaction(transaction=tx)
        tx_digest = self.ledger_api.send_signed_transaction(tx_signed=tx_signed)

        return self.ledger_api.get_transaction_receipt(tx_digest=tx_digest)

    def test_get_create_transaction(self) -> None:
        """Test `get_create_transaction` method."""
        tx = self.contract.get_create_transaction(
            ledger_api=self.ledger_api,
            contract_address=self.contract_address,
            owner=self.deployer_crypto.address,
            sender=self.deployer_crypto.address,
            metadata_hash=METADATA_HASH,
            agent_ids=[AGENT_ID],
            agent_params=[[NUMBER_OF_SLOTS, COST_OF_BOND]],
            threshold=THRESHOLD,
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

    def test_get_create_transaction_l2(self) -> None:
        """Test `get_create_transaction` method."""

        with mock.patch.object(
            self.ledger_api.api,
            "eth",
            return_value=mock.MagicMock(chain_id=100),
        ):
            tx = self.contract.get_create_transaction(
                ledger_api=self.ledger_api,
                contract_address=self.contract_address,
                owner=self.deployer_crypto.address,
                sender=self.deployer_crypto.address,
                metadata_hash=METADATA_HASH,
                agent_ids=[AGENT_ID],
                agent_params=[[NUMBER_OF_SLOTS, COST_OF_BOND]],
                threshold=THRESHOLD,
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

    def test_get_update_transaction(self) -> None:
        """Test `get_update_transaction` method."""
        tx = self.contract.get_update_transaction(
            ledger_api=self.ledger_api,
            contract_address=self.contract_address,
            sender=self.deployer_crypto.address,
            service_id=2,
            metadata_hash=METADATA_HASH,
            agent_ids=[AGENT_ID],
            agent_params=[[NUMBER_OF_SLOTS, COST_OF_BOND]],
            threshold=THRESHOLD,
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

    def test_get_activate_registration_transaction(self) -> None:
        """Test `get_activate_registration_transaction` method"""

        tx = self.contract.get_activate_registration_transaction(
            ledger_api=self.ledger_api,
            contract_address=self.contract_address,
            owner=self.deployer_crypto.address,
            service_id=1,
            security_deposit=COST_OF_BOND,
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

    def test_get_service_deploy_transaction(self) -> None:
        """Test `get_service_deploy_transaction` method"""

        tx = self.contract.get_service_deploy_transaction(
            ledger_api=self.ledger_api,
            contract_address=self.contract_address,
            owner=self.deployer_crypto.address,
            service_id=1,
            gnosis_safe_multisig="0x0E801D84Fa97b50751Dbf25036d067dCf18858bF",
            deployment_payload="0x",
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

    def test_get_terminate_service_transaction(self) -> None:
        """Test `get_terminate_service_transaction` method"""

        tx = self.contract.get_terminate_service_transaction(
            ledger_api=self.ledger_api,
            contract_address=self.contract_address,
            owner=self.deployer_crypto.address,
            service_id=1,
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

    def test_get_unbond_service_transaction(self) -> None:
        """Test `get_unbond_service_transaction` method"""

        tx = self.contract.get_unbond_service_transaction(
            ledger_api=self.ledger_api,
            contract_address=self.contract_address,
            owner=self.deployer_crypto.address,
            service_id=1,
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
