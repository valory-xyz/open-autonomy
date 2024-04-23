# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022-2024 Valory AG
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
from typing import Callable, Dict, List, Optional, Tuple, cast

from aea.configurations.data_types import PublicId
from aea.crypto.base import Crypto, LedgerApi

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
from autonomy.chain.tx import TxSettler


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


def get_min_threshold(n: int) -> int:
    """Calculate minimum threshold required for N number of agents."""
    return ceil((n * 2 + 1) / 3)


class MintManager:
    """Mint helper."""

    def __init__(  # pylint: disable=too-many-arguments
        self,
        ledger_api: LedgerApi,
        crypto: Crypto,
        chain_type: ChainType,
        dry_run: bool = False,
        timeout: Optional[float] = None,
        retries: Optional[int] = None,
        sleep: Optional[float] = None,
    ) -> None:
        """Initialize object."""
        self.crypto = crypto
        self.ledger_api = ledger_api
        self.chain_type = chain_type
        self.timeout = timeout
        self.retries = retries
        self.sleep = sleep
        self.dry_run = dry_run

    def _transact(
        self,
        method: Callable,
        kwargs: Dict,
        build_tx_ctr: str,
        event: str,
        process_receipt_ctr: PublicId,
    ) -> List[Dict]:
        """Auxiliary method for minting components."""
        tx_settler = TxSettler(
            ledger_api=self.ledger_api,
            crypto=self.crypto,
            chain_type=self.chain_type,
            timeout=self.timeout,
            retries=self.retries,
            sleep=self.sleep,
        )
        receipt = tx_settler.transact(
            method=method,
            contract=build_tx_ctr,
            kwargs=kwargs,
            dry_run=self.dry_run,
        )
        if self.dry_run:
            print("=== Dry run output ===")
            print("Method: " + str(method).split(" ")[2])
            print(
                f"Contract: {ContractConfigs.get(name=build_tx_ctr).contracts[self.chain_type]}"
            )
            print("Kwargs: ")
            for key, val in kwargs.items():
                print(f"    {key}: {val}")
            print("Transaction: ")
            for key, val in receipt.items():
                print(f"    {key}: {val}")
            return []
        events = tx_settler.process(
            event=event,
            receipt=receipt,
            contract=process_receipt_ctr,
        ).get("events")
        return cast(List[Dict], events)

    def validate_address(self, address: str) -> str:
        """Validate address string."""
        try:
            return self.ledger_api.api.to_checksum_address(address)
        except ValueError as e:  # pragma: nocover
            raise ComponentMintFailed(f"Invalid owner address {address}") from e

    def mint_component(
        self,
        metadata_hash: str,
        component_type: UnitType,
        owner: Optional[str] = None,
        dependencies: Optional[List[int]] = None,
    ) -> Optional[int]:
        """Publish component on-chain."""
        owner = self.validate_address(owner or self.crypto.address)
        if dependencies is not None:
            dependencies = sorted(set(dependencies))

        events = self._transact(
            method=registry_contracts.registries_manager.get_create_transaction,
            build_tx_ctr=REGISTRIES_MANAGER_CONTRACT.name,
            kwargs=dict(
                owner=owner,
                component_type=component_type,
                metadata_hash=metadata_hash,
                sender=self.crypto.address,
                dependencies=dependencies,
            ),
            event="CreateUnit",
            process_receipt_ctr=(
                COMPONENT_REGISTRY_CONTRACT
                if component_type == UnitType.COMPONENT
                else AGENT_REGISTRY_CONTRACT
            ),
        )
        for event in events:
            if (
                "unitHash" in event["args"]
                and event["args"]["unitHash"].hex() == metadata_hash[2:]
            ):
                return event["args"]["unitId"]
        return None

    def update_component(
        self, metadata_hash: str, unit_id: int, component_type: UnitType
    ) -> Optional[int]:
        """Update component on-chain."""

        events = self._transact(
            method=registry_contracts.registries_manager.get_update_hash_transaction,
            build_tx_ctr=REGISTRIES_MANAGER_CONTRACT.name,
            kwargs=dict(
                unit_id=unit_id,
                component_type=component_type,
                metadata_hash=metadata_hash,
                sender=self.crypto.address,
            ),
            event="UpdateUnitHash",
            process_receipt_ctr=(
                COMPONENT_REGISTRY_CONTRACT
                if component_type == UnitType.COMPONENT
                else AGENT_REGISTRY_CONTRACT
            ),
        )
        for event in events:
            if (
                "unitHash" in event["args"]
                and event["args"]["unitHash"].hex() == metadata_hash[2:]
            ):
                return event["args"]["unitId"]
        return None

    def mint_service(  # pylint: disable=too-many-arguments
        self,
        metadata_hash: str,
        agent_ids: List[int],
        number_of_slots_per_agent: List[int],
        cost_of_bond_per_agent: List[int],
        threshold: Optional[int] = None,
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
        if threshold is None:
            threshold = get_min_threshold(number_of_agent_instances)

        if threshold < get_min_threshold(n=number_of_agent_instances):
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

        owner = self.validate_address(owner or self.crypto.address)
        agent_params = [
            [n, c] for n, c in zip(number_of_slots_per_agent, cost_of_bond_per_agent)
        ]

        events = self._transact(
            method=registry_contracts.service_manager.get_create_transaction,
            build_tx_ctr=SERVICE_MANAGER_CONTRACT.name,
            kwargs=dict(
                metadata_hash=metadata_hash,
                agent_params=agent_params,
                agent_ids=agent_ids,
                threshold=threshold,
                token=token,
                owner=owner,
                sender=self.crypto.address,
            ),
            event="CreateService",
            process_receipt_ctr=SERVICE_REGISTRY_CONTRACT,
        )
        for event in events:
            if "serviceId" in event["args"]:
                return event["args"]["serviceId"]
        return None

    def update_service(  # pylint: disable=too-many-arguments
        self,
        metadata_hash: str,
        service_id: int,
        agent_ids: List[int],
        number_of_slots_per_agent: List[int],
        cost_of_bond_per_agent: List[int],
        threshold: Optional[int] = None,
        token: Optional[str] = None,
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
        if threshold is None:
            threshold = get_min_threshold(number_of_agent_instances)

        if threshold < get_min_threshold(number_of_agent_instances):
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

        events = self._transact(
            method=registry_contracts.service_manager.get_update_transaction,
            build_tx_ctr=SERVICE_MANAGER_CONTRACT.name,
            kwargs=dict(
                service_id=service_id,
                sender=self.crypto.address,
                metadata_hash=metadata_hash,
                agent_ids=agent_ids,
                agent_params=agent_params,
                threshold=threshold,
                token=token,
            ),
            event="UpdateService",
            process_receipt_ctr=SERVICE_REGISTRY_CONTRACT,
        )
        for event in events:
            if (
                "configHash" in event["args"]
                and event["args"]["configHash"].hex() == metadata_hash[2:]
            ):
                return event["args"]["serviceId"]
        return None
