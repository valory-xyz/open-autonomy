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

"""This module contains the class to connect to the Service Registry contract."""

import logging
from typing import Any, Optional, cast

from aea.common import JSONLike
from aea.configurations.base import PublicId
from aea.contracts.base import Contract
from aea.crypto.base import LedgerApi


PUBLIC_ID = PublicId.from_str("valory/agent_registry:0.1.0")

AGENT_UNIT_TYPE = 1
UNIT_HASH_PREFIX = "0x{metadata_hash}"

_logger = logging.getLogger(
    f"aea.packages.{PUBLIC_ID.author}.contracts.{PUBLIC_ID.name}.contract"
)


class AgentRegistryContract(Contract):
    """The Agent Registry contract."""

    contract_id = PUBLIC_ID

    @classmethod
    def get_raw_transaction(
        cls, ledger_api: LedgerApi, contract_address: str, **kwargs: Any
    ) -> Optional[JSONLike]:
        """Get the Safe transaction."""
        raise NotImplementedError

    @classmethod
    def get_raw_message(
        cls, ledger_api: LedgerApi, contract_address: str, **kwargs: Any
    ) -> Optional[bytes]:
        """Get raw message."""
        raise NotImplementedError

    @classmethod
    def get_state(
        cls, ledger_api: LedgerApi, contract_address: str, **kwargs: Any
    ) -> Optional[JSONLike]:
        """Get state."""
        raise NotImplementedError

    @classmethod
    def get_token_uri(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        token_id: int,
    ) -> str:
        """Returns `CreateUnit` event filter."""

        contract_interface = cls.get_instance(
            ledger_api=ledger_api,
            contract_address=contract_address,
        )
        return contract_interface.functions.tokenURI(token_id).call()

    @classmethod
    def filter_token_id_from_emitted_events(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        metadata_hash: str,
    ) -> Optional[int]:
        """Returns `CreateUnit` event filter."""

        contract_interface = cls.get_instance(
            ledger_api=ledger_api,
            contract_address=contract_address,
        )

        events = contract_interface.events.CreateUnit.createFilter(
            fromBlock="latest"
        ).get_all_entries()

        for event in events:
            event_args = event["args"]
            if event_args["uType"] == AGENT_UNIT_TYPE:
                hash_bytes32 = cast(bytes, event_args["unitHash"]).hex()
                unit_hash_bytes = UNIT_HASH_PREFIX.format(
                    metadata_hash=hash_bytes32
                ).encode()
                metadata_hash_bytes = ledger_api.api.toBytes(text=metadata_hash)
                if unit_hash_bytes == metadata_hash_bytes:
                    return cast(int, event_args["unitId"])

        return None
