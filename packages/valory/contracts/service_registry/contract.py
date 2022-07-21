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


# test_contract and test_agents, respectively...
DEPLOYED_BYTECODE_MD5_HASH = (
    "214e9d30f9c86845f893232219b3e47608a534d142451299cddfbcad5788d83e"
    "21aafff2ef613742e7d0ed5adeff302ef858004af158bba45936c57d1c3a1a70"
)

PUBLIC_ID = PublicId.from_str("valory/service_registry:0.1.0")

CHAIN_ADDRESS = "https://chain.staging.autonolas.tech"
CHAIN_ID = 31337

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
        ledger_api = cast(EthereumApi, ledger_api)
        deployed_bytecode = ledger_api.api.eth.get_code(contract_address).hex()
        sha512_hash = hashlib.sha512(deployed_bytecode.encode("utf-8")).hexdigest()
        verified = DEPLOYED_BYTECODE_MD5_HASH == sha512_hash
        if not verified:
            log_msg = "CONTRACT NOT VERIFIED! reason: frequent changes."
            log_msg += f". Verified: {verified}. Contract address: {contract_address}."
            _logger.error(f"{log_msg} Address: {CHAIN_ADDRESS}, chain_id: {CHAIN_ID}")
        return dict(verified=verified, sha512_hash=sha512_hash)

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
