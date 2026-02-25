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
from typing import Any, Dict, Optional, cast

from aea.common import JSONLike
from aea.configurations.base import PublicId
from aea.contracts.base import Contract
from aea.crypto.base import LedgerApi
from aea_ledger_ethereum import EthereumApi
from web3 import Web3


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
        return contract_interface.events.CreateUnit().process_receipt(receipt)

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
        _, hash_updates = contract_interface.functions.getUpdatedHashes(token_id).call()
        if len(hash_updates) > 0:  # pragma: nocover
            *_, latest_hash = hash_updates
            uri = f"https://gateway.autonolas.tech/ipfs/f01701220{latest_hash.hex()}"
        else:
            uri = contract_interface.functions.tokenURI(token_id).call()
        return uri

    @classmethod
    def get_hash(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        agent_id: int,
    ) -> JSONLike:
        """Retrieve an operator given its agent instance."""

        contract_instance = cls.get_instance(ledger_api, contract_address)
        res = contract_instance.functions.getHashes(agent_id).call()
        # ensure that the returned object has the expected format
        if len(res) != 2:
            msg = f"The `getHashes` method for {contract_address=} returned data in an unexpected format: {res}"
            return dict(error=msg)

        # get the agent hashes
        hashes = res.pop(-1)
        # ensure that there are hashes returned for the agent
        if len(hashes) == 0:
            msg = f"The `getHashes` method for {contract_address=} returned no hashes for {agent_id=}: {res}"
            return dict(error=msg)

        # get the most recent agent hash
        hash_ = hashes.pop(-1)
        # ensure that the hash is in bytes
        if not isinstance(hash_, bytes):
            msg = f"The `getHashes` method for {contract_address=} returned non-bytes {hash_=} for {agent_id=}: {res}"
            return dict(error=msg)

        # return the hash in hex
        return dict(hash=hash_.hex())

    @classmethod
    def authenticate_sender(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        sender_address: str,
        mech_address: str,
    ) -> Dict[str, Any]:
        """Check if the sender address is valid."""
        ledger_api = cast(EthereumApi, ledger_api)
        contract_instance = cls.get_instance(ledger_api, contract_address)

        # assume the owner is a multisig wallet, so we check whether the sender is an owner
        try:
            # running in a try catch block because theres no guarantee
            # that the agent owner matches the abi
            minimal_abi = [
                {
                    "constant": True,
                    "inputs": [],
                    "name": "getOwners",
                    "outputs": [{"name": "", "type": "address[]"}],
                    "payable": False,
                    "stateMutability": "view",
                    "type": "function",
                },
                {
                    "inputs": [],
                    "name": "tokenId",
                    "outputs": [
                        {"internalType": "uint256", "name": "", "type": "uint256"}
                    ],
                    "stateMutability": "view",
                    "type": "function",
                },
            ]
            contract = ledger_api.api.eth.contract(
                address=Web3.to_checksum_address(mech_address), abi=minimal_abi
            )
            agent_id = contract.functions.tokenId().call()

            agent_owner = contract_instance.functions.ownerOf(agent_id).call()
            if Web3.to_checksum_address(agent_owner) == Web3.to_checksum_address(
                sender_address
            ):
                return dict(is_valid=True)

            safe_contract = ledger_api.api.eth.contract(
                address=Web3.to_checksum_address(agent_owner), abi=minimal_abi
            )
            owners = safe_contract.functions.getOwners().call()
            if Web3.to_checksum_address(sender_address) in owners:
                return dict(is_valid=True)

            return dict(is_valid=False)

        except Exception as e:
            return dict(is_valid=False, error=str(e))  # pragma: no cover
