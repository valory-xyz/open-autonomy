<a id="packages.valory.skills.abstract_round_abci.base"></a>

# packages.valory.skills.abstract`_`round`_`abci.base

This module contains the base classes for the models classes of the skill.

<a id="packages.valory.skills.abstract_round_abci.base.consensus_threshold"></a>

#### consensus`_`threshold

```python
def consensus_threshold(n: int) -> int
```

Get consensus threshold.

**Arguments**:

- `n`: the number of participants

**Returns**:

the consensus threshold

<a id="packages.valory.skills.abstract_round_abci.base.ABCIAppException"></a>

## ABCIAppException Objects

```python
class ABCIAppException(Exception)
```

A parent class for all exceptions related to the ABCIApp.

<a id="packages.valory.skills.abstract_round_abci.base.SignatureNotValidError"></a>

## SignatureNotValidError Objects

```python
class SignatureNotValidError(ABCIAppException)
```

Error raised when a signature is invalid.

<a id="packages.valory.skills.abstract_round_abci.base.AddBlockError"></a>

## AddBlockError Objects

```python
class AddBlockError(ABCIAppException)
```

Exception raised when a block addition is not valid.

<a id="packages.valory.skills.abstract_round_abci.base.ABCIAppInternalError"></a>

## ABCIAppInternalError Objects

```python
class ABCIAppInternalError(ABCIAppException)
```

Internal error due to a bad implementation of the ABCIApp.

<a id="packages.valory.skills.abstract_round_abci.base.ABCIAppInternalError.__init__"></a>

#### `__`init`__`

```python
def __init__(message: str, *args: Any) -> None
```

Initialize the error object.

<a id="packages.valory.skills.abstract_round_abci.base.TransactionTypeNotRecognizedError"></a>

## TransactionTypeNotRecognizedError Objects

```python
class TransactionTypeNotRecognizedError(ABCIAppException)
```

Error raised when a transaction type is not recognized.

<a id="packages.valory.skills.abstract_round_abci.base.TransactionNotValidError"></a>

## TransactionNotValidError Objects

```python
class TransactionNotValidError(ABCIAppException)
```

Error raised when a transaction is not valid.

<a id="packages.valory.skills.abstract_round_abci.base.LateArrivingTransaction"></a>

## LateArrivingTransaction Objects

```python
class LateArrivingTransaction(ABCIAppException)
```

Error raised when the transaction belongs to previous round.

<a id="packages.valory.skills.abstract_round_abci.base._MetaPayload"></a>

## `_`MetaPayload Objects

```python
class _MetaPayload(ABCMeta)
```

Payload metaclass.

The purpose of this metaclass is to remember the association
between the type of payload and the payload class to build it.
This is necessary to recover the right payload class to instantiate
at decoding time.

Each class that has this class as metaclass must have a class
attribute 'transaction_type', which for simplicity is required
to be convertible to string, for serialization purposes.

<a id="packages.valory.skills.abstract_round_abci.base._MetaPayload.__new__"></a>

#### `__`new`__`

```python
def __new__(mcs, name: str, bases: Tuple, namespace: Dict, **kwargs: Any) -> Type
```

Create a new class object.

<a id="packages.valory.skills.abstract_round_abci.base.BaseTxPayload"></a>

## BaseTxPayload Objects

```python
class BaseTxPayload(ABC, metaclass=_MetaPayload)
```

This class represents a base class for transaction payload classes.

<a id="packages.valory.skills.abstract_round_abci.base.BaseTxPayload.__init__"></a>

#### `__`init`__`

```python
def __init__(sender: str, id_: Optional[str] = None, round_count: int = ROUND_COUNT_DEFAULT) -> None
```

Initialize a transaction payload.

**Arguments**:

- `sender`: the sender (Ethereum) address
- `id_`: the id of the transaction
- `round_count`: the count of the round in which the payload was sent

<a id="packages.valory.skills.abstract_round_abci.base.BaseTxPayload.round_count"></a>

#### round`_`count

```python
@property
def round_count() -> int
```

Get the round count.

<a id="packages.valory.skills.abstract_round_abci.base.BaseTxPayload.round_count"></a>

#### round`_`count

```python
@round_count.setter
def round_count(round_count: int) -> None
```

Set the round count.

<a id="packages.valory.skills.abstract_round_abci.base.BaseTxPayload.encode"></a>

#### encode

```python
def encode() -> bytes
```

Encode the payload.

<a id="packages.valory.skills.abstract_round_abci.base.BaseTxPayload.decode"></a>

#### decode

```python
@classmethod
def decode(cls, obj: bytes) -> "BaseTxPayload"
```

Decode the payload.

<a id="packages.valory.skills.abstract_round_abci.base.BaseTxPayload.from_json"></a>

#### from`_`json

```python
@classmethod
def from_json(cls, obj: Dict) -> "BaseTxPayload"
```

Decode the payload.

<a id="packages.valory.skills.abstract_round_abci.base.BaseTxPayload.json"></a>

#### json

```python
@property
def json() -> Dict
```

Get the JSON representation of the payload.

<a id="packages.valory.skills.abstract_round_abci.base.BaseTxPayload.data"></a>

#### data

```python
@property
def data() -> Dict
```

Get the dictionary data.

The returned dictionary is required to be used
as keyword constructor initializer, i.e. these two
should have the same effect:

    sender = "..."
    some_kwargs = {...}
    p1 = SomePayloadClass(sender, **some_kwargs)
    p2 = SomePayloadClass(sender, **p1.data)

**Returns**:

a dictionary which contains the payload data

<a id="packages.valory.skills.abstract_round_abci.base.BaseTxPayload.with_new_id"></a>

#### with`_`new`_`id

```python
def with_new_id() -> "BaseTxPayload"
```

Create a new payload with the same content but new id.

<a id="packages.valory.skills.abstract_round_abci.base.BaseTxPayload.__eq__"></a>

#### `__`eq`__`

```python
def __eq__(other: Any) -> bool
```

Check equality.

<a id="packages.valory.skills.abstract_round_abci.base.BaseTxPayload.__hash__"></a>

#### `__`hash`__`

```python
def __hash__() -> int
```

Hash the payload.

<a id="packages.valory.skills.abstract_round_abci.base.Transaction"></a>

## Transaction Objects

```python
class Transaction(ABC)
```

Class to represent a transaction for the ephemeral chain of a period.

<a id="packages.valory.skills.abstract_round_abci.base.Transaction.__init__"></a>

#### `__`init`__`

```python
def __init__(payload: BaseTxPayload, signature: str) -> None
```

Initialize a transaction object.

<a id="packages.valory.skills.abstract_round_abci.base.Transaction.encode"></a>

#### encode

```python
def encode() -> bytes
```

Encode the transaction.

<a id="packages.valory.skills.abstract_round_abci.base.Transaction.decode"></a>

#### decode

```python
@classmethod
def decode(cls, obj: bytes) -> "Transaction"
```

Decode the transaction.

<a id="packages.valory.skills.abstract_round_abci.base.Transaction.verify"></a>

#### verify

```python
def verify(ledger_id: str) -> None
```

Verify the signature is correct.

**Arguments**:

:raises: SignatureNotValidError: if the signature is not valid.
- `ledger_id`: the ledger id of the address

<a id="packages.valory.skills.abstract_round_abci.base.Transaction.__eq__"></a>

#### `__`eq`__`

```python
def __eq__(other: Any) -> bool
```

Check equality.

<a id="packages.valory.skills.abstract_round_abci.base.Block"></a>

## Block Objects

```python
class Block()
```

Class to represent (a subset of) data of a Tendermint block.

<a id="packages.valory.skills.abstract_round_abci.base.Block.__init__"></a>

#### `__`init`__`

```python
def __init__(header: Header, transactions: Sequence[Transaction]) -> None
```

Initialize the block.

<a id="packages.valory.skills.abstract_round_abci.base.Block.transactions"></a>

#### transactions

```python
@property
def transactions() -> Tuple[Transaction, ...]
```

Get the transactions.

<a id="packages.valory.skills.abstract_round_abci.base.Block.timestamp"></a>

#### timestamp

```python
@property
def timestamp() -> datetime.datetime
```

Get the block timestamp.

<a id="packages.valory.skills.abstract_round_abci.base.Blockchain"></a>

## Blockchain Objects

```python
class Blockchain()
```

Class to represent a (naive) Tendermint blockchain.

The consistency of the data in the blocks is guaranteed by Tendermint.

<a id="packages.valory.skills.abstract_round_abci.base.Blockchain.__init__"></a>

#### `__`init`__`

```python
def __init__(height_offset: int = 0) -> None
```

Initialize the blockchain.

<a id="packages.valory.skills.abstract_round_abci.base.Blockchain.add_block"></a>

#### add`_`block

```python
def add_block(block: Block) -> None
```

Add a block to the list.

<a id="packages.valory.skills.abstract_round_abci.base.Blockchain.height"></a>

#### height

```python
@property
def height() -> int
```

Get the height.

Tendermint's height starts from 1. A return value
    equal to 0 means empty blockchain.

**Returns**:

the height.

<a id="packages.valory.skills.abstract_round_abci.base.Blockchain.length"></a>

#### length

```python
@property
def length() -> int
```

Get the blockchain length.

<a id="packages.valory.skills.abstract_round_abci.base.Blockchain.blocks"></a>

#### blocks

```python
@property
def blocks() -> Tuple[Block, ...]
```

Get the blocks.

<a id="packages.valory.skills.abstract_round_abci.base.Blockchain.last_block"></a>

#### last`_`block

```python
@property
def last_block() -> Block
```

Returns the last stored block.

<a id="packages.valory.skills.abstract_round_abci.base.BlockBuilder"></a>

## BlockBuilder Objects

```python
class BlockBuilder()
```

Helper class to build a block.

<a id="packages.valory.skills.abstract_round_abci.base.BlockBuilder.__init__"></a>

#### `__`init`__`

```python
def __init__() -> None
```

Initialize the block builder.

<a id="packages.valory.skills.abstract_round_abci.base.BlockBuilder.reset"></a>

#### reset

```python
def reset() -> None
```

Reset the temporary data structures.

<a id="packages.valory.skills.abstract_round_abci.base.BlockBuilder.header"></a>

#### header

```python
@property
def header() -> Header
```

Get the block header.

**Returns**:

the block header

<a id="packages.valory.skills.abstract_round_abci.base.BlockBuilder.header"></a>

#### header

```python
@header.setter
def header(header: Header) -> None
```

Set the header.

<a id="packages.valory.skills.abstract_round_abci.base.BlockBuilder.transactions"></a>

#### transactions

```python
@property
def transactions() -> Tuple[Transaction, ...]
```

Get the sequence of transactions.

<a id="packages.valory.skills.abstract_round_abci.base.BlockBuilder.add_transaction"></a>

#### add`_`transaction

```python
def add_transaction(transaction: Transaction) -> None
```

Add a transaction.

<a id="packages.valory.skills.abstract_round_abci.base.BlockBuilder.get_block"></a>

#### get`_`block

```python
def get_block() -> Block
```

Get the block.

<a id="packages.valory.skills.abstract_round_abci.base.ConsensusParams"></a>

## ConsensusParams Objects

```python
class ConsensusParams()
```

Represent the consensus parameters.

<a id="packages.valory.skills.abstract_round_abci.base.ConsensusParams.__init__"></a>

#### `__`init`__`

```python
def __init__(max_participants: int)
```

Initialize the consensus parameters.

<a id="packages.valory.skills.abstract_round_abci.base.ConsensusParams.max_participants"></a>

#### max`_`participants

```python
@property
def max_participants() -> int
```

Get the maximum number of participants.

<a id="packages.valory.skills.abstract_round_abci.base.ConsensusParams.consensus_threshold"></a>

#### consensus`_`threshold

```python
@property
def consensus_threshold() -> int
```

Get the consensus threshold.

<a id="packages.valory.skills.abstract_round_abci.base.ConsensusParams.from_json"></a>

#### from`_`json

```python
@classmethod
def from_json(cls, obj: Dict) -> "ConsensusParams"
```

Get from JSON.

<a id="packages.valory.skills.abstract_round_abci.base.ConsensusParams.__eq__"></a>

#### `__`eq`__`

```python
def __eq__(other: Any) -> bool
```

Check equality.

<a id="packages.valory.skills.abstract_round_abci.base.AbciAppDB"></a>

## AbciAppDB Objects

```python
class AbciAppDB()
```

Class to represent all data replicated across agents.

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

To update the current period entry, just call update() on the class. The new values will be appended to the current list for each updated parameter.
To create a new period entry, call create() on the class. The new values will be stored in a new list for each updated parameter.

<a id="packages.valory.skills.abstract_round_abci.base.AbciAppDB.__init__"></a>

#### `__`init`__`

```python
def __init__(setup_data: Dict[str, List[Any]], cross_period_persisted_keys: Optional[List[str]] = None) -> None
```

Initialize the AbciApp database.

setup_data must be passed as a Dict[str, List[Any]] (the database internal format). The class method 'data_to_lists'
can be used to convert from Dict[str, Any] to Dict[str, List[Any]] before instantiating this class.

**Arguments**:

- `setup_data`: the setup data
- `cross_period_persisted_keys`: data keys that will be kept after a new period starts

<a id="packages.valory.skills.abstract_round_abci.base.AbciAppDB.setup_data"></a>

#### setup`_`data

```python
@property
def setup_data() -> Dict[str, Any]
```

Get the setup_data.

**Returns**:

the setup_data

<a id="packages.valory.skills.abstract_round_abci.base.AbciAppDB.reset_index"></a>

#### reset`_`index

```python
@property
def reset_index() -> int
```

Get the current reset index.

<a id="packages.valory.skills.abstract_round_abci.base.AbciAppDB.round_count"></a>

#### round`_`count

```python
@property
def round_count() -> int
```

Get the round count.

<a id="packages.valory.skills.abstract_round_abci.base.AbciAppDB.cross_period_persisted_keys"></a>

#### cross`_`period`_`persisted`_`keys

```python
@property
def cross_period_persisted_keys() -> List[str]
```

Keys in the database which are persistent across periods.

<a id="packages.valory.skills.abstract_round_abci.base.AbciAppDB.get"></a>

#### get

```python
def get(key: str, default: Any = VALUE_NOT_PROVIDED) -> Optional[Any]
```

Given a key, get its last for the current reset index.

<a id="packages.valory.skills.abstract_round_abci.base.AbciAppDB.get_strict"></a>

#### get`_`strict

```python
def get_strict(key: str) -> Any
```

Get a value from the data dictionary and raise if it is None.

<a id="packages.valory.skills.abstract_round_abci.base.AbciAppDB.update"></a>

#### update

```python
def update(**kwargs: Any) -> None
```

Update the current data.

<a id="packages.valory.skills.abstract_round_abci.base.AbciAppDB.create"></a>

#### create

```python
def create(**kwargs: List[Any]) -> None
```

Add a new entry to the data.

<a id="packages.valory.skills.abstract_round_abci.base.AbciAppDB.get_latest_from_reset_index"></a>

#### get`_`latest`_`from`_`reset`_`index

```python
def get_latest_from_reset_index(reset_index: int) -> Dict[str, Any]
```

Get the latest key-value pairs from the data dictionary for the specified period.

<a id="packages.valory.skills.abstract_round_abci.base.AbciAppDB.get_latest"></a>

#### get`_`latest

```python
def get_latest() -> Dict[str, Any]
```

Get the latest key-value pairs from the data dictionary for the current period.

<a id="packages.valory.skills.abstract_round_abci.base.AbciAppDB.increment_round_count"></a>

#### increment`_`round`_`count

```python
def increment_round_count() -> None
```

Increment the round count.

<a id="packages.valory.skills.abstract_round_abci.base.AbciAppDB.__repr__"></a>

#### `__`repr`__`

```python
def __repr__() -> str
```

Return a string representation of the data.

<a id="packages.valory.skills.abstract_round_abci.base.AbciAppDB.cleanup"></a>

#### cleanup

```python
def cleanup(cleanup_history_depth: int) -> None
```

Reset the db.

<a id="packages.valory.skills.abstract_round_abci.base.AbciAppDB.data_to_lists"></a>

#### data`_`to`_`lists

```python
@staticmethod
def data_to_lists(data: Dict[str, Any]) -> Dict[str, List[Any]]
```

Convert Dict[str, Any] to Dict[str, List[Any]].

<a id="packages.valory.skills.abstract_round_abci.base.BaseSynchronizedData"></a>

## BaseSynchronizedData Objects

```python
class BaseSynchronizedData()
```

Class to represent the synchronized data.

This is the relevant data constructed and replicated by the agents.

<a id="packages.valory.skills.abstract_round_abci.base.BaseSynchronizedData.__init__"></a>

#### `__`init`__`

```python
def __init__(db: AbciAppDB) -> None
```

Initialize the synchronized data.

<a id="packages.valory.skills.abstract_round_abci.base.BaseSynchronizedData.db"></a>

#### db

```python
@property
def db() -> AbciAppDB
```

Get DB.

<a id="packages.valory.skills.abstract_round_abci.base.BaseSynchronizedData.round_count"></a>

#### round`_`count

```python
@property
def round_count() -> int
```

Get the round count.

<a id="packages.valory.skills.abstract_round_abci.base.BaseSynchronizedData.period_count"></a>

#### period`_`count

```python
@property
def period_count() -> int
```

Get the period count.

Periods are executions between calls to AbciAppDB.create(), so as soon as it is called,
a new period begins. It is useful to have a logical subdivision of the FSM execution.
For example, if AbciAppDB.create() is called during reset, then a period will be the
execution between resets.

**Returns**:

the period count

<a id="packages.valory.skills.abstract_round_abci.base.BaseSynchronizedData.participants"></a>

#### participants

```python
@property
def participants() -> FrozenSet[str]
```

Get the participants.

<a id="packages.valory.skills.abstract_round_abci.base.BaseSynchronizedData.all_participants"></a>

#### all`_`participants

```python
@property
def all_participants() -> FrozenSet[str]
```

Get all the participants.

<a id="packages.valory.skills.abstract_round_abci.base.BaseSynchronizedData.sorted_participants"></a>

#### sorted`_`participants

```python
@property
def sorted_participants() -> Sequence[str]
```

Get the sorted participants' addresses.

The addresses are sorted according to their hexadecimal value;
this is the reason we use key=str.lower as comparator.

This property is useful when interacting with the Safe contract.

**Returns**:

the sorted participants' addresses

<a id="packages.valory.skills.abstract_round_abci.base.BaseSynchronizedData.nb_participants"></a>

#### nb`_`participants

```python
@property
def nb_participants() -> int
```

Get the number of participants.

<a id="packages.valory.skills.abstract_round_abci.base.BaseSynchronizedData.update"></a>

#### update

```python
def update(synchronized_data_class: Optional[Type] = None, **kwargs: Any, ,) -> "BaseSynchronizedData"
```

Copy and update the current data.

<a id="packages.valory.skills.abstract_round_abci.base.BaseSynchronizedData.create"></a>

#### create

```python
def create(synchronized_data_class: Optional[Type] = None, **kwargs: Any, ,) -> "BaseSynchronizedData"
```

Copy and update with new data.

<a id="packages.valory.skills.abstract_round_abci.base.BaseSynchronizedData.__repr__"></a>

#### `__`repr`__`

```python
def __repr__() -> str
```

Return a string representation of the data.

<a id="packages.valory.skills.abstract_round_abci.base.BaseSynchronizedData.keeper_randomness"></a>

#### keeper`_`randomness

```python
@property
def keeper_randomness() -> float
```

Get the keeper's random number [0-1].

<a id="packages.valory.skills.abstract_round_abci.base.BaseSynchronizedData.most_voted_randomness"></a>

#### most`_`voted`_`randomness

```python
@property
def most_voted_randomness() -> str
```

Get the most_voted_randomness.

<a id="packages.valory.skills.abstract_round_abci.base.BaseSynchronizedData.most_voted_keeper_address"></a>

#### most`_`voted`_`keeper`_`address

```python
@property
def most_voted_keeper_address() -> str
```

Get the most_voted_keeper_address.

<a id="packages.valory.skills.abstract_round_abci.base.BaseSynchronizedData.is_keeper_set"></a>

#### is`_`keeper`_`set

```python
@property
def is_keeper_set() -> bool
```

Check whether keeper is set.

<a id="packages.valory.skills.abstract_round_abci.base.BaseSynchronizedData.blacklisted_keepers"></a>

#### blacklisted`_`keepers

```python
@property
def blacklisted_keepers() -> Set[str]
```

Get the current cycle's blacklisted keepers who cannot submit a transaction.

<a id="packages.valory.skills.abstract_round_abci.base.BaseSynchronizedData.participant_to_selection"></a>

#### participant`_`to`_`selection

```python
@property
def participant_to_selection() -> Mapping
```

Check whether keeper is set.

<a id="packages.valory.skills.abstract_round_abci.base.BaseSynchronizedData.participant_to_randomness"></a>

#### participant`_`to`_`randomness

```python
@property
def participant_to_randomness() -> Mapping
```

Check whether keeper is set.

<a id="packages.valory.skills.abstract_round_abci.base.BaseSynchronizedData.participant_to_votes"></a>

#### participant`_`to`_`votes

```python
@property
def participant_to_votes() -> Mapping
```

Check whether keeper is set.

<a id="packages.valory.skills.abstract_round_abci.base.AbstractRound"></a>

## AbstractRound Objects

```python
class AbstractRound(Generic[EventType, TransactionType],  ABC)
```

This class represents an abstract round.

A round is a state of the FSM App execution. It usually involves
interactions between participants in the FSM App,
although this is not enforced at this level of abstraction.

Concrete classes must set:
- round_id: the identifier for the concrete round class;
- allowed_tx_type: the transaction type that is allowed for this round.

<a id="packages.valory.skills.abstract_round_abci.base.AbstractRound.__init__"></a>

#### `__`init`__`

```python
def __init__(synchronized_data: BaseSynchronizedData, consensus_params: ConsensusParams, previous_round_tx_type: Optional[TransactionType] = None) -> None
```

Initialize the round.

<a id="packages.valory.skills.abstract_round_abci.base.AbstractRound.synchronized_data"></a>

#### synchronized`_`data

```python
@property
def synchronized_data() -> BaseSynchronizedData
```

Get the synchronized data.

<a id="packages.valory.skills.abstract_round_abci.base.AbstractRound.check_transaction"></a>

#### check`_`transaction

```python
def check_transaction(transaction: Transaction) -> None
```

Check transaction against the current state.

**Arguments**:

- `transaction`: the transaction

<a id="packages.valory.skills.abstract_round_abci.base.AbstractRound.process_transaction"></a>

#### process`_`transaction

```python
def process_transaction(transaction: Transaction) -> None
```

Process a transaction.

By convention, the payload handler should be a method
of the class that is named '{payload_name}'.

**Arguments**:

- `transaction`: the transaction.

<a id="packages.valory.skills.abstract_round_abci.base.AbstractRound.end_block"></a>

#### end`_`block

```python
@abstractmethod
def end_block() -> Optional[Tuple[BaseSynchronizedData, Enum]]
```

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

<a id="packages.valory.skills.abstract_round_abci.base.AbstractRound.check_allowed_tx_type"></a>

#### check`_`allowed`_`tx`_`type

```python
def check_allowed_tx_type(transaction: Transaction) -> None
```

Check the transaction is of the allowed transaction type.

**Arguments**:

:raises: TransactionTypeNotRecognizedError if the transaction can be
         applied to the current state.
- `transaction`: the transaction

<a id="packages.valory.skills.abstract_round_abci.base.AbstractRound.check_majority_possible_with_new_voter"></a>

#### check`_`majority`_`possible`_`with`_`new`_`voter

```python
@classmethod
def check_majority_possible_with_new_voter(cls, votes_by_participant: Dict[Any, Any], new_voter: Any, new_vote: Any, nb_participants: int, exception_cls: Type[ABCIAppException] = ABCIAppException) -> None
```

Check that a Byzantine majority is achievable, once a new vote is added.

**Arguments**:

        before the new vote is added
                       check fails.
:raises: exception_cls: in case the check does not pass.
- `votes_by_participant`: a mapping from a participant to its vote,
- `new_voter`: the new voter
- `new_vote`: the new vote
- `nb_participants`: the total number of participants
- `exception_cls`: the class of the exception to raise in case the

<a id="packages.valory.skills.abstract_round_abci.base.AbstractRound.check_majority_possible"></a>

#### check`_`majority`_`possible

```python
@classmethod
def check_majority_possible(cls, votes_by_participant: Dict[Any, Any], nb_participants: int, exception_cls: Type[ABCIAppException] = ABCIAppException) -> None
```

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

**Arguments**:

                      check fails.
- `votes_by_participant`: a mapping from a participant to its vote
- `nb_participants`: the total number of participants
- `exception_cls`: the class of the exception to raise in case the

**Raises**:

- `exception_cls`: in case the check does not pass.

<a id="packages.valory.skills.abstract_round_abci.base.AbstractRound.is_majority_possible"></a>

#### is`_`majority`_`possible

```python
@classmethod
def is_majority_possible(cls, votes_by_participant: Dict[Any, Any], nb_participants: int) -> bool
```

Return true if a Byzantine majority is achievable, false otherwise.

**Arguments**:

- `votes_by_participant`: a mapping from a participant to its vote
- `nb_participants`: the total number of participants

**Returns**:

True if the majority is still possible, false otherwise.

<a id="packages.valory.skills.abstract_round_abci.base.AbstractRound.consensus_threshold"></a>

#### consensus`_`threshold

```python
@property
def consensus_threshold() -> int
```

Consensus threshold

<a id="packages.valory.skills.abstract_round_abci.base.AbstractRound.check_payload"></a>

#### check`_`payload

```python
@abstractmethod
def check_payload(payload: BaseTxPayload) -> None
```

Check payload.

<a id="packages.valory.skills.abstract_round_abci.base.AbstractRound.process_payload"></a>

#### process`_`payload

```python
@abstractmethod
def process_payload(payload: BaseTxPayload) -> None
```

Process payload.

<a id="packages.valory.skills.abstract_round_abci.base.DegenerateRound"></a>

## DegenerateRound Objects

```python
class DegenerateRound(AbstractRound)
```

This class represents the finished round during operation.

It is a sink round.

<a id="packages.valory.skills.abstract_round_abci.base.DegenerateRound.check_payload"></a>

#### check`_`payload

```python
def check_payload(payload: BaseTxPayload) -> None
```

Check payload.

<a id="packages.valory.skills.abstract_round_abci.base.DegenerateRound.process_payload"></a>

#### process`_`payload

```python
def process_payload(payload: BaseTxPayload) -> None
```

Process payload.

<a id="packages.valory.skills.abstract_round_abci.base.DegenerateRound.end_block"></a>

#### end`_`block

```python
def end_block() -> Optional[Tuple[BaseSynchronizedData, Enum]]
```

End block.

<a id="packages.valory.skills.abstract_round_abci.base.CollectionRound"></a>

## CollectionRound Objects

```python
class CollectionRound(AbstractRound)
```

CollectionRound.

This class represents abstract logic for collection based rounds where
the round object needs to collect data from different agents. The data
might for example be from a voting round or estimation round.

<a id="packages.valory.skills.abstract_round_abci.base.CollectionRound.__init__"></a>

#### `__`init`__`

```python
def __init__(*args: Any, **kwargs: Any)
```

Initialize the collection round.

<a id="packages.valory.skills.abstract_round_abci.base.CollectionRound.payloads"></a>

#### payloads

```python
@property
def payloads() -> List[BaseTxPayload]
```

Get all agent payloads

<a id="packages.valory.skills.abstract_round_abci.base.CollectionRound.payloads_count"></a>

#### payloads`_`count

```python
@property
def payloads_count() -> Counter
```

Get count of payload attributes

<a id="packages.valory.skills.abstract_round_abci.base.CollectionRound.process_payload"></a>

#### process`_`payload

```python
def process_payload(payload: BaseTxPayload) -> None
```

Process payload.

<a id="packages.valory.skills.abstract_round_abci.base.CollectionRound.check_payload"></a>

#### check`_`payload

```python
def check_payload(payload: BaseTxPayload) -> None
```

Check Payload

<a id="packages.valory.skills.abstract_round_abci.base._CollectUntilAllRound"></a>

## `_`CollectUntilAllRound Objects

```python
class _CollectUntilAllRound(CollectionRound,  ABC)
```

_CollectUntilAllRound

This class represents logic for when rounds need to collect payloads from all agents.

This round should only be used for registration of new agents.

<a id="packages.valory.skills.abstract_round_abci.base._CollectUntilAllRound.check_payload"></a>

#### check`_`payload

```python
def check_payload(payload: BaseTxPayload) -> None
```

Check Payload

<a id="packages.valory.skills.abstract_round_abci.base._CollectUntilAllRound.process_payload"></a>

#### process`_`payload

```python
def process_payload(payload: BaseTxPayload) -> None
```

Process payload.

<a id="packages.valory.skills.abstract_round_abci.base._CollectUntilAllRound.collection_threshold_reached"></a>

#### collection`_`threshold`_`reached

```python
@property
def collection_threshold_reached() -> bool
```

Check that the collection threshold has been reached.

<a id="packages.valory.skills.abstract_round_abci.base.CollectDifferentUntilAllRound"></a>

## CollectDifferentUntilAllRound Objects

```python
class CollectDifferentUntilAllRound(_CollectUntilAllRound,  ABC)
```

CollectDifferentUntilAllRound

This class represents logic for rounds where a round needs to collect
different payloads from each agent.

This round should only be used for registration of new agents when there is synchronization of the db.

<a id="packages.valory.skills.abstract_round_abci.base.CollectDifferentUntilAllRound.check_payload"></a>

#### check`_`payload

```python
def check_payload(payload: BaseTxPayload) -> None
```

Check Payload

<a id="packages.valory.skills.abstract_round_abci.base.CollectSameUntilAllRound"></a>

## CollectSameUntilAllRound Objects

```python
class CollectSameUntilAllRound(_CollectUntilAllRound,  ABC)
```

This class represents logic for when a round needs to collect the same payload from all the agents.

This round should only be used for registration of new agents when there is no synchronization of the db.

<a id="packages.valory.skills.abstract_round_abci.base.CollectSameUntilAllRound.check_payload"></a>

#### check`_`payload

```python
def check_payload(payload: BaseTxPayload) -> None
```

Check Payload

<a id="packages.valory.skills.abstract_round_abci.base.CollectSameUntilAllRound.common_payload"></a>

#### common`_`payload

```python
@property
def common_payload() -> Any
```

Get the common payload among the agents.

<a id="packages.valory.skills.abstract_round_abci.base.CollectSameUntilThresholdRound"></a>

## CollectSameUntilThresholdRound Objects

```python
class CollectSameUntilThresholdRound(CollectionRound)
```

CollectSameUntilThresholdRound

This class represents logic for rounds where a round needs to collect
same payload from k of n agents.

<a id="packages.valory.skills.abstract_round_abci.base.CollectSameUntilThresholdRound.threshold_reached"></a>

#### threshold`_`reached

```python
@property
def threshold_reached() -> bool
```

Check if the threshold has been reached.

<a id="packages.valory.skills.abstract_round_abci.base.CollectSameUntilThresholdRound.most_voted_payload"></a>

#### most`_`voted`_`payload

```python
@property
def most_voted_payload() -> Any
```

Get the most voted payload.

<a id="packages.valory.skills.abstract_round_abci.base.CollectSameUntilThresholdRound.end_block"></a>

#### end`_`block

```python
def end_block() -> Optional[Tuple[BaseSynchronizedData, Enum]]
```

Process the end of the block.

<a id="packages.valory.skills.abstract_round_abci.base.OnlyKeeperSendsRound"></a>

## OnlyKeeperSendsRound Objects

```python
class OnlyKeeperSendsRound(AbstractRound)
```

OnlyKeeperSendsRound

This class represents logic for rounds where only one agent sends a
payload

<a id="packages.valory.skills.abstract_round_abci.base.OnlyKeeperSendsRound.__init__"></a>

#### `__`init`__`

```python
def __init__(*args: Any, **kwargs: Any)
```

Initialize the 'collect-observation' round.

<a id="packages.valory.skills.abstract_round_abci.base.OnlyKeeperSendsRound.process_payload"></a>

#### process`_`payload

```python
def process_payload(payload: BaseTxPayload) -> None
```

Handle a deploy safe payload.

<a id="packages.valory.skills.abstract_round_abci.base.OnlyKeeperSendsRound.check_payload"></a>

#### check`_`payload

```python
def check_payload(payload: BaseTxPayload) -> None
```

Check a deploy safe payload can be applied to the current state.

<a id="packages.valory.skills.abstract_round_abci.base.OnlyKeeperSendsRound.has_keeper_sent_payload"></a>

#### has`_`keeper`_`sent`_`payload

```python
@property
def has_keeper_sent_payload() -> bool
```

Check if keeper has sent the payload.

<a id="packages.valory.skills.abstract_round_abci.base.OnlyKeeperSendsRound.end_block"></a>

#### end`_`block

```python
def end_block() -> Optional[Tuple[BaseSynchronizedData, Enum]]
```

Process the end of the block.

<a id="packages.valory.skills.abstract_round_abci.base.VotingRound"></a>

## VotingRound Objects

```python
class VotingRound(CollectionRound)
```

VotingRound

This class represents logic for rounds where a round needs votes from
agents, pass if k same votes of n agents

<a id="packages.valory.skills.abstract_round_abci.base.VotingRound.vote_count"></a>

#### vote`_`count

```python
@property
def vote_count() -> Counter
```

Get agent payload vote count

<a id="packages.valory.skills.abstract_round_abci.base.VotingRound.positive_vote_threshold_reached"></a>

#### positive`_`vote`_`threshold`_`reached

```python
@property
def positive_vote_threshold_reached() -> bool
```

Check that the vote threshold has been reached.

<a id="packages.valory.skills.abstract_round_abci.base.VotingRound.negative_vote_threshold_reached"></a>

#### negative`_`vote`_`threshold`_`reached

```python
@property
def negative_vote_threshold_reached() -> bool
```

Check that the vote threshold has been reached.

<a id="packages.valory.skills.abstract_round_abci.base.VotingRound.none_vote_threshold_reached"></a>

#### none`_`vote`_`threshold`_`reached

```python
@property
def none_vote_threshold_reached() -> bool
```

Check that the vote threshold has been reached.

<a id="packages.valory.skills.abstract_round_abci.base.VotingRound.end_block"></a>

#### end`_`block

```python
def end_block() -> Optional[Tuple[BaseSynchronizedData, Enum]]
```

Process the end of the block.

<a id="packages.valory.skills.abstract_round_abci.base.CollectDifferentUntilThresholdRound"></a>

## CollectDifferentUntilThresholdRound Objects

```python
class CollectDifferentUntilThresholdRound(CollectionRound)
```

CollectDifferentUntilThresholdRound

This class represents logic for rounds where a round needs to collect
different payloads from k of n agents

<a id="packages.valory.skills.abstract_round_abci.base.CollectDifferentUntilThresholdRound.collection_threshold_reached"></a>

#### collection`_`threshold`_`reached

```python
@property
def collection_threshold_reached() -> bool
```

Check if the threshold has been reached.

<a id="packages.valory.skills.abstract_round_abci.base.CollectDifferentUntilThresholdRound.end_block"></a>

#### end`_`block

```python
def end_block() -> Optional[Tuple[BaseSynchronizedData, Enum]]
```

Process the end of the block.

<a id="packages.valory.skills.abstract_round_abci.base.CollectNonEmptyUntilThresholdRound"></a>

## CollectNonEmptyUntilThresholdRound Objects

```python
class CollectNonEmptyUntilThresholdRound(CollectDifferentUntilThresholdRound)
```

Collect all the data among agents.

This class represents logic for rounds where we need to collect
payloads from each agent which will contain optional, different data and only keep the non-empty.

This round may be used for cases that we want to collect all the agent's data, such as late-arriving messages.

<a id="packages.valory.skills.abstract_round_abci.base.CollectNonEmptyUntilThresholdRound.end_block"></a>

#### end`_`block

```python
def end_block() -> Optional[Tuple[BaseSynchronizedData, Enum]]
```

Process the end of the block.

<a id="packages.valory.skills.abstract_round_abci.base.TimeoutEvent"></a>

## TimeoutEvent Objects

```python
@dataclass(order=True)
class TimeoutEvent(Generic[EventType])
```

Timeout event.

<a id="packages.valory.skills.abstract_round_abci.base.Timeouts"></a>

## Timeouts Objects

```python
class Timeouts(Generic[EventType])
```

Class to keep track of pending timeouts.

<a id="packages.valory.skills.abstract_round_abci.base.Timeouts.__init__"></a>

#### `__`init`__`

```python
def __init__() -> None
```

Initialize.

<a id="packages.valory.skills.abstract_round_abci.base.Timeouts.size"></a>

#### size

```python
@property
def size() -> int
```

Get the size of the timeout queue.

<a id="packages.valory.skills.abstract_round_abci.base.Timeouts.add_timeout"></a>

#### add`_`timeout

```python
def add_timeout(deadline: datetime.datetime, event: EventType) -> int
```

Add a timeout.

<a id="packages.valory.skills.abstract_round_abci.base.Timeouts.cancel_timeout"></a>

#### cancel`_`timeout

```python
def cancel_timeout(entry_count: int) -> None
```

Remove a timeout.

**Arguments**:

:raises: KeyError: if the entry count is not found.
- `entry_count`: the entry id to remove.

<a id="packages.valory.skills.abstract_round_abci.base.Timeouts.pop_earliest_cancelled_timeouts"></a>

#### pop`_`earliest`_`cancelled`_`timeouts

```python
def pop_earliest_cancelled_timeouts() -> None
```

Pop earliest cancelled timeouts.

<a id="packages.valory.skills.abstract_round_abci.base.Timeouts.get_earliest_timeout"></a>

#### get`_`earliest`_`timeout

```python
def get_earliest_timeout() -> Tuple[datetime.datetime, Any]
```

Get the earliest timeout-event pair.

<a id="packages.valory.skills.abstract_round_abci.base.Timeouts.pop_timeout"></a>

#### pop`_`timeout

```python
def pop_timeout() -> Tuple[datetime.datetime, Any]
```

Remove and return the earliest timeout-event pair.

<a id="packages.valory.skills.abstract_round_abci.base._MetaAbciApp"></a>

## `_`MetaAbciApp Objects

```python
class _MetaAbciApp(ABCMeta)
```

A metaclass that validates AbciApp's attributes.

<a id="packages.valory.skills.abstract_round_abci.base._MetaAbciApp.__new__"></a>

#### `__`new`__`

```python
def __new__(mcs, name: str, bases: Tuple, namespace: Dict, **kwargs: Any) -> Type
```

Initialize the class.

<a id="packages.valory.skills.abstract_round_abci.base.AbciApp"></a>

## AbciApp Objects

```python
class AbciApp(
    Generic[EventType],  ABC, metaclass=_MetaAbciApp)
```

Base class for ABCI apps.

Concrete classes of this class implement the ABCI App.

<a id="packages.valory.skills.abstract_round_abci.base.AbciApp.__init__"></a>

#### `__`init`__`

```python
def __init__(synchronized_data: BaseSynchronizedData, consensus_params: ConsensusParams, logger: logging.Logger)
```

Initialize the AbciApp.

<a id="packages.valory.skills.abstract_round_abci.base.AbciApp.synchronized_data"></a>

#### synchronized`_`data

```python
@property
def synchronized_data() -> BaseSynchronizedData
```

Return the current synchronized data.

<a id="packages.valory.skills.abstract_round_abci.base.AbciApp.reset_index"></a>

#### reset`_`index

```python
@property
def reset_index() -> int
```

Return the reset index.

<a id="packages.valory.skills.abstract_round_abci.base.AbciApp.get_all_rounds"></a>

#### get`_`all`_`rounds

```python
@classmethod
def get_all_rounds(cls) -> Set[AppState]
```

Get all the round states.

<a id="packages.valory.skills.abstract_round_abci.base.AbciApp.get_all_events"></a>

#### get`_`all`_`events

```python
@classmethod
def get_all_events(cls) -> Set[EventType]
```

Get all the events.

<a id="packages.valory.skills.abstract_round_abci.base.AbciApp.get_all_round_classes"></a>

#### get`_`all`_`round`_`classes

```python
@classmethod
def get_all_round_classes(cls) -> Set[AppState]
```

Get all round classes.

<a id="packages.valory.skills.abstract_round_abci.base.AbciApp.last_timestamp"></a>

#### last`_`timestamp

```python
@property
def last_timestamp() -> datetime.datetime
```

Get last timestamp.

<a id="packages.valory.skills.abstract_round_abci.base.AbciApp.setup"></a>

#### setup

```python
def setup() -> None
```

Set up the behaviour.

<a id="packages.valory.skills.abstract_round_abci.base.AbciApp.current_round"></a>

#### current`_`round

```python
@property
def current_round() -> AbstractRound
```

Get the current round.

<a id="packages.valory.skills.abstract_round_abci.base.AbciApp.current_round_id"></a>

#### current`_`round`_`id

```python
@property
def current_round_id() -> Optional[str]
```

Get the current round id.

<a id="packages.valory.skills.abstract_round_abci.base.AbciApp.current_round_height"></a>

#### current`_`round`_`height

```python
@property
def current_round_height() -> int
```

Get the current round height.

<a id="packages.valory.skills.abstract_round_abci.base.AbciApp.last_round_id"></a>

#### last`_`round`_`id

```python
@property
def last_round_id() -> Optional[str]
```

Get the last round id.

<a id="packages.valory.skills.abstract_round_abci.base.AbciApp.is_finished"></a>

#### is`_`finished

```python
@property
def is_finished() -> bool
```

Check whether the AbciApp execution has finished.

<a id="packages.valory.skills.abstract_round_abci.base.AbciApp.latest_result"></a>

#### latest`_`result

```python
@property
def latest_result() -> Optional[BaseSynchronizedData]
```

Get the latest result of the round.

<a id="packages.valory.skills.abstract_round_abci.base.AbciApp.check_transaction"></a>

#### check`_`transaction

```python
def check_transaction(transaction: Transaction) -> None
```

Check a transaction.

Forward the call to the current round object.

**Arguments**:

- `transaction`: the transaction.

<a id="packages.valory.skills.abstract_round_abci.base.AbciApp.process_transaction"></a>

#### process`_`transaction

```python
def process_transaction(transaction: Transaction) -> None
```

Process a transaction.

Forward the call to the current round object.

**Arguments**:

- `transaction`: the transaction.

<a id="packages.valory.skills.abstract_round_abci.base.AbciApp.process_event"></a>

#### process`_`event

```python
def process_event(event: EventType, result: Optional[BaseSynchronizedData] = None) -> None
```

Process a round event.

<a id="packages.valory.skills.abstract_round_abci.base.AbciApp.update_time"></a>

#### update`_`time

```python
def update_time(timestamp: datetime.datetime) -> None
```

Observe timestamp from last block.

**Arguments**:

- `timestamp`: the latest block's timestamp.

<a id="packages.valory.skills.abstract_round_abci.base.AbciApp.cleanup"></a>

#### cleanup

```python
def cleanup(cleanup_history_depth: int) -> None
```

Clear data.

<a id="packages.valory.skills.abstract_round_abci.base.RoundSequence"></a>

## RoundSequence Objects

```python
class RoundSequence()
```

This class represents a sequence of rounds

It is a generic class that keeps track of the current round
of the consensus period. It receives 'deliver_tx' requests
from the ABCI handlers and forwards them to the current
active round instance, which implements the ABCI app logic.
It also schedules the next round (if any) whenever a round terminates.

<a id="packages.valory.skills.abstract_round_abci.base.RoundSequence.__init__"></a>

#### `__`init`__`

```python
def __init__(abci_app_cls: Type[AbciApp])
```

Initialize the round.

<a id="packages.valory.skills.abstract_round_abci.base.RoundSequence.setup"></a>

#### setup

```python
def setup(*args: Any, **kwargs: Any) -> None
```

Set up the round sequence.

**Arguments**:

- `args`: the arguments to pass to the round constructor.
- `kwargs`: the keyword-arguments to pass to the round constructor.

<a id="packages.valory.skills.abstract_round_abci.base.RoundSequence.start_sync"></a>

#### start`_`sync

```python
def start_sync() -> None
```

Set `_syncing_up` flag to true.

if the _syncing_up flag is set to true, the `async_act` method won't be executed. For more details refer to
https://github.com/valory-xyz/open-autonomy/issues/247#issuecomment-1012268656

<a id="packages.valory.skills.abstract_round_abci.base.RoundSequence.end_sync"></a>

#### end`_`sync

```python
def end_sync() -> None
```

Set `_syncing_up` flag to false.

<a id="packages.valory.skills.abstract_round_abci.base.RoundSequence.syncing_up"></a>

#### syncing`_`up

```python
@property
def syncing_up() -> bool
```

Return if the app is in sync mode.

<a id="packages.valory.skills.abstract_round_abci.base.RoundSequence.abci_app"></a>

#### abci`_`app

```python
@property
def abci_app() -> AbciApp
```

Get the AbciApp.

<a id="packages.valory.skills.abstract_round_abci.base.RoundSequence.height"></a>

#### height

```python
@property
def height() -> int
```

Get the height.

<a id="packages.valory.skills.abstract_round_abci.base.RoundSequence.is_finished"></a>

#### is`_`finished

```python
@property
def is_finished() -> bool
```

Check if a round sequence has finished.

<a id="packages.valory.skills.abstract_round_abci.base.RoundSequence.check_is_finished"></a>

#### check`_`is`_`finished

```python
def check_is_finished() -> None
```

Check if a round sequence has finished.

<a id="packages.valory.skills.abstract_round_abci.base.RoundSequence.current_round"></a>

#### current`_`round

```python
@property
def current_round() -> AbstractRound
```

Get current round.

<a id="packages.valory.skills.abstract_round_abci.base.RoundSequence.current_round_id"></a>

#### current`_`round`_`id

```python
@property
def current_round_id() -> Optional[str]
```

Get the current round id.

<a id="packages.valory.skills.abstract_round_abci.base.RoundSequence.current_round_height"></a>

#### current`_`round`_`height

```python
@property
def current_round_height() -> int
```

Get the current round height.

<a id="packages.valory.skills.abstract_round_abci.base.RoundSequence.last_round_id"></a>

#### last`_`round`_`id

```python
@property
def last_round_id() -> Optional[str]
```

Get the last round id.

<a id="packages.valory.skills.abstract_round_abci.base.RoundSequence.last_timestamp"></a>

#### last`_`timestamp

```python
@property
def last_timestamp() -> datetime.datetime
```

Get the last timestamp.

<a id="packages.valory.skills.abstract_round_abci.base.RoundSequence.last_round_transition_timestamp"></a>

#### last`_`round`_`transition`_`timestamp

```python
@property
def last_round_transition_timestamp() -> datetime.datetime
```

Returns the timestamp for last round transition.

<a id="packages.valory.skills.abstract_round_abci.base.RoundSequence.last_round_transition_height"></a>

#### last`_`round`_`transition`_`height

```python
@property
def last_round_transition_height() -> int
```

Returns the height for last round transition.

<a id="packages.valory.skills.abstract_round_abci.base.RoundSequence.last_round_transition_root_hash"></a>

#### last`_`round`_`transition`_`root`_`hash

```python
@property
def last_round_transition_root_hash() -> bytes
```

Returns the root hash for last round transition.

<a id="packages.valory.skills.abstract_round_abci.base.RoundSequence.last_round_transition_tm_height"></a>

#### last`_`round`_`transition`_`tm`_`height

```python
@property
def last_round_transition_tm_height() -> int
```

Returns the Tendermint height for last round transition.

<a id="packages.valory.skills.abstract_round_abci.base.RoundSequence.latest_synchronized_data"></a>

#### latest`_`synchronized`_`data

```python
@property
def latest_synchronized_data() -> BaseSynchronizedData
```

Get the latest synchronized_data.

<a id="packages.valory.skills.abstract_round_abci.base.RoundSequence.root_hash"></a>

#### root`_`hash

```python
@property
def root_hash() -> bytes
```

Get the Merkle root hash of the application state.

Create an app hash that always increases in order to avoid conflicts between resets.
Eventually, we do not necessarily need to have a value that increases, but we have to generate a hash that
is always different among the resets, since our abci's state is different even thought we have reset the chain!
For example, if we are in height 11, reset and then reach height 11 again, if we end up using the same hash
at height 11 between the resets, then this is problematic.

**Returns**:

the root hash to be included as the Header.AppHash in the next block.

<a id="packages.valory.skills.abstract_round_abci.base.RoundSequence.tm_height"></a>

#### tm`_`height

```python
@property
def tm_height() -> int
```

Get Tendermint's current height.

<a id="packages.valory.skills.abstract_round_abci.base.RoundSequence.tm_height"></a>

#### tm`_`height

```python
@tm_height.setter
def tm_height(_tm_height: int) -> None
```

Set Tendermint's current height.

<a id="packages.valory.skills.abstract_round_abci.base.RoundSequence.init_chain"></a>

#### init`_`chain

```python
def init_chain(initial_height: int) -> None
```

Init chain.

<a id="packages.valory.skills.abstract_round_abci.base.RoundSequence.begin_block"></a>

#### begin`_`block

```python
def begin_block(header: Header) -> None
```

Begin block.

<a id="packages.valory.skills.abstract_round_abci.base.RoundSequence.deliver_tx"></a>

#### deliver`_`tx

```python
def deliver_tx(transaction: Transaction) -> None
```

Deliver a transaction.

Appends the transaction to build the block on 'end_block' later.

**Arguments**:

:raises:  an Error otherwise.
- `transaction`: the transaction.

<a id="packages.valory.skills.abstract_round_abci.base.RoundSequence.end_block"></a>

#### end`_`block

```python
def end_block() -> None
```

Process the 'end_block' request.

<a id="packages.valory.skills.abstract_round_abci.base.RoundSequence.commit"></a>

#### commit

```python
def commit() -> None
```

Process the 'commit' request.

<a id="packages.valory.skills.abstract_round_abci.base.RoundSequence.reset_blockchain"></a>

#### reset`_`blockchain

```python
def reset_blockchain(is_replay: bool = False) -> None
```

Reset blockchain after tendermint reset.

