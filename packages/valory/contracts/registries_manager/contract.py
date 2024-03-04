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

"""This module contains the class to connect to the Service Registry contract."""

import logging
from enum import Enum
from typing import Any, List, Optional

from aea.common import JSONLike
from aea.configurations.base import PublicId
from aea.contracts.base import Contract
from aea.crypto.base import LedgerApi


PUBLIC_ID = PublicId.from_str("valory/registries_manager:0.1.0")

_logger = logging.getLogger(
    f"aea.packages.{PUBLIC_ID.author}.contracts.{PUBLIC_ID.name}.contract"
)


class RegistriesManagerContract(Contract):
    """The Service Registry contract."""

    contract_id = PUBLIC_ID

    class UnitType(Enum):
        """Unit type."""

        COMPONENT = 0
        AGENT = 1

    @classmethod
    def get_raw_transaction(
        cls, ledger_api: LedgerApi, contract_address: str, **kwargs: Any
    ) -> Optional[JSONLike]:
        """Get the Safe transaction."""
        raise NotImplementedError  # pragma: nocover

    @classmethod
    def get_raw_message(
        cls, ledger_api: LedgerApi, contract_address: str, **kwargs: Any
    ) -> Optional[bytes]:
        """Get raw message."""
        raise NotImplementedError  # pragma: nocover

    @classmethod
    def get_state(
        cls, ledger_api: LedgerApi, contract_address: str, **kwargs: Any
    ) -> Optional[JSONLike]:
        """Get state."""
        raise NotImplementedError  # pragma: nocover

    @classmethod
    def get_create_transaction(  # pylint: disable=too-many-arguments
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        component_type: UnitType,
        metadata_hash: str,
        owner: str,
        sender: str,
        dependencies: Optional[List[int]] = None,
        raise_on_try: bool = False,
    ) -> JSONLike:
        """Create a component."""
        dependencies = list(sorted(dependencies or []))
        tx_params = ledger_api.build_transaction(
            contract_instance=cls.get_instance(
                ledger_api=ledger_api, contract_address=contract_address
            ),
            method_name="create",
            method_args={
                "unitType": component_type.value,
                "unitOwner": owner,
                "unitHash": metadata_hash,
                "dependencies": dependencies,
            },
            tx_args={
                "sender_address": sender,
            },
            raise_on_try=raise_on_try,
        )
        return tx_params

    @classmethod
    def get_update_hash_transaction(  # pylint: disable=too-many-arguments
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        component_type: UnitType,
        unit_id: int,
        metadata_hash: str,
        sender: str,
        raise_on_try: bool = False,
    ) -> JSONLike:
        """Create a component."""

        tx_params = ledger_api.build_transaction(
            contract_instance=cls.get_instance(
                ledger_api=ledger_api, contract_address=contract_address
            ),
            method_name="updateHash",
            method_args={
                "unitType": component_type.value,
                "unitId": unit_id,
                "unitHash": metadata_hash,
            },
            tx_args={
                "sender_address": sender,
            },
            raise_on_try=raise_on_try,
        )
        return tx_params
