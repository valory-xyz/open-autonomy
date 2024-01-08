# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2023 Valory AG
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

"""This module contains the class to connect to an Gnosis Safe contract."""
# heavily borrows from https://github.com/gnosis/gnosis-py/blob/51b41f5a8577a96e296b9b7e037491632cda9d8c/gnosis/safe/multi_send.py
import logging
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, cast

from aea.common import JSONLike
from aea.configurations.base import PublicId
from aea.contracts.base import Contract
from aea.crypto.base import LedgerApi
from hexbytes import HexBytes
from web3 import Web3


PUBLIC_ID = PublicId.from_str("valory/multisend:0.1.0")
MIN_GAS = MIN_GASPRICE = 1

_logger = logging.getLogger(
    f"aea.packages.{PUBLIC_ID.author}.contracts.{PUBLIC_ID.name}.contract"
)


class MultiSendOperation(Enum):
    """Operation types."""

    CALL = 0
    DELEGATE_CALL = 1


def encode_data(tx: Dict) -> bytes:
    """Encodes multisend transaction."""
    operation = HexBytes(
        "{:0>2x}".format(cast(MultiSendOperation, tx.get("operation")).value)
    )  # Operation 1 byte
    to = HexBytes(
        "{:0>40x}".format(int(cast(str, tx.get("to")), 16))
    )  # Address 20 bytes
    value = HexBytes("{:0>64x}".format(cast(int, tx.get("value"))))  # Value 32 bytes
    data = cast(bytes, tx.get("data", b""))
    data_ = HexBytes(data)
    data_length = HexBytes("{:0>64x}".format(len(data_)))  # Data length 32 bytes
    return operation + to + value + data_length + data_


def decode_data(encoded_tx: bytes) -> Tuple[Dict, int]:
    """Decodes multisend transaction."""
    encoded_tx = HexBytes(encoded_tx)
    operation = MultiSendOperation(encoded_tx[0])
    to = Web3.to_checksum_address(encoded_tx[1 : 1 + 20])
    value = int.from_bytes(encoded_tx[21 : 21 + 32], byteorder="big")
    data_length = int.from_bytes(encoded_tx[21 + 32 : 21 + 32 * 2], byteorder="big")
    data = encoded_tx[21 + 32 * 2 : 21 + 32 * 2 + data_length]
    len_data = len(data)
    if len_data != data_length:  # pragma: nocover
        raise ValueError(
            f"Data length {data_length} is different from len(data) {len_data}"
        )
    total_length = 21 + 32 * 2 + data_length
    return (
        {"operation": operation, "to": to, "value": value, "data": data},
        total_length,
    )


def to_bytes(multi_send_txs: List[Dict]) -> bytes:
    """Multi send tx list to bytes."""
    return b"".join([encode_data(tx) for tx in multi_send_txs])


def from_bytes(encoded_multisend_txs: bytes) -> List[Dict]:
    """Encoded multi send tx to list."""
    encoded_multisend_txs = HexBytes(encoded_multisend_txs)
    next_data_position = 0
    txs = []
    while len(encoded_multisend_txs[next_data_position:]) > 0:
        tx, total_length = decode_data(encoded_multisend_txs[next_data_position:])
        next_data_position += total_length
        txs.append(tx)
    return txs


class MultiSendContract(Contract):
    """The MultiSend contract."""

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
    def get_deploy_transaction(
        cls, ledger_api: LedgerApi, deployer_address: str, **kwargs: Any
    ) -> Optional[JSONLike]:
        """Get deploy transaction."""
        raise NotImplementedError

    @classmethod
    def get_tx_data(
        cls, ledger_api: LedgerApi, contract_address: str, multi_send_txs: List[Dict]
    ) -> Optional[JSONLike]:
        """
        Get a multisend transaction data from list.

        :param ledger_api: ledger API object.
        :param contract_address: the contract address.
        :param multi_send_txs: the multisend transaction list.
        :return: an optional JSON-like object.
        """
        multisend_contract = cls.get_instance(ledger_api, contract_address)
        encoded_multisend_data = to_bytes(multi_send_txs)
        return {
            "data": multisend_contract.functions.multiSend(
                encoded_multisend_data
            ).build_transaction({"gas": MIN_GAS, "gasPrice": MIN_GASPRICE})["data"]
        }

    @classmethod
    def get_multisend_tx(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        txs: List[Dict],
    ) -> Optional[JSONLike]:
        """
        Get a multisend transaction data from list.

        :param ledger_api: ledger API object.
        :param contract_address: the contract address.
        :param txs: the multisend transaction list.
        :return: an optional JSON-like object.
        """
        multisend_contract = cls.get_instance(ledger_api, contract_address)
        encoded_multisend_data = to_bytes(txs)
        return multisend_contract.functions.multiSend(
            encoded_multisend_data
        ).build_transaction({"gas": MIN_GAS, "gasPrice": MIN_GASPRICE})

    @classmethod
    def get_tx_list(
        cls, ledger_api: LedgerApi, contract_address: str, multi_send_data: str
    ) -> Optional[JSONLike]:
        """
        Get a multisend transaction list from encoded data.

        :param ledger_api: ledger API object.
        :param contract_address: the contract address.
        :param multi_send_data: the multisend transaction data.
        :return: an optional JSON-like object.
        """
        multisend_contract = cls.get_instance(ledger_api, contract_address)
        _, encoded_multisend_data = multisend_contract.decode_function_input(
            multi_send_data
        )
        return {"tx_list": from_bytes(encoded_multisend_data["transactions"])}
