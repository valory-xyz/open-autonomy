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

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from aea.common import JSONLike
from aea.configurations.base import PublicId
from aea.contracts.base import Contract
from aea.crypto.base import LedgerApi


PUBLIC_ID = PublicId.from_str("valory/service_manager:0.1.0")
ETHEREUM_ERC20 = "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE"
ETHEREUM_IDENTIFIER = "ethereum"
SERVICE_MANAGER_TOKEN_COMPATIBLE_CHAINS = (
    1,
    5,
    31337,
    100,
    10200,
)
SERVICE_MANAGER_BUILD = "ServiceManager.json"
_logger = logging.getLogger(
    f"aea.packages.{PUBLIC_ID.author}.contracts.{PUBLIC_ID.name}.contract"
)


class ServiceManagerContract(Contract):
    """The Service manager contract."""

    contract_id = PUBLIC_ID

    @classmethod
    def get_raw_transaction(  # pragma: nocover
        cls, ledger_api: LedgerApi, contract_address: str, **kwargs: Any
    ) -> Optional[JSONLike]:
        """Get the Safe transaction."""
        raise NotImplementedError

    @classmethod
    def get_raw_message(  # pragma: nocover
        cls, ledger_api: LedgerApi, contract_address: str, **kwargs: Any
    ) -> Optional[bytes]:
        """Get raw message."""
        raise NotImplementedError

    @classmethod
    def get_state(  # pragma: nocover
        cls, ledger_api: LedgerApi, contract_address: str, **kwargs: Any
    ) -> Optional[JSONLike]:
        """Get state."""
        raise NotImplementedError

    @staticmethod
    def load_service_manager_abi() -> JSONLike:
        """Load L2 ABI"""
        path = Path(__file__).parent / "build" / SERVICE_MANAGER_BUILD
        return json.loads(path.read_text(encoding="utf-8"))

    @staticmethod
    def is_service_manager_token_compatible_chain(ledger_api: LedgerApi) -> bool:
        """Check if we're interacting with a ServiceManagerToken compatible chain"""
        return ledger_api.api.eth.chain_id in SERVICE_MANAGER_TOKEN_COMPATIBLE_CHAINS

    @classmethod
    def get_instance(
        cls,
        ledger_api: LedgerApi,
        contract_address: Optional[str] = None,
    ) -> Any:
        """Get contract instance."""
        if ledger_api.identifier != ETHEREUM_IDENTIFIER:
            return super().get_instance(
                ledger_api=ledger_api, contract_address=contract_address
            )
        if cls.is_service_manager_token_compatible_chain(ledger_api=ledger_api):
            contract_interface = cls.contract_interface.get(ledger_api.identifier, {})
        else:
            contract_interface = cls.load_service_manager_abi()
        return ledger_api.get_contract_instance(contract_interface, contract_address)

    @classmethod
    def get_events(  # pragma: nocover
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        event: str,
        receipt: JSONLike,
    ) -> Dict:
        """Process receipt for events."""
        contract_interface = cls.get_instance(
            ledger_api=ledger_api,
            contract_address=contract_address,
        )
        Event = getattr(contract_interface.events, event, None)
        if Event is None:
            return {"events": []}
        return {"events": Event().process_receipt(receipt)}

    @classmethod
    def get_create_transaction(  # pylint: disable=too-many-arguments
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        owner: str,
        sender: str,
        metadata_hash: str,
        agent_ids: List[int],
        agent_params: List[List[int]],
        threshold: int,
        token: Optional[str] = None,
        raise_on_try: bool = False,
    ) -> Dict[str, Any]:
        """Retrieve the service owner."""
        method_args = {
            "serviceOwner": owner,
            "configHash": metadata_hash,
            "agentIds": agent_ids,
            "agentParams": agent_params,
            "threshold": threshold,
        }
        if cls.is_service_manager_token_compatible_chain(ledger_api=ledger_api):
            method_args["token"] = ledger_api.api.to_checksum_address(
                token or ETHEREUM_ERC20
            )

        return ledger_api.build_transaction(
            contract_instance=cls.get_instance(
                ledger_api=ledger_api, contract_address=contract_address
            ),
            method_name="create",
            method_args=method_args,
            tx_args={
                "sender_address": sender,
            },
            raise_on_try=raise_on_try,
        )

    @classmethod
    def get_update_transaction(  # pylint: disable=too-many-arguments
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        sender: str,
        service_id: int,
        metadata_hash: str,
        agent_ids: List[int],
        agent_params: List[List[int]],
        threshold: int,
        token: Optional[str] = None,
        raise_on_try: bool = False,
    ) -> Dict[str, Any]:
        """Retrieve the service owner."""
        method_args = {
            "serviceId": service_id,
            "configHash": metadata_hash,
            "agentIds": agent_ids,
            "agentParams": agent_params,
            "threshold": threshold,
        }
        if cls.is_service_manager_token_compatible_chain(ledger_api=ledger_api):
            method_args["token"] = ledger_api.api.to_checksum_address(
                token or ETHEREUM_ERC20
            )

        return ledger_api.build_transaction(
            contract_instance=cls.get_instance(
                ledger_api=ledger_api, contract_address=contract_address
            ),
            method_name="update",
            method_args=method_args,
            tx_args={
                "sender_address": sender,
            },
            raise_on_try=raise_on_try,
        )

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

    @classmethod
    def get_terminate_service_transaction(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        owner: str,
        service_id: int,
        raise_on_try: bool = False,
    ) -> Dict[str, Any]:
        """Retrieve the service owner."""

        tx_params = ledger_api.build_transaction(
            contract_instance=cls.get_instance(
                ledger_api=ledger_api, contract_address=contract_address
            ),
            method_name="terminate",
            method_args={
                "serviceId": service_id,
            },
            tx_args={"sender_address": owner},
            raise_on_try=raise_on_try,
        )

        return tx_params

    @classmethod
    def get_unbond_service_transaction(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        owner: str,
        service_id: int,
        raise_on_try: bool = False,
    ) -> Dict[str, Any]:
        """Retrieve the service owner."""

        tx_params = ledger_api.build_transaction(
            contract_instance=cls.get_instance(
                ledger_api=ledger_api, contract_address=contract_address
            ),
            method_name="unbond",
            method_args={
                "serviceId": service_id,
            },
            tx_args={"sender_address": owner},
            raise_on_try=raise_on_try,
        )

        return tx_params
