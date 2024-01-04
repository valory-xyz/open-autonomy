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

import hashlib
import json
import logging
from pathlib import Path
from typing import Any, Dict, FrozenSet, List, Optional, Tuple, Union, cast

from aea.common import JSONLike
from aea.configurations.base import PublicId
from aea.contracts.base import Contract
from aea.crypto.base import LedgerApi
from web3.types import BlockData, EventData, TxReceipt


PUBLIC_ID = PublicId.from_str("valory/service_registry:0.1.0")
ETHEREUM_IDENTIFIER = "ethereum"
UNIT_HASH_PREFIX = "0x{metadata_hash}"
EXPECTED_CONTRACT_ADDRESS_BY_CHAIN_ID = {
    1: "0x48b6af7B12C71f09e2fC8aF4855De4Ff54e775cA",
    5: "0x1cEe30D08943EB58EFF84DD1AB44a6ee6FEff63a",
    100: "0x9338b5153AE39BB89f50468E608eD9d764B755fD",
    137: "0xE3607b00E75f6405248323A9417ff6b39B244b50",
    31337: "0x998abeb3E57409262aE5b751f60747921B33613E",
}
DEPLOYED_BYTECODE_MD5_HASH_BY_CHAIN_ID = {
    1: "6f9fc7f3c2348801737120e6b5f8fa8e9670c65152c66d128ff4cddb465b4d705340c559e352f5e7f29bda3b84a8d36d4a9448b791cfe2d370e31c01276e0244",
    5: "d4a860f21f17762c99d93359244b39a878dd5bac9ea6056c0ff29c7558d6653aa0d5962aa819fc9f05f237d068845125cfc37a7fd7761b11c29a709ad5c48157",
    100: "10e2cfb500481d6c5a3b6b90507e4ac04d8b0d88741cea5568306ed4115f24e8b9747055423da5fca05838d5ccefebf41fb47d2ba1fb45215b6b21c0a27823be",
    137: "10e2cfb500481d6c5a3b6b90507e4ac04d8b0d88741cea5568306ed4115f24e8b9747055423da5fca05838d5ccefebf41fb47d2ba1fb45215b6b21c0a27823be",
    31337: "41ab54d43fd4bdfdc929658a0dc9bedd970c7339eecafbefda9892ab54c02c396bceedaa3a84a0f4690bee03dc11195a3267a264de7859c420efbf4291f1fef0",
}
L1_CHAINS = (
    1,
    5,
    31337,
)
L2_BUILD_FILENAME = "ServiceRegistryL2.json"

ServiceInfo = Tuple[int, str, bytes, int, int, int, int, List[int]]

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

    @staticmethod
    def is_l1_chain(ledger_api: LedgerApi) -> bool:
        """Check if we're interecting with an L1 chain"""
        return ledger_api.api.eth.chain_id in L1_CHAINS

    @staticmethod
    def load_l2_build() -> JSONLike:
        """Load L2 ABI"""
        path = Path(__file__).parent / "build" / L2_BUILD_FILENAME
        return json.loads(path.read_text(encoding="utf-8"))

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
        if cls.is_l1_chain(ledger_api=ledger_api):
            contract_interface = cls.contract_interface.get(ledger_api.identifier, {})
        else:
            contract_interface = cls.load_l2_build()
        instance = ledger_api.get_contract_instance(
            contract_interface, contract_address
        )
        return instance

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
        if not verified:  # pragma: nocover
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
            unitId=service_id,
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

    @classmethod
    def get_service_owner(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        service_id: int,
    ) -> Dict[str, Any]:
        """Retrieve the service owner."""
        contract_instance = cls.get_instance(ledger_api, contract_address)
        service_owner = contract_instance.functions.ownerOf(service_id).call()
        checksum_service_owner = ledger_api.api.to_checksum_address(service_owner)
        return dict(
            service_owner=checksum_service_owner,
        )

    @classmethod
    def get_service_information(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        token_id: int,
    ) -> ServiceInfo:
        """Retrieve service information"""

        contract_interface = cls.get_instance(
            ledger_api=ledger_api,
            contract_address=contract_address,
        )
        return contract_interface.functions.getService(token_id).call()

    @classmethod
    def get_token_uri(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        token_id: int,
    ) -> str:
        """Returns the latest metadata URI for a component."""
        contract_interface = cls.get_instance(
            ledger_api=ledger_api,
            contract_address=contract_address,
        )
        return contract_interface.functions.tokenURI(token_id).call()

    @classmethod
    def get_create_events(  # pragma: nocover
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        receipt: JSONLike,
    ) -> Optional[int]:
        """Returns `CreateUnit` event filter."""
        contract_interface = cls.get_instance(
            ledger_api=ledger_api,
            contract_address=contract_address,
        )
        return contract_interface.events.CreateService().process_receipt(receipt)

    @classmethod
    def get_update_events(  # pragma: nocover
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        receipt: JSONLike,
    ) -> Optional[int]:
        """Returns `CreateUnit` event filter."""
        contract_interface = cls.get_instance(
            ledger_api=ledger_api,
            contract_address=contract_address,
        )
        return contract_interface.events.UpdateService().process_receipt(receipt)

    @classmethod
    def get_update_hash_events(  # pragma: nocover
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        receipt: JSONLike,
    ) -> Optional[int]:
        """Returns `CreateUnit` event filter."""
        contract_interface = cls.get_instance(
            ledger_api=ledger_api,
            contract_address=contract_address,
        )
        return contract_interface.events.UpdateUnitHash().process_receipt(receipt)

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
    def process_receipt(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        event: str,
        receipt: JSONLike,
    ) -> JSONLike:
        """Checks for a successful service registration event in the latest block"""
        contract_interface = cls.get_instance(
            ledger_api=ledger_api,
            contract_address=contract_address,
        )
        Event = getattr(contract_interface.events, event, None)
        if Event is None:
            return {"events": []}
        return {"events": Event().process_receipt(receipt)}

    @classmethod
    def get_slash_data(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        agent_instances: List[str],
        amounts: List[int],
        service_id: int,
    ) -> Dict[str, bytes]:
        """Gets the encoded arguments for a slashing tx, which should only be called via the multisig."""

        contract_instance = cls.get_instance(
            ledger_api=ledger_api,
            contract_address=contract_address,
        )

        slash_kwargs = dict(
            agentInstances=agent_instances,
            amounts=amounts,
            serviceId=service_id,
        )

        data = contract_instance.encodeABI(fn_name="slash", kwargs=slash_kwargs)
        return {"data": bytes.fromhex(data[2:])}

    @classmethod
    def process_slash_receipt(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        tx_hash: str,
    ) -> Optional[JSONLike]:
        """
        Process the slash receipt.

        :param ledger_api: the ledger apis.
        :param contract_address: the contract address.
        :param tx_hash: the hash of a slash tx to be processed.
        :return: a dictionary with the timestamp of the slashing and the `OperatorSlashed` events.
        """
        contract = cls.get_instance(ledger_api, contract_address)
        receipt: TxReceipt = ledger_api.api.eth.get_transaction_receipt(tx_hash)
        logs: List[EventData] = list(
            contract.events.OperatorSlashed().process_receipt(receipt)
        )

        if len(logs) == 0:
            _logger.error(f"No `OperatorSlashed` event was emitted in tx {tx_hash}.")
            return None

        block: BlockData = ledger_api.api.eth.get_block(receipt["blockNumber"])

        return {
            "slash_timestamp": block["timestamp"],
            "events": [log["args"] for log in logs],
        }

    @classmethod
    def _get_operator(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        agent_instance: str,
    ) -> str:
        """Retrieve an operator given its agent instance."""

        contract_instance = cls.get_instance(ledger_api, contract_address)
        map_fn = contract_instance.functions.mapAgentInstanceOperators
        return map_fn(agent_instance).call()

    @classmethod
    def get_operators_mapping(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        agent_instances: FrozenSet[str],
    ) -> Dict[str, str]:
        """
        Retrieve a mapping of the given agent instances to their operators.

        Please keep in mind that this method performs a call for each agent instance.

        :param ledger_api: the ledger api.
        :param contract_address: the contract address.
        :param agent_instances: the agent instances to be mapped.
        :return: a mapping of the given agent instances to their operators.
        """
        return {
            agent: cls._get_operator(ledger_api, contract_address, agent)
            for agent in agent_instances
        }
