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
from typing import Dict, List, cast

from aea.common import JSONLike
from aea.configurations.base import PublicId
from aea.contracts.base import Contract
from aea_ledger_ethereum import LedgerApi, EthereumApi


address = hex

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
        # local_bytecode = cls.contract_interface["ethereum"]["deployedBytecode"]  # noqa:  E800
        # logging.error(deployed_bytecode)
        # verified = deployed_bytecode == DEPLOYED_BYTECODE
        # return dict(verified=verified)
        return deployed_bytecode

    @classmethod
    def get_service_info(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        service_id: int,
    ) -> Dict:
        """Retrieve on-chain service information"""

        contract_instance = cls.get_instance(ledger_api, contract_address)

        service_info = ledger_api.contract_method_call(
            contract_instance=contract_instance,
            method_name="getServiceInfo",
            serviceId=service_id,
        )

        owner: address = service_info[0]
        name: str = service_info[1]
        description: str = service_info[2]
        config_hash: int = service_info[4]
        threshold: int = service_info[5]
        num_agent_ids: int = service_info[6]
        agent_ids: List[int] = service_info[7]
        agent_params: List = service_info[8]

        return dict(
            owner=owner,
            name=name,
            description=description,
            config_hash=config_hash,
            threshold=threshold,
            num_agent_ids=num_agent_ids,
            agent_ids=agent_ids,
            agent_params=agent_params,
        )
