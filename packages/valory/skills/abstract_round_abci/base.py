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

"""This module contains the base classes for the models classes of the skill."""
import datetime
import heapq
import itertools
import json
import logging
import re
import sys
import textwrap
import uuid
from abc import ABC, ABCMeta, abstractmethod
from collections import Counter
from copy import copy, deepcopy
from dataclasses import asdict, dataclass, field
from enum import Enum
from inspect import isclass
from math import ceil
from typing import (
    Any,
    Dict,
    FrozenSet,
    Generic,
    List,
    Mapping,
    Optional,
    Sequence,
    Set,
    Tuple,
    Type,
    TypeVar,
    cast,
)

from aea.crypto.ledger_apis import LedgerApis
from aea.exceptions import enforce

from packages.valory.connections.abci.connection import MAX_READ_IN_BYTES
from packages.valory.connections.ledger.connection import (
    PUBLIC_ID as LEDGER_CONNECTION_PUBLIC_ID,
)
from packages.valory.protocols.abci.custom_types import Header


_logger = logging.getLogger("aea.packages.valory.skills.abstract_round_abci.base")

OK_CODE = 0
ERROR_CODE = 1
LEDGER_API_ADDRESS = str(LEDGER_CONNECTION_PUBLIC_ID)
ROUND_COUNT_DEFAULT = -1
RESET_INDEX_DEFAULT = -1
MIN_HISTORY_DEPTH = 1
ADDRESS_LENGTH = 42
MAX_INT_256 = 2 ** 256 - 1
RESET_COUNT_START = 0
VALUE_NOT_PROVIDED = object()
# tolerance in seconds for new blocks not having arrived yet
BLOCKS_STALL_TOLERANCE = 60

EventType = TypeVar("EventType")


def get_name(prop: Any) -> str:
    """Get the name of a property."""
    if not (isinstance(prop, property) and hasattr(prop, "fget")):
        raise ValueError(f"{prop} is not a property")
    if prop.fget is None:
        raise ValueError(f"fget of {prop} is None")  # pragma: nocover
    return prop.fget.__name__


def consensus_threshold(nb: int) -> int:
    """
    Get consensus threshold.

    :param nb: the number of participants
    :return: the consensus threshold
    """
    return ceil((2 * nb + 1) / 3)


class ABCIAppException(Exception):
    """A parent class for all exceptions related to the ABCIApp."""


class SignatureNotValidError(ABCIAppException):
    """Error raised when a signature is invalid."""


class AddBlockError(ABCIAppException):
    """Exception raised when a block addition is not valid."""


class ABCIAppInternalError(ABCIAppException):
    """Internal error due to a bad implementation of the ABCIApp."""

    def __init__(self, message: str, *args: Any) -> None:
        """Initialize the error object."""
        super().__init__("internal error: " + message, *args)


class TransactionTypeNotRecognizedError(ABCIAppException):
    """Error raised when a transaction type is not recognized."""


class TransactionNotValidError(ABCIAppException):
    """Error raised when a transaction is not valid."""


class LateArrivingTransaction(ABCIAppException):
    """Error raised when the transaction belongs to previous round."""


class AbstractRoundInternalError(ABCIAppException):
    """Internal error due to a bad implementation of the AbstractRound."""

    def __init__(self, message: str, *args: Any) -> None:
        """Initialize the error object."""
        super().__init__("internal error: " + message, *args)


class _MetaPayload(ABCMeta):
    """
    Payload metaclass.

    The purpose of this metaclass is to remember the association
    between the type of payload and the payload class to build it.
    This is necessary to recover the right payload class to instantiate
    at decoding time.
    """

    registry: Dict[str, Type["BaseTxPayload"]] = {}

    def __new__(mcs, name: str, bases: Tuple, namespace: Dict, **kwargs: Any) -> Type:  # type: ignore
        """Create a new class object."""
        new_cls = super().__new__(mcs, name, bases, namespace, **kwargs)

        if new_cls.__module__ == mcs.__module__ and new_cls.__name__ == "BaseTxPayload":
            return new_cls
        if not issubclass(new_cls, BaseTxPayload):
            raise ValueError(  # pragma: no cover
                f"class {name} must inherit from {BaseTxPayload.__name__}"
            )
        new_cls = cast(Type[BaseTxPayload], new_cls)
        # remember association from transaction type to payload class
        _metaclass_registry_key = f"{new_cls.__module__}.{new_cls.__name__}"  # type: ignore
        mcs.registry[_metaclass_registry_key] = new_cls

        return new_cls


@dataclass(frozen=True)
class BaseTxPayload(metaclass=_MetaPayload):
    """This class represents a base class for transaction payload classes."""

    sender: str
    round_count: int = field(default=ROUND_COUNT_DEFAULT, init=False)
    id_: str = field(default_factory=lambda: uuid.uuid4().hex, init=False)

    @property
    def data(self) -> Dict[str, Any]:
        """Data"""
        excluded = ["sender", "round_count", "id_", "_metaclass_registry_key"]
        return {k: v for k, v in asdict(self).items() if k not in excluded}

    # TODO: refactor - these methods are not strictly needed
    @property
    def json(self) -> Dict[str, Any]:
        """Json"""
        data, cls = asdict(self), self.__class__
        data["_metaclass_registry_key"] = f"{cls.__module__}.{cls.__name__}"
        return data

    @classmethod
    def from_json(cls, obj: Dict) -> "BaseTxPayload":
        """Decode the payload."""
        data = copy(obj)
        round_count, id_ = data.pop("round_count"), data.pop("id_")
        payload_cls = _MetaPayload.registry[data.pop("_metaclass_registry_key")]
        payload = payload_cls(**data)  # type: ignore
        object.__setattr__(payload, "round_count", round_count)
        object.__setattr__(payload, "id_", id_)
        return payload

    def with_new_id(self) -> "BaseTxPayload":
        """Create a new payload with the same content but new id."""
        new = type(self)(sender=self.sender, **self.data)  # type: ignore
        object.__setattr__(new, "round_count", self.round_count)
        return new

    def encode(self) -> bytes:
        """Encode"""
        encoded_data = json.dumps(self.json, sort_keys=True).encode()
        if sys.getsizeof(encoded_data) > MAX_READ_IN_BYTES:
            msg = f"{type(self)} must be smaller than {MAX_READ_IN_BYTES} bytes"
            raise ValueError(msg)
        return encoded_data

    @classmethod
    def decode(cls, obj: bytes) -> "BaseTxPayload":
        """Decode"""
        return cls.from_json(json.loads(obj.decode()))


@dataclass(frozen=True)
class Transaction(ABC):
    """Class to represent a transaction for the ephemeral chain of a period."""

    payload: BaseTxPayload
    signature: str

    def encode(self) -> bytes:
        """Encode the transaction."""

        data = dict(payload=self.payload.json, signature=self.signature)
        encoded_data = json.dumps(data, sort_keys=True).encode()
        if sys.getsizeof(encoded_data) > MAX_READ_IN_BYTES:
            raise ValueError(
                f"Transaction must be smaller than {MAX_READ_IN_BYTES} bytes"
            )
        return encoded_data

    @classmethod
    def decode(cls, obj: bytes) -> "Transaction":
        """Decode the transaction."""

        data = json.loads(obj.decode())
        signature = data["signature"]
        payload = BaseTxPayload.from_json(data["payload"])
        return Transaction(payload, signature)

    def verify(self, ledger_id: str) -> None:
        """
        Verify the signature is correct.

        :param ledger_id: the ledger id of the address
        :raises: SignatureNotValidError: if the signature is not valid.
        """
        payload_bytes = self.payload.encode()
        addresses = LedgerApis.recover_message(
            identifier=ledger_id, message=payload_bytes, signature=self.signature
        )
        if self.payload.sender not in addresses:
            raise SignatureNotValidError(f"Signature not valid on transaction: {self}")


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

    @property
    def timestamp(self) -> datetime.datetime:
        """Get the block timestamp."""
        return self.header.timestamp


class Blockchain:
    """
    Class to represent a (naive) Tendermint blockchain.

    The consistency of the data in the blocks is guaranteed by Tendermint.
    """

    def __init__(self, height_offset: int = 0, is_init: bool = True) -> None:
        """Initialize the blockchain."""
        self._blocks: List[Block] = []
        self._height_offset = height_offset
        self._is_init = is_init

    @property
    def is_init(self) -> bool:
        """Returns true if the blockchain is initialized."""
        return self._is_init

    def add_block(self, block: Block) -> None:
        """Add a block to the list."""
        expected_height = self.height + 1
        actual_height = block.header.height
        if actual_height < self._height_offset:
            # if the current block has a lower height than the
            # initial height, ignore it
            return

        if expected_height != actual_height:
            raise AddBlockError(
                f"expected height {expected_height}, got {actual_height}"
            )
        self._blocks.append(block)

    @property
    def height(self) -> int:
        """
        Get the height.

        Tendermint's height starts from 1. A return value
            equal to 0 means empty blockchain.

        :return: the height.
        """
        return self.length + self._height_offset

    @property
    def length(self) -> int:
        """Get the blockchain length."""
        return len(self._blocks)

    @property
    def blocks(self) -> Tuple[Block, ...]:
        """Get the blocks."""
        return tuple(self._blocks)

    @property
    def last_block(
        self,
    ) -> Block:
        """Returns the last stored block."""
        return self._blocks[-1]


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
    def consensus_threshold(self) -> int:
        """Get the consensus threshold."""
        return consensus_threshold(self.max_participants)

    @classmethod
    def from_json(cls, obj: Dict) -> "ConsensusParams":
        """Get from JSON."""
        max_participants = obj["max_participants"]
        enforce(
            isinstance(max_participants, int) and max_participants >= 0,
            "max_participants must be an integer greater than 0.",
        )
        return cls(max_participants)

    def __eq__(self, other: Any) -> bool:
        """Check equality."""
        if not isinstance(other, ConsensusParams):
            return NotImplemented
        return self.max_participants == other.max_participants


class AbciAppDB:
    """Class to represent all data replicated across agents.

    This class stores all the data in self._data. Every entry on this dict represents an optional "period" within your app execution.
    The concept of period is user-defined, so it might be something like a sequence of rounds that together conform a logical cycle of
    its execution, or it might have no sense at all (thus its optionality) and therefore only period 0 will be used.

    Every "period" entry stores a dict where every key is a saved parameter and its corresponding value a list containing the history
    of the parameter values. For instance, for period 0:

    0: {"parameter_name": [parameter_history]}

    A complete database could look like this:

    data = {
        0: {
            "participants":
                [
                    {"participant_a", "participant_b", "participant_c", "participant_d"},
                    {"participant_a", "participant_b", "participant_c"},
                    {"participant_a", "participant_b", "participant_c", "participant_d"},
                ]
            },
            "other_parameter": [0, 2, 8]
        },
        1: {
            "participants":
                [
                    {"participant_a", "participant_c", "participant_d"},
                    {"participant_a", "participant_b", "participant_c", "participant_d"},
                    {"participant_a", "participant_b", "participant_c"},
                    {"participant_a", "participant_b", "participant_d"},
                    {"participant_a", "participant_b", "participant_c", "participant_d"},
                ],
            "other_parameter": [3, 19, 10, 32, 6]
        },
        2: ...
    }

    # Adding and removing data from the current period
    --------------------------------------------------
    To update the current period entry, just call update() on the class. The new values will be appended to the current list for each updated parameter.

    To clean up old data from the current period entry, call cleanup_current_histories(cleanup_history_depth_current), where cleanup_history_depth_current
    is the amount of data that you want to keep after the cleanup. The newest cleanup_history_depth_current values will be kept for each parameter in the DB.

    # Creating and removing old periods
    -----------------------------------
    To create a new period entry, call create() on the class. The new values will be stored in a new list for each updated parameter.

    To remove old periods, call cleanup(cleanup_history_depth, [cleanup_history_depth_current]), where cleanup_history_depth is the amount of periods
    that you want to keep after the cleanup. The newest cleanup_history_depth periods will be kept. If you also specify cleanup_history_depth_current,
    cleanup_current_histories will be also called (see previous point).

    The parameters cleanup_history_depth and cleanup_history_depth_current can also be configured in skill.yaml so they are used automatically
    when the cleanup method is called from AbciApp.cleanup().

    # Memory warning
    -----------------------------------
    The database is implemented in such a way to avoid indirect modification of its contents.
    It copies all the mutable data structures*, which means that it consumes more memory than expected.
    This is necessary because otherwise it would risk chance of modification from the behaviour side,
    which is a safety concern.

    The effect of this on the memory usage should not be a big concern, because:

        1. The synchronized data of the agents are not intended to store large amount of data.
         IPFS should be used in such cases, and only the hash should be synchronized in the db.
        2. The data are automatically wiped after a predefined `cleanup_history` depth as described above.
        3. The retrieved data are only meant to be used for a short amount of time,
         e.g., to perform a decision on a behaviour, which means that the gc will collect them before they are noticed.

    * the in-built `copy` module is used, which automatically detects if an item is immutable and skips copying it.
    For more information take a look at the `_deepcopy_atomic` method and its usage:
    https://github.com/python/cpython/blob/3.10/Lib/copy.py#L182-L183
    """

    def __init__(
        self,
        setup_data: Dict[str, List[Any]],
        cross_period_persisted_keys: Optional[List[str]] = None,
    ) -> None:
        """Initialize the AbciApp database.

        setup_data must be passed as a Dict[str, List[Any]] (the database internal format).
        The staticmethod 'data_to_lists' can be used to convert from Dict[str, Any] to Dict[str, List[Any]]
        before instantiating this class.

        :param setup_data: the setup data
        :param cross_period_persisted_keys: data keys that will be kept after a new period starts
        """
        AbciAppDB._check_data(setup_data)
        self._setup_data = deepcopy(setup_data)
        self._cross_period_persisted_keys = (
            cross_period_persisted_keys.copy()
            if cross_period_persisted_keys is not None
            else []
        )
        self._data: Dict[int, Dict[str, List[Any]]] = {
            RESET_COUNT_START: self.setup_data  # the key represents the reset index
        }
        self._round_count = ROUND_COUNT_DEFAULT  # ensures first round is indexed at 0!

    @property
    def setup_data(self) -> Dict[str, Any]:
        """
        Get the setup_data without entries which have empty values.

        :return: the setup_data
        """
        # do not return data if no value has been set
        return {k: v for k, v in deepcopy(self._setup_data).items() if len(v)}

    @staticmethod
    def _check_data(data: Any) -> None:
        """Check that all fields in setup data were passed as a list"""
        if not isinstance(data, dict) or not all(
            [isinstance(v, list) for v in data.values()]
        ):
            raise ValueError(
                f"AbciAppDB data must be `Dict[str, List[Any]]`, found `{type(data)}` instead."
            )

    @property
    def reset_index(self) -> int:
        """Get the current reset index."""
        # should return the last key or 0 if we have no data
        return list(self._data)[-1] if self._data else 0

    @property
    def round_count(self) -> int:
        """Get the round count."""
        return self._round_count

    @round_count.setter
    def round_count(self, round_count: int) -> None:
        """Set the round count."""
        self._round_count = round_count

    @property
    def cross_period_persisted_keys(self) -> List[str]:
        """Keys in the database which are persistent across periods."""
        return self._cross_period_persisted_keys.copy()

    def get(self, key: str, default: Any = VALUE_NOT_PROVIDED) -> Optional[Any]:
        """Given a key, get its last for the current reset index."""
        if key in self._data[self.reset_index]:
            return deepcopy(self._data[self.reset_index][key][-1])
        if default != VALUE_NOT_PROVIDED:
            return default
        raise ValueError(
            f"'{key}' field is not set for this period [{self.reset_index}] and no default value was provided."
        )

    def get_strict(self, key: str) -> Any:
        """Get a value from the data dictionary and raise if it is None."""
        return self.get(key)

    def update(self, **kwargs: Any) -> None:
        """Update the current data."""
        # Append new data to the key history
        data = self._data[self.reset_index]
        for key, value in deepcopy(kwargs).items():
            data.setdefault(key, []).append(value)

    def create(self, **kwargs: Any) -> None:
        """Add a new entry to the data."""
        AbciAppDB._check_data(kwargs)
        self._data[self.reset_index + 1] = deepcopy(kwargs)

    def get_latest_from_reset_index(self, reset_index: int) -> Dict[str, Any]:
        """Get the latest key-value pairs from the data dictionary for the specified period."""
        return {
            key: values[-1]
            for key, values in deepcopy(self._data.get(reset_index, {})).items()
        }

    def get_latest(self) -> Dict[str, Any]:
        """Get the latest key-value pairs from the data dictionary for the current period."""
        return self.get_latest_from_reset_index(self.reset_index)

    def increment_round_count(self) -> None:
        """Increment the round count."""
        self._round_count += 1

    def __repr__(self) -> str:
        """Return a string representation of the data."""
        return f"AbciAppDB({self._data})"

    def cleanup(
        self,
        cleanup_history_depth: int,
        cleanup_history_depth_current: Optional[int] = None,
    ) -> None:
        """Reset the db, keeping only the latest entries (periods).

        If cleanup_history_depth_current has been also set, also clear oldest historic values in the current entry.

        :param cleanup_history_depth: depth to clean up history
        :param cleanup_history_depth_current: whether or not to clean up current entry too.
        """
        cleanup_history_depth = max(cleanup_history_depth, MIN_HISTORY_DEPTH)
        self._data = {
            key: self._data[key]
            for key in sorted(self._data.keys())[-cleanup_history_depth:]
        }
        if cleanup_history_depth_current:
            self.cleanup_current_histories(cleanup_history_depth_current)

    def cleanup_current_histories(self, cleanup_history_depth_current: int) -> None:
        """Reset the parameter histories for the current entry (period), keeping only the latest values for each parameter."""
        cleanup_history_depth_current = max(
            cleanup_history_depth_current, MIN_HISTORY_DEPTH
        )
        self._data[self.reset_index] = {
            key: history[-cleanup_history_depth_current:]
            for key, history in self._data[self.reset_index].items()
        }

    @staticmethod
    def data_to_lists(data: Dict[str, Any]) -> Dict[str, List[Any]]:
        """Convert Dict[str, Any] to Dict[str, List[Any]]."""
        return {k: [v] for k, v in data.items()}


class BaseSynchronizedData:
    """
    Class to represent the synchronized data.

    This is the relevant data constructed and replicated by the agents.
    """

    # Keys always set by default
    # `round_count` and `period_count` need to be guaranteed to be synchronized too:
    #
    # * `round_count` is only incremented when scheduling a new round,
    #    which is by definition always a synchronized action.
    # * `period_count` comes from the `reset_index` which is the last key of the `self._data`.
    #    The `self._data` keys are only updated on create, and cleanup operations,
    #    which are also meant to be synchronized since they are used at the rounds.
    default_db_keys: List[str] = [
        "round_count",
        "period_count",
        "nb_participants",
        "safe_contract_address",
    ]

    def __init__(
        self,
        db: AbciAppDB,
    ) -> None:
        """Initialize the synchronized data."""
        self._db = db

    @property
    def db(self) -> AbciAppDB:
        """Get DB."""
        return self._db

    @property
    def round_count(self) -> int:
        """Get the round count."""
        return self.db.round_count

    @property
    def period_count(self) -> int:
        """Get the period count.

        Periods are executions between calls to AbciAppDB.create(), so as soon as it is called,
        a new period begins. It is useful to have a logical subdivision of the FSM execution.
        For example, if AbciAppDB.create() is called during reset, then a period will be the
        execution between resets.

        :return: the period count
        """
        return self.db.reset_index

    @property
    def participants(self) -> FrozenSet[str]:
        """Get the currently active participants."""
        participants = self.db.get_strict("participants")
        if len(participants) == 0:
            raise ValueError("List participants cannot be empty.")
        return cast(FrozenSet[str], participants)

    @property
    def all_participants(self) -> FrozenSet[str]:
        """Get all registered participants."""
        all_participants = frozenset(self.db.get_strict("all_participants"))
        if len(all_participants) == 0:
            raise ValueError("List participants cannot be empty.")
        return cast(FrozenSet[str], all_participants)

    @property
    def sorted_participants(self) -> Sequence[str]:
        """
        Get the sorted participants' addresses.

        The addresses are sorted according to their hexadecimal value;
        this is the reason we use key=str.lower as comparator.

        This property is useful when interacting with the Safe contract.

        :return: the sorted participants' addresses
        """
        return sorted(self.participants, key=str.lower)

    @property
    def nb_participants(self) -> int:
        """Get the number of participants."""
        participants = cast(List, self.db.get("participants", []))
        return len(participants)

    def update(
        self,
        synchronized_data_class: Optional[Type] = None,
        **kwargs: Any,
    ) -> "BaseSynchronizedData":
        """Copy and update the current data."""
        self.db.update(**kwargs)

        class_ = (
            type(self) if synchronized_data_class is None else synchronized_data_class
        )
        return class_(db=self.db)

    def create(
        self,
        synchronized_data_class: Optional[Type] = None,
        **kwargs: Any,
    ) -> "BaseSynchronizedData":
        """Copy and update with new data."""
        self.db.create(**kwargs)
        class_ = (
            type(self) if synchronized_data_class is None else synchronized_data_class
        )
        return class_(db=self.db)

    def __repr__(self) -> str:
        """Return a string representation of the data."""
        return f"{self.__class__.__name__}(db={self._db})"

    @property
    def keeper_randomness(self) -> float:
        """Get the keeper's random number [0-1]."""
        return (
            int(self.most_voted_randomness, base=16) / MAX_INT_256
        )  # DRAND uses sha256 values

    @property
    def most_voted_randomness(self) -> str:
        """Get the most_voted_randomness."""
        return cast(str, self.db.get_strict("most_voted_randomness"))

    @property
    def most_voted_keeper_address(self) -> str:
        """Get the most_voted_keeper_address."""
        return cast(str, self.db.get_strict("most_voted_keeper_address"))

    @property
    def is_keeper_set(self) -> bool:
        """Check whether keeper is set."""
        return self.db.get("most_voted_keeper_address", None) is not None

    @property
    def blacklisted_keepers(self) -> Set[str]:
        """Get the current cycle's blacklisted keepers who cannot submit a transaction."""
        raw = cast(str, self.db.get("blacklisted_keepers", ""))
        return set(textwrap.wrap(raw, ADDRESS_LENGTH))

    @property
    def participant_to_selection(self) -> Mapping:
        """Check whether keeper is set."""
        return cast(Dict, self.db.get_strict("participant_to_selection"))

    @property
    def participant_to_randomness(self) -> Mapping:
        """Check whether keeper is set."""
        return cast(Dict, self.db.get_strict("participant_to_randomness"))

    @property
    def participant_to_votes(self) -> Mapping:
        """Check whether keeper is set."""
        return cast(Dict, self.db.get_strict("participant_to_votes"))

    @property
    def safe_contract_address(self) -> str:
        """Get the safe contract address."""
        return cast(str, self.db.get_strict("safe_contract_address"))


class _MetaAbstractRound(ABCMeta):
    """A metaclass that validates AbstractRound's attributes."""

    def __new__(mcs, name: str, bases: Tuple, namespace: Dict, **kwargs: Any) -> Type:  # type: ignore
        """Initialize the class."""
        new_cls = super().__new__(mcs, name, bases, namespace, **kwargs)

        if ABC in bases:
            # abstract class, return
            return new_cls
        if not issubclass(new_cls, AbstractRound):
            # the check only applies to AbstractRound subclasses
            return new_cls

        mcs._check_consistency(cast(Type[AbstractRound], new_cls))
        return new_cls

    @classmethod
    def _check_consistency(mcs, abstract_round_cls: Type["AbstractRound"]) -> None:
        """Check consistency of class attributes."""
        mcs._check_required_class_attributes(abstract_round_cls)

    @classmethod
    def _check_required_class_attributes(
        mcs, abstract_round_cls: Type["AbstractRound"]
    ) -> None:
        """Check that required class attributes are set."""
        if not hasattr(abstract_round_cls, "synchronized_data_class"):
            raise AbstractRoundInternalError(
                f"'synchronized_data_class' not set on {abstract_round_cls}"
            )
        if not hasattr(abstract_round_cls, "payload_class"):
            raise AbstractRoundInternalError(
                f"'payload_class' not set on {abstract_round_cls}"
            )
        if not hasattr(abstract_round_cls, "payload_attribute"):
            raise AbstractRoundInternalError(
                f"'payload_attribute' not set on {abstract_round_cls}"
            )


class AbstractRound(Generic[EventType], ABC, metaclass=_MetaAbstractRound):
    """
    This class represents an abstract round.

    A round is a state of the FSM App execution. It usually involves
    interactions between participants in the FSM App,
    although this is not enforced at this level of abstraction.

    Concrete classes must set:
    - synchronized_data_class: the data class associated with this round;
    - payload_class: the payload type that is allowed for this round;
    - payload_attribute: the attribute of the payload of this round.

    Optionally, round_id can be defined, although it is recommended to use the autogenerated id.
    """

    __pattern = re.compile(r"(?<!^)(?=[A-Z])")
    _previous_round_payload_class: Optional[Type[BaseTxPayload]]

    payload_class: Optional[Type[BaseTxPayload]]
    payload_attribute: str
    synchronized_data_class: Type[BaseSynchronizedData]

    round_id: str

    def __init__(
        self,
        synchronized_data: BaseSynchronizedData,
        consensus_params: ConsensusParams,
        previous_round_payload_class: Optional[Type[BaseTxPayload]] = None,
    ) -> None:
        """Initialize the round."""
        self._consensus_params = consensus_params
        self._synchronized_data = synchronized_data
        self.block_confirmations = 0
        self._previous_round_payload_class = previous_round_payload_class

    @classmethod
    def auto_round_id(cls) -> str:
        """
        Get round id automatically.

        This method returns the auto generated id from the class name if the
        class variable behaviour_id is not set on the child class.
        Otherwise, it returns the class variable behaviour_id.
        """
        return (
            cls.round_id
            if isinstance(cls.round_id, str)
            else cls.__pattern.sub("_", cls.__name__).lower()
        )

    @property  # type: ignore
    def round_id(self) -> str:
        """Get round id."""
        return self.auto_round_id()

    @property
    def synchronized_data(self) -> BaseSynchronizedData:
        """Get the synchronized data."""
        return self._synchronized_data

    def check_transaction(self, transaction: Transaction) -> None:
        """
        Check transaction against the current state.

        :param transaction: the transaction
        """
        self.check_payload_type(transaction)
        self.check_payload(transaction.payload)

    def process_transaction(self, transaction: Transaction) -> None:
        """
        Process a transaction.

        By convention, the payload handler should be a method
        of the class that is named '{payload_name}'.

        :param transaction: the transaction.
        """
        self.check_payload_type(transaction)
        self.process_payload(transaction.payload)

    @abstractmethod
    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Enum]]:
        """
        Process the end of the block.

        The role of this method is check whether the round
        is considered ended.

        If the round is ended, the return value is
         - the final result of the round.
         - the event that triggers a transition. If None, the period
            in which the round was executed is considered ended.

        This is done after each block because we consider the consensus engine's
        block, and not the transaction, as the smallest unit
        on which the consensus is reached; in other words,
        each read operation on the state should be done
        only after each block, and not after each transaction.
        """

    def check_payload_type(self, transaction: Transaction) -> None:
        """
        Check the transaction is of the allowed transaction type.

        :param transaction: the transaction
        :raises: TransactionTypeNotRecognizedError if the transaction can be
                 applied to the current state.
        """
        if self.payload_class is None:
            raise TransactionTypeNotRecognizedError(
                "current round does not allow transactions"
            )

        payload_class = type(transaction.payload)

        if payload_class is self._previous_round_payload_class:
            raise LateArrivingTransaction(
                f"request '{transaction.payload}' is from previous round; skipping"
            )

        if payload_class is not self.payload_class:
            raise TransactionTypeNotRecognizedError(
                f"request '{payload_class}' not recognized; only {self.payload_class} is supported"
            )

    @classmethod
    def check_majority_possible_with_new_voter(
        cls,
        votes_by_participant: Dict[str, BaseTxPayload],
        new_voter: str,
        new_vote: BaseTxPayload,
        nb_participants: int,
        exception_cls: Type[ABCIAppException] = ABCIAppException,
    ) -> None:
        """
        Check that a Byzantine majority is achievable, once a new vote is added.

         :param votes_by_participant: a mapping from a participant to its vote,
                before the new vote is added
         :param new_voter: the new voter
         :param new_vote: the new vote
         :param nb_participants: the total number of participants
         :param exception_cls: the class of the exception to raise in case the
                               check fails.
         :raises: exception_cls: in case the check does not pass.
        """
        # check preconditions
        enforce(
            new_voter not in votes_by_participant,
            "voter has already voted",
            ABCIAppInternalError,
        )
        enforce(
            len(votes_by_participant) <= nb_participants - 1,
            "nb_participants not consistent with votes_by_participants",
            ABCIAppInternalError,
        )

        # copy the input dictionary to avoid side effects
        votes_by_participant = copy(votes_by_participant)

        # add the new vote
        votes_by_participant[new_voter] = new_vote

        cls.check_majority_possible(
            votes_by_participant, nb_participants, exception_cls=exception_cls
        )

    @classmethod
    def check_majority_possible(
        cls,
        votes_by_participant: Dict[str, BaseTxPayload],
        nb_participants: int,
        exception_cls: Type[ABCIAppException] = ABCIAppException,
    ) -> None:
        """
        Check that a Byzantine majority is still achievable.

        The idea is that, even if all the votes have not been delivered yet,
        it can be deduced whether a quorum cannot be reached due to
        divergent preferences among the voters and due to a too small
        number of other participants whose vote has not been delivered yet.

        The check fails iff:

            nb_remaining_votes + largest_nb_votes < quorum

        That is, if the number of remaining votes is not enough to make
        the most voted item so far to exceed the quorum.

        Preconditions on the input:
        - the size of votes_by_participant should not be greater than
          "nb_participants - 1" voters
        - new voter must not be in the current votes_by_participant

        :param votes_by_participant: a mapping from a participant to its vote
        :param nb_participants: the total number of participants
        :param exception_cls: the class of the exception to raise in case the
                              check fails.
        :raises exception_cls: in case the check does not pass.
        """
        enforce(
            nb_participants > 0 and len(votes_by_participant) <= nb_participants,
            "nb_participants not consistent with votes_by_participants",
            ABCIAppInternalError,
        )
        if len(votes_by_participant) == 0:
            return

        votes = votes_by_participant.values()
        vote_count = Counter(tuple(sorted(v.data.items())) for v in votes)
        largest_nb_votes = max(vote_count.values())
        nb_votes_received = sum(vote_count.values())
        nb_remaining_votes = nb_participants - nb_votes_received

        threshold = consensus_threshold(nb_participants)

        if nb_remaining_votes + largest_nb_votes < threshold:
            raise exception_cls(
                f"cannot reach quorum={threshold}, number of remaining votes={nb_remaining_votes}, number of most voted item's votes={largest_nb_votes}"
            )

    @classmethod
    def is_majority_possible(
        cls, votes_by_participant: Dict[str, BaseTxPayload], nb_participants: int
    ) -> bool:
        """
        Return true if a Byzantine majority is achievable, false otherwise.

        :param votes_by_participant: a mapping from a participant to its vote
        :param nb_participants: the total number of participants
        :return: True if the majority is still possible, false otherwise.
        """
        try:
            cls.check_majority_possible(votes_by_participant, nb_participants)
        except ABCIAppException:
            return False
        return True

    @property
    def consensus_threshold(self) -> int:
        """Consensus threshold"""
        return self._consensus_params.consensus_threshold

    @abstractmethod
    def check_payload(self, payload: BaseTxPayload) -> None:
        """Check payload."""

    @abstractmethod
    def process_payload(self, payload: BaseTxPayload) -> None:
        """Process payload."""


class DegenerateRound(AbstractRound, ABC):
    """
    This class represents the finished round during operation.

    It is a sink round.
    """

    payload_class = None
    payload_attribute = ""
    synchronized_data_class = BaseSynchronizedData

    def check_payload(self, payload: BaseTxPayload) -> None:
        """Check payload."""
        raise NotImplementedError(  # pragma: nocover
            "DegenerateRound should not be used in operation."
        )

    def process_payload(self, payload: BaseTxPayload) -> None:
        """Process payload."""
        raise NotImplementedError(  # pragma: nocover
            "DegenerateRound should not be used in operation."
        )

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Enum]]:
        """End block."""
        raise NotImplementedError(  # pragma: nocover
            "DegenerateRound should not be used in operation."
        )


class CollectionRound(AbstractRound, ABC):
    """
    CollectionRound.

    This class represents abstract logic for collection based rounds where
    the round object needs to collect data from different agents. The data
    might for example be from a voting round or estimation round.
    """

    # allow_rejoin is used to allow agents not currently active to deliver a payload
    _allow_rejoin_payloads: bool = False
    # if the payload is serialized to bytes, we verify that the length specified matches
    _hash_length: Optional[int] = None

    def __init__(self, *args: Any, **kwargs: Any):
        """Initialize the collection round."""
        super().__init__(*args, **kwargs)
        self.collection: Dict[str, BaseTxPayload] = {}

    @property
    def accepting_payloads_from(self) -> FrozenSet[str]:
        """Accepting from the active set, or also from (re)joiners"""
        if self._allow_rejoin_payloads:
            return self.synchronized_data.all_participants
        return self.synchronized_data.participants

    @property
    def payloads(self) -> List[BaseTxPayload]:
        """Get all agent payloads"""
        return list(self.collection.values())

    @property
    def payloads_count(self) -> Counter:
        """Get count of payload attributes"""
        return Counter(map(lambda p: getattr(p, self.payload_attribute), self.payloads))

    def process_payload(self, payload: BaseTxPayload) -> None:
        """Process payload."""
        if payload.round_count != self.synchronized_data.round_count:
            raise ABCIAppInternalError(
                f"Expected round count {self.synchronized_data.round_count} and got {payload.round_count}."
            )

        sender = payload.sender
        if sender not in self.accepting_payloads_from:
            raise ABCIAppInternalError(
                f"{sender} not in list of participants: {sorted(self.accepting_payloads_from)}"
            )

        if sender in self.collection:
            raise ABCIAppInternalError(
                f"sender {sender} has already sent value for round: {self.round_id}"
            )

        if self._hash_length:
            content = payload.data.get(self.payload_attribute)
            if not content or len(content) % self._hash_length:
                msg = f"Expecting serialized data of chunk size {self._hash_length}"
                raise ABCIAppInternalError(f"{msg}, got: {content} in {self.round_id}")

        self.collection[sender] = payload

    def check_payload(self, payload: BaseTxPayload) -> None:
        """Check Payload"""

        # NOTE: the TransactionNotValidError is intercepted in ABCIRoundHandler.deliver_tx
        #  which means it will be logged instead of raised
        if payload.round_count != self.synchronized_data.round_count:
            raise TransactionNotValidError(
                f"Expected round count {self.synchronized_data.round_count} and got {payload.round_count}."
            )

        sender_in_participant_set = payload.sender in self.accepting_payloads_from
        if not sender_in_participant_set:
            raise TransactionNotValidError(
                f"{payload.sender} not in list of participants: {sorted(self.accepting_payloads_from)}"
            )

        if payload.sender in self.collection:
            raise TransactionNotValidError(
                f"sender {payload.sender} has already sent value for round: {self.round_id}"
            )

        if self._hash_length:
            content = payload.data.get(self.payload_attribute)
            if not content or len(content) % self._hash_length:
                msg = f"Expecting serialized data of chunk size {self._hash_length}"
                raise TransactionNotValidError(
                    f"{msg}, got: {content} in {self.round_id}"
                )


class _CollectUntilAllRound(CollectionRound, ABC):
    """
    _CollectUntilAllRound

    This class represents logic for when rounds need to collect payloads from all agents.

    This round should only be used for registration of new agents.
    """

    def check_payload(self, payload: BaseTxPayload) -> None:
        """Check Payload"""
        if payload.round_count != self.synchronized_data.round_count:
            raise TransactionNotValidError(
                f"Expected round count {self.synchronized_data.round_count} and got {payload.round_count}."
            )

        if payload.sender in self.collection:
            raise TransactionNotValidError(
                f"sender {payload.sender} has already sent value for round: {self.round_id}"
            )

    def process_payload(self, payload: BaseTxPayload) -> None:
        """Process payload."""
        try:
            self.check_payload(payload)
        except TransactionNotValidError as e:
            raise ABCIAppInternalError(e.args[0]) from e

        self.collection[payload.sender] = payload

    @property
    def collection_threshold_reached(
        self,
    ) -> bool:
        """Check that the collection threshold has been reached."""
        return len(self.collection) >= self._consensus_params.max_participants


class CollectDifferentUntilAllRound(_CollectUntilAllRound, ABC):
    """
    CollectDifferentUntilAllRound

    This class represents logic for rounds where a round needs to collect
    different payloads from each agent.

    This round should only be used for registration of new agents when there is synchronization of the db.
    """

    def check_payload(self, payload: BaseTxPayload) -> None:
        """Check Payload"""
        collected_value = getattr(payload, self.payload_attribute)
        attribute_values = (
            getattr(collection_value, self.payload_attribute)
            for collection_value in self.collection.values()
        )

        if (
            payload.sender not in self.collection
            and collected_value in attribute_values
        ):
            raise TransactionNotValidError(
                f"`CollectDifferentUntilAllRound` encountered a value '{collected_value}' that already exists. "
                f"All values: {attribute_values}"
            )

        super().check_payload(payload)


class CollectSameUntilAllRound(_CollectUntilAllRound, ABC):
    """
    This class represents logic for when a round needs to collect the same payload from all the agents.

    This round should only be used for registration of new agents when there is no synchronization of the db.
    """

    def check_payload(self, payload: BaseTxPayload) -> None:
        """Check Payload"""
        collected_value = getattr(payload, self.payload_attribute)
        attribute_values = tuple(
            getattr(collection_value, self.payload_attribute)
            for collection_value in self.collection.values()
        )

        if (
            payload.sender not in self.collection
            and len(self.collection)
            and collected_value not in attribute_values
        ):
            raise TransactionNotValidError(
                f"`CollectSameUntilAllRound` encountered a value '{collected_value}' "
                f"which is not the same as the already existing one: '{attribute_values[0]}'"
            )

        super().check_payload(payload)

    @property
    def common_payload(
        self,
    ) -> Any:
        """Get the common payload among the agents."""
        most_common_payload, max_votes = self.payloads_count.most_common(1)[0]
        if max_votes < self._consensus_params.max_participants:
            raise ABCIAppInternalError(
                f"{max_votes} votes are not enough for `CollectSameUntilAllRound`. Expected: "
                f"`n_votes = max_participants = {self._consensus_params.max_participants}`"
            )
        return most_common_payload


class CollectSameUntilThresholdRound(CollectionRound, ABC):
    """
    CollectSameUntilThresholdRound

    This class represents logic for rounds where a round needs to collect
    same payload from k of n agents.
    """

    done_event: Any
    no_majority_event: Any
    none_event: Any
    collection_key: str
    selection_key: str

    @property
    def threshold_reached(
        self,
    ) -> bool:
        """Check if the threshold has been reached."""
        counts = self.payloads_count.values()
        return any(count >= self.consensus_threshold for count in counts)

    @property
    def most_voted_payload(
        self,
    ) -> Any:
        """Get the most voted payload."""
        most_voted_payload, max_votes = self.payloads_count.most_common()[0]
        if max_votes < self.consensus_threshold:
            raise ABCIAppInternalError("not enough votes")
        return most_voted_payload

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Enum]]:
        """Process the end of the block."""
        if self.threshold_reached and self.most_voted_payload is not None:
            synchronized_data = self.synchronized_data.update(
                synchronized_data_class=self.synchronized_data_class,
                **{
                    self.collection_key: self.collection,
                    self.selection_key: self.most_voted_payload,
                },
            )
            return synchronized_data, self.done_event
        if self.threshold_reached and self.most_voted_payload is None:
            return self.synchronized_data, self.none_event
        if not self.is_majority_possible(
            self.collection, self.synchronized_data.nb_participants
        ):
            return self.synchronized_data, self.no_majority_event
        return None


class OnlyKeeperSendsRound(AbstractRound, ABC):
    """
    OnlyKeeperSendsRound

    This class represents logic for rounds where only one agent sends a
    payload
    """

    keeper_payload: Optional[Any]
    done_event: Any
    fail_event: Any
    payload_key: str

    def __init__(self, *args: Any, **kwargs: Any):
        """Initialize the 'collect-observation' round."""
        super().__init__(*args, **kwargs)
        self.keeper_sent_payload = False
        self.keeper_payload: Optional[Any] = None

    def process_payload(self, payload: BaseTxPayload) -> None:
        """Handle a deploy safe payload."""
        if payload.round_count != self.synchronized_data.round_count:
            raise ABCIAppInternalError(
                f"Expected round count {self.synchronized_data.round_count} and got {payload.round_count}."
            )

        sender = payload.sender

        if sender not in self.synchronized_data.participants:
            raise ABCIAppInternalError(
                f"{sender} not in list of participants: {sorted(self.synchronized_data.participants)}"
            )

        if sender != self.synchronized_data.most_voted_keeper_address:
            raise ABCIAppInternalError(f"{sender} not elected as keeper.")

        if self.keeper_sent_payload:
            raise ABCIAppInternalError("keeper already set the payload.")

        self.keeper_payload = getattr(payload, self.payload_attribute)
        self.keeper_sent_payload = True

    def check_payload(self, payload: BaseTxPayload) -> None:
        """Check a deploy safe payload can be applied to the current state."""
        if payload.round_count != self.synchronized_data.round_count:
            raise TransactionNotValidError(
                f"Expected round count {self.synchronized_data.round_count} and got {payload.round_count}."
            )

        sender = payload.sender
        sender_in_participant_set = sender in self.synchronized_data.participants
        if not sender_in_participant_set:
            raise TransactionNotValidError(
                f"{sender} not in list of participants: {sorted(self.synchronized_data.participants)}"
            )

        sender_is_elected_sender = (
            sender == self.synchronized_data.most_voted_keeper_address
        )
        if not sender_is_elected_sender:
            raise TransactionNotValidError(f"{sender} not elected as keeper.")

        if self.keeper_sent_payload:
            raise TransactionNotValidError("keeper payload value already set.")

    @property
    def has_keeper_sent_payload(
        self,
    ) -> bool:
        """Check if keeper has sent the payload."""

        return self.keeper_sent_payload

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Enum]]:
        """Process the end of the block."""
        # if reached participant threshold, set the result
        if self.has_keeper_sent_payload and self.keeper_payload is not None:
            synchronized_data = self.synchronized_data.update(
                synchronized_data_class=self.synchronized_data_class,
                **{self.payload_key: self.keeper_payload},
            )
            return synchronized_data, self.done_event
        if self.has_keeper_sent_payload and self.keeper_payload is None:
            return self.synchronized_data, self.fail_event
        return None


class VotingRound(CollectionRound, ABC):
    """
    VotingRound

    This class represents logic for rounds where a round needs votes from
    agents, pass if k same votes of n agents
    """

    done_event: Any
    negative_event: Any
    none_event: Any
    no_majority_event: Any
    collection_key: str

    @property
    def vote_count(self) -> Counter:
        """Get agent payload vote count"""

        def parse_payload(payload: Any) -> Optional[bool]:
            if not hasattr(payload, "vote"):
                raise ValueError(f"payload {payload} has no attribute `vote`")
            return payload.vote

        return Counter(parse_payload(payload) for payload in self.collection.values())

    @property
    def positive_vote_threshold_reached(self) -> bool:
        """Check that the vote threshold has been reached."""
        return self.vote_count[True] >= self.consensus_threshold

    @property
    def negative_vote_threshold_reached(self) -> bool:
        """Check that the vote threshold has been reached."""
        return self.vote_count[False] >= self.consensus_threshold

    @property
    def none_vote_threshold_reached(self) -> bool:
        """Check that the vote threshold has been reached."""
        return self.vote_count[None] >= self.consensus_threshold

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Enum]]:
        """Process the end of the block."""
        # if reached participant threshold, set the result
        if self.positive_vote_threshold_reached:
            synchronized_data = self.synchronized_data.update(
                synchronized_data_class=self.synchronized_data_class,
                **{self.collection_key: self.collection},
            )
            return synchronized_data, self.done_event
        if self.negative_vote_threshold_reached:
            return self.synchronized_data, self.negative_event
        if self.none_vote_threshold_reached:
            return self.synchronized_data, self.none_event
        if not self.is_majority_possible(
            self.collection, self.synchronized_data.nb_participants
        ):
            return self.synchronized_data, self.no_majority_event
        return None


class CollectDifferentUntilThresholdRound(CollectionRound, ABC):
    """
    CollectDifferentUntilThresholdRound

    This class represents logic for rounds where a round needs to collect
    different payloads from k of n agents
    """

    done_event: Any
    no_majority_event: Any
    collection_key: str
    required_block_confirmations: int = 0

    @property
    def collection_threshold_reached(
        self,
    ) -> bool:
        """Check if the threshold has been reached."""
        return len(self.collection) >= self.consensus_threshold

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Enum]]:
        """Process the end of the block."""
        if self.collection_threshold_reached:
            self.block_confirmations += 1
        if (  # contracts are set from previous rounds
            self.collection_threshold_reached
            and self.block_confirmations > self.required_block_confirmations
            # we also wait here as it gives more (available) agents time to join
        ):
            synchronized_data = self.synchronized_data.update(
                synchronized_data_class=self.synchronized_data_class,
                **{
                    self.collection_key: self.collection,
                },
            )
            return synchronized_data, self.done_event
        if (
            not self.is_majority_possible(
                self.collection, self.synchronized_data.nb_participants
            )
            and self.block_confirmations > self.required_block_confirmations
        ):
            return self.synchronized_data, self.no_majority_event  # pragma: no cover
        return None


class CollectNonEmptyUntilThresholdRound(CollectDifferentUntilThresholdRound, ABC):
    """
    Collect all the data among agents.

    This class represents logic for rounds where we need to collect
    payloads from each agent which will contain optional, different data and only keep the non-empty.

    This round may be used for cases that we want to collect all the agent's data, such as late-arriving messages.
    """

    none_event: Any

    def _get_non_empty_values(self) -> List:
        """Get the non-empty values from the payload, for the given attribute."""
        non_empty_values = []

        for payload in self.collection.values():
            attribute_value = getattr(payload, self.payload_attribute, None)
            if attribute_value is not None:
                non_empty_values.append(attribute_value)

        return non_empty_values

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Enum]]:
        """Process the end of the block."""
        if self.collection_threshold_reached:
            self.block_confirmations += 1
        if (
            self.collection_threshold_reached
            and self.block_confirmations > self.required_block_confirmations
        ):
            non_empty_values = self._get_non_empty_values()

            synchronized_data = self.synchronized_data.update(
                synchronized_data_class=self.synchronized_data_class,
                **{
                    self.collection_key: non_empty_values,
                },
            )

            if len(non_empty_values) == 0:
                return synchronized_data, self.none_event
            return synchronized_data, self.done_event

        # TODO: https://github.com/valory-xyz/open-autonomy/pull/1466#issuecomment-1288067700
        if (
            not self.is_majority_possible(
                self.collection, self.synchronized_data.nb_participants
            )
            and self.block_confirmations > self.required_block_confirmations
        ):
            return self.synchronized_data, self.no_majority_event
        return None


AppState = Type[AbstractRound]
AbciAppTransitionFunction = Dict[AppState, Dict[EventType, AppState]]
EventToTimeout = Dict[EventType, float]


@dataclass(order=True)
class TimeoutEvent(Generic[EventType]):
    """Timeout event."""

    deadline: datetime.datetime
    entry_count: int
    event: EventType = field(compare=False)
    cancelled: bool = field(default=False, compare=False)


class Timeouts(Generic[EventType]):
    """Class to keep track of pending timeouts."""

    def __init__(self) -> None:
        """Initialize."""
        # The entry count serves as a tie-breaker so that two tasks with
        # the same priority are returned in the order they were added
        self._counter = itertools.count()

        # The timeout priority queue keeps the earliest deadline at the top.
        self._heap: List[TimeoutEvent[EventType]] = []

        # Mapping from entry id to task
        self._entry_finder: Dict[int, TimeoutEvent[EventType]] = {}

    @property
    def size(self) -> int:
        """Get the size of the timeout queue."""
        return len(self._heap)

    def add_timeout(self, deadline: datetime.datetime, event: EventType) -> int:
        """Add a timeout."""
        entry_count = next(self._counter)
        timeout_event = TimeoutEvent[EventType](deadline, entry_count, event)
        heapq.heappush(self._heap, timeout_event)
        self._entry_finder[entry_count] = timeout_event
        return entry_count

    def cancel_timeout(self, entry_count: int) -> None:
        """
        Remove a timeout.

        :param entry_count: the entry id to remove.
        :raises: KeyError: if the entry count is not found.
        """
        if entry_count in self._entry_finder:
            self._entry_finder[entry_count].cancelled = True

    def pop_earliest_cancelled_timeouts(self) -> None:
        """Pop earliest cancelled timeouts."""
        if self.size == 0:
            return
        entry = self._heap[0]  # heap peak
        while entry.cancelled:
            self.pop_timeout()
            if self.size == 0:
                break
            entry = self._heap[0]

    def get_earliest_timeout(self) -> Tuple[datetime.datetime, Any]:
        """Get the earliest timeout-event pair."""
        entry = self._heap[0]
        return entry.deadline, entry.event

    def pop_timeout(self) -> Tuple[datetime.datetime, Any]:
        """Remove and return the earliest timeout-event pair."""
        entry = heapq.heappop(self._heap)
        del self._entry_finder[entry.entry_count]
        return entry.deadline, entry.event


class _MetaAbciApp(ABCMeta):
    """A metaclass that validates AbciApp's attributes."""

    def __new__(mcs, name: str, bases: Tuple, namespace: Dict, **kwargs: Any) -> Type:  # type: ignore
        """Initialize the class."""
        new_cls = super().__new__(mcs, name, bases, namespace, **kwargs)

        if ABC in bases:
            # abstract class, return
            return new_cls
        if not issubclass(new_cls, AbciApp):
            # the check only applies to AbciApp subclasses
            return new_cls

        mcs._check_consistency(cast(Type[AbciApp], new_cls))
        return new_cls

    @classmethod
    def _check_consistency(mcs, abci_app_cls: Type["AbciApp"]) -> None:
        """Check consistency of class attributes."""
        mcs._check_required_class_attributes(abci_app_cls)
        mcs._check_initial_states_and_final_states(abci_app_cls)
        mcs._check_consistency_outgoing_transitions_from_non_final_states(abci_app_cls)
        mcs._check_db_constraints_consistency(abci_app_cls)

    @classmethod
    def _check_required_class_attributes(mcs, abci_app_cls: Type["AbciApp"]) -> None:
        """Check that required class attributes are set."""
        if not hasattr(abci_app_cls, "initial_round_cls"):
            raise ABCIAppInternalError("'initial_round_cls' field not set")
        if not hasattr(abci_app_cls, "transition_function"):
            raise ABCIAppInternalError("'transition_function' field not set")

    @classmethod
    def _check_initial_states_and_final_states(
        mcs,
        abci_app_cls: Type["AbciApp"],
    ) -> None:
        """
        Check that initial states and final states are consistent.

        I.e.:
        - check that all the initial states are in the set of states specified
          by the transition function.
        - check that the initial state has outgoing transitions
        - check that the initial state does not trigger timeout events. This is
          because we need at least one block/timestamp to start timeouts.
        - check that initial states are not final states.
        - check that the set of final states is a proper subset of the set of
          states.
        - check that a final state does not have outgoing transitions.

        :param abci_app_cls: the AbciApp class
        """
        initial_round_cls = abci_app_cls.initial_round_cls
        initial_states = abci_app_cls.initial_states
        transition_function = abci_app_cls.transition_function
        final_states = abci_app_cls.final_states
        states = abci_app_cls.get_all_rounds()

        enforce(
            initial_states == set() or initial_round_cls in initial_states,
            f"initial round class {initial_round_cls} is not in the set of "
            f"initial states: {initial_states}",
        )
        enforce(
            initial_round_cls in states
            and all(initial_state in states for initial_state in initial_states),
            "initial states must be in the set of states",
        )

        true_initial_states = (
            initial_states if initial_states != set() else {initial_round_cls}
        )
        enforce(
            all(
                initial_state not in final_states
                for initial_state in true_initial_states
            ),
            "initial states cannot be final states",
        )

        unknown_final_states = set.difference(final_states, states)
        enforce(
            len(unknown_final_states) == 0,
            f"the following final states are not in the set of states:"
            f" {unknown_final_states}",
        )

        enforce(
            all(
                len(transition_function[final_state]) == 0
                for final_state in final_states
            ),
            "final states cannot have outgoing transitions",
        )

        enforce(
            all(
                issubclass(final_state, DegenerateRound) for final_state in final_states
            ),
            "final round classes must be subclasses of the DegenerateRound class",
        )

    @classmethod
    def _check_db_constraints_consistency(mcs, abci_app_cls: Type["AbciApp"]) -> None:
        """Check that the pre and post conditions on the db are consistent with the initial and final states."""
        expected = abci_app_cls.initial_states
        actual = abci_app_cls.db_pre_conditions.keys()
        is_pre_conditions_set = len(actual) != 0
        invalid_initial_states = (
            set.difference(expected, actual) if is_pre_conditions_set else set()
        )
        enforce(
            len(invalid_initial_states) == 0,
            f"db pre conditions contain invalid initial states: {invalid_initial_states}",
        )
        expected = abci_app_cls.final_states
        actual = abci_app_cls.db_post_conditions.keys()
        is_post_conditions_set = len(actual) != 0
        invalid_final_states = (
            set.difference(expected, actual) if is_post_conditions_set else set()
        )
        enforce(
            len(invalid_final_states) == 0,
            f"db post conditions contain invalid final states: {invalid_final_states}",
        )
        all_pre_conditions = {
            value
            for values in abci_app_cls.db_pre_conditions.values()
            for value in values
        }
        all_post_conditions = {
            value
            for values in abci_app_cls.db_post_conditions.values()
            for value in values
        }
        enforce(
            len(all_pre_conditions.intersection(all_post_conditions)) == 0,
            "db pre and post conditions intersect",
        )
        intersection = set(abci_app_cls.default_db_preconditions).intersection(
            all_pre_conditions
        )
        enforce(
            len(intersection) == 0,
            f"db pre conditions contain value that is a default pre condition: {intersection}",
        )
        intersection = set(abci_app_cls.default_db_preconditions).intersection(
            all_post_conditions
        )
        enforce(
            len(intersection) == 0,
            f"db post conditions contain value that is a default post condition: {intersection}",
        )

    @classmethod
    def _check_consistency_outgoing_transitions_from_non_final_states(
        mcs, abci_app_cls: Type["AbciApp"]
    ) -> None:
        """
        Check consistency of outgoing transitions from non-final states.

        In particular, check that all non-final states have:
        - at least one non-timeout transition.
        - at most one timeout transition

        :param abci_app_cls: the AbciApp class
        """
        states = abci_app_cls.get_all_rounds()
        event_to_timeout = abci_app_cls.event_to_timeout

        non_final_states = states.difference(abci_app_cls.final_states)
        timeout_events = set(event_to_timeout.keys())
        for non_final_state in non_final_states:
            outgoing_transitions = abci_app_cls.transition_function[non_final_state]

            outgoing_events = set(outgoing_transitions.keys())
            outgoing_timeout_events = set.intersection(outgoing_events, timeout_events)
            outgoing_nontimeout_events = set.difference(outgoing_events, timeout_events)

            enforce(
                len(outgoing_timeout_events) < 2,
                f"non-final state {non_final_state} cannot have more than one "
                f"outgoing timeout event, got: "
                f"{', '.join(map(str, outgoing_timeout_events))}",
            )
            enforce(
                len(outgoing_nontimeout_events) > 0,
                f"non-final state {non_final_state} must have at least one "
                f"non-timeout transition",
            )


class AbciApp(
    Generic[EventType], ABC, metaclass=_MetaAbciApp
):  # pylint: disable=too-many-instance-attributes
    """
    Base class for ABCI apps.

    Concrete classes of this class implement the ABCI App.
    """

    initial_round_cls: AppState
    initial_states: Set[AppState] = set()
    transition_function: AbciAppTransitionFunction
    final_states: Set[AppState] = set()
    event_to_timeout: EventToTimeout = {}
    cross_period_persisted_keys: List[str] = ["safe_contract_address"]
    background_round_cls: Optional[AppState] = None
    termination_transition_function: Optional[AbciAppTransitionFunction] = None
    termination_event: Optional[EventType] = None
    default_db_preconditions: List[str] = BaseSynchronizedData.default_db_keys
    db_pre_conditions: Dict[AppState, List[str]] = {}
    db_post_conditions: Dict[AppState, List[str]] = {}
    _is_abstract: bool = True

    def __init__(
        self,
        synchronized_data: BaseSynchronizedData,
        consensus_params: ConsensusParams,
        logger: logging.Logger,
    ):
        """Initialize the AbciApp."""

        synchronized_data_class = self.initial_round_cls.synchronized_data_class
        synchronized_data = synchronized_data_class(db=synchronized_data.db)

        self._initial_synchronized_data = synchronized_data
        self.consensus_params = consensus_params
        self.logger = logger

        self._current_round_cls: Optional[AppState] = None
        self._current_round: Optional[AbstractRound] = None
        self._background_round: Optional[AbstractRound] = None
        self._last_round: Optional[AbstractRound] = None
        self._previous_rounds: List[AbstractRound] = []
        self._current_round_height: int = 0
        self._round_results: List[BaseSynchronizedData] = []
        self._last_timestamp: Optional[datetime.datetime] = None
        self._current_timeout_entries: List[int] = []
        self._timeouts = Timeouts[EventType]()
        self._reset_index = 0
        self._is_termination_set = (
            self.background_round_cls is not None
            and self.termination_transition_function is not None
            and self.termination_event is not None
        )

    @classmethod
    def is_abstract(cls) -> bool:
        """Return if the abci app is abstract."""
        return cls._is_abstract

    @classmethod
    def add_termination(
        cls,
        background_round_cls: AppState,
        termination_event: EventType,
        termination_abci_app: Type["AbciApp"],
    ) -> Type["AbciApp"]:
        """Sets the termination related class variables."""
        cls.background_round_cls = background_round_cls
        cls.termination_transition_function = termination_abci_app.transition_function
        cls.termination_event = termination_event
        new_cross_period_persisted_keys = copy(cls.cross_period_persisted_keys)
        new_cross_period_persisted_keys.extend(
            termination_abci_app.cross_period_persisted_keys
        )
        new_cross_period_persisted_keys = list(set(new_cross_period_persisted_keys))
        cls.cross_period_persisted_keys = new_cross_period_persisted_keys
        return cls

    @property
    def synchronized_data(self) -> BaseSynchronizedData:
        """Return the current synchronized data."""
        latest_result = self.latest_result or self._initial_synchronized_data
        if self._current_round_cls is None:
            return latest_result
        synchronized_data_class = self._current_round_cls.synchronized_data_class
        result = (
            synchronized_data_class(db=latest_result.db)
            if isclass(synchronized_data_class)
            and issubclass(synchronized_data_class, BaseSynchronizedData)
            else latest_result
        )
        return result

    @property
    def reset_index(self) -> int:
        """Return the reset index."""
        return self._reset_index

    @reset_index.setter
    def reset_index(self, reset_index: int) -> None:
        """Set the reset index."""
        self._reset_index = reset_index

    @classmethod
    def get_all_rounds(cls) -> Set[AppState]:
        """Get all the round states."""
        return set(cls.transition_function)

    @classmethod
    def get_all_events(cls) -> Set[EventType]:
        """Get all the events."""
        events: Set[EventType] = set()
        for _, transitions in cls.transition_function.items():
            events.update(transitions.keys())
        return events

    @staticmethod
    def _get_rounds_from_transition_function(
        transition_function: Optional[AbciAppTransitionFunction],
    ) -> Set[AppState]:
        """Get rounds from a transition function."""
        if transition_function is None:
            return set()
        result: Set[AppState] = set()
        for start, transitions in transition_function.items():
            result.add(start)
            result.update(transitions.values())
        return result

    @classmethod
    def get_all_round_classes(
        cls, include_termination_rounds: bool = False
    ) -> Set[AppState]:
        """Get all round classes."""
        result: Set[AppState] = cls._get_rounds_from_transition_function(
            cls.transition_function
        )
        if include_termination_rounds:
            termination_rounds = cls._get_rounds_from_transition_function(
                cls.termination_transition_function,
            )
            result.update(termination_rounds)
        return result

    @property
    def last_timestamp(self) -> datetime.datetime:
        """Get last timestamp."""
        if self._last_timestamp is None:
            raise ABCIAppInternalError("last timestamp is None")
        return self._last_timestamp

    def setup(self) -> None:
        """Set up the behaviour."""
        self.schedule_round(self.initial_round_cls)
        if self.is_termination_set:
            self.background_round_cls = cast(AppState, self.background_round_cls)
            self._background_round = self.background_round_cls(
                self._initial_synchronized_data,
                self.consensus_params,
            )

    def _log_start(self) -> None:
        """Log the entering in the round."""
        self.logger.info(
            f"Entered in the '{self.current_round.round_id}' round for period "
            f"{self.synchronized_data.period_count}"
        )

    def _log_end(self, event: EventType) -> None:
        """Log the exiting from the round."""
        self.logger.info(
            f"'{self.current_round.round_id}' round is done with event: {event}"
        )

    def _extend_previous_rounds_with_current_round(self) -> None:
        self._previous_rounds.append(self.current_round)
        self._current_round_height += 1

    def schedule_round(self, round_cls: AppState) -> None:
        """
        Schedule a round class.

        this means:
        - cancel timeout events belonging to the current round;
        - instantiate the new round class and set it as current round;
        - create new timeout events and schedule them according to the latest
          timestamp.

        :param round_cls: the class of the new round.
        """
        self.logger.debug("scheduling new round: %s", round_cls)
        for entry_id in self._current_timeout_entries:
            self._timeouts.cancel_timeout(entry_id)

        self._current_timeout_entries = []
        next_events = list(self.transition_function.get(round_cls, {}).keys())
        for event in next_events:
            timeout = self.event_to_timeout.get(event, None)
            # if first round, last_timestamp is None.
            # This means we do not schedule timeout events,
            # but we allow timeout events from the initial state
            # in case of concatenation.
            if timeout is not None and self._last_timestamp is not None:
                # last timestamp can be in the past relative to last seen block
                # time if we're scheduling from within update_time
                deadline = self.last_timestamp + datetime.timedelta(0, timeout)
                entry_id = self._timeouts.add_timeout(deadline, event)
                self.logger.info(
                    "scheduling timeout of %s seconds for event %s with deadline %s",
                    timeout,
                    event,
                    deadline,
                )
                self._current_timeout_entries.append(entry_id)

        self._last_round = self._current_round
        self._current_round_cls = round_cls
        self._current_round = round_cls(
            self.synchronized_data,
            self.consensus_params,
            (
                self._last_round.payload_class
                if self._last_round is not None
                and self._last_round.payload_class
                != self._current_round_cls.payload_class
                # when transitioning to a round with the same payload type we set None as otherwise it will allow no tx to be sumitted
                else None
            ),
        )
        self._log_start()
        self.synchronized_data.db.increment_round_count()  # ROUND_COUNT_DEFAULT is -1

    @property
    def current_round(self) -> AbstractRound:
        """Get the current round."""
        if self._current_round is None:
            raise ValueError("current_round not set!")
        return self._current_round

    @property
    def background_round(self) -> AbstractRound:
        """Get the background round."""
        if self._background_round is None:
            raise ValueError("background_round not set!")
        return self._background_round

    @property
    def is_termination_set(self) -> bool:
        """Get whether termination is set."""
        return self._is_termination_set

    @property
    def current_round_id(self) -> Optional[str]:
        """Get the current round id."""
        return self._current_round.round_id if self._current_round else None

    @property
    def current_round_height(self) -> int:
        """Get the current round height."""
        return self._current_round_height

    @property
    def last_round_id(self) -> Optional[str]:
        """Get the last round id."""
        return self._last_round.round_id if self._last_round else None

    @property
    def is_finished(self) -> bool:
        """Check whether the AbciApp execution has finished."""
        return self._current_round is None

    @property
    def latest_result(self) -> Optional[BaseSynchronizedData]:
        """Get the latest result of the round."""
        return None if len(self._round_results) == 0 else self._round_results[-1]

    def check_transaction(self, transaction: Transaction) -> None:
        """
        Check a transaction.

        The background round runs concurrently with other (normal) rounds.
        First we check if the transaction is meant for the background round,
        if not we forward to the current round object.

        :param transaction: the transaction.
        """

        payload_type = type(transaction.payload)
        if (
            self.is_termination_set
            and payload_type is cast(AppState, self.background_round_cls).payload_class
        ):
            self.background_round.check_transaction(transaction)
            return
        self.current_round.check_transaction(transaction)

    def process_transaction(self, transaction: Transaction) -> None:
        """
        Process a transaction.

        The background round runs concurrently with other (normal) rounds.
        First we check if the transaction is meant for the background round,
        if not we forward to the current round object.

        :param transaction: the transaction.
        """

        payload_type = type(transaction.payload)
        if (
            self.is_termination_set
            and payload_type is cast(AppState, self.background_round_cls).payload_class
        ):
            self.background_round.process_transaction(transaction)
            return
        self.current_round.process_transaction(transaction)

    def process_event(
        self, event: EventType, result: Optional[BaseSynchronizedData] = None
    ) -> None:
        """Process a round event."""
        if self._current_round_cls is None:
            self.logger.info(
                f"cannot process event '{event}' as current state is not set"
            )
            return

        # we first check whether the event is the special termination event.
        # if that's the case, we proceed with the termination transition function,
        # regardless of what the current round is
        if self.is_termination_set and event == self.termination_event:
            self.termination_transition_function = cast(
                AbciAppTransitionFunction, self.termination_transition_function
            )
            self.background_round_cls = cast(AppState, self.background_round_cls)
            next_round_cls = self.termination_transition_function[
                self.background_round_cls
            ].get(event, None)

            # we switch the current transition function, with the termination
            # transition function. Note that we don't need to return to the
            # normal transition function (self.transition_function) because
            # the termination transition function is sufficient for going
            # through the necessary rounds
            self.transition_function = self.termination_transition_function
            self.logger.info(
                f"The termination event was produced, transitioning to `{cast(AppState, next_round_cls).auto_round_id()}`."
            )
        else:
            next_round_cls = self.transition_function[self._current_round_cls].get(
                event, None
            )
        self._extend_previous_rounds_with_current_round()
        if result is not None:
            self._round_results.append(result)
        else:
            # we duplicate the state since the round was preemptively ended
            self._round_results.append(self.current_round.synchronized_data)

        self._log_end(event)
        if next_round_cls is not None:
            self.schedule_round(next_round_cls)
        else:
            self.logger.warning("AbciApp has reached a dead end.")
            self._current_round_cls = None
            self._current_round = None

    def update_time(self, timestamp: datetime.datetime) -> None:
        """
        Observe timestamp from last block.

        :param timestamp: the latest block's timestamp.
        """
        self.logger.info("arrived block with timestamp: %s", timestamp)
        self.logger.info("current AbciApp time: %s", self._last_timestamp)
        self._timeouts.pop_earliest_cancelled_timeouts()

        if self._timeouts.size == 0:
            # if no pending timeouts, then it is safe to
            # move forward the last known timestamp to the
            # latest block's timestamp.
            self.logger.info("no pending timeout, move time forward")
            self._last_timestamp = timestamp
            return

        earliest_deadline, _ = self._timeouts.get_earliest_timeout()
        while earliest_deadline <= timestamp:
            # the earliest deadline is expired. Pop it from the
            # priority queue and process the timeout event.
            expired_deadline, timeout_event = self._timeouts.pop_timeout()
            self.logger.warning(
                "expired deadline %s with event %s at AbciApp time %s",
                expired_deadline,
                timeout_event,
                timestamp,
            )

            # the last timestamp now becomes the expired deadline
            # clearly, it is earlier than the current highest known
            # timestamp that comes from the consensus engine.
            # However, we need it to correctly simulate the timeouts
            # of the next rounds. (for now we set it to timestamp to explore
            # the impact)
            self._last_timestamp = timestamp
            self.logger.info(
                "current AbciApp time after expired deadline: %s", self.last_timestamp
            )

            self.process_event(timeout_event)

            self._timeouts.pop_earliest_cancelled_timeouts()
            if self._timeouts.size == 0:
                break
            earliest_deadline, _ = self._timeouts.get_earliest_timeout()

        # at this point, there is no timeout event left to be triggered,
        # so it is safe to move forward the last known timestamp to the
        # new block's timestamp
        self._last_timestamp = timestamp
        self.logger.debug("final AbciApp time: %s", self._last_timestamp)

    def cleanup(
        self,
        cleanup_history_depth: int,
        cleanup_history_depth_current: Optional[int] = None,
    ) -> None:
        """Clear data."""
        if len(self._round_results) != len(self._previous_rounds):
            raise ABCIAppInternalError("Inconsistent round lengths")  # pragma: nocover
        # we need at least the last round result, and for symmetry we impose the same condition
        # on previous rounds and state.db
        cleanup_history_depth = max(cleanup_history_depth, MIN_HISTORY_DEPTH)
        self._previous_rounds = self._previous_rounds[-cleanup_history_depth:]
        self._round_results = self._round_results[-cleanup_history_depth:]
        self.synchronized_data.db.cleanup(
            cleanup_history_depth, cleanup_history_depth_current
        )
        self._reset_index += 1

    def cleanup_current_histories(self, cleanup_history_depth_current: int) -> None:
        """Reset the parameter histories for the current entry (period), keeping only the latest values for each parameter."""
        self.synchronized_data.db.cleanup_current_histories(
            cleanup_history_depth_current
        )


class RoundSequence:  # pylint: disable=too-many-instance-attributes
    """
    This class represents a sequence of rounds

    It is a generic class that keeps track of the current round
    of the consensus period. It receives 'deliver_tx' requests
    from the ABCI handlers and forwards them to the current
    active round instance, which implements the ABCI app logic.
    It also schedules the next round (if any) whenever a round terminates.
    """

    class _BlockConstructionState(Enum):
        """
        Phases of an ABCI-based block construction.

        WAITING_FOR_BEGIN_BLOCK: the app is ready to accept
            "begin_block" requests from the consensus engine node.
            Then, it transitions into the 'WAITING_FOR_DELIVER_TX' phase.
        WAITING_FOR_DELIVER_TX: the app is building the block
            by accepting "deliver_tx" requests, and waits
            until the "end_block" request.
            Then, it transitions into the 'WAITING_FOR_COMMIT' phase.
        WAITING_FOR_COMMIT: the app finished the construction
            of the block, but it is waiting for the "commit"
            request from the consensus engine node.
            Then, it transitions into the 'WAITING_FOR_BEGIN_BLOCK' phase.
        """

        WAITING_FOR_BEGIN_BLOCK = "waiting_for_begin_block"
        WAITING_FOR_DELIVER_TX = "waiting_for_deliver_tx"
        WAITING_FOR_COMMIT = "waiting_for_commit"

    def __init__(self, abci_app_cls: Type[AbciApp]):
        """Initialize the round."""
        self._blockchain = Blockchain()
        self._syncing_up = True

        self._block_construction_phase = (
            RoundSequence._BlockConstructionState.WAITING_FOR_BEGIN_BLOCK
        )

        self._block_builder = BlockBuilder()
        self._abci_app_cls = abci_app_cls
        self._abci_app: Optional[AbciApp] = None
        self._last_round_transition_timestamp: Optional[datetime.datetime] = None
        self._last_round_transition_height = 0
        self._last_round_transition_root_hash = b""
        self._last_round_transition_tm_height: Optional[int] = None
        self._tm_height: Optional[int] = None
        self._block_stall_deadline: Optional[datetime.datetime] = None
        self._termination_called: bool = False

    def setup(self, *args: Any, **kwargs: Any) -> None:
        """
        Set up the round sequence.

        :param args: the arguments to pass to the round constructor.
        :param kwargs: the keyword-arguments to pass to the round constructor.
        """
        self._abci_app = self._abci_app_cls(*args, **kwargs)
        self._abci_app.setup()

    def start_sync(
        self,
    ) -> None:  # pragma: nocover
        """
        Set `_syncing_up` flag to true.

        if the _syncing_up flag is set to true, the `async_act` method won't be executed. For more details refer to
        https://github.com/valory-xyz/open-autonomy/issues/247#issuecomment-1012268656
        """
        self._syncing_up = True

    def end_sync(
        self,
    ) -> None:
        """Set `_syncing_up` flag to false."""
        self._syncing_up = False

    @property
    def syncing_up(
        self,
    ) -> bool:
        """Return if the app is in sync mode."""
        return self._syncing_up

    @property
    def abci_app(self) -> AbciApp:
        """Get the AbciApp."""
        if self._abci_app is None:
            raise ABCIAppInternalError("AbciApp not set")  # pragma: nocover
        return self._abci_app

    @property
    def blockchain(self) -> Blockchain:
        """Get the Blockchain instance."""
        return self._blockchain

    @blockchain.setter
    def blockchain(self, _blockchain: Blockchain) -> None:
        """Get the Blockchain instance."""
        self._blockchain = _blockchain

    @property
    def height(self) -> int:
        """Get the height."""
        return self._blockchain.height

    @property
    def is_finished(self) -> bool:
        """Check if a round sequence has finished."""
        return self.abci_app.is_finished

    def check_is_finished(self) -> None:
        """Check if a round sequence has finished."""
        if self.is_finished:
            raise ValueError(
                "round sequence is finished, cannot accept new transactions"
            )

    @property
    def current_round(self) -> AbstractRound:
        """Get current round."""
        return self.abci_app.current_round

    @property
    def background_round(self) -> AbstractRound:
        """Get the background round."""
        return self.abci_app.background_round

    @property
    def current_round_id(self) -> Optional[str]:
        """Get the current round id."""
        return self.abci_app.current_round_id

    @property
    def current_round_height(self) -> int:
        """Get the current round height."""
        return self.abci_app.current_round_height

    @property
    def last_round_id(self) -> Optional[str]:
        """Get the last round id."""
        return self.abci_app.last_round_id

    @property
    def last_timestamp(self) -> datetime.datetime:
        """Get the last timestamp."""
        last_timestamp = (
            self._blockchain.blocks[-1].timestamp
            if self._blockchain.length != 0
            else None
        )
        if last_timestamp is None:
            raise ABCIAppInternalError("last timestamp is None")
        return last_timestamp

    @property
    def last_round_transition_timestamp(
        self,
    ) -> datetime.datetime:
        """Returns the timestamp for last round transition."""
        if self._last_round_transition_timestamp is None:
            raise ValueError(
                "Trying to access `last_round_transition_timestamp` while no transition has been completed yet."
            )

        return self._last_round_transition_timestamp

    @property
    def last_round_transition_height(
        self,
    ) -> int:
        """Returns the height for last round transition."""
        if self._last_round_transition_height == 0:
            raise ValueError(
                "Trying to access `last_round_transition_height` while no transition has been completed yet."
            )

        return self._last_round_transition_height

    @property
    def last_round_transition_root_hash(
        self,
    ) -> bytes:
        """Returns the root hash for last round transition."""
        if self._last_round_transition_root_hash == b"":
            # if called for the first chain initialization, return the hash resulting from the initial abci app's state
            return self.root_hash
        return self._last_round_transition_root_hash

    @property
    def last_round_transition_tm_height(self) -> int:
        """Returns the Tendermint height for last round transition."""
        if self._last_round_transition_tm_height is None:
            raise ValueError(
                "Trying to access Tendermint's last round transition height before any `end_block` calls."
            )
        return self._last_round_transition_tm_height

    @property
    def latest_synchronized_data(self) -> BaseSynchronizedData:
        """Get the latest synchronized_data."""
        return self.abci_app.synchronized_data

    @property
    def root_hash(self) -> bytes:
        """
        Get the Merkle root hash of the application state.

        Create an app hash that always increases in order to avoid conflicts between resets.
        Eventually, we do not necessarily need to have a value that increases, but we have to generate a hash that
        is always different among the resets, since our abci's state is different even thought we have reset the chain!
        For example, if we are in height 11, reset and then reach height 11 again, if we end up using the same hash
        at height 11 between the resets, then this is problematic.

        :return: the root hash to be included as the Header.AppHash in the next block.
        """
        return f"root:{self.abci_app.synchronized_data.db.round_count}reset:{self.abci_app.reset_index}".encode(
            "utf-8"
        )

    @property
    def tm_height(self) -> int:
        """Get Tendermint's current height."""
        if self._tm_height is None:
            raise ValueError(
                "Trying to access Tendermint's current height before any `end_block` calls."
            )
        return self._tm_height

    @tm_height.setter
    def tm_height(self, _tm_height: int) -> None:
        """Set Tendermint's current height."""
        self._tm_height = _tm_height

    @property
    def block_stall_deadline_expired(self) -> bool:
        """Get if the deadline for not having received any begin block requests from the Tendermint node has expired."""
        if self._block_stall_deadline is None:
            return False
        return datetime.datetime.now() > self._block_stall_deadline

    def init_chain(self, initial_height: int) -> None:
        """Init chain."""
        # reduce `initial_height` by 1 to get block count offset as per Tendermint protocol
        self._blockchain = Blockchain(initial_height - 1)

    def begin_block(self, header: Header) -> None:
        """Begin block."""
        if self.is_finished:
            raise ABCIAppInternalError(
                "round sequence is finished, cannot accept new blocks"
            )
        if (
            self._block_construction_phase
            != RoundSequence._BlockConstructionState.WAITING_FOR_BEGIN_BLOCK
        ):
            raise ABCIAppInternalError(
                f"cannot accept a 'begin_block' request. Current phase={self._block_construction_phase}"
            )

        # From now on, the ABCI app waits for 'deliver_tx' requests, until 'end_block' is received
        self._block_construction_phase = (
            RoundSequence._BlockConstructionState.WAITING_FOR_DELIVER_TX
        )
        self._block_builder.reset()
        self._block_builder.header = header
        self.abci_app.update_time(header.timestamp)
        # we use the local time of the agent to specify the expiration of the deadline
        self._block_stall_deadline = datetime.datetime.now() + datetime.timedelta(
            seconds=BLOCKS_STALL_TOLERANCE
        )
        _logger.info(
            "Created a new local deadline for the next `begin_block` request from the Tendermint node: "
            f"{self._block_stall_deadline}"
        )

    def deliver_tx(self, transaction: Transaction) -> None:
        """
        Deliver a transaction.

        Appends the transaction to build the block on 'end_block' later.
        :param transaction: the transaction.
        :raises:  an Error otherwise.
        """
        if (
            self._block_construction_phase
            != RoundSequence._BlockConstructionState.WAITING_FOR_DELIVER_TX
        ):
            raise ABCIAppInternalError(
                f"cannot accept a 'deliver_tx' request. Current phase={self._block_construction_phase}"
            )

        self.abci_app.check_transaction(transaction)
        self.abci_app.process_transaction(transaction)
        self._block_builder.add_transaction(transaction)

    def end_block(self) -> None:
        """Process the 'end_block' request."""
        if (
            self._block_construction_phase
            != RoundSequence._BlockConstructionState.WAITING_FOR_DELIVER_TX
        ):
            raise ABCIAppInternalError(
                f"cannot accept a 'end_block' request. Current phase={self._block_construction_phase}"
            )
        # The ABCI app waits for the commit
        self._block_construction_phase = (
            RoundSequence._BlockConstructionState.WAITING_FOR_COMMIT
        )

    def commit(self) -> None:
        """Process the 'commit' request."""
        if (
            self._block_construction_phase
            != RoundSequence._BlockConstructionState.WAITING_FOR_COMMIT
        ):
            raise ABCIAppInternalError(
                f"cannot accept a 'commit' request. Current phase={self._block_construction_phase}"
            )
        block = self._block_builder.get_block()
        try:
            if self._blockchain.is_init:
                # There are occasions where we wait for an init_chain() before accepting blocks.
                # This can happen during hard reset, where we might've reset the local blockchain,
                # But are still receiving requests from the not yet reset tendermint node.
                # We only process blocks on an initialized local blockchain.
                # The local blockchain gets initialized upon receiving an init_chain request from
                # the tendermint node. In cases where we don't want to wait for the init_chain req,
                # one can create a Blockchain instance with `is_init=True`, i.e. the default args.
                self._blockchain.add_block(block)
                self._update_round()
            else:
                logging.warning(
                    f"Received block with height {block.header.height} before the blockchain was initialized."
                )
            # The ABCI app now waits again for the next block
            self._block_construction_phase = (
                RoundSequence._BlockConstructionState.WAITING_FOR_BEGIN_BLOCK
            )
        except AddBlockError as exception:
            raise exception

    def reset_blockchain(self, is_replay: bool = False, is_init: bool = False) -> None:
        """
        Reset blockchain after tendermint reset.

        :param is_replay: whether we are resetting the blockchain while replaying blocks.
        :param is_init: whether to process blocks before receiving an init_chain req from tendermint.
        """
        if is_replay:
            self._block_construction_phase = (
                RoundSequence._BlockConstructionState.WAITING_FOR_BEGIN_BLOCK
            )
        self._blockchain = Blockchain(is_init=is_init)

    def _update_round(self) -> None:
        """
        Update a round.

        Check whether the round has finished. If so, get the
        new round and set it as the current round.
        """
        background_result: Optional[Tuple[BaseSynchronizedData, Any]] = None
        if self.abci_app.is_termination_set:
            background_result = self.abci_app.background_round.end_block()
        if background_result is not None and not self._termination_called:
            # when the background round returns, it takes priority over normal rounds
            # because the BackgroundRound never ends, we should only take into account
            # its response only once
            self._termination_called = True
            result: Optional[Tuple[BaseSynchronizedData, Any]] = background_result
        else:
            result = self.abci_app.current_round.end_block()

        if result is None:
            # the termination round, nor the current round returned, so no update needs to be made
            return

        self._last_round_transition_timestamp = self._blockchain.last_block.timestamp
        self._last_round_transition_height = self.height
        self._last_round_transition_root_hash = self.root_hash
        self._last_round_transition_tm_height = self.tm_height
        round_result, event = result
        _logger.debug(
            f"updating round, current_round {self.current_round.round_id}, event: {event}, round result {round_result}"
        )
        self.abci_app.process_event(event, result=round_result)

    def _reset_to_default_params(self) -> None:
        """Resets the instance params to their default value."""
        self._last_round_transition_timestamp = None
        self._last_round_transition_height = 0
        self._last_round_transition_root_hash = b""
        self._last_round_transition_tm_height = None
        self._tm_height = None

    def reset_state(
        self,
        restart_from_round: str,
        round_count: int,
        reset_index: int,
    ) -> None:
        """
        This method resets the state of RoundSequence to the begging of the period.

        Note: This is intended to be used only for agent <-> tendermint communication recovery only!

        :param restart_from_round: from which round to restart the abci. This round should be the first round in the last period.
        :param round_count: the round count at the beginning of the period -1.
        :param reset_index: the reset index (a.k.a. period count) -1.
        """
        self._reset_to_default_params()
        self.abci_app.synchronized_data.db.round_count = round_count
        self.abci_app.reset_index = reset_index
        round_id_to_cls = {
            cls.auto_round_id(): cls for cls in self.abci_app.transition_function
        }
        restart_from_round_cls = round_id_to_cls.get(restart_from_round, None)
        if restart_from_round_cls is None:
            raise ABCIAppInternalError(
                "Cannot reset state. The Tendermint recovery parameters are incorrect. "
                "Did you update the `restart_from_round` with an incorrect round id? "
                f"Found {restart_from_round}, but the app's transition function has the following round ids: "
                f"{set(round_id_to_cls.keys())}."
            )
        self.abci_app.schedule_round(restart_from_round_cls)
