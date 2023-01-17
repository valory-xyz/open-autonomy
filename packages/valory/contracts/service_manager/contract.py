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
from typing import Any, Dict, List, Optional

from aea.common import JSONLike
from aea.configurations.base import PublicId
from aea.contracts.base import Contract
from aea.crypto.base import LedgerApi


PUBLIC_ID = PublicId.from_str("valory/service_manager:0.1.0")

_logger = logging.getLogger(
    f"aea.packages.{PUBLIC_ID.author}.contracts.{PUBLIC_ID.name}.contract"
)


class ServiceManagerContract(Contract):
    """The Service manager contract."""

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
    def get_create_transaction(  # pylint: disable=too-many-arguments
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        owner: str,
        metadata_hash: str,
        agent_ids: List[int],
        agent_params: List[List[int]],
        threshold: int,
        raise_on_try: bool = False,
    ) -> Dict[str, Any]:
        """Retrieve the service owner."""

        tx_params = ledger_api.build_transaction(
            contract_instance=cls.get_instance(
                ledger_api=ledger_api, contract_address=contract_address
            ),
            method_name="create",
            method_args={
                "serviceOwner": owner,
                "configHash": metadata_hash,
                "agentIds": agent_ids,
                "agentParams": agent_params,
                "threshold": threshold,
            },
            tx_args={
                "sender_address": owner,
            },
            raise_on_try=raise_on_try,
        )
        return tx_params

    @classmethod
    def get_activate_registration_transaction(  # pylint: disable=too-many-arguments
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        owner: str,
        service_id: int,
        security_deposit: int,
        raise_on_try: bool = False,
    ) -> Dict[str, Any]:
        """Retrieve the service owner."""

        tx_params = ledger_api.build_transaction(
            contract_instance=cls.get_instance(
                ledger_api=ledger_api, contract_address=contract_address
            ),
            method_name="activateRegistration",
            method_args={
                "serviceId": service_id,
            },
            tx_args={"sender_address": owner, "value": security_deposit},
            raise_on_try=raise_on_try,
        )

        return tx_params

    @classmethod
    def get_register_instance_transaction(  # pylint: disable=too-many-arguments
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        owner: str,
        service_id: int,
        instances: List[str],
        agent_ids: List[int],
        security_deposit: int,
        raise_on_try: bool = False,
    ) -> Dict[str, Any]:
        """Retrieve the service owner."""

        tx_params = ledger_api.build_transaction(
            contract_instance=cls.get_instance(
                ledger_api=ledger_api, contract_address=contract_address
            ),
            method_name="registerAgents",
            method_args={
                "serviceId": service_id,
                "agentInstances": instances,
                "agentIds": agent_ids,
            },
            tx_args={"sender_address": owner, "value": security_deposit},
            raise_on_try=raise_on_try,
        )

        return tx_params

    @classmethod
    def get_service_deploy_transaction(  # pylint: disable=too-many-arguments
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        owner: str,
        service_id: int,
        gnosis_safe_multisig: str,
        deployment_payload: str,
        raise_on_try: bool = False,
    ) -> Dict[str, Any]:
        """Retrieve the service owner."""

        tx_params = ledger_api.build_transaction(
            contract_instance=cls.get_instance(
                ledger_api=ledger_api, contract_address=contract_address
            ),
            method_name="deploy",
            method_args={
                "serviceId": service_id,
                "multisigImplementation": gnosis_safe_multisig,
                "data": deployment_payload,
            },
            tx_args={"sender_address": owner},
            raise_on_try=raise_on_try,
        )

        return tx_params
