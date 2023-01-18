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

from typing import Dict, List, Optional, Tuple

from aea.crypto.base import Crypto, LedgerApi
from requests.exceptions import ConnectionError as RequestsConnectionError
from web3.exceptions import ContractLogicError

from autonomy.chain.base import ServiceState, registry_contracts
from autonomy.chain.config import ChainType, ContractConfigs
from autonomy.chain.constants import (
    GNOSIS_SAFE_MULTISIG_CONTRACT,
    SERVICE_MANAGER_CONTRACT,
    SERVICE_REGISTRY_CONTRACT,
)
from autonomy.chain.exceptions import (
    InstanceRegistrationFailed,
    ServiceDeployFailed,
    ServiceRegistrationFailed,
)
from autonomy.chain.mint import transact


DEFAULT_DEPLOY_PAYLOAD = "0x"

ServiceInfo = Tuple[int, str, bytes, int, int, int, int, List[int]]


def get_agent_instances(
    ledger_api: LedgerApi, chain_type: ChainType, token_id: int
) -> Dict:
    """
    Get the list of agent instances.

    :param ledger_api: `aea.crypto.LedgerApi` object for interacting with the chain
    :param chain_type: Chain type
    :param token_id: Token ID pointing to the on-chain service
    :returns: number of agent instances and the list of registered addressed
    """

    return registry_contracts.service_registry.get_agent_instances(
        ledger_api=ledger_api,
        contract_address=ContractConfigs.get(SERVICE_REGISTRY_CONTRACT.name).contracts[
            chain_type
        ],
        service_id=token_id,
    )


def get_service_info(
    ledger_api: LedgerApi, chain_type: ChainType, token_id: int
) -> ServiceInfo:
    """
    Returns service info.

    :param ledger_api: `aea.crypto.LedgerApi` object for interacting with the chain
    :param chain_type: Chain type
    :param token_id: Token ID pointing to the on-chain service
    :returns: security deposit, multisig address, IPFS hash for config,
            threshold, max number of agent instances, number of agent instances,
            service state, list of cannonical agents
    """

    return registry_contracts.service_registry.get_service_information(
        ledger_api=ledger_api,
        contract_address=ContractConfigs.get(SERVICE_REGISTRY_CONTRACT.name).contracts[
            chain_type
        ],
        token_id=token_id,
    )


def activate_service(
    ledger_api: LedgerApi,
    crypto: Crypto,
    chain_type: ChainType,
    service_id: int,
) -> None:
    """Activate service."""

    (cost_of_bond, *_, service_state, _,) = get_service_info(
        ledger_api=ledger_api, chain_type=chain_type, token_id=service_id
    )

    if service_state == ServiceState.NON_EXISTENT.value:
        raise ServiceRegistrationFailed("Service does not exist")

    if service_state != ServiceState.PRE_REGISTRATION.value:
        raise ServiceRegistrationFailed("Service must be inactive")

    try:
        tx = registry_contracts.service_manager.get_activate_registration_transaction(
            ledger_api=ledger_api,
            contract_address=ContractConfigs.get(
                SERVICE_MANAGER_CONTRACT.name
            ).contracts[chain_type],
            owner=crypto.address,
            service_id=service_id,
            security_deposit=cost_of_bond,
            raise_on_try=True,
        )
        transact(ledger_api=ledger_api, crypto=crypto, tx=tx)
    except RequestsConnectionError as e:
        raise ServiceRegistrationFailed(
            "Service activation failed; Error connecting to the RPC"
        ) from e
    except ContractLogicError as e:
        raise ServiceRegistrationFailed(f"Service activation failed; {e}") from e


def register_instance(  # pylint: disable=too-many-arguments
    ledger_api: LedgerApi,
    crypto: Crypto,
    chain_type: ChainType,
    service_id: int,
    instance: str,
    agent_id: int,
) -> None:
    """Activate service."""

    (cost_of_bond, *_, service_state, _,) = get_service_info(
        ledger_api=ledger_api,
        chain_type=chain_type,
        token_id=service_id,
    )

    if service_state == ServiceState.NON_EXISTENT.value:
        raise InstanceRegistrationFailed("Service does not exist")

    if service_state != ServiceState.ACTIVE_REGISTRATION.value:
        raise InstanceRegistrationFailed("Service needs to be in active state")

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
            security_deposit=cost_of_bond,
            raise_on_try=True,
        )

        transact(ledger_api=ledger_api, crypto=crypto, tx=tx)
    except RequestsConnectionError as e:
        raise InstanceRegistrationFailed(
            "Instance registration failed; Error connecting to the RPC"
        ) from e
    except ContractLogicError as e:
        raise InstanceRegistrationFailed(f"Instance registration failed; {e}") from e


def deploy_service(
    ledger_api: LedgerApi,
    crypto: Crypto,
    chain_type: ChainType,
    service_id: int,
    deployment_payload: Optional[str] = None,
) -> None:
    """Activate service."""

    deployment_payload = deployment_payload or DEFAULT_DEPLOY_PAYLOAD
    (*_, service_state, _,) = get_service_info(
        ledger_api=ledger_api,
        chain_type=chain_type,
        token_id=service_id,
    )

    if service_state == ServiceState.NON_EXISTENT.value:
        raise ServiceDeployFailed("Service does not exist")

    if service_state != ServiceState.FINISHED_REGISTRATION.value:
        raise ServiceDeployFailed("Service needs to be in finished registration state")

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
            raise_on_try=True,
        )
        transact(ledger_api=ledger_api, crypto=crypto, tx=tx)
    except RequestsConnectionError as e:
        raise ServiceDeployFailed(
            "Service deployment failed; Cannot connect to the RPC"
        ) from e
    except ContractLogicError as e:
        raise ServiceDeployFailed(f"Service deployment failed; {e}") from e
