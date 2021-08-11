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

"""This module contains the base classes for the models classes of the skill."""
import pickle  # nosec
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Callable, List, Optional, Sequence, Tuple, Type, cast

from aea.exceptions import enforce
from eth_account import Account
from eth_account.messages import encode_defunct

from packages.valory.protocols.abci.custom_types import Header
from packages.valory.skills.price_estimation_abci.params import ConsensusParams


OK_CODE = 0
ERROR_CODE = 1


class BaseTxPayload(ABC):
    """This class represents a transaction payload."""

    def __init__(self, transaction_type: Enum, sender: str) -> None:
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
        public_key = Account.recover_message(  # pylint: disable=no-value-for-parameter
            encoded_payload_bytes, signature=self.signature
        )
        if public_key != self.payload.sender:
            raise ValueError("signature not valid.")


class Block:
    """Class to represent (a subset of) data of a Tendermint block."""

    def __init__(
        self,
        header: Header,
        transactions: Sequence[Transaction],
    ) -> None:
        """Initialize the block."""
        self.header = header
        self._transactions: Tuple[Transaction, ...] = tuple(transactions)

    @property
    def transactions(self) -> Tuple[Transaction, ...]:
        """Get the transactions."""
        return self._transactions


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


class BlockBuilder:
    """Helper class to build a block."""

    _current_header: Optional[Header] = None
    _current_transactions: List[Transaction] = []

    def __init__(self):
        """Initialize the block builder."""
        self.reset()

    def reset(self) -> None:
        """Reset the temporary data structures."""
        self._current_header = None
        self._current_transactions = []

    @property
    def header(self) -> Header:
        """
        Get the block header.

        :return: the block header
        """
        if self._current_header is None:
            raise ValueError("header not set")
        return self._current_header

    @header.setter
    def header(self, header: Header) -> None:
        """Set the header."""
        if self._current_header is not None:
            raise ValueError("header already set")
        self._current_header = header

    @property
    def transactions(self) -> Tuple[Transaction]:
        """Get the sequence of transactions."""
        return tuple(self._current_transactions)

    def add_transaction(self, transaction: Transaction):
        """Add a transaction."""
        self._current_transactions.append(transaction)

    def get_block(self) -> Block:
        """Get the block."""
        return Block(
            self.header,
            self._current_transactions,
        )


class AbstractRound(ABC):
    """
    This class represents an abstract round.

    A round is a state of a period. It usually involves
    interactions between participants in the period,
    although this is not enforced at this level of abstraction.
    """

    round_id: str

    def __init__(self, consensus_params: ConsensusParams) -> None:
        """Initialize the round."""
        self._consensus_params = consensus_params

    def check_transaction(self, transaction: Transaction) -> bool:
        """
        Check transaction against the current state.

        By convention, the payload handler should be a method
        of the class that is named 'check_{payload_name}'.

        :param transaction: the transaction
        :return: True if the transaction can be applied to the current
            state, False otherwise.
        """
        tx_type = transaction.payload.transaction_type.value
        payload_handler: Callable[[BaseTxPayload], bool] = getattr(
            self, "check_" + tx_type, None
        )
        if payload_handler is None:
            # request not recognized
            return False
        return payload_handler(transaction.payload)

    def add_transaction(self, transaction: Transaction) -> None:
        """
        Process a transaction.

        By convention, the payload handler should be a method
        of the class that is named '{payload_name}'.

        :param transaction: the transaction.
        """
        tx_type = transaction.payload.transaction_type.value
        handler: Callable[[BaseTxPayload], None] = getattr(self, tx_type, None)
        if handler is None:
            raise ValueError("request not recognized")
        if not self.check_transaction(transaction):
            raise ValueError("transaction not valid")
        handler(transaction.payload)

    @abstractmethod
    def end_block(self) -> Optional[Tuple[Any, Optional["AbstractRound"]]]:
        """
        Process the end of the block.

        The role of this method is check whether the round
        is considered ended.

        If the round is ended, the return value
         - return the final result of the round.
         - schedule the next round (if any). If None, the period
            in which the round was executed is considered ended.

        This is done after each block because we consider the Tendermint
        block, and not the transaction, as the smallest unit
        on which the consensus is reached; in other words,
        each read operation on  the state should be done
        only after each block, and not after each transaction.
        """


class Period:
    """This class represents a period (i.e. a sequence of rounds)"""

    def __init__(
        self, consensus_params: ConsensusParams, starting_round_cls: Type[AbstractRound]
    ):
        """Initialize the round."""
        self._consensus_params = consensus_params
        self._blockchain = Blockchain()

        # this flag is set when the object has not finished processing a block.
        # i.e. 'begin_block' called, but not yet 'commit'.
        self._in_block_processing = False

        self._block_builder = BlockBuilder()
        self._current_round: AbstractRound = starting_round_cls(consensus_params)

        self._previous_rounds: List[AbstractRound] = []
        self._round_results: List[Any] = []

    @property
    def is_finished(self):
        """Check if a period has finished."""
        return self._current_round is None

    @property
    def current_round_id(self) -> str:
        """Get the current round id."""
        return self._current_round.round_id

    @property
    def latest_result(self) -> Optional[Any]:
        """Get the latest result of the round."""
        return None if len(self._round_results) == 0 else self._round_results[-1]

    def begin_block(self, header: Header) -> None:
        """Begin block."""
        if self._in_block_processing:
            raise ValueError("already processing a block")
        if self.is_finished:
            raise ValueError("period is finished, cannot accept new blocks")
        self._in_block_processing = True
        self._block_builder.reset()
        self._block_builder.header = header

    def deliver_tx(self, transaction: Transaction) -> bool:
        """
        Deliver a transaction.

        Appends the transaction to build the block on 'end_block' later.

        :param transaction: the transaction.
        :return: True if the transaction delivery was successful, False otherwise.
        """
        if not self._in_block_processing:
            raise ValueError("not processing a block")
        is_valid = self._current_round.check_transaction(transaction)
        if is_valid:
            self._current_round.add_transaction(transaction)
            self._block_builder.add_transaction(transaction)
        return is_valid

    def end_block(self) -> None:
        """Process the 'end_block' request."""
        if not self._in_block_processing:
            raise ValueError("not processing a block")

    def commit(self) -> None:
        """Process the 'commit' request."""
        block = self._block_builder.get_block()
        self._blockchain.add_block(block)
        self._update_round()
        self._in_block_processing = False

    def _update_round(self) -> None:
        """
        Update a round.

        Check whether the round has finished. If so, get the
        new round and set it as the current round.
        """
        result = self._current_round.end_block()
        if result is None:
            return
        round_result, next_round = result
        self._previous_rounds.append(self._current_round)
        self._round_results.append(round_result)
        self._current_round = next_round
