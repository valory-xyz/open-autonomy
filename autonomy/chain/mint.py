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

from typing import Dict, List, Optional, cast

from aea.crypto.base import Crypto, LedgerApi
from requests.exceptions import ConnectionError as RequestsConnectionError

from autonomy.chain.base import ContractsHelper, UnitType
from autonomy.chain.config import ChainType, ContractConfigs
from autonomy.chain.constants import (
    COMPONENT_REGISTRY_CONTRACT,
    REGISTRIES_MANAGER_CONTRACT,
)
from autonomy.chain.exceptions import ComponentMintFailed, FailedToRetrieveTokenId
from autonomy.chain.metadata import UNIT_HASH_PREFIX


DEFAULT_NFT_IMAGE_HASH = "bafybeiggnad44tftcrenycru2qtyqnripfzitv5yume4szbkl33vfd4abm"


def verify_and_fetch_token_id_from_event(
    event: Dict,
    unit_type: UnitType,
    metadata_hash: str,
    ledger_api: LedgerApi,
) -> Optional[int]:
    """Verify and extract token id from a registry event"""
    event_args = event["args"]
    if event_args["uType"] == unit_type.value:
        hash_bytes32 = cast(bytes, event_args["unitHash"]).hex()
        unit_hash_bytes = UNIT_HASH_PREFIX.format(metadata_hash=hash_bytes32).encode()
        metadata_hash_bytes = ledger_api.api.toBytes(text=metadata_hash)
        if unit_hash_bytes == metadata_hash_bytes:
            return cast(int, event_args["unitId"])

    return None


def transact(ledger_api: LedgerApi, crypto: Crypto, tx: Dict) -> Dict:
    """Make a transaction and return a receipt"""

    tx_signed = crypto.sign_transaction(transaction=tx)
    tx_digest = ledger_api.send_signed_transaction(tx_signed=tx_signed)

    return ledger_api.get_transaction_receipt(tx_digest=tx_digest)


def mint_component(
    contracts_helper: ContractsHelper,
    ledger_api: LedgerApi,
    crypto: Crypto,
    metadata_hash: str,
    component_type: UnitType,
    chain_type: ChainType,
    dependencies: Optional[List[int]] = None,
) -> Optional[int]:
    """Publish component on-chain."""

    try:
        tx = contracts_helper.registries_manager.get_create_transaction(
            ledger_api=ledger_api,
            contract_address=ContractConfigs.get(
                REGISTRIES_MANAGER_CONTRACT.name
            ).contracts[chain_type],
            owner=crypto.address,
            component_type=component_type,
            metadata_hash=metadata_hash,
            dependencies=dependencies,
        )
        transact(
            ledger_api=ledger_api,
            crypto=crypto,
            tx=tx,
        )
    except RequestsConnectionError as e:
        raise ComponentMintFailed("Cannot connect to the given RPC") from e

    try:
        for (
            event_dict
        ) in contracts_helper.component_registry.get_create_unit_event_filter(
            ledger_api=ledger_api,
            contract_address=ContractConfigs.get(
                COMPONENT_REGISTRY_CONTRACT.name
            ).contracts[chain_type],
        ):
            token_id = verify_and_fetch_token_id_from_event(
                event=event_dict,
                unit_type=component_type,
                metadata_hash=metadata_hash,
                ledger_api=ledger_api,
            )
            if token_id is not None:
                return token_id
    except RequestsConnectionError as e:
        raise FailedToRetrieveTokenId(
            "Connection interrupted while waiting for the unitId emit event"
        ) from e

    return None
