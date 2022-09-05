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

import hashlib
import logging
from typing import Any, Dict, Optional, Union, cast

from aea.common import JSONLike
from aea.configurations.base import PublicId
from aea.contracts.base import Contract
from aea_ledger_ethereum import EthereumApi, LedgerApi


EXPECTED_CONTRACT_ADDRESS_BY_CHAIN_ID = {
    1: "0x48b6af7B12C71f09e2fC8aF4855De4Ff54e775cA",
    5: "0x1cEe30D08943EB58EFF84DD1AB44a6ee6FEff63a",
    31337: "0x998abeb3E57409262aE5b751f60747921B33613E",
}
DEPLOYED_BYTECODE_MD5_HASH_BY_CHAIN_ID = {
    1: "6f9fc7f3c2348801737120e6b5f8fa8e9670c65152c66d128ff4cddb465b4d705340c559e352f5e7f29bda3b84a8d36d4a9448b791cfe2d370e31c01276e0244",
    5: "d4a860f21f17762c99d93359244b39a878dd5bac9ea6056c0ff29c7558d6653aa0d5962aa819fc9f05f237d068845125cfc37a7fd7761b11c29a709ad5c48157",
    31337: "d8084598f884509694ab1f244cbb8e7697d8db00c241710b89b2ec3037d2edd3b82d01f1f0ca6bd9b265b1184d9c563a6000c30958c2a7ae5a9c35e5ff2ba7de",
}

PUBLIC_ID = PublicId.from_str("valory/service_registry:0.1.0")

_logger = logging.getLogger(
    f"aea.packages.{PUBLIC_ID.author}.contracts.{PUBLIC_ID.name}.contract"
)


class ServiceRegistryContract(Contract):
    """The Service Registry contract."""

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
    def verify_contract(
        cls, ledger_api: LedgerApi, contract_address: str
    ) -> Dict[str, Union[bool, str]]:
        """
        Verify the contract's bytecode

        :param ledger_api: the ledger API object
        :param contract_address: the contract address
        :return: the verified status
        """
        verified = False
        ledger_api = cast(EthereumApi, ledger_api)
        chain_id = ledger_api.api.eth.chain_id
        expected_address = EXPECTED_CONTRACT_ADDRESS_BY_CHAIN_ID[chain_id]
        if contract_address != expected_address:
            _logger.error(
                f"For chain_id {chain_id} expected {expected_address} and got {contract_address}."
            )
            return dict(verified=verified)
        deployed_bytecode = ledger_api.api.eth.get_code(contract_address).hex()
        sha512_hash = hashlib.sha512(deployed_bytecode.encode("utf-8")).hexdigest()
        verified = DEPLOYED_BYTECODE_MD5_HASH_BY_CHAIN_ID[chain_id] == sha512_hash
        if not verified:
            _logger.error(
                f"CONTRACT NOT VERIFIED! Contract address: {contract_address}, chain_id: {chain_id}."
            )
        return dict(verified=verified)

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
    def get_agent_instances(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        service_id: int,
    ) -> Dict[str, Any]:
        """Retrieve on-chain agent instances."""

        contract_instance = cls.get_instance(ledger_api, contract_address)
        service_info = ledger_api.contract_method_call(
            contract_instance=contract_instance,
            method_name="getAgentInstances",
            serviceId=service_id,
        )

        return dict(
            numAgentInstances=service_info[0],
            agentInstances=service_info[1],
        )
