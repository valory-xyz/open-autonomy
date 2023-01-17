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

"""Helper functions to manage on-chain services"""

from typing import Optional

from aea.crypto.base import Crypto, LedgerApi
from requests.exceptions import ConnectionError as RequestsConnectionError

from autonomy.chain.base import registry_contracts
from autonomy.chain.config import ChainType, ContractConfigs
from autonomy.chain.constants import (
    GNOSIS_SAFE_MULTISIG_CONTRACT,
    SERVICE_MANAGER_CONTRACT,
)
from autonomy.chain.exceptions import (
    InstanceRegistrationFailed,
    ServiceDeployFailed,
    ServiceRegistrationFailed,
)
from autonomy.chain.mint import transact


DEFAULT_DEPLOY_PAYLOAD = "0x"


def activate_service(
    ledger_api: LedgerApi,
    crypto: Crypto,
    chain_type: ChainType,
    service_id: int,
    bond_value: int,
) -> None:
    """Activate service."""

    try:
        tx = registry_contracts.service_manager.get_activate_registration_transaction(
            ledger_api=ledger_api,
            contract_address=ContractConfigs.get(
                SERVICE_MANAGER_CONTRACT.name
            ).contracts[chain_type],
            owner=crypto.address,
            service_id=service_id,
            security_deposit=bond_value,
        )

        transact(ledger_api=ledger_api, crypto=crypto, tx=tx)
    except RequestsConnectionError as e:
        raise ServiceRegistrationFailed(
            "Service registration failed; Error connecting to the RPC"
        ) from e


def register_instance(  # pylint: disable=too-many-arguments
    ledger_api: LedgerApi,
    crypto: Crypto,
    chain_type: ChainType,
    service_id: int,
    instance: str,
    agent_id: int,
    bond_value: int,
) -> None:
    """Activate service."""

    try:
        tx = registry_contracts.service_manager.get_register_instance_transaction(
            ledger_api=ledger_api,
            contract_address=ContractConfigs.get(
                SERVICE_MANAGER_CONTRACT.name
            ).contracts[chain_type],
            owner=crypto.address,
            service_id=service_id,
            instances=[
                instance,
            ],
            agent_ids=[
                agent_id,
            ],
            security_deposit=bond_value,
        )

        transact(ledger_api=ledger_api, crypto=crypto, tx=tx)
    except RequestsConnectionError as e:
        raise InstanceRegistrationFailed(
            "Instance registration failed; Error connecting to the RPC"
        ) from e


def deploy_service(
    ledger_api: LedgerApi,
    crypto: Crypto,
    chain_type: ChainType,
    service_id: int,
    deployment_payload: Optional[str] = None,
) -> None:
    """Activate service."""

    deployment_payload = deployment_payload or DEFAULT_DEPLOY_PAYLOAD

    try:
        tx = registry_contracts.service_manager.get_service_deploy_transaction(
            ledger_api=ledger_api,
            contract_address=ContractConfigs.get(
                SERVICE_MANAGER_CONTRACT.name
            ).contracts[chain_type],
            owner=crypto.address,
            service_id=service_id,
            gnosis_safe_multisig=ContractConfigs.get(
                GNOSIS_SAFE_MULTISIG_CONTRACT.name
            ).contracts[chain_type],
            deployment_payload=deployment_payload,
        )
        transact(ledger_api=ledger_api, crypto=crypto, tx=tx)
    except RequestsConnectionError as e:
        raise ServiceDeployFailed(
            "Service deploymeny failed; Cannot connect to the RPC"
        ) from e
