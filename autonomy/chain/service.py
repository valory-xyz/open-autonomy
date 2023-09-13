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

import binascii
import time
from enum import Enum
from typing import Dict, List, Optional, Tuple, cast

from aea.crypto.base import Crypto, LedgerApi
from hexbytes import HexBytes
from requests.exceptions import ConnectionError as RequestsConnectionError

from autonomy.chain.base import ServiceState, registry_contracts
from autonomy.chain.config import ChainType, ContractConfigs
from autonomy.chain.constants import (
    GNOSIS_SAFE_PROXY_FACTORY_CONTRACT,
    GNOSIS_SAFE_SAME_ADDRESS_MULTISIG_CONTRACT,
    MULTISEND_CONTRACT,
    SERVICE_MANAGER_CONTRACT,
    SERVICE_REGISTRY_CONTRACT,
    SERVICE_REGISTRY_TOKEN_UTILITY_CONTRACT,
)
from autonomy.chain.exceptions import (
    ChainInteractionError,
    InstanceRegistrationFailed,
    ServiceDeployFailed,
    ServiceRegistrationFailed,
    TerminateServiceFailed,
    UnbondServiceFailed,
)
from autonomy.chain.mint import transact


try:
    from web3.exceptions import Web3Exception
except (ModuleNotFoundError, ImportError):  # pragma: nocover
    Web3Exception = Exception

NULL_ADDRESS = "0x0000000000000000000000000000000000000000"
DEFAULT_DEPLOY_PAYLOAD = "0x0000000000000000000000000000000000000000f48f2b2d2a534e402487b3ee7c18c33aec0fe5e4000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"

ServiceInfo = Tuple[int, str, bytes, int, int, int, int, List[int]]


class MultiSendOperation(Enum):
    """Operation types."""

    CALL = 0
    DELEGATE_CALL = 1


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


def get_token_deposit_amount(
    ledger_api: LedgerApi,
    chain_type: ChainType,
    service_id: int,
    agent_id: Optional[int] = None,
) -> int:
    """Returns service info."""
    if agent_id is None:
        *_, (agent_id, *_) = get_service_info(
            ledger_api=ledger_api, chain_type=chain_type, token_id=service_id
        )
    return registry_contracts.service_registry_token_utility.get_agent_bond(
        ledger_api=ledger_api,
        contract_address=ContractConfigs.get(
            SERVICE_REGISTRY_TOKEN_UTILITY_CONTRACT.name
        ).contracts[chain_type],
        service_id=service_id,
        agent_id=agent_id,
    ).get("bond")


def get_activate_registration_amount(
    ledger_api: LedgerApi,
    chain_type: ChainType,
    service_id: int,
    agents: List[int],
) -> int:
    """Get activate registration amount."""
    agent_to_deposit = {}
    amount = 0
    for agent in agents:
        if agent not in agent_to_deposit:
            agent_to_deposit[agent] = get_token_deposit_amount(
                ledger_api=ledger_api,
                chain_type=chain_type,
                service_id=service_id,
                agent_id=agent,
            )
        amount += agent_to_deposit[agent]
    return amount


def is_service_token_secured(
    ledger_api: LedgerApi,
    chain_type: ChainType,
    service_id: int,
) -> bool:
    """Check if the service is token secured."""
    response = (
        registry_contracts.service_registry_token_utility.is_token_secured_service(
            ledger_api=ledger_api,
            contract_address=ContractConfigs.get(
                SERVICE_REGISTRY_TOKEN_UTILITY_CONTRACT.name
            ).contracts[chain_type],
            service_id=service_id,
        )
    )
    return response["is_token_secured_service"]


def approve_erc20_usage(  # pylint: disable=too-many-arguments
    ledger_api: LedgerApi,
    crypto: Crypto,
    contract_address: str,
    spender: str,
    amount: int,
    sender: str,
    timeout: Optional[float] = None,
) -> None:
    """Approve ERC20 token usage."""

    try:
        tx = registry_contracts.erc20.get_approve_tx(
            ledger_api=ledger_api,
            contract_address=contract_address,
            spender=spender,
            amount=amount,
            sender=sender,
        )
        tx_receipt = transact(
            ledger_api=ledger_api,
            crypto=crypto,
            tx=tx,
            timeout=timeout,
        )
    except (ValueError, TimeoutError, RequestsConnectionError, Web3Exception) as e:
        raise ChainInteractionError(f"Funds approval request failed; {e}") from e

    events = registry_contracts.erc20.get_approval_events(
        ledger_api=ledger_api, contract_address=contract_address, tx_receipt=tx_receipt
    )

    for event in events:
        if event["args"]["spender"] == spender:
            return

    raise ChainInteractionError("Funds approval request failed")


def verify_service_event(
    ledger_api: LedgerApi,
    chain_type: ChainType,
    service_id: int,
    event: str,
    receipt: Dict,
) -> bool:
    """Verify service event."""
    response = registry_contracts.service_registry.process_receipt(
        ledger_api=ledger_api,
        contract_address=ContractConfigs.get(SERVICE_REGISTRY_CONTRACT.name).contracts[
            chain_type
        ],
        event=event,
        receipt=receipt,
    )
    for _event in response["events"]:
        if _event["args"]["serviceId"] == service_id:
            return True
    return False


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
        tx_receipt = transact(
            ledger_api=ledger_api,
            crypto=crypto,
            tx=tx,
            timeout=timeout,
        )
    except (ValueError, TimeoutError, RequestsConnectionError, Web3Exception) as e:
        raise ServiceRegistrationFailed(f"Service activation failed; {e}") from e

    if not verify_service_event(
        ledger_api=ledger_api,
        chain_type=chain_type,
        service_id=service_id,
        event="ActivateRegistration",
        receipt=tx_receipt,
    ):
        raise ServiceRegistrationFailed("Could not verify the activation event.")


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
        tx_receipt = transact(
            ledger_api=ledger_api,
            crypto=crypto,
            tx=tx,
            timeout=timeout,
        )
    except RequestsConnectionError as e:
        raise InstanceRegistrationFailed(
            "Instance registration failed; Error connecting to the RPC"
        ) from e
    except (Web3Exception, ValueError) as e:  # pragma: nocover
        raise InstanceRegistrationFailed(f"Instance registration failed; {e}") from e

    if not verify_service_event(
        ledger_api=ledger_api,
        chain_type=chain_type,
        service_id=service_id,
        event="RegisterInstance",
        receipt=tx_receipt,
    ):
        raise InstanceRegistrationFailed("Could not verify the registration event.")


def deploy_service(  # pylint: disable=too-many-arguments
    ledger_api: LedgerApi,
    crypto: Crypto,
    chain_type: ChainType,
    service_id: int,
    deployment_payload: Optional[str] = None,
    reuse_multisig: bool = False,
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
    :param reuse_multisig: Use multisig from the previous deployment
    :param timeout: Time to wait for deploy event to emit
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
        raise ServiceDeployFailed("Service does not exist")

    if service_state != ServiceState.FINISHED_REGISTRATION.value:
        raise ServiceDeployFailed("Service needs to be in finished registration state")

    deployment_payload = deployment_payload or get_default_delployment_payload()
    gnosis_safe_multisig = ContractConfigs.get(
        GNOSIS_SAFE_PROXY_FACTORY_CONTRACT.name
    ).contracts[chain_type]
    if reuse_multisig:
        _deployment_payload, error = get_reuse_multisig_payload(
            ledger_api=ledger_api,
            crypto=crypto,
            chain_type=chain_type,
            service_id=service_id,
        )
        if _deployment_payload is None:
            raise ServiceDeployFailed(error)
        deployment_payload = _deployment_payload
        gnosis_safe_multisig = ContractConfigs.get(
            GNOSIS_SAFE_SAME_ADDRESS_MULTISIG_CONTRACT.name
        ).contracts[chain_type]

    try:
        tx = registry_contracts.service_manager.get_service_deploy_transaction(
            ledger_api=ledger_api,
            contract_address=ContractConfigs.get(
                SERVICE_MANAGER_CONTRACT.name
            ).contracts[chain_type],
            owner=crypto.address,
            service_id=service_id,
            gnosis_safe_multisig=gnosis_safe_multisig,
            deployment_payload=deployment_payload,
            raise_on_try=True,
        )
        tx_receipt = transact(
            ledger_api=ledger_api,
            crypto=crypto,
            tx=tx,
            timeout=timeout,
        )
    except RequestsConnectionError as e:
        raise ServiceDeployFailed(
            "Service deployment failed; Cannot connect to the RPC"
        ) from e
    except (ValueError, Web3Exception) as e:  # pragma: nocover
        raise ServiceDeployFailed(f"Service deployment failed; {e}") from e

    if not verify_service_event(
        ledger_api=ledger_api,
        chain_type=chain_type,
        service_id=service_id,
        event="DeployService",
        receipt=tx_receipt,
    ):
        raise ServiceDeployFailed("Could not verify the deploy event.")


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
        tx_receipt = transact(
            ledger_api=ledger_api,
            crypto=crypto,
            tx=tx,
        )
    except RequestsConnectionError as e:  # pragma: nocover
        raise TerminateServiceFailed(
            "Service termination failed; Cannot connect to the RPC"
        ) from e
    except ValueError as e:
        raise TerminateServiceFailed(f"Service termination failed; {e}") from e

    if not verify_service_event(
        ledger_api=ledger_api,
        chain_type=chain_type,
        service_id=service_id,
        event="TerminateService",
        receipt=tx_receipt,
    ):
        raise TerminateServiceFailed("Could not verify the terminate event.")


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
        tx_receipt = transact(
            ledger_api=ledger_api,
            crypto=crypto,
            tx=tx,
        )
    except RequestsConnectionError as e:  # pragma: nocover
        raise UnbondServiceFailed(
            "Service unbond failed; Cannot connect to the RPC"
        ) from e
    except ValueError as e:
        raise UnbondServiceFailed(f"Service unbond failed; {e}") from e

    if not verify_service_event(
        ledger_api=ledger_api,
        chain_type=chain_type,
        service_id=service_id,
        event="OperatorUnbond",
        receipt=tx_receipt,
    ):
        raise UnbondServiceFailed("Could not verify the unbond event.")


def get_reuse_multisig_payload(  # pylint: disable=too-many-locals
    ledger_api: LedgerApi,
    crypto: Crypto,
    chain_type: ChainType,
    service_id: int,
) -> Tuple[Optional[str], Optional[str]]:
    """Reuse multisig."""
    _, multisig_address, _, threshold, *_ = get_service_info(
        ledger_api=ledger_api,
        chain_type=chain_type,
        token_id=service_id,
    )
    if multisig_address == NULL_ADDRESS:
        return None, "Cannot reuse multisig, No previous deployment exist!"

    service_owner = crypto.address
    multisend_address = ContractConfigs.get(MULTISEND_CONTRACT.name).contracts[
        chain_type
    ]
    multisig_instance = registry_contracts.gnosis_safe.get_instance(
        ledger_api=ledger_api,
        contract_address=multisig_address,
    )

    # Verify if the service was terminated properly or not
    old_owners = multisig_instance.functions.getOwners().call()
    if len(old_owners) != 1 or service_owner not in old_owners:
        return (
            None,
            "Service was not terminated properly, the service owner should be the only owner of the safe",
        )

    # Build multisend tx to add new instances as owners
    txs = []
    new_owners = cast(
        List[str],
        get_agent_instances(
            ledger_api=ledger_api,
            chain_type=chain_type,
            token_id=service_id,
        ).get("agentInstances"),
    )
    for _owner in new_owners[1:]:
        txs.append(
            {
                "to": multisig_address,
                "data": HexBytes(
                    bytes.fromhex(
                        multisig_instance.encodeABI(
                            fn_name="addOwnerWithThreshold",
                            args=[_owner, 1],
                        )[2:]
                    )
                ),
                "operation": MultiSendOperation.CALL,
                "value": 0,
            }
        )

    txs.append(
        {
            "to": multisig_address,
            "data": HexBytes(
                bytes.fromhex(
                    multisig_instance.encodeABI(
                        fn_name="swapOwner",
                        args=[new_owners[1], service_owner, new_owners[0]],
                    )[2:]
                )
            ),
            "operation": MultiSendOperation.CALL,
            "value": 0,
        }
    )

    txs.append(
        {
            "to": multisig_address,
            "data": HexBytes(
                bytes.fromhex(
                    multisig_instance.encodeABI(
                        fn_name="changeThreshold",
                        args=[threshold],
                    )[2:]
                )
            ),
            "operation": MultiSendOperation.CALL,
            "value": 0,
        }
    )

    multisend_tx = registry_contracts.multisend.get_multisend_tx(
        ledger_api=ledger_api,
        contract_address=multisend_address,
        txs=txs,
    )
    safe_tx_hash = registry_contracts.gnosis_safe.get_raw_safe_transaction_hash(
        ledger_api=ledger_api,
        contract_address=multisig_address,
        to_address=multisend_address,
        value=multisend_tx["value"],
        data=multisend_tx["data"],
        operation=1,
    ).get("tx_hash")
    approve_hash_tx = registry_contracts.gnosis_safe.get_approve_hash_tx(
        ledger_api=ledger_api,
        contract_address=multisig_address,
        tx_hash=safe_tx_hash,
        sender=crypto.address,
    )
    transact(
        ledger_api=ledger_api,
        crypto=crypto,
        tx=approve_hash_tx,
    )

    safe_tx_bytes = binascii.unhexlify(safe_tx_hash[2:])
    owner_to_signature = {
        crypto.address: crypto.sign_message(
            message=safe_tx_bytes,
            is_deprecated_mode=True,
        )[2:]
    }
    signature_bytes = registry_contracts.gnosis_safe.get_packed_signatures(
        owners=tuple(old_owners), signatures_by_owner=owner_to_signature
    )
    safe_exec_data = multisig_instance.encodeABI(
        fn_name="execTransaction",
        args=[
            multisend_address,  # to address
            multisend_tx["value"],  # value
            multisend_tx["data"],  # data
            1,  # operation
            0,  # safe tx gas
            0,  # bas gas
            0,  # safe gas price
            NULL_ADDRESS,  # gas token
            NULL_ADDRESS,  # refund receiver
            signature_bytes,  # signatures
        ],
    )
    payload = multisig_address + safe_exec_data[2:]
    return payload, None
