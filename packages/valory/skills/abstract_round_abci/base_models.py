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
from abc import ABC, ABCMeta, abstractmethod
from copy import copy
from math import ceil
from typing import (
    Any,
    Callable,
    Dict,
    FrozenSet,
    List,
    Optional,
    Sequence,
    Tuple,
    Type,
    cast,
)

from aea.exceptions import enforce
from eth_account import Account
from eth_account.messages import encode_defunct

from packages.fetchai.connections.ledger.base import (
    CONNECTION_ID as LEDGER_CONNECTION_PUBLIC_ID,
)
from packages.valory.protocols.abci.custom_types import Header
from packages.valory.skills.abstract_round_abci.serializer import (
    DictProtobufStructSerializer,
)


OK_CODE = 0
ERROR_CODE = 1
LEDGER_API_ADDRESS = str(LEDGER_CONNECTION_PUBLIC_ID)


class _MetaPayload(ABCMeta):
    """
    Payload metaclass.

    The purpose of this metaclass is to remember the association
    between the type of a payload and the payload class to build it.
    This is necessary to recover the right payload class to instantiate
    at decoding time.

    Each class that has this class as metaclass must have a class
    attribute 'transaction_type', which for simplicity is required
    to be convertible to string, for serialization purposes.
    """

    transaction_type_to_payload_cls: Dict[str, Type["BaseTxPayload"]] = {}

    def __new__(mcs, name: str, bases: Tuple, namespace: Dict, **kwargs: Any) -> Type:  # type: ignore
        """Create a new class object."""
        new_cls = super().__new__(mcs, name, bases, namespace, **kwargs)

        if new_cls.__module__.startswith("packages."):
            # ignore class if it is from an import with prefix "packages."
            return new_cls
        if ABC in bases:
            # abstract class, return
            return new_cls
        if not issubclass(new_cls, BaseTxPayload):
            raise ValueError(f"class {name} must inherit from {BaseTxPayload.__name__}")
        new_cls = cast(Type[BaseTxPayload], new_cls)

        transaction_type = str(mcs._get_field(new_cls, "transaction_type"))
        mcs._validate_transaction_type(transaction_type, new_cls)
        # remember association from transaction type to payload class
        mcs.transaction_type_to_payload_cls[transaction_type] = new_cls

        return new_cls

    @classmethod
    def _validate_transaction_type(
        mcs, transaction_type: str, new_payload_cls: Type["BaseTxPayload"]
    ) -> None:
        """Check that a transaction type is not already associated to a concrete payload class."""
        if transaction_type in mcs.transaction_type_to_payload_cls:
            previous_payload_cls = mcs.transaction_type_to_payload_cls[transaction_type]
            if new_payload_cls != previous_payload_cls:
                raise ValueError(
                    f"transaction type with name {transaction_type} already used by class {previous_payload_cls}, and cannot be used by class {new_payload_cls}"
                )

    @classmethod
    def _get_field(mcs, cls: Type, field_name: str) -> Any:
        """Get a field from a class if present, otherwise raise error."""
        if not hasattr(cls, field_name) and getattr(cls, field_name) is None:
            raise ValueError(f"class {cls} must set '{field_name}' class field")
        return getattr(cls, field_name)


class BaseTxPayload(ABC, metaclass=_MetaPayload):
    """This class represents a base class for transaction payload classes."""

    transaction_type: Any

    def __init__(self, sender: str) -> None:
        """
        Initialize a transaction payload.

        :param sender: the sender (Ethereum) address
        """
        self.sender = sender

    def encode(self) -> bytes:
        """Encode the payload."""
        return DictProtobufStructSerializer.encode(self.json)

    @classmethod
    def decode(cls, obj: bytes) -> "BaseTxPayload":
        """Decode the payload."""
        return cls.from_json(DictProtobufStructSerializer.decode(obj))

    @classmethod
    def from_json(cls, obj: Dict) -> "BaseTxPayload":
        """Decode the payload."""
        data = copy(obj)
        transaction_type = str(data.pop("transaction_type"))
        payload_cls = _MetaPayload.transaction_type_to_payload_cls[transaction_type]
        return payload_cls(**data)

    @property
    def json(self) -> Dict:
        """Get the JSON representation of the payload."""
        return dict(
            transaction_type=str(self.transaction_type), sender=self.sender, **self.data
        )

    @property
    def data(self) -> Dict:
        """
        Get the dictionary data.

        The returned dictionary is required to be used
        as keyword constructor initializer, i.e. these two
        should have the same effect:

            sender = "..."
            some_kwargs = {...}
            p1 = SomePayloadClass(sender, **some_kwargs)
            p2 = SomePayloadClass(sender, **p1.data)

        :return: a dictionary which contains the payload data
        """
        return {}

    def __eq__(self, other: Any) -> bool:
        """Check equality."""
        return self.sender == other.sender and self.data == other.data


class Transaction(ABC):
    """Class to represent a transaction."""

    def __init__(self, payload: BaseTxPayload, signature: str) -> None:
        """Initialize a transaction object."""
        self.payload = payload
        self.signature = signature

    def encode(self) -> bytes:
        """Encode the transaction."""
        data = dict(payload=self.payload.json, signature=self.signature)
        return DictProtobufStructSerializer.encode(data)

    @classmethod
    def decode(cls, obj: bytes) -> "Transaction":
        """Decode the transaction."""
        data = DictProtobufStructSerializer.decode(obj)
        signature = data["signature"]
        payload_dict = data["payload"]
        payload = BaseTxPayload.from_json(payload_dict)
        return Transaction(payload, signature)

    def verify(self) -> None:
        """Verify the signature is correct."""
        payload_bytes = DictProtobufStructSerializer.encode(self.payload.json)
        encoded_payload_bytes = encode_defunct(payload_bytes)
        public_key = Account.recover_message(  # pylint: disable=no-value-for-parameter
            encoded_payload_bytes, signature=self.signature
        )
        if public_key != self.payload.sender:
            raise ValueError("signature not valid.")

    def __eq__(self, other: Any) -> bool:
        """Check equality."""
        return (
            isinstance(other, Transaction)
            and self.payload == other.payload
            and self.signature == other.signature
        )


class Block:  # pylint: disable=too-few-public-methods
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

    def __init__(self) -> None:
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
    def transactions(self) -> Tuple[Transaction, ...]:
        """Get the sequence of transactions."""
        return tuple(self._current_transactions)

    def add_transaction(self, transaction: Transaction) -> None:
        """Add a transaction."""
        self._current_transactions.append(transaction)

    def get_block(self) -> Block:
        """Get the block."""
        return Block(
            self.header,
            self._current_transactions,
        )


class ConsensusParams:
    """Represent the consensus parameters."""

    def __init__(self, max_participants: int):
        """Initialize the consensus parameters."""
        self._max_participants = max_participants

    @property
    def max_participants(self) -> int:
        """Get the maximum number of participants."""
        return self._max_participants

    @property
    def two_thirds_threshold(self) -> int:
        """Get the 2/3 threshold."""
        return ceil(self.max_participants * 2 / 3)

    @classmethod
    def from_json(cls, obj: Dict) -> "ConsensusParams":
        """Get from JSON."""
        max_participants = obj["max_participants"]
        enforce(
            isinstance(max_participants, int) and max_participants >= 0,
            "max_participants must be an integer greater than 0.",
        )

        return ConsensusParams(max_participants)


class BasePeriodState:
    """Class to represent a period state."""

    def __init__(
        self,
        participants: Optional[FrozenSet[str]] = None,
    ) -> None:
        """Initialize a period state."""
        self._participants = participants

    @property
    def participants(self) -> FrozenSet[str]:
        """Get the participants."""
        enforce(self._participants is not None, "'participants' field is None")
        return cast(FrozenSet[str], self._participants)

    @classmethod
    def update(cls, state: "BasePeriodState", **kwargs: Any) -> "BasePeriodState":
        """Copy and update the state."""
        # remove leading underscore from keys
        data = {key[1:]: value for key, value in state.__dict__.items()}
        data.update(kwargs)
        return cls(**data)


class AbstractRound(ABC):
    """
    This class represents an abstract round.

    A round is a state of a period. It usually involves
    interactions between participants in the period,
    although this is not enforced at this level of abstraction.
    """

    round_id: str

    def __init__(
        self,
        state: BasePeriodState,
        consensus_params: ConsensusParams,
    ) -> None:
        """Initialize the round."""
        self._consensus_params = consensus_params
        self._state = state

    @property
    def state(self) -> BasePeriodState:
        """Get the period state."""
        return self._state

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

    def __init__(self, starting_round_cls: Type[AbstractRound]):
        """Initialize the round."""
        self._blockchain = Blockchain()

        # this flag is set when the object has not finished processing a block.
        # i.e. 'begin_block' called, but not yet 'commit'.
        self._in_block_processing = False

        self._block_builder = BlockBuilder()
        self._starting_round_cls = starting_round_cls
        self._current_round: Optional[AbstractRound] = None

        self._previous_rounds: List[AbstractRound] = []
        self._round_results: List[Any] = []

    def setup(self, *args: Any, **kwargs: Any) -> None:
        """
        Set up the period.

        :param args: the arguments to pass to the round constructor.
        :param kwargs: the keyword-arguments to pass to the round constructor.
        """
        self._current_round = self._starting_round_cls(*args, **kwargs)

    @property
    def is_finished(self) -> bool:
        """Check if a period has finished."""
        return self._current_round is None

    def check_is_finished(self) -> None:
        """Check if a period has finished."""
        if self.is_finished:
            raise ValueError("period is finished, cannot accept new transactions")

    @property
    def current_round_id(self) -> Optional[str]:
        """Get the current round id."""
        return self._current_round.round_id if self._current_round else None

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
        is_valid = cast(AbstractRound, self._current_round).check_transaction(
            transaction
        )
        if is_valid:
            cast(AbstractRound, self._current_round).add_transaction(transaction)
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
        current_round = cast(AbstractRound, self._current_round)
        result = current_round.end_block()
        if result is None:
            return
        round_result, next_round = result
        self._previous_rounds.append(current_round)
        self._round_results.append(round_result)
        self._current_round = next_round
