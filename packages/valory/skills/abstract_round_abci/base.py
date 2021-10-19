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
import datetime
import heapq
import itertools
import logging
import uuid
from abc import ABC, ABCMeta, abstractmethod
from copy import copy
from dataclasses import dataclass, field
from enum import Enum
from math import ceil
from typing import (
    AbstractSet,
    Any,
    Dict,
    FrozenSet,
    Generic,
    List,
    Optional,
    Sequence,
    Tuple,
    Type,
    TypeVar,
    cast,
)

from aea.crypto.ledger_apis import LedgerApis
from aea.exceptions import enforce

from packages.fetchai.connections.ledger.base import (
    CONNECTION_ID as LEDGER_CONNECTION_PUBLIC_ID,
)
from packages.valory.protocols.abci.custom_types import Header
from packages.valory.skills.abstract_round_abci.serializer import (
    DictProtobufStructSerializer,
)


_logger = logging.getLogger("aea.packages.valory.skills.abstract_round_abci.base")


OK_CODE = 0
ERROR_CODE = 1
LEDGER_API_ADDRESS = str(LEDGER_CONNECTION_PUBLIC_ID)

EventType = TypeVar("EventType")


def consensus_threshold(n: int) -> int:  # pylint: disable=invalid-name
    """
    Get consensus threshold.

    :param n: the number of participants
    :return: the consensus threshold
    """
    return ceil((2 * n + 1) / 3)


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
            raise ValueError(  # pragma: no cover
                f"class {name} must inherit from {BaseTxPayload.__name__}"
            )
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
        if not hasattr(cls, field_name) or getattr(cls, field_name) is None:
            raise ValueError(f"class {cls} must set '{field_name}' class field")
        return getattr(cls, field_name)


class BaseTxPayload(ABC, metaclass=_MetaPayload):
    """This class represents a base class for transaction payload classes."""

    transaction_type: Any

    def __init__(self, sender: str, id_: Optional[str] = None) -> None:
        """
        Initialize a transaction payload.

        :param sender: the sender (Ethereum) address
        :param id_: the id of the transaction
        """
        self.id_ = uuid.uuid4().hex if id_ is None else id_
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
            transaction_type=str(self.transaction_type),
            id_=self.id_,
            sender=self.sender,
            **self.data,
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
        return (
            self.id_ == other.id_
            and self.sender == other.sender
            and self.data == other.data
        )


class Transaction(ABC):
    """Class to represent a transaction for the ephemeral chain of a period."""

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

    def verify(self, ledger_id: str) -> None:
        """
        Verify the signature is correct.

        :param ledger_id: the ledger id of the address
        :raises: SignatureNotValidError: if the signature is not valid.
        """
        payload_bytes = DictProtobufStructSerializer.encode(self.payload.json)
        addresses = LedgerApis.recover_message(
            identifier=ledger_id, message=payload_bytes, signature=self.signature
        )
        if self.payload.sender not in addresses:
            raise SignatureNotValidError("signature not valid.")

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

    @property
    def timestamp(self) -> datetime.datetime:
        """Get the block timestamp."""
        return self.header.timestamp


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
        expected_height = self.height + 1
        actual_height = block.header.height
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
        return self.length

    @property
    def length(self) -> int:
        """Get the blockchain length."""
        return len(self._blocks)

    @property
    def blocks(self) -> Tuple[Block, ...]:
        """Get the blocks."""
        return tuple(self._blocks)


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
        return ConsensusParams(max_participants)

    def __eq__(self, other: Any) -> bool:
        """Check equality."""
        return (
            isinstance(other, ConsensusParams)
            and self.max_participants == other.max_participants
        )


class BasePeriodState:
    """
    Class to represent a period state.

    This is the relevant state constructed and replicated by the agents in a period.
    """

    def __init__(
        self,
        participants: Optional[AbstractSet[str]] = None,
    ) -> None:
        """Initialize a period state."""
        self._participants = frozenset(participants) if participants else None

    @property
    def participants(self) -> FrozenSet[str]:
        """Get the participants."""
        if self._participants is None:
            raise ValueError("'participants' field is None")
        return self._participants

    def update(self, **kwargs: Any) -> "BasePeriodState":
        """Copy and update the state."""
        # remove leading underscore from keys
        data = {key[1:]: value for key, value in self.__dict__.items()}
        data.update(kwargs)
        return type(self)(**data)

    def __repr__(self) -> str:
        """Return a string representation of the state."""
        return f"BasePeriodState({self.__dict__})"


class AbstractRound(ABC):
    """
    This class represents an abstract round.

    A round is a state of a period. It usually involves
    interactions between participants in the period,
    although this is not enforced at this level of abstraction.
    """

    round_id: str
    allowed_tx_type: Any

    def __init__(
        self,
        state: BasePeriodState,
        consensus_params: ConsensusParams,
    ) -> None:
        """Initialize the round."""
        self._consensus_params = consensus_params
        self._state = state

        self._check_class_attributes()

    def _check_class_attributes(self) -> None:
        """Check that required class attributes are set."""
        try:
            self.round_id
        except AttributeError as exc:
            raise ABCIAppInternalError("round id not set") from exc
        try:
            self.allowed_tx_type
        except AttributeError as exc:
            raise ABCIAppInternalError("allowed tx type not set") from exc

    @property
    def period_state(self) -> BasePeriodState:
        """Get the period state."""
        return self._state

    def check_transaction(self, transaction: Transaction) -> None:
        """
        Check transaction against the current state.

        :param transaction: the transaction
        """
        self.check_allowed_tx_type(transaction)
        self.check_payload(transaction.payload)

    def process_transaction(self, transaction: Transaction) -> None:
        """
        Process a transaction.

        By convention, the payload handler should be a method
        of the class that is named '{payload_name}'.

        :param transaction: the transaction.
        """
        self.check_allowed_tx_type(transaction)
        self.process_payload(transaction.payload)

    @abstractmethod
    def end_block(self) -> Optional[Tuple[BasePeriodState, Any]]:
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

    def check_allowed_tx_type(self, transaction: Transaction) -> None:
        """
        Check the transaction is of the allowed transaction type.

        :param transaction: the transaction
        :raises:
            TransactionTypeNotRecognizedError if the transaction can be applied to the current state.
        """
        if self.allowed_tx_type is None:
            raise TransactionTypeNotRecognizedError(
                "current round does not allow transactions"
            )
        tx_type = transaction.payload.transaction_type
        if str(tx_type) != str(self.allowed_tx_type):
            raise TransactionTypeNotRecognizedError(
                f"request '{tx_type}' not recognized; only {self.allowed_tx_type} is supported"
            )

    @abstractmethod
    def check_payload(self, payload: BaseTxPayload) -> None:
        """Check payload."""

    @abstractmethod
    def process_payload(self, payload: BaseTxPayload) -> None:
        """Process payload."""


AbciAppTransitionFunction = Dict[
    Type[AbstractRound], Dict[EventType, Type[AbstractRound]]
]


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

        # The timeout priority queue keeps the the earliest deadline at the top.
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
        entry = self._heap[0]
        while entry.cancelled:
            self._entry_finder.pop(entry.entry_count)
            heapq.heappop(self._heap)
            if len(self._heap) == 0:
                break
            entry = self._heap[0]

    def get_earliest_timeout(self) -> Tuple[datetime.datetime, Any]:
        """Get the earliest timeout-event pair."""
        self.pop_earliest_cancelled_timeouts()
        entry = self._heap[0]
        return entry.deadline, entry.event

    def pop_timeout(self) -> Tuple[datetime.datetime, Any]:
        """Remove and return the earliest timeout-event pair."""
        self.pop_earliest_cancelled_timeouts()
        entry = heapq.heappop(self._heap)
        del self._entry_finder[entry.entry_count]
        return entry.deadline, entry.event


class AbciApp(Generic[EventType]):  # pylint: disable=too-many-instance-attributes
    """
    Base class for ABCI apps.

    Concrete classes of this class implement the ABCI App.
    It requires to set
    """

    initial_round_cls: Type[AbstractRound]
    transition_function: AbciAppTransitionFunction
    event_to_timeout: Dict[EventType, float]

    def __init__(
        self,
        state: BasePeriodState,
        consensus_params: ConsensusParams,
        logger: logging.Logger,
    ):
        """Initialize the AbciApp."""
        self.state = state
        self.consensus_params = consensus_params
        self.logger = logger

        self._current_round_cls: Optional[Type[AbstractRound]] = None
        self._current_round: Optional[AbstractRound] = None
        self._last_round: Optional[AbstractRound] = None
        self._previous_rounds: List[AbstractRound] = []
        self._round_results: List[Any] = []
        self._last_timestamp: Optional[datetime.datetime] = None
        self._current_timeout_entries: List[int] = []
        self._timeouts = Timeouts[EventType]()

        self._check_class_attributes()
        self._check_class_attributes_consistency(
            self.initial_round_cls, self.transition_function, self.event_to_timeout
        )

    def _check_class_attributes(self) -> None:
        """Check that required class attributes are set."""
        try:
            self.initial_round_cls
        except AttributeError as exc:
            raise ABCIAppInternalError("initial round class not set") from exc
        try:
            self.transition_function
        except AttributeError as exc:
            raise ABCIAppInternalError("transition function not set") from exc

    @classmethod
    def _check_class_attributes_consistency(
        cls,
        initial_round_cls: Type[AbstractRound],
        transition_function: AbciAppTransitionFunction,
        event_to_timeout: Dict[EventType, float],
    ) -> None:
        """
        Check that required class attributes values are consistent.

        I.e.:
        - check that the initial state is in the set of states specified by the transition function.
        - check that the initial state has outgoing transitions
        - check that the initial state does not trigger timeout events. This is because we need at
          least one block/timestamp to start timeouts.

        :param initial_round_cls: the initial round class
        :param transition_function: the transition function
        :param event_to_timeout: mapping from events to its timeout in seconds.
        :raises:
            ValueError if the initial round class is not in the set of rounds.
        """
        states = set()
        for start_state, transitions in transition_function.items():
            states.add(start_state)
            for _event, end_state in transitions.items():
                states.add(end_state)
        enforce(
            initial_round_cls in states,
            f"initial round class {initial_round_cls} is not in the set of rounds: {states}",
        )
        enforce(
            initial_round_cls in transition_function,
            f"initial round class {initial_round_cls} does not have outgoing transitions",
        )

        timeout_events_from_initial_state = {
            e for e in transition_function[initial_round_cls] if e in event_to_timeout
        }
        enforce(
            len(timeout_events_from_initial_state) == 0,
            f"initial round class {initial_round_cls} has timeout events in outgoing transitions: {timeout_events_from_initial_state}",
        )

    @property
    def last_timestamp(self) -> datetime.datetime:
        """Get last timestamp."""
        if self._last_timestamp is None:
            raise ABCIAppInternalError("last timestamp is None")
        return self._last_timestamp

    def setup(self) -> None:
        """Set up the behaviour."""
        self._schedule_round(self.initial_round_cls)

    def _log_start(self) -> None:
        """Log the entering in the round."""
        self.logger.info(f"Entered in the '{self.current_round.round_id}' round")

    def _log_end(self, event: EventType) -> None:
        """Log the exiting from the round."""
        self.logger.info(
            f"'{self.current_round.round_id}' round is done with event: {event}"
        )

    def _schedule_round(self, round_cls: Type[AbstractRound]) -> None:
        """
        Schedule a round class.

        this means:
        - cancel timeout events belonging to the current round;
        - instantiate the new round class and set it as current round;
        - create new timeout events and schedule them according to latest timestamp.

        :param round_cls: the class of the new round.
        """
        for entry_id in self._current_timeout_entries:
            self._timeouts.cancel_timeout(entry_id)

        self._current_timeout_entries = []
        next_events = list(self.transition_function.get(round_cls, {}).keys())
        for event in next_events:
            timeout = self.event_to_timeout.get(event, None)
            if timeout is not None:
                # last_timestamp is not None because we are not in the first round
                # (see consistency check)
                deadline = self.last_timestamp + datetime.timedelta(0, timeout)
                entry_id = self._timeouts.add_timeout(deadline, event)
                self._current_timeout_entries.append(entry_id)

        last_result = (
            self._round_results[-1] if len(self._round_results) > 0 else self.state
        )
        self._last_round = self._current_round
        self._current_round_cls = round_cls
        self._current_round = round_cls(last_result, self.consensus_params)
        self._log_start()

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
    def last_round_id(self) -> Optional[str]:
        """Get the last round id."""
        return self._last_round.round_id if self._last_round else None

    @property
    def is_finished(self) -> bool:
        """Check whether the AbciApp execution has finished."""
        return self._current_round is None

    @property
    def latest_result(self) -> Optional[Any]:
        """Get the latest result of the round."""
        return None if len(self._round_results) == 0 else self._round_results[-1]

    def check_transaction(self, transaction: Transaction) -> None:
        """
        Check a transaction.

        Forward the call to the current round object.

        :param transaction: the transaction.
        """
        self.current_round.check_transaction(transaction)

    def process_transaction(self, transaction: Transaction) -> None:
        """
        Process a transaction.

        Forward the call to the current round object.

        :param transaction: the transaction.
        """
        self.current_round.process_transaction(transaction)

    def process_event(self, event: EventType, result: Optional[Any] = None) -> None:
        """Process a round event."""
        if self._current_round_cls is None:
            self.logger.info(
                f"cannot process event {event} as current state is not set"
            )
            return

        next_round_cls = self.transition_function[self._current_round_cls].get(
            event, None
        )
        self._previous_rounds.append(self.current_round)
        if result is not None:
            self._round_results.append(result)
        else:
            # we duplicate the state since the round was preemptively ended
            self._round_results.append(self.current_round.period_state)

        self._log_end(event)
        if next_round_cls is not None:
            self._schedule_round(next_round_cls)
        else:
            self.logger.info("AbciApp has reached a dead end.")
            self._current_round_cls = None
            self._current_round = None

    def update_time(self, timestamp: datetime.datetime) -> None:
        """
        Observe timestamp from last block.

        :param timestamp: the latest block's timestamp.
        """
        self._timeouts.pop_earliest_cancelled_timeouts()

        if self._timeouts.size == 0:
            # if no pending timeouts, then it is safe to
            # move forward the last known timestamp to the
            # latest block's timestamp.
            self._last_timestamp = timestamp
            return

        earliest_deadline, _ = self._timeouts.get_earliest_timeout()
        while earliest_deadline <= timestamp:
            # the earliest deadline is expired. Pop it from the
            # priority queue and process the timeout event.
            expired_deadline, timeout_event = self._timeouts.pop_timeout()

            # the last timestamp now becomes the expired deadline
            # clearly, it is earlier than the current highest known
            # timestamp that comes from the consensus engine.
            # However, we need it to correctly simulate the timeouts
            # of the next rounds.
            self._last_timestamp = expired_deadline

            self.process_event(timeout_event)

            if self._timeouts.size == 0:
                break
            earliest_deadline, _ = self._timeouts.get_earliest_timeout()

        # at this point, there is no timeout event left to be triggered
        # so it is safe to move forward the last known timestamp to the
        # new block's timestamp
        self._last_timestamp = timestamp


class Period:
    """
    This class represents a period (i.e. a sequence of rounds)

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

        self._block_construction_phase = (
            Period._BlockConstructionState.WAITING_FOR_BEGIN_BLOCK
        )

        self._block_builder = BlockBuilder()
        self._abci_app_cls = abci_app_cls
        self._abci_app: Optional[AbciApp] = None

    def setup(self, *args: Any, **kwargs: Any) -> None:
        """
        Set up the period.

        :param args: the arguments to pass to the round constructor.
        :param kwargs: the keyword-arguments to pass to the round constructor.
        """
        self._abci_app = self._abci_app_cls(*args, **kwargs)
        self._abci_app.setup()

    @property
    def abci_app(self) -> AbciApp:
        """Get the AbciApp."""
        if self._abci_app is None:
            raise ABCIAppInternalError("AbciApp not set")
        return self._abci_app

    @property
    def is_finished(self) -> bool:
        """Check if a period has finished."""
        return self.abci_app.is_finished

    def check_is_finished(self) -> None:
        """Check if a period has finished."""
        if self.is_finished:
            raise ValueError("period is finished, cannot accept new transactions")

    @property
    def current_round(self) -> AbstractRound:
        """Get current round."""
        return self.abci_app.current_round

    @property
    def current_round_id(self) -> Optional[str]:
        """Get the current round id."""
        return self.abci_app.current_round_id

    @property
    def last_round_id(self) -> Optional[str]:
        """Get the last round id."""
        return self.abci_app.last_round_id

    @property
    def last_timestamp(self) -> Optional[datetime.datetime]:
        """Get the last timestamp."""
        return (
            self._blockchain.blocks[-1].timestamp
            if self._blockchain.length != 0
            else None
        )

    @property
    def latest_result(self) -> Optional[Any]:
        """Get the latest result of the round."""
        return self.abci_app.latest_result

    def begin_block(self, header: Header) -> None:
        """Begin block."""
        if self.is_finished:
            raise ABCIAppInternalError("period is finished, cannot accept new blocks")
        if (
            self._block_construction_phase
            != Period._BlockConstructionState.WAITING_FOR_BEGIN_BLOCK
        ):
            raise ABCIAppInternalError("cannot accept a 'begin_block' request.")

        # From now on, the ABCI app waits for 'deliver_tx' requests, until 'end_block' is received
        self._block_construction_phase = (
            Period._BlockConstructionState.WAITING_FOR_DELIVER_TX
        )
        self._block_builder.reset()
        self._block_builder.header = header
        self.abci_app.update_time(header.timestamp)

    def deliver_tx(self, transaction: Transaction) -> None:
        """
        Deliver a transaction.

        Appends the transaction to build the block on 'end_block' later.

        :param transaction: the transaction.
        :raises:  an Error otherwise.
        """
        if (
            self._block_construction_phase
            != Period._BlockConstructionState.WAITING_FOR_DELIVER_TX
        ):
            raise ABCIAppInternalError("cannot accept a 'deliver_tx' request")

        self.abci_app.check_transaction(transaction)
        self.abci_app.process_transaction(transaction)
        self._block_builder.add_transaction(transaction)

    def end_block(self) -> None:
        """Process the 'end_block' request."""
        if (
            self._block_construction_phase
            != Period._BlockConstructionState.WAITING_FOR_DELIVER_TX
        ):
            raise ABCIAppInternalError("cannot accept a 'end_block' request.")
        # The ABCI app waits for the commit
        self._block_construction_phase = (
            Period._BlockConstructionState.WAITING_FOR_COMMIT
        )

    def commit(self) -> None:
        """Process the 'commit' request."""
        if (
            self._block_construction_phase
            != Period._BlockConstructionState.WAITING_FOR_COMMIT
        ):
            raise ABCIAppInternalError("cannot accept a 'commit' request.")
        block = self._block_builder.get_block()
        try:
            self._blockchain.add_block(block)
            self._update_round()
            # The ABCI app now waits again for the next block
            self._block_construction_phase = (
                Period._BlockConstructionState.WAITING_FOR_BEGIN_BLOCK
            )
        except AddBlockError as exception:
            raise exception

    def _update_round(self) -> None:
        """
        Update a round.

        Check whether the round has finished. If so, get the
        new round and set it as the current round.
        """
        result = self.current_round.end_block()
        if result is None:
            return
        round_result, event = result
        _logger.debug(
            f"updating round, current_round {self.current_round.round_id}, event: {event}, round result {round_result}"
        )
        self.abci_app.process_event(event, result=round_result)
