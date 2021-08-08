# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021 Valory AG
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

"""This module contains the data classes for the price estimation ABCI application."""
import pickle  # nosec
from abc import ABC
from enum import Enum
from typing import List, Tuple, cast

from aea.exceptions import enforce
from eth_account import Account
from eth_account.messages import encode_defunct

from packages.valory.protocols.abci.custom_types import Header


class Round:  # pylint: disable=too-few-public-methods
    """Class to represent the round state."""

    def __init__(self):
        """Initialize the round."""


class TransactionType(Enum):
    """Enumeration of transaction types."""

    REGISTRATION = "registration"
    COMMIT_OBSERVATION = "commit_observation"


class BaseTxPayload(ABC):
    """This class represents a transaction payload."""

    def __init__(self, transaction_type: TransactionType, sender: str) -> None:
        """
        Initialize a transaction payload.

        :param transaction_type: the transaction type.
        :param sender: the sender (Ethereum) address
        """
        self.transaction_type = transaction_type
        self.sender = sender

    def encode(self) -> bytes:
        """Encode the payload."""
        return pickle.dumps(self)  # nosec

    @classmethod
    def decode(cls, obj: bytes) -> "BaseTxPayload":
        """Decode the payload."""
        return pickle.loads(obj)  # nosec


class RegistrationPayload(BaseTxPayload):
    """Represent a transaction payload of type 'registration'."""

    def __init__(self, sender: str) -> None:
        """
        Initialize a 'registration' transaction payload.

        :param sender: the sender (Ethereum) address
        """
        super().__init__(TransactionType.REGISTRATION, sender)


class CommitObservationPayload(BaseTxPayload):
    """Represent a transaction payload of type 'commit observation'."""

    def __init__(self, sender: str) -> None:
        """Initialize a 'commit_observation' transaction payload.

        :param sender: the sender (Ethereum) address
        """
        super().__init__(TransactionType.COMMIT_OBSERVATION, sender)


class Transaction(ABC):
    """Class to represent a transaction."""

    def __init__(self, payload: BaseTxPayload, signature: str) -> None:
        """Initialize a transaction object."""
        self.payload = payload
        self.signature = signature

    def encode(self) -> bytes:
        """Encode the transaction."""
        return pickle.dumps(self)  # nosec

    @classmethod
    def decode(cls, obj: bytes) -> "Transaction":
        """Decode the transaction."""
        transaction_obj = pickle.loads(obj)  # nosec
        enforce(
            isinstance(transaction_obj, Transaction), "not an instance of 'Transaction'"
        )
        transaction_obj = cast(Transaction, transaction_obj)
        return transaction_obj

    def verify(self) -> None:
        """Verify the signature is correct."""
        payload_bytes = self.payload.encode()
        encoded_payload_bytes = encode_defunct(payload_bytes)
        public_key = Account.recover_message(
            encoded_payload_bytes, signature=self.signature
        )
        if public_key != self.payload.sender:
            raise ValueError("signature not valid.")


class Block:
    """Class to represent (a subset of) data of a Tendermint block."""

    def __init__(self, header: Header) -> None:
        """Initialize the block."""
        self.header = header
        self._transactions: List[Transaction] = []

    @property
    def transactions(self) -> Tuple[Transaction, ...]:
        """Get the transactions."""
        return tuple(self._transactions)

    def add_transaction(self, transaction: Transaction) -> None:
        """Add transaction to the block."""
        self._transactions.append(transaction)


class Blockchain:
    """
    Class to represent a (naive) Tendermint blockchain.

    The consistency of the data in the blocks is guaranteed by Tendermint.
    """

    def __init__(self) -> None:
        """Initialize the blockchain."""
        self._blocks: List[Block] = []

    def add_block(self, block: Block) -> None:
        """Add a block to the list."""
        expected_height = self.height
        actual_height = block.header.height
        if expected_height != actual_height:
            raise ValueError(f"expected height {expected_height}, got {actual_height}")
        self._blocks.append(block)

    @property
    def height(self) -> int:
        """Get the height."""
        return self.length + 1

    @property
    def length(self) -> int:
        """Get the blockchain length."""
        return len(self._blocks)

    def get_block(self, height: int) -> Block:
        """Get the ith block."""
        if not self.length > height >= 0:
            raise ValueError(
                f"height {height} not valid, must be between {self.length} and 0"
            )
        return self._blocks[height]
