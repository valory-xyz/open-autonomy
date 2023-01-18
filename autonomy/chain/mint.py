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
from autonomy.chain.exceptions import (
    ComponentMintFailed,
    FailedToRetrieveTokenId,
    InvalidMintParameter,
)


DEFAULT_NFT_IMAGE_HASH = "bafybeiggnad44tftcrenycru2qtyqnripfzitv5yume4szbkl33vfd4abm"


def transact(ledger_api: LedgerApi, crypto: Crypto, tx: Dict) -> Dict:
    """Make a transaction and return a receipt"""

    tx_signed = crypto.sign_transaction(transaction=tx)
    tx_digest = ledger_api.send_signed_transaction(tx_signed=tx_signed)

    return ledger_api.get_transaction_receipt(tx_digest=tx_digest)


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


def mint_component(
    ledger_api: LedgerApi,
    crypto: Crypto,
    metadata_hash: str,
    component_type: UnitType,
    chain_type: ChainType,
    dependencies: Optional[List[int]] = None,
) -> Optional[int]:
    """Publish component on-chain."""

    if dependencies is not None:
        dependencies = sorted(set(dependencies))

    try:
        tx = registry_contracts.registries_manager.get_create_transaction(
            ledger_api=ledger_api,
            contract_address=ContractConfigs.get(
                REGISTRIES_MANAGER_CONTRACT.name
            ).contracts[chain_type],
            owner=crypto.address,
            component_type=component_type,
            metadata_hash=metadata_hash,
            dependencies=dependencies,
            raise_on_try=True,
        )
        transact(
            ledger_api=ledger_api,
            crypto=crypto,
            tx=tx,
        )
    except RequestsConnectionError as e:
        raise ComponentMintFailed("Cannot connect to the given RPC") from e

    try:
        if component_type == UnitType.COMPONENT:
            return registry_contracts.component_registry.filter_token_id_from_emitted_events(
                ledger_api=ledger_api,
                contract_address=ContractConfigs.get(
                    COMPONENT_REGISTRY_CONTRACT.name
                ).contracts[chain_type],
                metadata_hash=metadata_hash,
            )

        return registry_contracts.agent_registry.filter_token_id_from_emitted_events(
            ledger_api=ledger_api,
            contract_address=ContractConfigs.get(
                AGENT_REGISTRY_CONTRACT.name
            ).contracts[chain_type],
            metadata_hash=metadata_hash,
        )

    except RequestsConnectionError as e:
        raise FailedToRetrieveTokenId(
            "Connection interrupted while waiting for the unitId emit event"
        ) from e


def mint_service(  # pylint: disable=too-many-arguments
    ledger_api: LedgerApi,
    crypto: Crypto,
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
        tx = registry_contracts.service_manager.get_create_transaction(
            ledger_api=ledger_api,
            contract_address=ContractConfigs.get(
                SERVICE_MANAGER_CONTRACT.name
            ).contracts[chain_type],
            owner=crypto.address,
            metadata_hash=metadata_hash,
            agent_ids=agent_ids,
            agent_params=agent_params,
            threshold=threshold,
            raise_on_try=True,
        )
        transact(
            ledger_api=ledger_api,
            crypto=crypto,
            tx=tx,
        )
    except RequestsConnectionError as e:
        raise ComponentMintFailed("Cannot connect to the given RPC") from e

    try:
        return registry_contracts.service_registry.filter_token_id_from_emitted_events(
            ledger_api=ledger_api,
            contract_address=ContractConfigs.get(
                SERVICE_REGISTRY_CONTRACT.name
            ).contracts[chain_type],
        )

    except RequestsConnectionError as e:
        raise FailedToRetrieveTokenId(
            "Connection interrupted while waiting for the unitId emit event"
        ) from e
