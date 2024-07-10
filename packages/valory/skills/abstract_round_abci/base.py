# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2024 Valory AG
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
import hashlib
import heapq
import itertools
import json
import logging
import re
import sys
import textwrap
import uuid
from abc import ABC, ABCMeta, abstractmethod
from collections import Counter, deque
from copy import copy, deepcopy
from dataclasses import asdict, astuple, dataclass, field, is_dataclass
from enum import Enum
from inspect import isclass
from math import ceil
from typing import (
    Any,
    Callable,
    Deque,
    Dict,
    FrozenSet,
    Generic,
    Iterator,
    List,
    Mapping,
    Optional,
    Sequence,
    Set,
    Tuple,
    Type,
    TypeVar,
    Union,
    cast,
)

from aea.crypto.ledger_apis import LedgerApis
from aea.exceptions import enforce
from aea.skills.base import SkillContext

from packages.valory.connections.abci.connection import MAX_READ_IN_BYTES
from packages.valory.connections.ledger.connection import (
    PUBLIC_ID as LEDGER_CONNECTION_PUBLIC_ID,
)
from packages.valory.protocols.abci.custom_types import (
    EvidenceType,
    Evidences,
    Header,
    LastCommitInfo,
    Validator,
)
from packages.valory.skills.abstract_round_abci.utils import (
    consensus_threshold,
    is_json_serializable,
)


_logger = logging.getLogger("aea.packages.valory.skills.abstract_round_abci.base")

OK_CODE = 0
ERROR_CODE = 1
LEDGER_API_ADDRESS = str(LEDGER_CONNECTION_PUBLIC_ID)
ROUND_COUNT_DEFAULT = -1
MIN_HISTORY_DEPTH = 1
ADDRESS_LENGTH = 42
MAX_INT_256 = 2**256 - 1
RESET_COUNT_START = 0
VALUE_NOT_PROVIDED = object()
# tolerance in seconds for new blocks not having arrived yet
BLOCKS_STALL_TOLERANCE = 60
SERIOUS_OFFENCE_ENUM_MIN = 1000
NUMBER_OF_BLOCKS_TRACKED = 10_000
NUMBER_OF_ROUNDS_TRACKED = 50

EventType = TypeVar("EventType")


def get_name(prop: Any) -> str:
    """Get the name of a property."""
    if not (isinstance(prop, property) and hasattr(prop, "fget")):
        raise ValueError(f"{prop} is not a property")
    if prop.fget is None:
        raise ValueError(f"fget of {prop} is None")  # pragma: nocover
    return prop.fget.__name__


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
        excluded = ["sender", "round_count", "id_"]
        return {k: v for k, v in asdict(self).items() if k not in excluded}

    @property
    def values(self) -> Tuple[Any, ...]:
        """Data"""
        excluded = 3  # refers to ["sender", "round_count", "id_"]
        return astuple(self)[excluded:]

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

    DB_DATA_KEY = "db_data"
    SLASHING_CONFIG_KEY = "slashing_config"

    # database keys which values are always set for the next period by default
    default_cross_period_keys: FrozenSet[str] = frozenset(
        {
            "all_participants",
            "participants",
            "consensus_threshold",
            "safe_contract_address",
        }
    )

    def __init__(
        self,
        setup_data: Dict[str, List[Any]],
        cross_period_persisted_keys: Optional[FrozenSet[str]] = None,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        """Initialize the AbciApp database.

        setup_data must be passed as a Dict[str, List[Any]] (the database internal format).
        The staticmethod 'data_to_lists' can be used to convert from Dict[str, Any] to Dict[str, List[Any]]
        before instantiating this class.

        :param setup_data: the setup data
        :param cross_period_persisted_keys: data keys that will be kept after a new period starts
        :param logger: the logger of the abci app
        """
        self.logger = logger or _logger
        AbciAppDB._check_data(setup_data)
        self._setup_data = deepcopy(setup_data)
        self._data: Dict[int, Dict[str, List[Any]]] = {
            RESET_COUNT_START: self.setup_data  # the key represents the reset index
        }
        self._round_count = ROUND_COUNT_DEFAULT  # ensures first round is indexed at 0!

        self._cross_period_persisted_keys = self.default_cross_period_keys.union(
            cross_period_persisted_keys or frozenset()
        )
        self._cross_period_check()
        self.slashing_config: str = ""

    def _cross_period_check(self) -> None:
        """Check the cross period keys against the setup data."""
        not_in_cross_period = set(self._setup_data).difference(
            self.cross_period_persisted_keys
        )
        if not_in_cross_period:
            self.logger.warning(
                f"The setup data ({self._setup_data.keys()}) contain keys that are not in the "
                f"cross period persisted keys ({self.cross_period_persisted_keys}): {not_in_cross_period}"
            )

    @staticmethod
    def normalize(value: Any) -> str:
        """Attempt to normalize a non-primitive type to insert it into the db."""
        if is_json_serializable(value):
            return value

        if isinstance(value, Enum):
            return value.value

        if isinstance(value, bytes):
            return value.hex()

        if isinstance(value, set):
            try:
                return json.dumps(list(value))
            except TypeError:
                pass

        raise ValueError(f"Cannot normalize {value} to insert it in the db!")

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
        """Check that all fields in setup data were passed as a list, and that the data can be accepted into the db."""
        if (
            not isinstance(data, dict)
            or not all((isinstance(k, str) for k in data.keys()))
            or not all((isinstance(v, list) for v in data.values()))
        ):
            raise ValueError(
                f"AbciAppDB data must be `Dict[str, List[Any]]`, found `{type(data)}` instead."
            )

        AbciAppDB.validate(data)

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
    def cross_period_persisted_keys(self) -> FrozenSet[str]:
        """Keys in the database which are persistent across periods."""
        return self._cross_period_persisted_keys

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

    @staticmethod
    def validate(data: Any) -> None:
        """Validate if the given data are json serializable and therefore can be accepted into the database.

        :param data: the data to check.
        :raises ABCIAppInternalError: If the data are not serializable.
        """
        if not is_json_serializable(data):
            raise ABCIAppInternalError(
                f"`AbciAppDB` data must be json-serializable. Please convert non-serializable data in `{data}`. "
                "You may use `AbciAppDB.validate(your_data)` to validate your data for the `AbciAppDB`."
            )

    def update(self, **kwargs: Any) -> None:
        """Update the current data."""
        self.validate(kwargs)

        # Append new data to the key history
        data = self._data[self.reset_index]
        for key, value in deepcopy(kwargs).items():
            data.setdefault(key, []).append(value)

    def create(self, **kwargs: Any) -> None:
        """Add a new entry to the data.

        Passes automatically the values of the `cross_period_persisted_keys` to the next period.

        :param kwargs: keyword arguments
        """
        for key in self.cross_period_persisted_keys.union(kwargs.keys()):
            value = kwargs.get(key, VALUE_NOT_PROVIDED)
            if value is VALUE_NOT_PROVIDED:
                value = self.get_latest().get(key, VALUE_NOT_PROVIDED)
            if value is VALUE_NOT_PROVIDED:
                raise ABCIAppInternalError(
                    f"Cross period persisted key `{key}` was not found in the db but was required for the next period."
                )
            if isinstance(value, (set, frozenset)):
                value = tuple(sorted(value))
            kwargs[key] = value

        data = self.data_to_lists(kwargs)
        self._create_from_keys(**data)

    def _create_from_keys(self, **kwargs: Any) -> None:
        """Add a new entry to the data using the provided key-value pairs."""
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

    def serialize(self) -> str:
        """Serialize the data of the database to a string."""
        db = {
            self.DB_DATA_KEY: self._data,
            self.SLASHING_CONFIG_KEY: self.slashing_config,
        }
        return json.dumps(db, sort_keys=True)

    @staticmethod
    def _as_abci_data(data: Dict) -> Dict[int, Any]:
        """Hook to load serialized data as `AbciAppDB` data."""
        return {int(index): content for index, content in data.items()}

    def sync(self, serialized_data: str) -> None:
        """Synchronize the data using a serialized object.

        :param serialized_data: the serialized data to use in order to sync the db.
        :raises ABCIAppInternalError: if the given data cannot be deserialized.
        """
        try:
            loaded_data = json.loads(serialized_data)
        except json.JSONDecodeError as exc:
            raise ABCIAppInternalError(
                f"Could not decode data using {serialized_data}: {exc}"
            ) from exc

        input_report = f"\nThe following serialized data were given: {serialized_data}"
        try:
            db_data = loaded_data[self.DB_DATA_KEY]
            slashing_config = loaded_data[self.SLASHING_CONFIG_KEY]
        except KeyError as exc:
            raise ABCIAppInternalError(
                "Mandatory keys `db_data`, `slashing_config` are missing from the deserialized data: "
                f"{loaded_data}{input_report}"
            ) from exc

        try:
            db_data = self._as_abci_data(db_data)
        except AttributeError as exc:
            raise ABCIAppInternalError(
                f"Could not decode db data with an invalid format: {db_data}{input_report}"
            ) from exc
        except ValueError as exc:
            raise ABCIAppInternalError(
                f"An invalid index was found while trying to sync the db using data: {db_data}{input_report}"
            ) from exc

        self._check_data(dict(tuple(db_data.values())[0]))
        self._data = db_data
        self.slashing_config = slashing_config

    def hash(self) -> bytes:
        """Create a hash of the data."""
        # Compute the sha256 hash of the serialized data
        sha256 = hashlib.sha256()
        data = self.serialize()
        sha256.update(data.encode("utf-8"))
        hash_ = sha256.digest()
        self.logger.debug(f"root hash: {hash_.hex()}; data: {data}")
        return hash_

    @staticmethod
    def data_to_lists(data: Dict[str, Any]) -> Dict[str, List[Any]]:
        """Convert Dict[str, Any] to Dict[str, List[Any]]."""
        return {k: [v] for k, v in data.items()}


SerializedCollection = Dict[str, Dict[str, Any]]
DeserializedCollection = Mapping[str, BaseTxPayload]


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
    default_db_keys: Set[str] = {
        "round_count",
        "period_count",
        "all_participants",
        "nb_participants",
        "max_participants",
        "consensus_threshold",
        "safe_contract_address",
    }

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
        participants = frozenset(self.db.get_strict("participants"))
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
    def max_participants(self) -> int:
        """Get the number of all the participants."""
        return len(self.all_participants)

    @property
    def consensus_threshold(self) -> int:
        """Get the consensus threshold."""
        threshold = self.db.get_strict("consensus_threshold")
        min_threshold = consensus_threshold(self.max_participants)

        if threshold is None:
            return min_threshold

        threshold = int(threshold)
        max_threshold = len(self.all_participants)

        if min_threshold <= threshold <= max_threshold:
            return threshold

        expected_range = (
            f"can only be {min_threshold}"
            if min_threshold == max_threshold
            else f"not in [{min_threshold}, {max_threshold}]"
        )
        raise ValueError(f"Consensus threshold {threshold} {expected_range}.")

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

    @property
    def slashing_config(self) -> str:
        """Get the slashing configuration."""
        return self.db.slashing_config

    @slashing_config.setter
    def slashing_config(self, config: str) -> None:
        """Set the slashing configuration."""
        self.db.slashing_config = config

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
    ) -> "BaseSynchronizedData":
        """Copy and update with new data. Set values are stored as sorted tuples to the db for determinism."""
        self.db.create()
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
    def participant_to_selection(self) -> DeserializedCollection:
        """Check whether keeper is set."""
        serialized = self.db.get_strict("participant_to_selection")
        deserialized = CollectionRound.deserialize_collection(serialized)
        return cast(DeserializedCollection, deserialized)

    @property
    def participant_to_randomness(self) -> DeserializedCollection:
        """Check whether keeper is set."""
        serialized = self.db.get_strict("participant_to_randomness")
        deserialized = CollectionRound.deserialize_collection(serialized)
        return cast(DeserializedCollection, deserialized)

    @property
    def participant_to_votes(self) -> DeserializedCollection:
        """Check whether keeper is set."""
        serialized = self.db.get_strict("participant_to_votes")
        deserialized = CollectionRound.deserialize_collection(serialized)
        return cast(DeserializedCollection, deserialized)

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


class AbstractRound(Generic[EventType], ABC, metaclass=_MetaAbstractRound):
    """
    This class represents an abstract round.

    A round is a state of the FSM App execution. It usually involves
    interactions between participants in the FSM App,
    although this is not enforced at this level of abstraction.

    Concrete classes must set:
    - synchronized_data_class: the data class associated with this round;
    - payload_class: the payload type that is allowed for this round;

    Optionally, round_id can be defined, although it is recommended to use the autogenerated id.
    """

    __pattern = re.compile(r"(?<!^)(?=[A-Z])")
    _previous_round_payload_class: Optional[Type[BaseTxPayload]]

    payload_class: Optional[Type[BaseTxPayload]]
    synchronized_data_class: Type[BaseSynchronizedData]

    round_id: str

    def __init__(
        self,
        synchronized_data: BaseSynchronizedData,
        context: SkillContext,
        previous_round_payload_class: Optional[Type[BaseTxPayload]] = None,
    ) -> None:
        """Initialize the round."""
        self._synchronized_data = synchronized_data
        self.block_confirmations = 0
        self._previous_round_payload_class = previous_round_payload_class
        self.context = context

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

    def check_majority_possible_with_new_voter(
        self,
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

        self.check_majority_possible(
            votes_by_participant, nb_participants, exception_cls=exception_cls
        )

    def check_majority_possible(
        self,
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

        if (
            nb_remaining_votes + largest_nb_votes
            < self.synchronized_data.consensus_threshold
        ):
            raise exception_cls(
                f"cannot reach quorum={self.synchronized_data.consensus_threshold}, "
                f"number of remaining votes={nb_remaining_votes}, number of most voted item's votes={largest_nb_votes}"
            )

    def is_majority_possible(
        self, votes_by_participant: Dict[str, BaseTxPayload], nb_participants: int
    ) -> bool:
        """
        Return true if a Byzantine majority is achievable, false otherwise.

        :param votes_by_participant: a mapping from a participant to its vote
        :param nb_participants: the total number of participants
        :return: True if the majority is still possible, false otherwise.
        """
        try:
            self.check_majority_possible(votes_by_participant, nb_participants)
        except ABCIAppException:
            return False
        return True

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

    `_allow_rejoin_payloads` is used to allow agents not currently active to
    deliver a payload.
    """

    _allow_rejoin_payloads: bool = False

    def __init__(self, *args: Any, **kwargs: Any):
        """Initialize the collection round."""
        super().__init__(*args, **kwargs)
        self.collection: Dict[str, BaseTxPayload] = {}

    @staticmethod
    def serialize_collection(
        collection: DeserializedCollection,
    ) -> SerializedCollection:
        """Deserialize a serialized collection."""
        return {address: payload.json for address, payload in collection.items()}

    @staticmethod
    def deserialize_collection(
        serialized: SerializedCollection,
    ) -> DeserializedCollection:
        """Deserialize a serialized collection."""
        return {
            address: BaseTxPayload.from_json(payload_json)
            for address, payload_json in serialized.items()
        }

    @property
    def serialized_collection(self) -> SerializedCollection:
        """A collection with the addresses mapped to serialized payloads."""
        return self.serialize_collection(self.collection)

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
    def payload_values_count(self) -> Counter:
        """Get count of payload values."""
        return Counter(map(lambda p: p.values, self.payloads))

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


class _CollectUntilAllRound(CollectionRound, ABC):
    """
    _CollectUntilAllRound

    This class represents abstract logic for when rounds need to collect payloads from all agents.

    This round should only be used when non-BFT behaviour is acceptable.
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
        return len(self.collection) >= self.synchronized_data.max_participants


class CollectDifferentUntilAllRound(_CollectUntilAllRound, ABC):
    """
    CollectDifferentUntilAllRound

    This class represents logic for rounds where a round needs to collect
    different payloads from each agent.

    This round should only be used for registration of new agents when there is synchronization of the db.
    """

    def check_payload(self, payload: BaseTxPayload) -> None:
        """Check Payload"""
        new = payload.values
        existing = [payload_.values for payload_ in self.collection.values()]

        if payload.sender not in self.collection and new in existing:
            raise TransactionNotValidError(
                f"`CollectDifferentUntilAllRound` encountered a value '{new}' that already exists. "
                f"All values: {existing}"
            )

        super().check_payload(payload)


class CollectSameUntilAllRound(_CollectUntilAllRound, ABC):
    """
    This class represents logic for when a round needs to collect the same payload from all the agents.

    This round should only be used for registration of new agents when there is no synchronization of the db.
    """

    def check_payload(self, payload: BaseTxPayload) -> None:
        """Check Payload"""
        new = payload.values
        existing_ = [payload_.values for payload_ in self.collection.values()]

        if (
            payload.sender not in self.collection
            and len(self.collection)
            and new not in existing_
        ):
            raise TransactionNotValidError(
                f"`CollectSameUntilAllRound` encountered a value '{new}' "
                f"which is not the same as the already existing one: '{existing_[0]}'"
            )

        super().check_payload(payload)

    @property
    def common_payload(
        self,
    ) -> Any:
        """Get the common payload among the agents."""
        return self.common_payload_values[0]

    @property
    def common_payload_values(
        self,
    ) -> Tuple[Any, ...]:
        """Get the common payload among the agents."""
        most_common_payload_values, max_votes = self.payload_values_count.most_common(
            1
        )[0]
        if max_votes < self.synchronized_data.max_participants:
            raise ABCIAppInternalError(
                f"{max_votes} votes are not enough for `CollectSameUntilAllRound`. Expected: "
                f"`n_votes = max_participants = {self.synchronized_data.max_participants}`"
            )
        return most_common_payload_values


class CollectSameUntilThresholdRound(CollectionRound, ABC):
    """
    CollectSameUntilThresholdRound

    This class represents logic for rounds where a round needs to collect
    same payload from k of n agents.

    `done_event` is emitted when a) the collection threshold (k of n) is reached,
    and b) the most voted payload has non-empty attributes. In this case all
    payloads are saved under `collection_key` and the most voted payload attributes
    are saved under `selection_key`.

    `none_event` is emitted when a) the collection threshold (k of n) is reached,
    and b) the most voted payload has only empty attributes.

    `no_majority_event` is emitted when it is impossible to reach a k of n majority.
    """

    done_event: Any
    no_majority_event: Any
    none_event: Any
    collection_key: str
    selection_key: Union[str, Tuple[str, ...]]

    @property
    def threshold_reached(
        self,
    ) -> bool:
        """Check if the threshold has been reached."""
        counts = self.payload_values_count.values()
        return any(
            count >= self.synchronized_data.consensus_threshold for count in counts
        )

    @property
    def most_voted_payload(
        self,
    ) -> Any:
        """
        Get the most voted payload value.

        Kept for backward compatibility.
        """
        return self.most_voted_payload_values[0]

    @property
    def most_voted_payload_values(
        self,
    ) -> Tuple[Any, ...]:
        """Get the most voted payload values."""
        most_voted_payload_values, max_votes = self.payload_values_count.most_common()[
            0
        ]
        if max_votes < self.synchronized_data.consensus_threshold:
            raise ABCIAppInternalError("not enough votes")
        return most_voted_payload_values

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Enum]]:
        """Process the end of the block."""
        if self.threshold_reached and any(
            [val is not None for val in self.most_voted_payload_values]
        ):
            if isinstance(self.selection_key, tuple):
                data = dict(zip(self.selection_key, self.most_voted_payload_values))
                data[self.collection_key] = self.serialized_collection
            else:
                data = {
                    self.collection_key: self.serialized_collection,
                    self.selection_key: self.most_voted_payload,
                }
            synchronized_data = self.synchronized_data.update(
                synchronized_data_class=self.synchronized_data_class,
                **data,
            )
            return synchronized_data, self.done_event
        if self.threshold_reached and not any(
            [val is not None for val in self.most_voted_payload_values]
        ):
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
    payload.

    `done_event` is emitted when a) the keeper payload has been received and b)
    the keeper payload has non-empty attributes. In this case all attributes are saved
    under `payload_key`.

    `fail_event` is emitted when a) the keeper payload has been received and b)
    the keeper payload has only empty attributes
    """

    keeper_payload: Optional[BaseTxPayload] = None
    done_event: Any
    fail_event: Any
    payload_key: Union[str, Tuple[str, ...]]

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

        if self.keeper_payload is not None:
            raise ABCIAppInternalError("keeper already set the payload.")

        self.keeper_payload = payload

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

        if self.keeper_payload is not None:
            raise TransactionNotValidError("keeper payload value already set.")

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Enum]]:
        """Process the end of the block."""
        if self.keeper_payload is not None and any(
            [val is not None for val in self.keeper_payload.values]
        ):
            if isinstance(self.payload_key, tuple):
                data = dict(zip(self.payload_key, self.keeper_payload.values))
            else:
                data = {
                    self.payload_key: self.keeper_payload.values[0],
                }
            synchronized_data = self.synchronized_data.update(
                synchronized_data_class=self.synchronized_data_class,
                **data,
            )
            return synchronized_data, self.done_event
        if self.keeper_payload is not None and not any(
            [val is not None for val in self.keeper_payload.values]
        ):
            return self.synchronized_data, self.fail_event
        return None


class VotingRound(CollectionRound, ABC):
    """
    VotingRound

    This class represents logic for rounds where a round needs votes from
    agents. Votes are in the form of `True` (positive), `False` (negative)
    and `None` (abstain). The round ends when k of n agents make the same vote.

    `done_event` is emitted when a) the collection threshold (k of n) is reached
    with k positive votes. In this case all payloads are saved under `collection_key`.

    `negative_event` is emitted when a) the collection threshold (k of n) is reached
    with k negative votes.

    `none_event` is emitted when a) the collection threshold (k of n) is reached
    with k abstain votes.

    `no_majority_event` is emitted when it is impossible to reach a k of n majority for
    either of the options.
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
        return self.vote_count[True] >= self.synchronized_data.consensus_threshold

    @property
    def negative_vote_threshold_reached(self) -> bool:
        """Check that the vote threshold has been reached."""
        return self.vote_count[False] >= self.synchronized_data.consensus_threshold

    @property
    def none_vote_threshold_reached(self) -> bool:
        """Check that the vote threshold has been reached."""
        return self.vote_count[None] >= self.synchronized_data.consensus_threshold

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Enum]]:
        """Process the end of the block."""
        if self.positive_vote_threshold_reached:
            synchronized_data = self.synchronized_data.update(
                synchronized_data_class=self.synchronized_data_class,
                **{self.collection_key: self.serialized_collection},
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
    different payloads from k of n agents.

    `done_event` is emitted when a) the required block confirmations
    have been met, and b) the collection threshold (k of n) is reached. In
    this case all payloads are saved under `collection_key`.

    Extended `required_block_confirmations` to allow for arrival of more
    payloads.
    """

    done_event: Any
    collection_key: str
    required_block_confirmations: int = 0

    @property
    def collection_threshold_reached(
        self,
    ) -> bool:
        """Check if the threshold has been reached."""
        return len(self.collection) >= self.synchronized_data.consensus_threshold

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Enum]]:
        """Process the end of the block."""
        if self.collection_threshold_reached:
            self.block_confirmations += 1
        if (
            self.collection_threshold_reached
            and self.block_confirmations > self.required_block_confirmations
        ):
            synchronized_data = self.synchronized_data.update(
                synchronized_data_class=self.synchronized_data_class,
                **{
                    self.collection_key: self.serialized_collection,
                },
            )
            return synchronized_data, self.done_event

        return None


class CollectNonEmptyUntilThresholdRound(CollectDifferentUntilThresholdRound, ABC):
    """
    CollectNonEmptyUntilThresholdRound

    This class represents logic for rounds where a round needs to collect
    optionally different payloads from k of n agents, where we only keep the non-empty attributes.

    `done_event` is emitted when a) the required block confirmations
    have been met, b) the collection threshold (k of n) is reached, and
    c) some non-empty attribute values have been collected. In this case
    all payloads are saved under `collection_key`. Under `selection_key`
    the non-empty attribute values are stored.

    `none_event` is emitted when a) the required block confirmations
    have been met, b) the collection threshold (k of n) is reached, and
    c) no non-empty attribute values have been collected.

    Attention: A `none_event` might be triggered even though some of the
    remaining n-k agents might send non-empty attributes! Extended
    `required_block_confirmations` can alleviate this somewhat.
    """

    none_event: Any
    selection_key: Union[str, Tuple[str, ...]]

    def _get_non_empty_values(self) -> Dict[str, Tuple[Any, ...]]:
        """Get the non-empty values from the payload, for all attributes."""
        non_empty_values: Dict[str, List[List[Any]]] = {}

        for sender, payload in self.collection.items():
            if sender not in non_empty_values:
                non_empty_values[sender] = [
                    value for value in payload.values if value is not None
                ]
                if len(non_empty_values[sender]) == 0:
                    del non_empty_values[sender]
                continue
        non_empty_values_ = {
            sender: tuple(li) for sender, li in non_empty_values.items()
        }
        return non_empty_values_

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Enum]]:
        """Process the end of the block."""
        if self.collection_threshold_reached:
            self.block_confirmations += 1
        if (
            self.collection_threshold_reached
            and self.block_confirmations > self.required_block_confirmations
        ):
            non_empty_values = self._get_non_empty_values()

            if isinstance(self.selection_key, tuple):
                data: Dict[str, Any] = {
                    sender: dict(zip(self.selection_key, values))
                    for sender, values in non_empty_values.items()
                }
            else:
                data = {
                    self.selection_key: {
                        sender: values[0] for sender, values in non_empty_values.items()
                    },
                }
            data[self.collection_key] = self.serialized_collection

            synchronized_data = self.synchronized_data.update(
                synchronized_data_class=self.synchronized_data_class,
                **data,
            )

            if all([len(tu) == 0 for tu in non_empty_values]):
                return self.synchronized_data, self.none_event
            return synchronized_data, self.done_event
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

    bg_round_added: bool = False

    def __new__(mcs, name: str, bases: Tuple, namespace: Dict, **kwargs: Any) -> Type:  # type: ignore
        """Initialize the class."""
        new_cls = super().__new__(mcs, name, bases, namespace, **kwargs)

        if ABC in bases:
            # abstract class, return
            return new_cls
        if not issubclass(new_cls, AbciApp):
            # the check only applies to AbciApp subclasses
            return new_cls

        if not mcs.bg_round_added:
            mcs._add_pending_offences_bg_round(new_cls)
            mcs.bg_round_added = True

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
        intersection = abci_app_cls.default_db_preconditions.intersection(
            all_pre_conditions
        )
        enforce(
            len(intersection) == 0,
            f"db pre conditions contain value that is a default pre condition: {intersection}",
        )
        intersection = abci_app_cls.default_db_preconditions.intersection(
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

    @classmethod
    def _add_pending_offences_bg_round(cls, abci_app_cls: Type["AbciApp"]) -> None:
        """Add the pending offences synchronization background round."""
        config: BackgroundAppConfig = BackgroundAppConfig(PendingOffencesRound)
        abci_app_cls.add_background_app(config)


class BackgroundAppType(Enum):
    """
    The type of a background app.

    Please note that the values correspond to the priority in which the background apps should be processed
    when updating rounds.
    """

    TERMINATING = 0
    EVER_RUNNING = 1
    NORMAL = 2
    INCORRECT = 3

    @staticmethod
    def correct_types() -> Set[str]:
        """Return the correct types only."""
        return set(BackgroundAppType.__members__) - {BackgroundAppType.INCORRECT.name}


@dataclass(frozen=True)
class BackgroundAppConfig(Generic[EventType]):
    """
    Necessary configuration for a background app.

    For a deeper understanding of the various types of background apps and how the config influences
    the generated background app's type, please refer to the `BackgroundApp` class.
    The `specify_type` method provides further insight on the subject matter.
    """

    # the class of the background round
    round_cls: AppState
    # the abci app of the background round
    # the abci app must specify a valid transition function if the round is not of an ever-running type
    abci_app: Optional[Type["AbciApp"]] = None
    # the start event of the background round
    # if no event or transition function is specified, then the round is running in the background forever
    start_event: Optional[EventType] = None
    # the end event of the background round
    # if not specified, then the round is terminating the abci app
    end_event: Optional[EventType] = None


class BackgroundApp(Generic[EventType]):
    """A background app."""

    def __init__(
        self,
        config: BackgroundAppConfig,
    ) -> None:
        """Initialize the BackgroundApp."""
        given_args = locals()

        self.config = config
        self.round_cls: AppState = config.round_cls
        self.transition_function: Optional[AbciAppTransitionFunction] = (
            config.abci_app.transition_function if config.abci_app is not None else None
        )
        self.start_event: Optional[EventType] = config.start_event
        self.end_event: Optional[EventType] = config.end_event

        self.type = self.specify_type()
        if self.type == BackgroundAppType.INCORRECT:  # pragma: nocover
            raise ValueError(
                f"Background app has not been initialized correctly with {given_args}. "
                f"Cannot match with any of the possible background apps' types: {BackgroundAppType.correct_types()}"
            )
        _logger.debug(
            f"Created background app of type '{self.type}' using {given_args}."
        )
        self._background_round: Optional[AbstractRound] = None

    def __eq__(self, other: Any) -> bool:  # pragma: no cover
        """Custom equality comparing operator."""
        if not isinstance(other, BackgroundApp):
            return False

        return self.config == other.config

    def __hash__(self) -> int:
        """Custom hashing operator"""
        return hash(self.config)

    def specify_type(self) -> BackgroundAppType:
        """Specify the type of the background app."""
        if (
            self.start_event is None
            and self.end_event is None
            and self.transition_function is None
        ):
            self.transition_function = {}
            return BackgroundAppType.EVER_RUNNING
        if (
            self.start_event is not None
            and self.end_event is None
            and self.transition_function is not None
        ):
            return BackgroundAppType.TERMINATING
        if (
            self.start_event is not None
            and self.end_event is not None
            and self.transition_function is not None
        ):
            return BackgroundAppType.NORMAL
        return BackgroundAppType.INCORRECT  # pragma: nocover

    def setup(
        self, initial_synchronized_data: BaseSynchronizedData, context: SkillContext
    ) -> None:
        """Set up the background round."""
        round_cls = cast(Type[AbstractRound], self.round_cls)
        self._background_round = round_cls(
            initial_synchronized_data,
            context,
        )

    @property
    def background_round(self) -> AbstractRound:
        """Get the background round."""
        if self._background_round is None:  # pragma: nocover
            raise ValueError(f"Background round with class `{self.round_cls}` not set!")
        return self._background_round

    def process_transaction(self, transaction: Transaction, dry: bool = False) -> bool:
        """Process a transaction."""

        payload_class = type(transaction.payload)
        bg_payload_class = cast(AppState, self.round_cls).payload_class
        if payload_class is bg_payload_class:
            processor = (
                self.background_round.check_transaction
                if dry
                else self.background_round.process_transaction
            )
            processor(transaction)
            return True
        return False


@dataclass
class TransitionBackup:
    """Holds transition related information as a backup in case we want to transition back from a background app."""

    round: Optional[AbstractRound] = None
    round_cls: Optional[AppState] = None
    transition_function: Optional[AbciAppTransitionFunction] = None


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
    cross_period_persisted_keys: FrozenSet[str] = frozenset()
    background_apps: Set[BackgroundApp] = set()
    default_db_preconditions: Set[str] = BaseSynchronizedData.default_db_keys
    db_pre_conditions: Dict[AppState, Set[str]] = {}
    db_post_conditions: Dict[AppState, Set[str]] = {}
    _is_abstract: bool = True

    def __init__(
        self,
        synchronized_data: BaseSynchronizedData,
        logger: logging.Logger,
        context: SkillContext,
    ):
        """Initialize the AbciApp."""

        synchronized_data_class = self.initial_round_cls.synchronized_data_class
        synchronized_data = synchronized_data_class(db=synchronized_data.db)

        self._initial_synchronized_data = synchronized_data
        self.logger = logger
        self.context = context
        self._current_round_cls: Optional[AppState] = None
        self._current_round: Optional[AbstractRound] = None
        self._last_round: Optional[AbstractRound] = None
        self._previous_rounds: List[AbstractRound] = []
        self._current_round_height: int = 0
        self._round_results: List[BaseSynchronizedData] = []
        self._last_timestamp: Optional[datetime.datetime] = None
        self._current_timeout_entries: List[int] = []
        self._timeouts = Timeouts[EventType]()
        self._transition_backup = TransitionBackup()
        self._switched = False

    @classmethod
    def is_abstract(cls) -> bool:
        """Return if the abci app is abstract."""
        return cls._is_abstract

    @classmethod
    def add_background_app(
        cls,
        config: BackgroundAppConfig,
    ) -> Type["AbciApp"]:
        """
        Sets the background related class variables.

        For a deeper understanding of the various types of background apps and how the inputs of this method influence
        the generated background app's type, please refer to the `BackgroundApp` class.
        The `specify_type` method provides further insight on the subject matter.

        :param config: the background app's configuration.
        :return: the `AbciApp` with the new background app contained in the `background_apps` set.
        """
        background_app: BackgroundApp = BackgroundApp(config)
        cls.background_apps.add(background_app)
        cross_period_keys = (
            config.abci_app.cross_period_persisted_keys
            if config.abci_app is not None
            else frozenset()
        )
        cls.cross_period_persisted_keys = cls.cross_period_persisted_keys.union(
            cross_period_keys
        )
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
        cls,
        bg_round_cls: Set[Type[AbstractRound]],
        include_background_rounds: bool = False,
    ) -> Set[AppState]:
        """Get all round classes."""
        full_fn = deepcopy(cls.transition_function)

        if include_background_rounds:
            for app in cls.background_apps:
                if (
                    app.type != BackgroundAppType.EVER_RUNNING
                    and app.round_cls in bg_round_cls
                ):
                    transition_fn = cast(
                        AbciAppTransitionFunction, app.transition_function
                    )
                    full_fn.update(transition_fn)

        return cls._get_rounds_from_transition_function(full_fn)

    @property
    def bg_apps_prioritized(self) -> Tuple[List[BackgroundApp], ...]:
        """Get the background apps grouped and prioritized by their types."""
        n_correct_types = len(BackgroundAppType.correct_types())
        grouped_prioritized: Tuple[List, ...] = ([],) * n_correct_types
        for app in self.background_apps:
            # reminder: the values correspond to the priority of the background apps
            for priority in range(n_correct_types):
                if app.type == BackgroundAppType(priority):
                    grouped_prioritized[priority].append(app)

        return grouped_prioritized

    @property
    def last_timestamp(self) -> datetime.datetime:
        """Get last timestamp."""
        if self._last_timestamp is None:
            raise ABCIAppInternalError("last timestamp is None")
        return self._last_timestamp

    def _setup_background(self) -> None:
        """Set up the background rounds."""
        for app in self.background_apps:
            app.setup(self._initial_synchronized_data, self.context)

    def _get_synced_value(
        self,
        db_key: str,
        sync_classes: Set[Type[BaseSynchronizedData]],
        default: Any = None,
    ) -> Any:
        """Get the value of a specific database key using the synchronized data."""
        for cls in sync_classes:
            # try to find the value using the synchronized data as suggested in #2131
            synced_data = cls(db=self.synchronized_data.db)
            try:
                res = getattr(synced_data, db_key)
            except AttributeError:
                # if the property does not exist in the db try the next synced data class
                continue
            except ValueError:
                # if the property raised because of using `get_strict` and the key not being present in the db
                break

            # if there is a property with the same name as the key in the db, return the result, normalized
            return AbciAppDB.normalize(res)

        # as a last resort, try to get the value from the db
        return self.synchronized_data.db.get(db_key, default)

    def setup(self) -> None:
        """Set up the behaviour."""
        self.schedule_round(self.initial_round_cls)
        self._setup_background()
        # iterate through all the rounds and get all the unique synced data classes
        sync_classes = {
            _round.synchronized_data_class for _round in self.transition_function
        }
        # Add `BaseSynchronizedData` in case it does not exist (TODO: investigate and remove as it might always exist)
        sync_classes.add(BaseSynchronizedData)
        # set the cross-period persisted keys; avoid raising when the first period ends without a key in the db
        update = {
            db_key: self._get_synced_value(db_key, sync_classes)
            for db_key in self.cross_period_persisted_keys
        }
        self.synchronized_data.db.update(**update)

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
                self.logger.debug(
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
            self.context,
            (
                self._last_round.payload_class
                if self._last_round is not None
                and self._last_round.payload_class
                != self._current_round_cls.payload_class
                # when transitioning to a round with the same payload type we set None
                # as otherwise it will allow no tx to be submitted
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

    def cleanup_timeouts(self) -> None:
        """
        Remove all timeouts.

        Note that this is method is meant to be used only when performing recovery.
        Calling it in normal execution will result in unexpected behaviour.
        """
        self._timeouts = Timeouts[EventType]()
        self._current_timeout_entries = []
        self._last_timestamp = None

    def check_transaction(self, transaction: Transaction) -> None:
        """Check a transaction."""

        self.process_transaction(transaction, dry=True)

    def process_transaction(self, transaction: Transaction, dry: bool = False) -> None:
        """
        Process a transaction.

        The background rounds run concurrently with other (normal) rounds.
        First we check if the transaction is meant for a background round,
        if not we forward it to the current round object.

        :param transaction: the transaction.
        :param dry: whether the transaction should only be checked and not processed.
        """

        for app in self.background_apps:
            processed = app.process_transaction(transaction, dry)
            if processed:
                return

        processor = (
            self.current_round.check_transaction
            if dry
            else self.current_round.process_transaction
        )
        processor(transaction)

    def _resolve_bg_transition(
        self, app: BackgroundApp, event: EventType
    ) -> Tuple[bool, Optional[AppState]]:
        """
        Resolve a background app's transition.

        First check whether the event is a special start event.
        If that's the case, proceed with the corresponding background app's transition function,
         regardless of what the current round is.

        :param app: the background app instance.
        :param event: the event for the transition.
        :return: the new app state.
        """

        if (
            app.type in (BackgroundAppType.NORMAL, BackgroundAppType.TERMINATING)
            and event == app.start_event
        ):
            app.transition_function = cast(
                AbciAppTransitionFunction, app.transition_function
            )
            app.round_cls = cast(AppState, app.round_cls)
            next_round_cls = app.transition_function[app.round_cls].get(event, None)
            if next_round_cls is None:  # pragma: nocover
                return True, None

            # we backup the current round so we can return back to normal, in case the end event is received later
            self._transition_backup.round = self._current_round
            self._transition_backup.round_cls = self._current_round_cls
            # we switch the current transition function, with the background app's transition function
            self._transition_backup.transition_function = deepcopy(
                self.transition_function
            )
            self.transition_function = app.transition_function
            self.logger.info(
                f"The {event} event was produced, transitioning to "
                f"`{next_round_cls.auto_round_id()}`."
            )
            return True, next_round_cls

        return False, None

    def _adjust_transition_fn(self, event: EventType) -> None:
        """
        Adjust the transition function if necessary.

        Check whether the event is a special end event.
        If that's the case, reset the transition function back to normal.
        This method is meant to be called after resolving the next round transition, given an event.

        :param event: the emitted event.
        """
        if self._transition_backup.transition_function is None:
            return

        for app in self.background_apps:
            if app.type == BackgroundAppType.NORMAL and event == app.end_event:
                self._current_round = self._transition_backup.round
                self._transition_backup.round = None
                self._current_round_cls = self._transition_backup.round_cls
                self._transition_backup.round_cls = None
                backup_fn = cast(
                    AbciAppTransitionFunction,
                    self._transition_backup.transition_function,
                )
                self.transition_function = deepcopy(backup_fn)
                self._transition_backup.transition_function = None
                self._switched = True
                self.logger.info(
                    f"The {app.end_event} event was produced. Switching back to the normal FSM."
                )

    def _resolve_transition(self, event: EventType) -> Optional[Type[AbstractRound]]:
        """Resolve the transitioning based on the given event."""
        for app in self.background_apps:
            matched, next_round_cls = self._resolve_bg_transition(app, event)
            if matched:
                return next_round_cls

        self._adjust_transition_fn(event)

        current_round_cls = cast(AppState, self._current_round_cls)
        next_round_cls = self.transition_function[current_round_cls].get(event, None)
        if next_round_cls is None:
            return None

        return next_round_cls

    def process_event(
        self, event: EventType, result: Optional[BaseSynchronizedData] = None
    ) -> None:
        """Process a round event."""
        if self._current_round_cls is None:
            self.logger.warning(
                f"Cannot process event '{event}' as current state is not set"
            )
            return

        next_round_cls = self._resolve_transition(event)
        self._extend_previous_rounds_with_current_round()
        # if there is no result, we duplicate the state since the round was preemptively ended
        result = self.current_round.synchronized_data if result is None else result
        self._round_results.append(result)

        self._log_end(event)
        if next_round_cls is not None:
            self.schedule_round(next_round_cls)
            return

        if self._switched:
            self._switched = False
            return

        self.logger.warning("AbciApp has reached a dead end.")
        self._current_round_cls = None
        self._current_round = None

    def update_time(self, timestamp: datetime.datetime) -> None:
        """
        Observe timestamp from last block.

        :param timestamp: the latest block's timestamp.
        """
        self.logger.debug("arrived block with timestamp: %s", timestamp)
        self.logger.debug("current AbciApp time: %s", self._last_timestamp)
        self._timeouts.pop_earliest_cancelled_timeouts()

        if self._timeouts.size == 0:
            # if no pending timeouts, then it is safe to
            # move forward the last known timestamp to the
            # latest block's timestamp.
            self.logger.debug("no pending timeout, move time forward")
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
            self.logger.warning(
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

    def cleanup_current_histories(self, cleanup_history_depth_current: int) -> None:
        """Reset the parameter histories for the current entry (period), keeping only the latest values for each parameter."""
        self.synchronized_data.db.cleanup_current_histories(
            cleanup_history_depth_current
        )


class OffenseType(Enum):
    """
    The types of offenses.

    The values of the enum represent the seriousness of the offence.
    Offense types with values >1000 are considered serious.
    See also `is_light_offence` and `is_serious_offence` functions.
    """

    NO_OFFENCE = -2
    CUSTOM = -1
    VALIDATOR_DOWNTIME = 0
    INVALID_PAYLOAD = 1
    BLACKLISTED = 2
    SUSPECTED = 3
    UNKNOWN = SERIOUS_OFFENCE_ENUM_MIN
    DOUBLE_SIGNING = SERIOUS_OFFENCE_ENUM_MIN + 1
    LIGHT_CLIENT_ATTACK = SERIOUS_OFFENCE_ENUM_MIN + 2


def is_light_offence(offence_type: OffenseType) -> bool:
    """Check if an offence type is light."""
    return 0 <= offence_type.value < SERIOUS_OFFENCE_ENUM_MIN


def is_serious_offence(offence_type: OffenseType) -> bool:
    """Check if an offence type is serious."""
    return offence_type.value >= SERIOUS_OFFENCE_ENUM_MIN


def light_offences() -> Iterator[OffenseType]:
    """Get the light offences."""
    return filter(is_light_offence, OffenseType)


def serious_offences() -> Iterator[OffenseType]:
    """Get the serious offences."""
    return filter(is_serious_offence, OffenseType)


class AvailabilityWindow:
    """
    A cyclic array with a maximum length that holds boolean values.

    When an element is added to the array and the maximum length has been reached,
    the oldest element is removed. Two attributes `num_positive` and `num_negative`
    reflect the number of positive and negative elements in the AvailabilityWindow,
    they are updated every time a new element is added.
    """

    def __init__(self, max_length: int) -> None:
        """
        Initializes the `AvailabilityWindow` instance.

        :param max_length: the maximum length of the cyclic array.
        """
        if max_length < 1:
            raise ValueError(
                f"An `AvailabilityWindow` with a `max_length` {max_length} < 1 is not valid."
            )

        self._max_length = max_length
        self._window: Deque[bool] = deque(maxlen=max_length)
        self._num_positive = 0
        self._num_negative = 0

    def __eq__(self, other: Any) -> bool:
        """Compare `AvailabilityWindow` objects."""
        if isinstance(other, AvailabilityWindow):
            return self.to_dict() == other.to_dict()
        return False

    def has_bad_availability_rate(self, threshold: float = 0.95) -> bool:
        """Whether the agent on which the window belongs to has a bad availability rate or not."""
        return self._num_positive >= ceil(self._max_length * threshold)

    def _update_counters(self, positive: bool, removal: bool = False) -> None:
        """Updates the `num_positive` and `num_negative` counters."""
        update_amount = -1 if removal else 1

        if positive:
            if self._num_positive == 0 and update_amount == -1:  # pragma: no cover
                return
            self._num_positive += update_amount
        else:
            if self._num_negative == 0 and update_amount == -1:  # pragma: no cover
                return
            self._num_negative += update_amount

    def add(self, value: bool) -> None:
        """
        Adds a new boolean value to the cyclic array.

        If the maximum length has been reached, the oldest element is removed.

        :param value: The boolean value to add to the cyclic array.
        """
        if len(self._window) == self._max_length and self._max_length > 0:
            # we have filled the window, we need to pop the oldest element
            # and update the score accordingly
            oldest_value = self._window.popleft()
            self._update_counters(oldest_value, removal=True)

        self._window.append(value)
        self._update_counters(value)

    def to_dict(self) -> Dict[str, int]:
        """Returns a dictionary representation of the `AvailabilityWindow` instance."""
        return {
            "max_length": self._max_length,
            # Please note that the value cannot be represented if the max length of the availability window is > 14_285
            "array": (
                int("".join(str(int(flag)) for flag in self._window), base=2)
                if len(self._window)
                else 0
            ),
            "num_positive": self._num_positive,
            "num_negative": self._num_negative,
        }

    @staticmethod
    def _validate_key(
        data: Dict[str, int], key: str, validator: Callable[[int], bool]
    ) -> None:
        """Validate the given key in the data."""
        value = data.get(key, None)
        if value is None:
            raise ValueError(f"Missing required key: {key}.")

        if not isinstance(value, int):
            raise ValueError(f"{key} must be of type int.")

        if not validator(value):
            raise ValueError(f"{key} has invalid value {value}.")

    @staticmethod
    def _validate(data: Dict[str, int]) -> None:
        """Check if the input can be properly mapped to the class attributes."""
        if not isinstance(data, dict):
            raise TypeError(f"Expected dict, got {type(data)}")

        attribute_to_validator = {
            "max_length": lambda x: x > 0,
            "array": lambda x: 0 <= x < 2 ** data["max_length"],
            "num_positive": lambda x: x >= 0,
            "num_negative": lambda x: x >= 0,
        }

        errors = []
        for attribute, validator in attribute_to_validator.items():
            try:
                AvailabilityWindow._validate_key(data, attribute, validator)
            except ValueError as e:
                errors.append(str(e))

        if errors:
            raise ValueError("Invalid input:\n" + "\n".join(errors))

    @classmethod
    def from_dict(cls, data: Dict[str, int]) -> "AvailabilityWindow":
        """Initializes an `AvailabilityWindow` instance from a dictionary."""
        cls._validate(data)

        # convert the serialized array to a binary string
        binary_number = bin(data["array"])[2:]
        # convert each character in the binary string to a flag
        flags = (bool(int(digit)) for digit in binary_number)

        instance = cls(max_length=data["max_length"])
        instance._window.extend(flags)
        instance._num_positive = data["num_positive"]
        instance._num_negative = data["num_negative"]
        return instance


@dataclass
class OffenceStatus:
    """A class that holds information about offence status for an agent."""

    validator_downtime: AvailabilityWindow = field(
        default_factory=lambda: AvailabilityWindow(NUMBER_OF_BLOCKS_TRACKED)
    )
    invalid_payload: AvailabilityWindow = field(
        default_factory=lambda: AvailabilityWindow(NUMBER_OF_ROUNDS_TRACKED)
    )
    blacklisted: AvailabilityWindow = field(
        default_factory=lambda: AvailabilityWindow(NUMBER_OF_ROUNDS_TRACKED)
    )
    suspected: AvailabilityWindow = field(
        default_factory=lambda: AvailabilityWindow(NUMBER_OF_ROUNDS_TRACKED)
    )
    num_unknown_offenses: int = 0
    num_double_signed: int = 0
    num_light_client_attack: int = 0
    custom_offences_amount: int = 0

    def slash_amount(self, light_unit_amount: int, serious_unit_amount: int) -> int:
        """Get the slash amount of the current status."""
        offence_types = []

        if self.validator_downtime.has_bad_availability_rate():
            offence_types.append(OffenseType.VALIDATOR_DOWNTIME)
        if self.invalid_payload.has_bad_availability_rate():
            offence_types.append(OffenseType.INVALID_PAYLOAD)
        if self.blacklisted.has_bad_availability_rate():
            offence_types.append(OffenseType.BLACKLISTED)
        if self.suspected.has_bad_availability_rate():
            offence_types.append(OffenseType.SUSPECTED)
        offence_types.extend([OffenseType.UNKNOWN] * self.num_unknown_offenses)
        offence_types.extend([OffenseType.UNKNOWN] * self.num_double_signed)
        offence_types.extend([OffenseType.UNKNOWN] * self.num_light_client_attack)

        light_multiplier = 0
        serious_multiplier = 0
        for offence_type in offence_types:
            light_multiplier += bool(is_light_offence(offence_type))
            serious_multiplier += bool(is_serious_offence(offence_type))

        return (
            light_multiplier * light_unit_amount
            + serious_multiplier * serious_unit_amount
            + self.custom_offences_amount
        )


class OffenseStatusEncoder(json.JSONEncoder):
    """A custom JSON encoder for the offence status dictionary."""

    def default(self, o: Any) -> Any:
        """The default JSON encoder."""
        if is_dataclass(o):
            return asdict(o)
        if isinstance(o, AvailabilityWindow):
            return o.to_dict()
        return super().default(o)


class OffenseStatusDecoder(json.JSONDecoder):
    """A custom JSON decoder for the offence status dictionary."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the custom JSON decoder."""
        super().__init__(object_hook=self.hook, *args, **kwargs)

    @staticmethod
    def hook(
        data: Dict[str, Any]
    ) -> Union[AvailabilityWindow, OffenceStatus, Dict[str, OffenceStatus]]:
        """Perform the custom decoding."""
        # if this is an `AvailabilityWindow`
        window_attributes = sorted(AvailabilityWindow(1).to_dict().keys())
        if window_attributes == sorted(data.keys()):
            return AvailabilityWindow.from_dict(data)

        # if this is an `OffenceStatus`
        status_attributes = (
            OffenceStatus.__annotations__.keys()  # pylint: disable=no-member
        )
        if sorted(status_attributes) == sorted(data.keys()):
            return OffenceStatus(**data)

        return data


@dataclass(frozen=True, eq=True)
class PendingOffense:
    """A dataclass to represent offences that need to be addressed."""

    accused_agent_address: str
    round_count: int
    offense_type: OffenseType
    last_transition_timestamp: float
    time_to_live: float
    # only takes effect if the `OffenseType` is of type `CUSTOM`, otherwise it is ignored
    custom_amount: int = 0

    def __post_init__(self) -> None:
        """Post initialization for offence type conversion in case it is given as an `int`."""
        if isinstance(self.offense_type, int):
            super().__setattr__("offense_type", OffenseType(self.offense_type))


class SlashingNotConfiguredError(Exception):
    """Custom exception raised when slashing configuration is requested but is not available."""


DEFAULT_PENDING_OFFENCE_TTL = 2 * 60 * 60  # 1 hour


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

    def __init__(self, context: SkillContext, abci_app_cls: Type[AbciApp]):
        """Initialize the round."""
        self._blockchain = Blockchain()
        self._syncing_up = True
        self._context = context
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
        self._terminating_round_called: bool = False
        # a mapping of the validators' addresses to their agent addresses
        # we create a mapping to avoid calculating the agent address from the validator address every time we need it
        # since this is an operation that will be performed every time we want to create an offence
        self._validator_to_agent: Dict[str, str] = {}
        # a mapping of the agents' addresses to their offence status
        self._offence_status: Dict[str, OffenceStatus] = {}
        self._slashing_enabled = False
        self.pending_offences: Set[PendingOffense] = set()

    def enable_slashing(self) -> None:
        """Enable slashing."""
        self._slashing_enabled = True

    @property
    def validator_to_agent(self) -> Dict[str, str]:
        """Get the mapping of the validators' addresses to their agent addresses."""
        if self._validator_to_agent:
            return self._validator_to_agent
        raise SlashingNotConfiguredError(
            "The mapping of the validators' addresses to their agent addresses has not been set."
        )

    @validator_to_agent.setter
    def validator_to_agent(self, validator_to_agent: Dict[str, str]) -> None:
        """Set the mapping of the validators' addresses to their agent addresses."""
        if self._validator_to_agent:
            raise ValueError(
                "The mapping of the validators' addresses to their agent addresses can only be set once. "
                f"Attempted to set with {validator_to_agent} but it has content already: {self._validator_to_agent}."
            )
        self._validator_to_agent = validator_to_agent

    @property
    def offence_status(self) -> Dict[str, OffenceStatus]:
        """Get the mapping of the agents' addresses to their offence status."""
        if self._offence_status:
            return self._offence_status
        raise SlashingNotConfiguredError(  # pragma: nocover
            "The mapping of the agents' addresses to their offence status has not been set."
        )

    @offence_status.setter
    def offence_status(self, offence_status: Dict[str, OffenceStatus]) -> None:
        """Set the mapping of the agents' addresses to their offence status."""
        self.abci_app.logger.debug(f"Setting offence status to: {offence_status}")
        self._offence_status = offence_status
        self.store_offence_status()

    def add_pending_offence(self, pending_offence: PendingOffense) -> None:
        """
        Add a pending offence to the set of pending offences.

        Pending offences are offences that have been detected, but not yet agreed upon by the consensus.
        A pending offence is removed from the set of pending offences and added to the OffenceStatus of a validator
        when the majority of the agents agree on it.

        :param pending_offence: the pending offence to add
        :return: None
        """
        self.pending_offences.add(pending_offence)

    def sync_db_and_slashing(self, serialized_db_state: str) -> None:
        """Sync the database and the slashing configuration."""
        self.abci_app.synchronized_data.db.sync(serialized_db_state)
        offence_status = self.latest_synchronized_data.slashing_config
        if offence_status:
            # deserialize the offence status and load it to memory
            self.offence_status = json.loads(
                offence_status,
                cls=OffenseStatusDecoder,
            )

    def serialized_offence_status(self) -> str:
        """Serialize the offence status."""
        return json.dumps(self.offence_status, cls=OffenseStatusEncoder, sort_keys=True)

    def store_offence_status(self) -> None:
        """Store the serialized offence status."""
        if not self._slashing_enabled:
            # if slashing is not enabled, we do not update anything
            return
        encoded_status = self.serialized_offence_status()
        self.latest_synchronized_data.slashing_config = encoded_status
        self.abci_app.logger.debug(f"Updated db with: {encoded_status}")
        self.abci_app.logger.debug(f"App hash now is: {self.root_hash.hex()}")

    def get_agent_address(self, validator: Validator) -> str:
        """Get corresponding agent address from a `Validator` instance."""
        validator_address = validator.address.hex().upper()

        try:
            return self.validator_to_agent[validator_address]
        except KeyError as exc:
            raise ValueError(
                f"Requested agent address for an unknown validator address {validator_address}. "
                f"Available validators are: {self.validator_to_agent.keys()}"
            ) from exc

    def setup(self, *args: Any, **kwargs: Any) -> None:
        """
        Set up the round sequence.

        :param args: the arguments to pass to the round constructor.
        :param kwargs: the keyword-arguments to pass to the round constructor.
        """
        kwargs["context"] = self._context
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

        This is going to be the database's hash.
        In this way, the app hash will be reflecting our application's state,
        and will guarantee that all the agents on the chain apply the changes of the arriving blocks in the same way.

        :return: the root hash to be included as the Header.AppHash in the next block.
        """
        return self.abci_app.synchronized_data.db.hash()

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

    def set_block_stall_deadline(self) -> None:
        """Use the local time of the agent and a predefined tolerance, to specify the expiration of the deadline."""
        self._block_stall_deadline = datetime.datetime.now() + datetime.timedelta(
            seconds=BLOCKS_STALL_TOLERANCE
        )

    def init_chain(self, initial_height: int) -> None:
        """Init chain."""
        # reduce `initial_height` by 1 to get block count offset as per Tendermint protocol
        self._blockchain = Blockchain(initial_height - 1)

    def _track_tm_offences(
        self, evidences: Evidences, last_commit_info: LastCommitInfo
    ) -> None:
        """Track offences provided by Tendermint, if there are any."""
        for vote_info in last_commit_info.votes:
            agent_address = self.get_agent_address(vote_info.validator)
            was_down = not vote_info.signed_last_block
            self.offence_status[agent_address].validator_downtime.add(was_down)

        for byzantine_validator in evidences.byzantine_validators:
            agent_address = self.get_agent_address(byzantine_validator.validator)
            evidence_type = byzantine_validator.evidence_type
            self.offence_status[agent_address].num_unknown_offenses += bool(
                evidence_type == EvidenceType.UNKNOWN
            )
            self.offence_status[agent_address].num_double_signed += bool(
                evidence_type == EvidenceType.DUPLICATE_VOTE
            )
            self.offence_status[agent_address].num_light_client_attack += bool(
                evidence_type == EvidenceType.LIGHT_CLIENT_ATTACK
            )

    def _track_app_offences(self) -> None:
        """Track offences provided by the app level, if there are any."""
        synced_data = self.abci_app.synchronized_data
        for agent in self.offence_status.keys():
            blacklisted = agent in synced_data.blacklisted_keepers
            suspected = agent in cast(tuple, synced_data.db.get("suspects", tuple()))
            agent_status = self.offence_status[agent]
            agent_status.blacklisted.add(blacklisted)
            agent_status.suspected.add(suspected)

    def _handle_slashing_not_configured(self, exc: SlashingNotConfiguredError) -> None:
        """Handle a `SlashingNotConfiguredError`."""
        # In the current slashing implementation, we do not track offences before setting the slashing
        # configuration, i.e., before successfully sharing the tm configuration via ACN on registration.
        # That is because we cannot slash an agent if we do not map their validator address to their agent address.
        # Checking the number of participants will allow us to identify whether the registration round has finished,
        # and therefore expect that the slashing configuration has been set if ACN registration is enabled.
        if self.abci_app.synchronized_data.nb_participants:
            _logger.error(
                f"{exc} This error may occur when the ACN registration has not been successfully performed. "
                "Have you set the `share_tm_config_on_startup` flag to `true` in the configuration?"
            )
            self._slashing_enabled = False
            _logger.warning("Slashing has been disabled!")

    def _try_track_offences(
        self, evidences: Evidences, last_commit_info: LastCommitInfo
    ) -> None:
        """Try to track the offences. If an error occurs, log it, disable slashing, and warn about the latter."""
        try:
            if self._slashing_enabled:
                # only track offences if the first round has finished
                # we avoid tracking offences in the first round
                # because we do not have the slashing configuration synced yet
                self._track_tm_offences(evidences, last_commit_info)
                self._track_app_offences()
        except SlashingNotConfiguredError as exc:
            self._handle_slashing_not_configured(exc)

    def begin_block(
        self,
        header: Header,
        evidences: Evidences,
        last_commit_info: LastCommitInfo,
    ) -> None:
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
        self.set_block_stall_deadline()
        self.abci_app.logger.debug(
            "Created a new local deadline for the next `begin_block` request from the Tendermint node: "
            f"{self._block_stall_deadline}"
        )
        self._try_track_offences(evidences, last_commit_info)

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
                self.abci_app.logger.warning(
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

    def _get_round_result(
        self,
    ) -> Optional[Tuple[BaseSynchronizedData, Any]]:
        """
        Get the round's result.

        Give priority to:
            1. terminating bg rounds
            2. ever running bg rounds
            3. normal bg rounds
            4. normal rounds

        :return: the round's result.
        """
        for prioritized_group in self.abci_app.bg_apps_prioritized:
            for app in prioritized_group:
                result = app.background_round.end_block()
                if (
                    result is None
                    or app.type == BackgroundAppType.TERMINATING
                    and self._terminating_round_called
                ):
                    continue
                if (
                    app.type == BackgroundAppType.TERMINATING
                    and not self._terminating_round_called
                ):
                    self._terminating_round_called = True
                return result
        return self.abci_app.current_round.end_block()

    def _update_round(self) -> None:
        """
        Update a round.

        Check whether the round has finished. If so, get the new round and set it as the current round.
        If a termination app's round has returned a result, then the other apps' rounds are ignored.
        """
        result = self._get_round_result()

        if result is None:
            # neither the background rounds, nor the current round returned, so no update needs to be made
            return

        # update the offence status at the end of each round
        # this is done to ensure that the offence status is always up-to-date & in sync
        # the next step is a no-op if slashing is not enabled
        self.store_offence_status()

        self._last_round_transition_timestamp = self._blockchain.last_block.timestamp
        self._last_round_transition_height = self.height
        self._last_round_transition_root_hash = self.root_hash
        self._last_round_transition_tm_height = self.tm_height

        round_result, event = result
        self.abci_app.logger.debug(
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
        self._slashing_enabled = False
        self.pending_offences = set()

    def reset_state(
        self,
        restart_from_round: str,
        round_count: int,
        serialized_db_state: Optional[str] = None,
    ) -> None:
        """
        This method resets the state of RoundSequence to the beginning of the period.

        Note: This is intended to be used for agent <-> tendermint communication recovery only!

        :param restart_from_round: from which round to restart the abci.
         This round should be the first round in the last period.
        :param round_count: the round count at the beginning of the period -1.
        :param serialized_db_state: the state of the database at the beginning of the period.
         If provided, the database will be reset to this state.
        """
        self._reset_to_default_params()
        self.abci_app.synchronized_data.db.round_count = round_count
        if serialized_db_state is not None:
            self.sync_db_and_slashing(serialized_db_state)
            # Furthermore, that hash is then in turn used as the init hash when the tm network is reset.
            self._last_round_transition_root_hash = self.root_hash

        self.abci_app.cleanup_timeouts()
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


@dataclass(frozen=True)
class PendingOffencesPayload(BaseTxPayload):
    """Represent a transaction payload for pending offences."""

    accused_agent_address: str
    offense_round: int
    offense_type_value: int
    last_transition_timestamp: float
    time_to_live: float
    custom_amount: int


class PendingOffencesRound(CollectSameUntilThresholdRound):
    """Defines the pending offences background round, which runs concurrently with other rounds to sync the offences."""

    payload_class = PendingOffencesPayload
    synchronized_data_class = BaseSynchronizedData

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the `PendingOffencesRound`."""
        super().__init__(*args, **kwargs)
        self._latest_round_processed = -1

    @property
    def offence_status(self) -> Dict[str, OffenceStatus]:
        """Get the offence status from the round sequence."""
        return self.context.state.round_sequence.offence_status

    def end_block(self) -> None:
        """
        Process the end of the block for the pending offences background round.

        It is important to note that this is a non-standard type of round, meaning it does not emit any events.
        Instead, it continuously runs in the background.
        The objective of this round is to consistently monitor the received pending offences
        and achieve a consensus among the agents.
        """
        if not self.threshold_reached:
            return

        offence = PendingOffense(*self.most_voted_payload_values)

        # an offence should only be tracked once, not every time a payload is processed after the threshold is reached
        if self._latest_round_processed == offence.round_count:
            return

        # add synchronized offence to the offence status
        # only `INVALID_PAYLOAD` offence types are supported at the moment as pending offences:
        # https://github.com/valory-xyz/open-autonomy/blob/6831d6ebaf10ea8e3e04624b694c7f59a6d05bb4/packages/valory/skills/abstract_round_abci/handlers.py#L215-L222  # noqa
        invalid = offence.offense_type == OffenseType.INVALID_PAYLOAD
        self.offence_status[offence.accused_agent_address].invalid_payload.add(invalid)

        # if the offence is of custom type, then add the custom amount to it
        if offence.offense_type == OffenseType.CUSTOM:
            self.offence_status[
                offence.accused_agent_address
            ].custom_offences_amount += offence.custom_amount
        elif offence.custom_amount != 0:
            self.context.logger.warning(
                f"Custom amount for {offence=} will not take effect as it is not of `CUSTOM` type."
            )

        self._latest_round_processed = offence.round_count
