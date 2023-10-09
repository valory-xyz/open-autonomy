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

"""Helpers for minting components"""

import time
from datetime import datetime
from math import ceil
from typing import Dict, List, Optional, Tuple

from aea.crypto.base import Crypto, LedgerApi
from requests.exceptions import ConnectionError as RequestsConnectionError

from autonomy.chain.base import UnitType, registry_contracts
from autonomy.chain.config import ChainType, ContractConfigs
from autonomy.chain.constants import (
    AGENT_REGISTRY_CONTRACT,
    COMPONENT_REGISTRY_CONTRACT,
    REGISTRIES_MANAGER_CONTRACT,
    SERVICE_MANAGER_CONTRACT,
    SERVICE_REGISTRY_CONTRACT,
)
from autonomy.chain.exceptions import ComponentMintFailed, InvalidMintParameter


try:
    from web3.exceptions import Web3Exception
except (ModuleNotFoundError, ImportError):
    Web3Exception = Exception


DEFAULT_NFT_IMAGE_HASH = "bafybeiggnad44tftcrenycru2qtyqnripfzitv5yume4szbkl33vfd4abm"
DEFAULT_TRANSACTION_WAIT_TIMEOUT = 60.0


def transact(
    ledger_api: LedgerApi,
    crypto: Crypto,
    tx: Dict,
    max_retries: int = 5,
    sleep: float = 5.0,
    timeout: Optional[float] = None,
) -> Dict:
    """Make a transaction and return a receipt"""
    retries = 0
    tx_receipt = None
    tx_signed = crypto.sign_transaction(transaction=tx)
    tx_digest = ledger_api.send_signed_transaction(tx_signed=tx_signed)
    deadline = datetime.now().timestamp() + (
        timeout or DEFAULT_TRANSACTION_WAIT_TIMEOUT
    )
    while (
        tx_receipt is None
        and retries < max_retries
        and deadline >= datetime.now().timestamp()
    ):
        try:
            return ledger_api.api.eth.get_transaction_receipt(tx_digest)
        except Web3Exception:  # pylint: disable=broad-except
            time.sleep(sleep)
    raise TimeoutError("Timed out when waiting for transaction to go through")


def sort_service_dependency_metadata(
    agent_ids: List[int],
    number_of_slots_per_agents: List[int],
    cost_of_bond_per_agent: List[int],
) -> Tuple[List[int], ...]:
    """Sort service dependencies and their respective parameters"""

    ids_sorted = []
    slots_sorted = []
    securities_sorted = []

    for idx, n_slots, b_cost in sorted(
        zip(agent_ids, number_of_slots_per_agents, cost_of_bond_per_agent),
        key=lambda x: x[0],
    ):
        ids_sorted.append(idx)
        slots_sorted.append(n_slots)
        securities_sorted.append(b_cost)

    return ids_sorted, slots_sorted, securities_sorted


def mint_component(  # pylint: disable=too-many-arguments
    ledger_api: LedgerApi,
    crypto: Crypto,
    metadata_hash: str,
    component_type: UnitType,
    chain_type: ChainType,
    owner: Optional[str] = None,
    dependencies: Optional[List[int]] = None,
) -> Optional[int]:
    """Publish component on-chain."""

    if dependencies is not None:
        dependencies = sorted(set(dependencies))

    try:
        owner = ledger_api.api.to_checksum_address(owner or crypto.address)
    except ValueError as e:  # pragma: nocover
        raise ComponentMintFailed(f"Invalid owner address {owner}") from e

    try:
        tx = registry_contracts.registries_manager.get_create_transaction(
            ledger_api=ledger_api,
            contract_address=ContractConfigs.get(
                REGISTRIES_MANAGER_CONTRACT.name
            ).contracts[chain_type],
            owner=owner,
            sender=crypto.address,
            component_type=component_type,
            metadata_hash=metadata_hash,
            dependencies=dependencies,
            raise_on_try=True,
        )
        tx_receipt = transact(
            ledger_api=ledger_api,
            crypto=crypto,
            tx=tx,
        )
    except RequestsConnectionError as e:
        raise ComponentMintFailed("Cannot connect to the given RPC") from e

    if component_type == UnitType.COMPONENT:
        events = registry_contracts.component_registry.get_create_events(
            ledger_api=ledger_api,
            contract_address=ContractConfigs.get(
                COMPONENT_REGISTRY_CONTRACT.name
            ).contracts[chain_type],
            receipt=tx_receipt,
        )
    else:
        events = registry_contracts.agent_registry.get_create_events(
            ledger_api=ledger_api,
            contract_address=ContractConfigs.get(
                AGENT_REGISTRY_CONTRACT.name
            ).contracts[chain_type],
            receipt=tx_receipt,
        )
    for event in events:
        if (
            "unitHash" in event["args"]
            and event["args"]["unitHash"].hex() == metadata_hash[2:]
        ):
            return event["args"]["unitId"]
    return None


def update_component(  # pylint: disable=too-many-arguments
    ledger_api: LedgerApi,
    crypto: Crypto,
    unit_id: int,
    metadata_hash: str,
    component_type: UnitType,
    chain_type: ChainType,
) -> Optional[int]:
    """Publish component on-chain."""

    try:
        tx = registry_contracts.registries_manager.get_update_hash_transaction(
            ledger_api=ledger_api,
            contract_address=ContractConfigs.get(
                REGISTRIES_MANAGER_CONTRACT.name
            ).contracts[chain_type],
            component_type=component_type,
            unit_id=unit_id,
            metadata_hash=metadata_hash,
            sender=crypto.address,
            raise_on_try=True,
        )
        tx_receipt = transact(
            ledger_api=ledger_api,
            crypto=crypto,
            tx=tx,
        )
    except RequestsConnectionError as e:
        raise ComponentMintFailed("Cannot connect to the given RPC") from e

    if component_type == UnitType.COMPONENT:
        events = registry_contracts.component_registry.get_update_hash_events(
            ledger_api=ledger_api,
            contract_address=ContractConfigs.get(
                COMPONENT_REGISTRY_CONTRACT.name
            ).contracts[chain_type],
            receipt=tx_receipt,
        )
    else:
        events = registry_contracts.agent_registry.get_update_hash_events(
            ledger_api=ledger_api,
            contract_address=ContractConfigs.get(
                AGENT_REGISTRY_CONTRACT.name
            ).contracts[chain_type],
            receipt=tx_receipt,
        )
    for event in events:
        if (
            "unitHash" in event["args"]
            and event["args"]["unitHash"].hex() == metadata_hash[2:]
        ):
            return event["args"]["unitId"]
    return None


def mint_service(  # pylint: disable=too-many-arguments,too-many-locals
    ledger_api: LedgerApi,
    crypto: Crypto,
    metadata_hash: str,
    chain_type: ChainType,
    agent_ids: List[int],
    number_of_slots_per_agent: List[int],
    cost_of_bond_per_agent: List[int],
    threshold: int,
    token: Optional[str] = None,
    owner: Optional[str] = None,
) -> Optional[int]:
    """Publish component on-chain."""

    if len(agent_ids) == 0:
        raise InvalidMintParameter("Please provide at least one agent id")

    if len(number_of_slots_per_agent) == 0:
        raise InvalidMintParameter("Please for provide number of slots for agents")

    if len(cost_of_bond_per_agent) == 0:
        raise InvalidMintParameter("Please for provide cost of bond for agents")

    if (
        len(agent_ids) != len(number_of_slots_per_agent)
        or len(agent_ids) != len(cost_of_bond_per_agent)
        or len(number_of_slots_per_agent) != len(cost_of_bond_per_agent)
    ):
        raise InvalidMintParameter(
            "Make sure the number of agent ids, number of slots for agents and cost of bond for agents match"
        )

    if any(map(lambda x: x == 0, number_of_slots_per_agent)):
        raise InvalidMintParameter("Number of slots cannot be zero")

    if any(map(lambda x: x == 0, cost_of_bond_per_agent)):
        raise InvalidMintParameter("Cost of bond cannot be zero")

    number_of_agent_instances = sum(number_of_slots_per_agent)
    if threshold < (ceil((number_of_agent_instances * 2 + 1) / 3)):
        raise InvalidMintParameter(
            "The threshold value should at least be greater than or equal to ceil((n * 2 + 1) / 3), "
            "n is total number of agent instances in the service"
        )

    (
        agent_ids,
        number_of_slots_per_agent,
        cost_of_bond_per_agent,
    ) = sort_service_dependency_metadata(
        agent_ids=agent_ids,
        number_of_slots_per_agents=number_of_slots_per_agent,
        cost_of_bond_per_agent=cost_of_bond_per_agent,
    )

    agent_params = [
        [n, c] for n, c in zip(number_of_slots_per_agent, cost_of_bond_per_agent)
    ]

    try:
        owner = ledger_api.api.to_checksum_address(owner or crypto.address)
    except ValueError as e:
        raise ComponentMintFailed(f"Invalid owner address {owner}") from e

    try:
        tx = registry_contracts.service_manager.get_create_transaction(
            ledger_api=ledger_api,
            contract_address=ContractConfigs.get(
                SERVICE_MANAGER_CONTRACT.name
            ).contracts[chain_type],
            owner=owner,
            sender=crypto.address,
            metadata_hash=metadata_hash,
            agent_ids=agent_ids,
            agent_params=agent_params,
            threshold=threshold,
            token=token,
            raise_on_try=True,
        )
        tx_receipt = transact(
            ledger_api=ledger_api,
            crypto=crypto,
            tx=tx,
        )
        if tx_receipt is None:
            raise ComponentMintFailed("Could not retrieve the transaction receipt")
    except RequestsConnectionError as e:
        raise ComponentMintFailed("Cannot connect to the given RPC") from e

    events = registry_contracts.service_registry.get_create_events(
        ledger_api=ledger_api,
        contract_address=ContractConfigs.get(SERVICE_REGISTRY_CONTRACT.name).contracts[
            chain_type
        ],
        receipt=tx_receipt,
    )
    for event in events:
        if "serviceId" in event["args"]:
            return event["args"]["serviceId"]
    return None


def update_service(  # pylint: disable=too-many-arguments,too-many-locals
    ledger_api: LedgerApi,
    crypto: Crypto,
    service_id: int,
    metadata_hash: str,
    chain_type: ChainType,
    agent_ids: List[int],
    number_of_slots_per_agent: List[int],
    cost_of_bond_per_agent: List[int],
    threshold: int,
) -> Optional[int]:
    """Publish component on-chain."""

    if len(agent_ids) == 0:
        raise InvalidMintParameter("Please provide at least one agent id")

    if len(number_of_slots_per_agent) == 0:
        raise InvalidMintParameter("Please for provide number of slots for agents")

    if len(cost_of_bond_per_agent) == 0:
        raise InvalidMintParameter("Please for provide cost of bond for agents")

    if (
        len(agent_ids) != len(number_of_slots_per_agent)
        or len(agent_ids) != len(cost_of_bond_per_agent)
        or len(number_of_slots_per_agent) != len(cost_of_bond_per_agent)
    ):
        raise InvalidMintParameter(
            "Make sure the number of agent ids, number of slots for agents and cost of bond for agents match"
        )

    if any(map(lambda x: x == 0, number_of_slots_per_agent)):
        raise InvalidMintParameter("Number of slots cannot be zero")

    if any(map(lambda x: x == 0, cost_of_bond_per_agent)):
        raise InvalidMintParameter("Cost of bond cannot be zero")

    number_of_agent_instances = sum(number_of_slots_per_agent)
    if threshold < (ceil((number_of_agent_instances * 2 + 1) / 3)):
        raise InvalidMintParameter(
            "The threshold value should at least be greater than or equal to ceil((n * 2 + 1) / 3), "
            "n is total number of agent instances in the service"
        )

    (
        agent_ids,
        number_of_slots_per_agent,
        cost_of_bond_per_agent,
    ) = sort_service_dependency_metadata(
        agent_ids=agent_ids,
        number_of_slots_per_agents=number_of_slots_per_agent,
        cost_of_bond_per_agent=cost_of_bond_per_agent,
    )

    agent_params = [
        [n, c] for n, c in zip(number_of_slots_per_agent, cost_of_bond_per_agent)
    ]

    try:
        tx = registry_contracts.service_manager.get_update_transaction(
            ledger_api=ledger_api,
            contract_address=ContractConfigs.get(
                SERVICE_MANAGER_CONTRACT.name
            ).contracts[chain_type],
            service_id=service_id,
            sender=crypto.address,
            metadata_hash=metadata_hash,
            agent_ids=agent_ids,
            agent_params=agent_params,
            threshold=threshold,
            raise_on_try=True,
        )
        tx_receipt = transact(
            ledger_api=ledger_api,
            crypto=crypto,
            tx=tx,
        )
        if tx_receipt is None:
            raise ComponentMintFailed("Could not retrieve the transaction receipt")
    except RequestsConnectionError as e:
        raise ComponentMintFailed("Cannot connect to the given RPC") from e

    events = registry_contracts.service_registry.get_update_events(
        ledger_api=ledger_api,
        contract_address=ContractConfigs.get(SERVICE_REGISTRY_CONTRACT.name).contracts[
            chain_type
        ],
        receipt=tx_receipt,
    )
    for event in events:
        if (
            "configHash" in event["args"]
            and event["args"]["configHash"].hex() == metadata_hash[2:]
        ):
            return event["args"]["serviceId"]
    return None
