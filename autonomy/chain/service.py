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

import datetime
import time
from typing import Callable, Dict, List, Optional, Tuple

from aea.crypto.base import Crypto, LedgerApi
from requests.exceptions import ConnectionError as RequestsConnectionError

from autonomy.chain.base import ServiceState, registry_contracts
from autonomy.chain.config import ChainType, ContractConfigs
from autonomy.chain.constants import (
    EVENT_VERIFICATION_TIMEOUT,
    GNOSIS_SAFE_MULTISIG_CONTRACT,
    SERVICE_MANAGER_CONTRACT,
    SERVICE_REGISTRY_CONTRACT,
)
from autonomy.chain.exceptions import (
    InstanceRegistrationFailed,
    ServiceDeployFailed,
    ServiceRegistrationFailed,
    TerminateServiceFailed,
    UnbondServiceFailed,
)
from autonomy.chain.mint import transact


try:
    from web3.exceptions import Web3Exception
except (ModuleNotFoundError, ImportError):
    Web3Exception = Exception


DEFAULT_DEPLOY_PAYLOAD = "0x0000000000000000000000000000000000000000f48f2b2d2a534e402487b3ee7c18c33aec0fe5e4000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"

ServiceInfo = Tuple[int, str, bytes, int, int, int, int, List[int]]


def get_default_delployment_payload() -> str:
    """Return default deployment payload."""
    return DEFAULT_DEPLOY_PAYLOAD + int(time.time()).to_bytes(32, "big").hex()


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


def wait_for_success_event(
    success_check: Callable[[], bool],
    message: str = "Timeout error",
    timeout: Optional[float] = None,
    sleep: float = 1.0,
) -> None:
    """Wait for success event."""

    timeout = timeout or EVENT_VERIFICATION_TIMEOUT
    deadline = datetime.datetime.now() + datetime.timedelta(seconds=timeout)
    while datetime.datetime.now() < deadline:
        if success_check():
            return
        time.sleep(sleep)
    raise TimeoutError(message)


def wait_for_agent_instance_registration(
    ledger_api: LedgerApi,
    chain_type: ChainType,
    service_id: int,
    instances: List[str],
    timeout: Optional[float] = None,
) -> None:
    """Wait for agent instance registration."""

    timeout = timeout or EVENT_VERIFICATION_TIMEOUT
    deadline = datetime.datetime.now() + datetime.timedelta(seconds=timeout)
    instance_check = set(instances)

    while datetime.datetime.now() < deadline:
        successful_instances = (
            registry_contracts.service_registry.verify_agent_instance_registration(
                ledger_api=ledger_api,
                contract_address=ContractConfigs.get(
                    SERVICE_REGISTRY_CONTRACT.name
                ).contracts[chain_type],
                service_id=service_id,
                instance_check=instance_check,
            )
        )

        instance_check = instance_check.difference(successful_instances)
        if len(instance_check) == 0:
            return

    raise TimeoutError(
        f"Could not verify the instance registration for {instance_check} in given time"
    )


def activate_service(
    ledger_api: LedgerApi,
    crypto: Crypto,
    chain_type: ChainType,
    service_id: int,
    timeout: Optional[float] = None,
) -> None:
    """
    Activate service.

    Once you have minted the service on-chain, you'll have to activate the service
    before you can proceed further.

    :param ledger_api: `aea.crypto.LedgerApi` object for interacting with the chain
    :param crypto: `aea.crypto.Crypto` object which has a funded key
    :param chain_type: Chain type
    :param service_id: Service ID retrieved after minting a service
    :param timeout: Time to wait for activation event to emit
    """

    (
        cost_of_bond,
        *_,
        service_state,
        _,
    ) = get_service_info(
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
    except ValueError as e:
        raise ServiceRegistrationFailed(f"Service activation failed; {e}") from e

    try:

        def success_check() -> bool:
            """Success check"""
            return (
                registry_contracts.service_registry.verify_service_has_been_activated(
                    ledger_api=ledger_api,
                    contract_address=ContractConfigs.get(
                        SERVICE_REGISTRY_CONTRACT.name
                    ).contracts[chain_type],
                    service_id=service_id,
                )
            )

        wait_for_success_event(
            success_check=success_check,
            message="Could not verify the service activation in given time",
            timeout=timeout,
        )
    except TimeoutError as e:
        raise ServiceRegistrationFailed(e) from e


def register_instance(  # pylint: disable=too-many-arguments
    ledger_api: LedgerApi,
    crypto: Crypto,
    chain_type: ChainType,
    service_id: int,
    instances: List[str],
    agent_ids: List[int],
    timeout: Optional[float] = None,
) -> None:
    """
    Register instance.

    Once you have a service with an active registration, you can register agent
    which will be a part of the service deployment. Using this method you can
    register maximum N amounts per agents, N being the number of slots for an agent
    with agent id being `agent_id`.

    Make sure the instance address you provide is not already a part of any service
    and not as same as the service owner.

    :param ledger_api: `aea.crypto.LedgerApi` object for interacting with the chain
    :param crypto: `aea.crypto.Crypto` object which has a funded key
    :param chain_type: Chain type
    :param service_id: Service ID retrieved after minting a service
    :param instances: Address of the agent instance
    :param agent_ids: Agent ID of the agent that you want this instance to be a part
                    of when deployed
    :param timeout: Time to wait for register instance event to emit
    """

    if len(agent_ids) != len(instances):
        raise InstanceRegistrationFailed(
            "Number of agent instances and agent IDs needs to be same"
        )

    (
        cost_of_bond,
        *_,
        service_state,
        _,
    ) = get_service_info(
        ledger_api=ledger_api,
        chain_type=chain_type,
        token_id=service_id,
    )

    if service_state == ServiceState.NON_EXISTENT.value:
        raise InstanceRegistrationFailed("Service does not exist")

    if service_state != ServiceState.ACTIVE_REGISTRATION.value:
        raise InstanceRegistrationFailed("Service needs to be in active state")

    security_deposit = cost_of_bond * len(agent_ids)

    try:
        tx = registry_contracts.service_manager.get_register_instance_transaction(
            ledger_api=ledger_api,
            contract_address=ContractConfigs.get(
                SERVICE_MANAGER_CONTRACT.name
            ).contracts[chain_type],
            owner=crypto.address,
            service_id=service_id,
            instances=instances,
            agent_ids=agent_ids,
            security_deposit=security_deposit,
            raise_on_try=True,
        )

        transact(ledger_api=ledger_api, crypto=crypto, tx=tx)
    except RequestsConnectionError as e:
        raise InstanceRegistrationFailed(
            "Instance registration failed; Error connecting to the RPC"
        ) from e
    except (Web3Exception, ValueError) as e:  # pragma: nocover
        raise InstanceRegistrationFailed(f"Instance registration failed; {e}") from e

    try:
        wait_for_agent_instance_registration(
            ledger_api=ledger_api,
            chain_type=chain_type,
            service_id=service_id,
            instances=instances,
            timeout=timeout,
        )
    except TimeoutError as e:
        raise InstanceRegistrationFailed(e) from e


def deploy_service(
    ledger_api: LedgerApi,
    crypto: Crypto,
    chain_type: ChainType,
    service_id: int,
    deployment_payload: Optional[str] = None,
    timeout: Optional[float] = None,
) -> None:
    """
    Deploy service.

    Using this method you can deploy a service on-chain once you have activated
    the service and registered the required agent instances.

    :param ledger_api: `aea.crypto.LedgerApi` object for interacting with the chain
    :param crypto: `aea.crypto.Crypto` object which has a funded key
    :param chain_type: Chain type
    :param service_id: Service ID retrieved after minting a service
    :param deployment_payload: Deployment payload to include when making the
                            deployment transaction
    :param timeout: Time to wait for deploy event to emit
    """
    deployment_payload = deployment_payload or get_default_delployment_payload()
    (
        *_,
        service_state,
        _,
    ) = get_service_info(
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
    except ValueError as e:  # pragma: nocover
        raise ServiceDeployFailed(f"Service deployment failed; {e}") from e

    try:

        def success_check() -> bool:
            """Success check"""
            return registry_contracts.service_registry.verify_service_has_been_deployed(
                ledger_api=ledger_api,
                contract_address=ContractConfigs.get(
                    SERVICE_REGISTRY_CONTRACT.name
                ).contracts[chain_type],
                service_id=service_id,
            )

        wait_for_success_event(
            success_check=success_check,
            message=f"Could not verify the service deployment for service {service_id} in given time",
            timeout=timeout,
        )
    except TimeoutError as e:
        raise ServiceDeployFailed(e) from e


def terminate_service(
    ledger_api: LedgerApi,
    crypto: Crypto,
    chain_type: ChainType,
    service_id: int,
) -> None:
    """
    Terminate service.

    Using this method you can terminate a service on-chain once you have activated
    the service and registered the required agent instances.

    :param ledger_api: `aea.crypto.LedgerApi` object for interacting with the chain
    :param crypto: `aea.crypto.Crypto` object which has a funded key
    :param chain_type: Chain type
    :param service_id: Service ID retrieved after minting a service
    """

    (
        *_,
        service_state,
        _,
    ) = get_service_info(
        ledger_api=ledger_api,
        chain_type=chain_type,
        token_id=service_id,
    )

    if service_state == ServiceState.NON_EXISTENT.value:
        raise TerminateServiceFailed("Service does not exist")

    if service_state == ServiceState.PRE_REGISTRATION.value:
        raise TerminateServiceFailed("Service not active")

    if service_state == ServiceState.TERMINATED_BONDED.value:
        raise TerminateServiceFailed("Service already terminated")

    try:
        tx = registry_contracts.service_manager.get_terminate_service_transaction(
            ledger_api=ledger_api,
            contract_address=ContractConfigs.get(
                SERVICE_MANAGER_CONTRACT.name
            ).contracts[chain_type],
            owner=crypto.address,
            service_id=service_id,
            raise_on_try=True,
        )
        transact(ledger_api=ledger_api, crypto=crypto, tx=tx)
    except RequestsConnectionError as e:  # pragma: nocover
        raise TerminateServiceFailed(
            "Service termination failed; Cannot connect to the RPC"
        ) from e
    except ValueError as e:
        raise TerminateServiceFailed(f"Service termination failed; {e}") from e


def unbond_service(
    ledger_api: LedgerApi,
    crypto: Crypto,
    chain_type: ChainType,
    service_id: int,
) -> None:
    """
    Unbond service.

    Using this method you can unbond a service on-chain once you have terminated
    the service.

    :param ledger_api: `aea.crypto.LedgerApi` object for interacting with the chain
    :param crypto: `aea.crypto.Crypto` object which has a funded key
    :param chain_type: Chain type
    :param service_id: Service ID retrieved after minting a service
    """

    (
        *_,
        service_state,
        _,
    ) = get_service_info(
        ledger_api=ledger_api,
        chain_type=chain_type,
        token_id=service_id,
    )

    if service_state == ServiceState.NON_EXISTENT.value:
        raise UnbondServiceFailed("Service does not exist")

    if service_state != ServiceState.TERMINATED_BONDED.value:
        raise UnbondServiceFailed("Service needs to be in terminated-bonded state")

    try:
        tx = registry_contracts.service_manager.get_unbond_service_transaction(
            ledger_api=ledger_api,
            contract_address=ContractConfigs.get(
                SERVICE_MANAGER_CONTRACT.name
            ).contracts[chain_type],
            owner=crypto.address,
            service_id=service_id,
            raise_on_try=True,
        )
        transact(ledger_api=ledger_api, crypto=crypto, tx=tx)
    except RequestsConnectionError as e:  # pragma: nocover
        raise UnbondServiceFailed(
            "Service unbond failed; Cannot connect to the RPC"
        ) from e
    except ValueError as e:
        raise UnbondServiceFailed(f"Service unbond failed; {e}") from e
