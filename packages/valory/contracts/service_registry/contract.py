# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
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
from typing import Dict, List, Tuple, Any, Optional, cast

import hashlib
from aea.common import JSONLike
from aea.configurations.base import PublicId
from aea.contracts.base import Contract
from aea_ledger_ethereum import LedgerApi, EthereumApi


DEPLOYED_BYTECODE_MD5_HASH = "dbddd97ffe22b97d04cfe242e3570fd0"

Address = hex
ConfigHash = Tuple[bytes, int, int]
AgentParams = Tuple[int, int]

PUBLIC_ID = PublicId.from_str("valory/service_registry:0.1.0")

_logger = logging.getLogger(
    f"aea.packages.{PUBLIC_ID.author}.contracts.{PUBLIC_ID.name}.contract"
)


class ServiceRegistryContract(Contract):
    """The Service Registry contract."""

    contract_id = PUBLIC_ID

    @classmethod
    def verify_contract(
        cls, ledger_api: LedgerApi, contract_address: str
    ) -> JSONLike:
        """
        Verify the contract's bytecode

        :param ledger_api: the ledger API object
        :param contract_address: the contract address
        :return: the verified status
        """
        ledger_api = cast(EthereumApi, ledger_api)
        deployed_bytecode = ledger_api.api.eth.get_code(contract_address).hex()
        md5_hash = hashlib.md5(deployed_bytecode.encode("utf-8")).hexdigest()
        verified = md5_hash == DEPLOYED_BYTECODE_MD5_HASH
        return dict(verified=verified)

    @classmethod
    def change_service_manager(
        cls,
        ledger_api,
        contract_address,
        new_manager: Address,
        **tx_args: Any,
    ) -> JSONLike:
        """Change service manager"""

        contract_instance = cls.get_instance(ledger_api, contract_address)
        kwargs = dict(newManager=new_manager)

        return ledger_api.build_transaction(
            contract_instance,
            "changeManager",
            method_args=kwargs,
            tx_args=tx_args,
        )

    @classmethod
    def create_service(
        cls,
        ledger_api,
        contract_address,
        owner: Address,
        name: str,
        description: str,
        config_hash: ConfigHash,
        agent_ids: List[int],
        agent_params: List[AgentParams],
        threshold: int,
        **tx_args: Any,
    ) -> JSONLike:
        """Create service on-chain"""

        contract_instance = cls.get_instance(ledger_api, contract_address)
        kwargs = dict(
            owner=owner,
            name=name,
            description=description,
            configHash=config_hash,
            agentIds=agent_ids,
            agentParams=agent_params,
            threshold=threshold,
        )

        return ledger_api.build_transaction(
            contract_instance,
            "createService",
            method_args=kwargs,
            tx_args=tx_args,
        )

    @classmethod
    def owner_of(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        service_id: int,
    ) -> Address:
        """Gets the allowance for a spender."""

        contract_instance = cls.get_instance(ledger_api, contract_address)
        owner = ledger_api.contract_method_call(
            contract_instance=contract_instance,
            method_name="ownerOf",
            serviceId=service_id,
        )

        return owner

    @classmethod
    def exists(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        service_id: int,
    ) -> bool:
        """Check if the service id exists"""

        contract_instance = cls.get_instance(ledger_api, contract_address)
        exists = ledger_api.contract_method_call(
            contract_instance=contract_instance,
            method_name="exists",
            serviceId=service_id,
        )

        return cast(bool, exists)

    @classmethod
    def get_service_info(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        service_id: int,
    ) -> JSONLike:
        """Retrieve on-chain service information"""

        contract_instance = cls.get_instance(ledger_api, contract_address)

        return ledger_api.contract_method_call(
            contract_instance=contract_instance,
            method_name="getServiceInfo",
            serviceId=service_id,
        )
