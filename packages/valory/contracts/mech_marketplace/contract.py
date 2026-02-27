# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2023-2026 Valory AG
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

"""This module contains the Mech Marketplace contract definition."""

import logging
from enum import Enum
from typing import Any, Dict, List, Union, cast

from aea.common import JSONLike
from aea.configurations.base import PublicId
from aea.contracts.base import Contract
from aea.crypto.base import LedgerApi
from aea_ledger_ethereum import EthereumApi
from eth_typing import ChecksumAddress
from eth_utils import event_abi_to_log_topic
from hexbytes import HexBytes
from web3 import Web3
from web3._utils.events import get_event_data
from web3.types import BlockIdentifier, FilterParams, TxReceipt


PUBLIC_ID = PublicId.from_str("valory/mech_marketplace:0.1.0")

_logger = logging.getLogger(
    f"aea.packages.{PUBLIC_ID.author}.contracts.{PUBLIC_ID.name}.contract"
)

BATCH_REQUESTID_STATUS_DATA = {
    "abi": [
        {
            "inputs": [
                {
                    "internalType": "contract IMechMarketplace",
                    "name": "_marketplace",
                    "type": "address",
                },
                {
                    "internalType": "bytes32[]",
                    "name": "_requestIds",
                    "type": "bytes32[]",
                },
            ],
            "stateMutability": "nonpayable",
            "type": "constructor",
        }
    ],
    "bytecode": "608060405234801561000f575f5ffd5b5060405161071a38038061071a8339818101604052810190610031919061049b565b5f815190505f8167ffffffffffffffff8111156100515761005061032c565b5b60405190808252806020026020018201604052801561007f5781602001602082028036833780820191505090505b5090505f5f5b838110156101d1575f8673ffffffffffffffffffffffffffffffffffffffff166345d076648784815181106100bd576100bc6104f5565b5b60200260200101516040518263ffffffff1660e01b81526004016100e19190610531565b602060405180830381865afa1580156100fc573d5f5f3e3d5ffd5b505050506040513d601f19601f82011682018060405250810190610120919061056d565b90506001600381111561013657610135610598565b5b81600381111561014957610148610598565b5b148061017957506002600381111561016457610163610598565b5b81600381111561017757610176610598565b5b145b156101c557858281518110610191576101906104f5565b5b60200260200101518484815181106101ac576101ab6104f5565b5b602002602001018181525050826101c2906105fb565b92505b81600101915050610085565b505f8167ffffffffffffffff8111156101ed576101ec61032c565b5b60405190808252806020026020018201604052801561021b5781602001602082028036833780820191505090505b5090505f5b8281101561026d5783818151811061023b5761023a6104f5565b5b6020026020010151828281518110610256576102556104f5565b5b602002602001018181525050806001019050610220565b505f8160405160200161028091906106f9565b6040516020818303038152906040529050602081018059038082f35b5f604051905090565b5f5ffd5b5f5ffd5b5f73ffffffffffffffffffffffffffffffffffffffff82169050919050565b5f6102d6826102ad565b9050919050565b5f6102e7826102cc565b9050919050565b6102f7816102dd565b8114610301575f5ffd5b50565b5f81519050610312816102ee565b92915050565b5f5ffd5b5f601f19601f8301169050919050565b7f4e487b71000000000000000000000000000000000000000000000000000000005f52604160045260245ffd5b6103628261031c565b810181811067ffffffffffffffff821117156103815761038061032c565b5b80604052505050565b5f61039361029c565b905061039f8282610359565b919050565b5f67ffffffffffffffff8211156103be576103bd61032c565b5b602082029050602081019050919050565b5f5ffd5b5f819050919050565b6103e5816103d3565b81146103ef575f5ffd5b50565b5f81519050610400816103dc565b92915050565b5f610418610413846103a4565b61038a565b9050808382526020820190506020840283018581111561043b5761043a6103cf565b5b835b81811015610464578061045088826103f2565b84526020840193505060208101905061043d565b5050509392505050565b5f82601f83011261048257610481610318565b5b8151610492848260208601610406565b91505092915050565b5f5f604083850312156104b1576104b06102a5565b5b5f6104be85828601610304565b925050602083015167ffffffffffffffff8111156104df576104de6102a9565b5b6104eb8582860161046e565b9150509250929050565b7f4e487b71000000000000000000000000000000000000000000000000000000005f52603260045260245ffd5b61052b816103d3565b82525050565b5f6020820190506105445f830184610522565b92915050565b60048110610556575f5ffd5b50565b5f815190506105678161054a565b92915050565b5f60208284031215610582576105816102a5565b5b5f61058f84828501610559565b91505092915050565b7f4e487b71000000000000000000000000000000000000000000000000000000005f52602160045260245ffd5b7f4e487b71000000000000000000000000000000000000000000000000000000005f52601160045260245ffd5b5f819050919050565b5f610605826105f2565b91507fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff8203610637576106366105c5565b5b600182019050919050565b5f81519050919050565b5f82825260208201905092915050565b5f819050602082019050919050565b610674816103d3565b82525050565b5f610685838361066b565b60208301905092915050565b5f602082019050919050565b5f6106a782610642565b6106b1818561064c565b93506106bc8361065c565b805f5b838110156106ec5781516106d3888261067a565b97506106de83610691565b9250506001810190506106bf565b5085935050505092915050565b5f6020820190508181035f830152610711818461069d565b90509291505056fe",
}

TOPIC_BYTES = 32
TOPIC_CHARS = TOPIC_BYTES * 2
Ox = "0x"
Ox_CHARS = len(Ox)
DELIVERY_RATE_INDEX = 4


class MechOperation(Enum):
    """Operation types."""

    CALL = 0
    DELEGATE_CALL = 1


def pad_address_for_topic(address: str) -> HexBytes:
    """Left-pad an Ethereum address to 32 bytes for use in a topic."""
    return HexBytes(Ox + address[Ox_CHARS:].zfill(TOPIC_CHARS))


class MechMarketplaceContract(Contract):
    """The scaffold contract class for a smart contract."""

    contract_id = PublicId.from_str("valory/mech_marketplace:0.1.0")

    @classmethod
    def get_raw_transaction(
        cls, ledger_api: LedgerApi, contract_address: str, **kwargs: Any
    ) -> JSONLike:
        """
        Handler method for the 'GET_RAW_TRANSACTION' requests.

        Implement this method in the sub class if you want
        to handle the contract requests manually.

        :param ledger_api: the ledger apis.
        :param contract_address: the contract address.
        :param kwargs: the keyword arguments.
        :return: the tx  # noqa: DAR202
        """
        raise NotImplementedError

    @classmethod
    def get_raw_message(
        cls, ledger_api: LedgerApi, contract_address: str, **kwargs: Any
    ) -> bytes:
        """
        Handler method for the 'GET_RAW_MESSAGE' requests.

        Implement this method in the sub class if you want
        to handle the contract requests manually.

        :param ledger_api: the ledger apis.
        :param contract_address: the contract address.
        :param kwargs: the keyword arguments.
        :return: the tx  # noqa: DAR202
        """
        raise NotImplementedError

    @classmethod
    def get_state(
        cls, ledger_api: LedgerApi, contract_address: str, **kwargs: Any
    ) -> JSONLike:
        """
        Handler method for the 'GET_STATE' requests.

        Implement this method in the sub class if you want
        to handle the contract requests manually.

        :param ledger_api: the ledger apis.
        :param contract_address: the contract address.
        :param kwargs: the keyword arguments.
        :return: the tx  # noqa: DAR202
        """
        raise NotImplementedError

    @classmethod
    def get_deliver_data(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        sender_address: str,
        request_id: int,
        data: str,
        delivery_mech_staking_instance: str,
        delivery_mech_service_id: int,
    ) -> JSONLike:
        """
        Deliver a response to a request.

        :param ledger_api: LedgerApi object
        :param contract_address: the address of the token to be used
        :param sender_address: the address of the sender
        :param request_id: the id of the target request
        :param data: the response data
        :param delivery_mech_staking_instance: the staking instance
        :param delivery_mech_service_id: the service id
        :return: the deliver data
        """
        ledger_api = cast(EthereumApi, ledger_api)
        contract_instance = cls.get_instance(ledger_api, contract_address)
        data = contract_instance.encode_abi(
            abi_element_identifier="deliverMarketplace",
            args=[
                request_id,
                bytes.fromhex(data),
                delivery_mech_staking_instance,
                delivery_mech_service_id,
            ],
        )

        simulation_ok = cls.simulate_tx(
            ledger_api, contract_address, sender_address, data
        ).pop("data")
        return {"data": bytes.fromhex(data[2:]), "simulation_ok": simulation_ok}  # type: ignore

    @classmethod
    def get_request_events(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        from_block: BlockIdentifier = "earliest",
        to_block: BlockIdentifier = "latest",
    ) -> JSONLike:
        """Get the Request events emitted by the contract."""
        ledger_api = cast(EthereumApi, ledger_api)
        contract_instance = cls.get_instance(ledger_api, contract_address)
        event_abi = contract_instance.events.MarketplaceRequest().abi
        entries = cls.get_event_entries(
            ledger_api=ledger_api,
            event_abi=event_abi,
            address=contract_instance.address,
            from_block=from_block,
            to_block=to_block,
        )

        request_events = list(
            {
                "tx_hash": entry.transactionHash.to_0x_hex(),
                "block_number": entry.blockNumber,
                **entry["args"],
                "sender": entry["args"]["requester"],
            }
            for entry in entries
        )
        return {"data": request_events}

    @classmethod
    def get_deliver_events(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        from_block: BlockIdentifier = "earliest",
        to_block: BlockIdentifier = "latest",
    ) -> JSONLike:
        """Get the Deliver events emitted by the contract."""
        ledger_api = cast(EthereumApi, ledger_api)
        contract_instance = cls.get_instance(ledger_api, contract_address)
        event_abi = contract_instance.events.MarketplaceDeliver().abi
        entries = cls.get_event_entries(
            ledger_api=ledger_api,
            event_abi=event_abi,
            address=contract_instance.address,
            from_block=from_block,
            to_block=to_block,
        )

        request_events = list(
            {
                "tx_hash": entry.transactionHash.to_0x_hex(),
                "block_number": entry.blockNumber,
                **entry["args"],
                "contract_address": contract_address,
            }
            for entry in entries
        )
        return {"data": request_events}

    @classmethod
    def get_marketplace_undelivered_reqs(  # pylint: disable=too-many-locals,unused-argument
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        wait_for_timeout_tasks: List[Dict[str, Any]],
        timeout_tasks: List[Dict[str, Any]],
        marketplace_address: str,
        from_block: BlockIdentifier = "earliest",
        to_block: BlockIdentifier = "latest",
        max_block_window: int = 1000,
        **kwargs: Any,
    ) -> JSONLike:
        """Get the requests that are not delivered."""
        if from_block == "earliest":
            from_block = 0
        current_block = ledger_api.api.eth.block_number
        checksumed_contract_address = Web3.to_checksum_address(marketplace_address)
        requests, delivers = [], []
        for from_block_batch in range(int(from_block), current_block, max_block_window):
            to_block_batch: Union[int, str] = (from_block_batch + max_block_window) - 1
            if to_block_batch >= current_block:
                to_block_batch = "latest"
            requests_batch: List[Dict[str, Any]] = cls.get_marketplace_request_events(
                ledger_api,
                checksumed_contract_address,
                from_block_batch,
                to_block_batch,
            )["data"]
            delivers_batch: List[Dict[str, Any]] = cls.get_marketplace_deliver_events(
                ledger_api,
                checksumed_contract_address,
                from_block_batch,
                to_block_batch,
            )["data"]
            requests.extend(requests_batch)
            delivers.extend(delivers_batch)
        existing_ids = {rid for d in delivers for rid in d["requestIds"]}
        pending_tasks: List[Dict[str, Any]] = []

        for req in requests:
            ids = req.get("requestIds", [])
            datas = req.get("requestDatas", [])
            for i, rid in enumerate(ids):
                if rid in existing_ids:
                    continue  # skip delivered
                st = cls.get_request_id_status(ledger_api, marketplace_address, rid)[
                    "data"
                ]
                info = cls.get_request_id_info(ledger_api, marketplace_address, rid)[
                    "data"
                ]
                pending_tasks.append(
                    {
                        "tx_hash": req.get("tx_hash"),
                        "block_number": req.get("block_number"),
                        "priorityMech": req.get("priorityMech"),
                        "requester": req.get("requester"),
                        "contract_address": contract_address,
                        "requestId": rid,
                        "data": datas[i],
                        "status": int(st),
                        "request_delivery_rate": int(info[DELIVERY_RATE_INDEX]),
                    }
                )

        updated_wait: List[Dict[str, Any]] = []
        for existing_req in wait_for_timeout_tasks:
            request_id = existing_req["requestId"]
            if request_id not in existing_ids:
                status = cls.get_request_id_status(
                    ledger_api, marketplace_address, request_id
                )
                existing_req["status"] = status["data"]
                updated_wait.append(existing_req)
        timed_out: List[Dict[str, Any]] = []
        for timed_req in timeout_tasks:
            request_id = timed_req["requestId"]
            if request_id not in existing_ids:
                status = cls.get_request_id_status(
                    ledger_api, marketplace_address, request_id
                )
                timed_req["status"] = status["data"]
                timed_out.append(timed_req)
        return {
            "data": pending_tasks,
            "wait_for_timeout_tasks": updated_wait,
            "timed_out_requests": timed_out,
        }

    @classmethod
    def get_marketplace_request_events(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        from_block: BlockIdentifier = "earliest",
        to_block: BlockIdentifier = "latest",
    ) -> JSONLike:
        """Get the Request events emitted by the contract."""
        ledger_api = cast(EthereumApi, ledger_api)
        contract_instance = cls.get_instance(ledger_api, contract_address)
        event_abi = contract_instance.events.MarketplaceRequest().abi
        entries = cls.get_event_entries(
            ledger_api=ledger_api,
            from_block=from_block,
            to_block=to_block,
            event_abi=event_abi,
            address=contract_instance.address,
        )

        request_events = list(
            {
                "tx_hash": entry.transactionHash.to_0x_hex(),
                "block_number": entry.blockNumber,
                **entry["args"],
                "contract_address": contract_address,
            }
            for entry in entries
        )
        return {"data": request_events}

    @classmethod
    def get_marketplace_deliver_events(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        from_block: BlockIdentifier = "earliest",
        to_block: BlockIdentifier = "latest",
    ) -> JSONLike:
        """Get the Deliver events emitted by the contract."""
        ledger_api = cast(EthereumApi, ledger_api)
        contract_instance = cls.get_instance(ledger_api, contract_address)
        event_abi = contract_instance.events.MarketplaceDelivery().abi
        entries = cls.get_event_entries(
            ledger_api=ledger_api,
            event_abi=event_abi,
            address=contract_instance.address,
            from_block=from_block,
            to_block=to_block,
        )

        deliver_events = list(
            {
                "tx_hash": entry.transactionHash.to_0x_hex(),
                "block_number": entry.blockNumber,
                **entry["args"],
                "contract_address": contract_address,
            }
            for entry in entries
        )
        return {"data": deliver_events}

    @classmethod
    def process_tx_receipt(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        tx_receipt: TxReceipt,
    ) -> JSONLike:
        """Process transaction receipt to filter contract events."""

        ledger_api = cast(EthereumApi, ledger_api)
        contract_instance = cls.get_instance(ledger_api, contract_address)
        event, *_ = contract_instance.events.Request().processReceipt(tx_receipt)
        return dict(event["args"])

    @classmethod
    def fetch_batch_request_id_status(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        request_ids: List[bytes],
    ) -> Dict[str, Any]:
        """Check requests are yet to be delivered."""
        # BatchRequestIdStatusData contract is a special contract used specifically for batching request id status
        # It is not deployed anywhere, nor it needs to be deployed
        batch_workable_contract = ledger_api.api.eth.contract(
            abi=BATCH_REQUESTID_STATUS_DATA["abi"],
            bytecode=BATCH_REQUESTID_STATUS_DATA["bytecode"],
        )

        # Encode the input data (constructor params)
        encoded_input_data = ledger_api.api.codec.encode(
            ["address", "bytes32[]"],
            [contract_address, request_ids],
        )

        # Concatenate the bytecode with the encoded input data to create the contract creation code
        contract_creation_code = batch_workable_contract.bytecode + encoded_input_data

        # Call the function with the contract creation code
        # Note that we are not sending any transaction, we are just calling the function
        # This is a special contract creation code that will return some result
        encoded_req_ids = ledger_api.api.eth.call({"data": contract_creation_code})

        # Decode the raw response
        # the decoding returns a Tuple with a single element so we need to access the first element of the tuple,
        request_ids = ledger_api.api.codec.decode(["bytes32[]"], encoded_req_ids)[0]
        return dict(request_ids=request_ids)

    @classmethod
    def get_undelivered_reqs(  # pylint: disable=too-many-locals,unused-argument
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        my_mech: str,
        from_block: BlockIdentifier = "earliest",
        to_block: BlockIdentifier = "latest",
        max_block_window: int = 1000,
        **kwargs: Any,
    ) -> JSONLike:
        """Get the requests that are not delivered."""
        if from_block == "earliest":
            from_block = 0

        current_block = ledger_api.api.eth.block_number
        requests, delivers = [], []
        for from_block_batch in range(int(from_block), current_block, max_block_window):
            to_block_batch: Union[int, str] = (from_block_batch + max_block_window) - 1
            if to_block_batch >= current_block:
                to_block_batch = "latest"
            requests_batch: List[Dict[str, Any]] = cls.get_request_events(
                ledger_api, contract_address, from_block_batch, to_block_batch
            )["data"]
            delivers_batch: List[Dict[str, Any]] = cls.get_deliver_events(
                ledger_api, contract_address, from_block_batch, to_block_batch
            )["data"]
            requests.extend(requests_batch)
            delivers.extend(delivers_batch)
        pending_tasks: List[Dict[str, Any]] = []
        for request in requests:
            if request["requestId"] not in [
                deliver["requestId"] for deliver in delivers
            ]:
                # store each requests in the pending_tasks list, make sure each req is stored once
                pending_tasks.append(request)

        request_ids = [req["requestId"] for req in pending_tasks]
        eligible_request_ids = cls.has_priority_passed(  # pylint: disable=no-member
            ledger_api, contract_address, my_mech, request_ids
        ).pop("request_ids")
        pending_tasks = [
            req for req in pending_tasks if req["requestId"] in eligible_request_ids
        ]
        return {"data": pending_tasks}

    @classmethod
    def simulate_tx(
        cls,
        ledger_api: EthereumApi,
        contract_address: str,
        sender_address: str,
        data: str,
    ) -> JSONLike:
        """Simulate the transaction."""
        try:
            ledger_api.api.eth.call(
                {
                    "from": ledger_api.api.to_checksum_address(sender_address),
                    "to": ledger_api.api.to_checksum_address(contract_address),
                    "data": data,
                }
            )
            simulation_ok = True
        except Exception as e:  # pylint: disable=broad-except
            _logger.info(f"Simulation failed: {str(e)}")
            simulation_ok = False

        return dict(data=simulation_ok)

    @classmethod
    def get_encoded_data_for_request(
        cls,
        ledger_api: EthereumApi,
        contract_address: str,
        request_id: bytes,
        data: str,
        delivery_rate: int,
    ) -> JSONLike:
        """Fetch info for a given request id."""
        request_id_info = cls.get_request_id_info(
            ledger_api, contract_address, request_id
        )
        final_delivery_rate = min(
            request_id_info["data"][DELIVERY_RATE_INDEX], delivery_rate
        )
        encoded_data = ledger_api.api.codec.encode(
            ["uint256", "bytes"], [final_delivery_rate, data]
        )

        return dict(data=encoded_data)

    @classmethod
    def get_request_id_info(
        cls,
        ledger_api: EthereumApi,
        contract_address: str,
        request_id: bytes,
    ) -> JSONLike:
        """Fetch info for a given request id."""
        ledger_api = cast(EthereumApi, ledger_api)
        contract_instance = cls.get_instance(ledger_api, contract_address)
        request_id_info = contract_instance.functions.mapRequestIdInfos(
            request_id
        ).call()

        return dict(data=request_id_info)

    @classmethod
    def get_request_id_status(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        request_id: bytes,
    ) -> JSONLike:
        """Fetch status for a given request id."""
        ledger_api = cast(EthereumApi, ledger_api)
        contract_instance = cls.get_instance(ledger_api, contract_address)
        status = contract_instance.functions.getRequestStatus(request_id).call()
        return dict(data=status)

    @classmethod
    def get_balance_tracker_for_mech_type(
        cls,
        ledger_api: EthereumApi,
        contract_address: str,
        mech_type: str,
    ) -> JSONLike:
        """Fetch balance tracker address for a given mech type."""
        contract_instance = cls.get_instance(ledger_api, contract_address)

        balance_tracker_address = (
            contract_instance.functions.mapPaymentTypeBalanceTrackers(mech_type).call()
        )
        return dict(data=balance_tracker_address)

    @classmethod
    def get_fee(
        cls,
        ledger_api: EthereumApi,
        contract_address: str,
    ) -> JSONLike:
        """Fetch marketplace fee"""
        contract_instance = cls.get_instance(ledger_api, contract_address)

        fee = contract_instance.functions.fee().call()
        return dict(data=fee)

    @classmethod
    def get_event_entries(
        cls,
        ledger_api: EthereumApi,
        event_abi: Any,
        address: ChecksumAddress,
        from_block: BlockIdentifier = "earliest",
        to_block: BlockIdentifier = "latest",
    ) -> List:
        """Helper method to extract the events."""

        event_topic = event_abi_to_log_topic(event_abi)

        filter_params: FilterParams = {
            "fromBlock": from_block,
            "toBlock": to_block,
            "address": address,
            "topics": [event_topic],
        }

        w3 = ledger_api.api.eth
        logs = w3.get_logs(filter_params)
        entries = [get_event_data(w3.codec, event_abi, log) for log in logs]
        return entries
