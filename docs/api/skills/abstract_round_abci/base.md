<a id="packages.valory.skills.abstract_round_abci.base"></a>

# packages.valory.skills.abstract`_`round`_`abci.base

This module contains the base classes for the models classes of the skill.

<a id="packages.valory.skills.abstract_round_abci.base.get_name"></a>

#### get`_`name

```python
def get_name(prop: Any) -> str
```

Get the name of a property.

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

<a id="packages.valory.skills.abstract_round_abci.base.AbstractRoundInternalError"></a>

## AbstractRoundInternalError Objects

```python
class AbstractRoundInternalError(ABCIAppException)
```

Internal error due to a bad implementation of the AbstractRound.

<a id="packages.valory.skills.abstract_round_abci.base.AbstractRoundInternalError.__init__"></a>

#### `__`init`__`

```python
def __init__(message: str, *args: Any) -> None
```

Initialize the error object.

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

<a id="packages.valory.skills.abstract_round_abci.base._MetaPayload.__new__"></a>

#### `__`new`__`

```python
def __new__(mcs, name: str, bases: Tuple, namespace: Dict,
            **kwargs: Any) -> Type
```

Create a new class object.

<a id="packages.valory.skills.abstract_round_abci.base.BaseTxPayload"></a>

## BaseTxPayload Objects

```python
@dataclass(frozen=True)
class BaseTxPayload(metaclass=_MetaPayload)
```

This class represents a base class for transaction payload classes.

<a id="packages.valory.skills.abstract_round_abci.base.BaseTxPayload.data"></a>

#### data

```python
@property
def data() -> Dict[str, Any]
```

Data

<a id="packages.valory.skills.abstract_round_abci.base.BaseTxPayload.values"></a>

#### values

```python
@property
def values() -> Tuple[Any, ...]
```

Data

<a id="packages.valory.skills.abstract_round_abci.base.BaseTxPayload.json"></a>

#### json

```python
@property
def json() -> Dict[str, Any]
```

Json

<a id="packages.valory.skills.abstract_round_abci.base.BaseTxPayload.from_json"></a>

#### from`_`json

```python
@classmethod
def from_json(cls, obj: Dict) -> "BaseTxPayload"
```

Decode the payload.

<a id="packages.valory.skills.abstract_round_abci.base.BaseTxPayload.with_new_id"></a>

#### with`_`new`_`id

```python
def with_new_id() -> "BaseTxPayload"
```

Create a new payload with the same content but new id.

<a id="packages.valory.skills.abstract_round_abci.base.BaseTxPayload.encode"></a>

#### encode

```python
def encode() -> bytes
```

Encode

<a id="packages.valory.skills.abstract_round_abci.base.BaseTxPayload.decode"></a>

#### decode

```python
@classmethod
def decode(cls, obj: bytes) -> "BaseTxPayload"
```

Decode

<a id="packages.valory.skills.abstract_round_abci.base.Transaction"></a>

## Transaction Objects

```python
@dataclass(frozen=True)
class Transaction(ABC)
```

Class to represent a transaction for the ephemeral chain of a period.

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

- `ledger_id`: the ledger id of the address

**Raises**:

- `None`: SignatureNotValidError: if the signature is not valid.

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
def __init__(height_offset: int = 0, is_init: bool = True) -> None
```

Initialize the blockchain.

<a id="packages.valory.skills.abstract_round_abci.base.Blockchain.is_init"></a>

#### is`_`init

```python
@property
def is_init() -> bool
```

Returns true if the blockchain is initialized.

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

__Adding and removing data from the current period__

--------------------------------------------------
To update the current period entry, just call update() on the class. The new values will be appended to the current list for each updated parameter.

To clean up old data from the current period entry, call cleanup_current_histories(cleanup_history_depth_current), where cleanup_history_depth_current
is the amount of data that you want to keep after the cleanup. The newest cleanup_history_depth_current values will be kept for each parameter in the DB.

__Creating and removing old periods__

-----------------------------------
To create a new period entry, call create() on the class. The new values will be stored in a new list for each updated parameter.

To remove old periods, call cleanup(cleanup_history_depth, [cleanup_history_depth_current]), where cleanup_history_depth is the amount of periods
that you want to keep after the cleanup. The newest cleanup_history_depth periods will be kept. If you also specify cleanup_history_depth_current,
cleanup_current_histories will be also called (see previous point).

The parameters cleanup_history_depth and cleanup_history_depth_current can also be configured in skill.yaml so they are used automatically
when the cleanup method is called from AbciApp.cleanup().

__Memory warning__

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

<a id="packages.valory.skills.abstract_round_abci.base.AbciAppDB.__init__"></a>

#### `__`init`__`

```python
def __init__(setup_data: Dict[str, List[Any]],
             cross_period_persisted_keys: Optional[FrozenSet[str]] = None,
             logger: Optional[logging.Logger] = None) -> None
```

Initialize the AbciApp database.

setup_data must be passed as a Dict[str, List[Any]] (the database internal format).
The staticmethod 'data_to_lists' can be used to convert from Dict[str, Any] to Dict[str, List[Any]]
before instantiating this class.

**Arguments**:

- `setup_data`: the setup data
- `cross_period_persisted_keys`: data keys that will be kept after a new period starts
- `logger`: the logger of the abci app

<a id="packages.valory.skills.abstract_round_abci.base.AbciAppDB.normalize"></a>

#### normalize

```python
@staticmethod
def normalize(value: Any) -> str
```

Attempt to normalize a non-primitive type to insert it into the db.

<a id="packages.valory.skills.abstract_round_abci.base.AbciAppDB.setup_data"></a>

#### setup`_`data

```python
@property
def setup_data() -> Dict[str, Any]
```

Get the setup_data without entries which have empty values.

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

<a id="packages.valory.skills.abstract_round_abci.base.AbciAppDB.round_count"></a>

#### round`_`count

```python
@round_count.setter
def round_count(round_count: int) -> None
```

Set the round count.

<a id="packages.valory.skills.abstract_round_abci.base.AbciAppDB.cross_period_persisted_keys"></a>

#### cross`_`period`_`persisted`_`keys

```python
@property
def cross_period_persisted_keys() -> FrozenSet[str]
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

<a id="packages.valory.skills.abstract_round_abci.base.AbciAppDB.validate"></a>

#### validate

```python
@staticmethod
def validate(data: Any) -> None
```

Validate if the given data are json serializable and therefore can be accepted into the database.

**Arguments**:

- `data`: the data to check.

**Raises**:

- `ABCIAppInternalError`: If the data are not serializable.

<a id="packages.valory.skills.abstract_round_abci.base.AbciAppDB.update"></a>

#### update

```python
def update(**kwargs: Any) -> None
```

Update the current data.

<a id="packages.valory.skills.abstract_round_abci.base.AbciAppDB.create"></a>

#### create

```python
def create(**kwargs: Any) -> None
```

Add a new entry to the data.

Passes automatically the values of the `cross_period_persisted_keys` to the next period.

**Arguments**:

- `kwargs`: keyword arguments

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
def cleanup(cleanup_history_depth: int,
            cleanup_history_depth_current: Optional[int] = None) -> None
```

Reset the db, keeping only the latest entries (periods).

If cleanup_history_depth_current has been also set, also clear oldest historic values in the current entry.

**Arguments**:

- `cleanup_history_depth`: depth to clean up history
- `cleanup_history_depth_current`: whether or not to clean up current entry too.

<a id="packages.valory.skills.abstract_round_abci.base.AbciAppDB.cleanup_current_histories"></a>

#### cleanup`_`current`_`histories

```python
def cleanup_current_histories(cleanup_history_depth_current: int) -> None
```

Reset the parameter histories for the current entry (period), keeping only the latest values for each parameter.

<a id="packages.valory.skills.abstract_round_abci.base.AbciAppDB.serialize"></a>

#### serialize

```python
def serialize() -> str
```

Serialize the data of the database to a string.

<a id="packages.valory.skills.abstract_round_abci.base.AbciAppDB.sync"></a>

#### sync

```python
def sync(serialized_data: str) -> None
```

Synchronize the data using a serialized object.

**Arguments**:

- `serialized_data`: the serialized data to use in order to sync the db.

**Raises**:

- `ABCIAppInternalError`: if the given data cannot be deserialized.

<a id="packages.valory.skills.abstract_round_abci.base.AbciAppDB.hash"></a>

#### hash

```python
def hash() -> bytes
```

Create a hash of the data.

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

Get the currently active participants.

<a id="packages.valory.skills.abstract_round_abci.base.BaseSynchronizedData.all_participants"></a>

#### all`_`participants

```python
@property
def all_participants() -> FrozenSet[str]
```

Get all registered participants.

<a id="packages.valory.skills.abstract_round_abci.base.BaseSynchronizedData.max_participants"></a>

#### max`_`participants

```python
@property
def max_participants() -> int
```

Get the number of all the participants.

<a id="packages.valory.skills.abstract_round_abci.base.BaseSynchronizedData.consensus_threshold"></a>

#### consensus`_`threshold

```python
@property
def consensus_threshold() -> int
```

Get the consensus threshold.

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

<a id="packages.valory.skills.abstract_round_abci.base.BaseSynchronizedData.slashing_config"></a>

#### slashing`_`config

```python
@property
def slashing_config() -> str
```

Get the slashing configuration.

<a id="packages.valory.skills.abstract_round_abci.base.BaseSynchronizedData.slashing_config"></a>

#### slashing`_`config

```python
@slashing_config.setter
def slashing_config(config: str) -> None
```

Set the slashing configuration.

<a id="packages.valory.skills.abstract_round_abci.base.BaseSynchronizedData.update"></a>

#### update

```python
def update(synchronized_data_class: Optional[Type] = None,
           **kwargs: Any) -> "BaseSynchronizedData"
```

Copy and update the current data.

<a id="packages.valory.skills.abstract_round_abci.base.BaseSynchronizedData.create"></a>

#### create

```python
def create(
        synchronized_data_class: Optional[Type] = None
) -> "BaseSynchronizedData"
```

Copy and update with new data. Set values are stored as sorted tuples to the db for determinism.

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
def participant_to_selection() -> DeserializedCollection
```

Check whether keeper is set.

<a id="packages.valory.skills.abstract_round_abci.base.BaseSynchronizedData.participant_to_randomness"></a>

#### participant`_`to`_`randomness

```python
@property
def participant_to_randomness() -> DeserializedCollection
```

Check whether keeper is set.

<a id="packages.valory.skills.abstract_round_abci.base.BaseSynchronizedData.participant_to_votes"></a>

#### participant`_`to`_`votes

```python
@property
def participant_to_votes() -> DeserializedCollection
```

Check whether keeper is set.

<a id="packages.valory.skills.abstract_round_abci.base.BaseSynchronizedData.safe_contract_address"></a>

#### safe`_`contract`_`address

```python
@property
def safe_contract_address() -> str
```

Get the safe contract address.

<a id="packages.valory.skills.abstract_round_abci.base._MetaAbstractRound"></a>

## `_`MetaAbstractRound Objects

```python
class _MetaAbstractRound(ABCMeta)
```

A metaclass that validates AbstractRound's attributes.

<a id="packages.valory.skills.abstract_round_abci.base._MetaAbstractRound.__new__"></a>

#### `__`new`__`

```python
def __new__(mcs, name: str, bases: Tuple, namespace: Dict,
            **kwargs: Any) -> Type
```

Initialize the class.

<a id="packages.valory.skills.abstract_round_abci.base.AbstractRound"></a>

## AbstractRound Objects

```python
class AbstractRound(Generic[EventType], ABC, metaclass=_MetaAbstractRound)
```

This class represents an abstract round.

A round is a state of the FSM App execution. It usually involves
interactions between participants in the FSM App,
although this is not enforced at this level of abstraction.

Concrete classes must set:
- synchronized_data_class: the data class associated with this round;
- payload_class: the payload type that is allowed for this round;

Optionally, round_id can be defined, although it is recommended to use the autogenerated id.

<a id="packages.valory.skills.abstract_round_abci.base.AbstractRound.__init__"></a>

#### `__`init`__`

```python
def __init__(
    synchronized_data: BaseSynchronizedData,
    context: SkillContext,
    previous_round_payload_class: Optional[Type[BaseTxPayload]] = None
) -> None
```

Initialize the round.

<a id="packages.valory.skills.abstract_round_abci.base.AbstractRound.auto_round_id"></a>

#### auto`_`round`_`id

```python
@classmethod
def auto_round_id(cls) -> str
```

Get round id automatically.

This method returns the auto generated id from the class name if the
class variable behaviour_id is not set on the child class.
Otherwise, it returns the class variable behaviour_id.

<a id="packages.valory.skills.abstract_round_abci.base.AbstractRound.round_id"></a>

#### round`_`id

```python
@property
def round_id() -> str
```

Get round id.

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

<a id="packages.valory.skills.abstract_round_abci.base.AbstractRound.check_payload_type"></a>

#### check`_`payload`_`type

```python
def check_payload_type(transaction: Transaction) -> None
```

Check the transaction is of the allowed transaction type.

**Arguments**:

- `transaction`: the transaction

**Raises**:

- `None`: TransactionTypeNotRecognizedError if the transaction can be
applied to the current state.

<a id="packages.valory.skills.abstract_round_abci.base.AbstractRound.check_majority_possible_with_new_voter"></a>

#### check`_`majority`_`possible`_`with`_`new`_`voter

```python
def check_majority_possible_with_new_voter(
        votes_by_participant: Dict[str, BaseTxPayload],
        new_voter: str,
        new_vote: BaseTxPayload,
        nb_participants: int,
        exception_cls: Type[ABCIAppException] = ABCIAppException) -> None
```

Check that a Byzantine majority is achievable, once a new vote is added.

**Arguments**:

- `votes_by_participant`: a mapping from a participant to its vote,
before the new vote is added
- `new_voter`: the new voter
- `new_vote`: the new vote
- `nb_participants`: the total number of participants
- `exception_cls`: the class of the exception to raise in case the
check fails.

**Raises**:

- `None`: exception_cls: in case the check does not pass.

<a id="packages.valory.skills.abstract_round_abci.base.AbstractRound.check_majority_possible"></a>

#### check`_`majority`_`possible

```python
def check_majority_possible(
        votes_by_participant: Dict[str, BaseTxPayload],
        nb_participants: int,
        exception_cls: Type[ABCIAppException] = ABCIAppException) -> None
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

- `votes_by_participant`: a mapping from a participant to its vote
- `nb_participants`: the total number of participants
- `exception_cls`: the class of the exception to raise in case the
check fails.

**Raises**:

- `exception_cls`: in case the check does not pass.

<a id="packages.valory.skills.abstract_round_abci.base.AbstractRound.is_majority_possible"></a>

#### is`_`majority`_`possible

```python
def is_majority_possible(votes_by_participant: Dict[str, BaseTxPayload],
                         nb_participants: int) -> bool
```

Return true if a Byzantine majority is achievable, false otherwise.

**Arguments**:

- `votes_by_participant`: a mapping from a participant to its vote
- `nb_participants`: the total number of participants

**Returns**:

True if the majority is still possible, false otherwise.

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
class DegenerateRound(AbstractRound, ABC)
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
class CollectionRound(AbstractRound, ABC)
```

CollectionRound.

This class represents abstract logic for collection based rounds where
the round object needs to collect data from different agents. The data
might for example be from a voting round or estimation round.

`_allow_rejoin_payloads` is used to allow agents not currently active to
deliver a payload.

<a id="packages.valory.skills.abstract_round_abci.base.CollectionRound.__init__"></a>

#### `__`init`__`

```python
def __init__(*args: Any, **kwargs: Any)
```

Initialize the collection round.

<a id="packages.valory.skills.abstract_round_abci.base.CollectionRound.serialize_collection"></a>

#### serialize`_`collection

```python
@staticmethod
def serialize_collection(
        collection: DeserializedCollection) -> SerializedCollection
```

Deserialize a serialized collection.

<a id="packages.valory.skills.abstract_round_abci.base.CollectionRound.deserialize_collection"></a>

#### deserialize`_`collection

```python
@staticmethod
def deserialize_collection(
        serialized: SerializedCollection) -> DeserializedCollection
```

Deserialize a serialized collection.

<a id="packages.valory.skills.abstract_round_abci.base.CollectionRound.serialized_collection"></a>

#### serialized`_`collection

```python
@property
def serialized_collection() -> SerializedCollection
```

A collection with the addresses mapped to serialized payloads.

<a id="packages.valory.skills.abstract_round_abci.base.CollectionRound.accepting_payloads_from"></a>

#### accepting`_`payloads`_`from

```python
@property
def accepting_payloads_from() -> FrozenSet[str]
```

Accepting from the active set, or also from (re)joiners

<a id="packages.valory.skills.abstract_round_abci.base.CollectionRound.payloads"></a>

#### payloads

```python
@property
def payloads() -> List[BaseTxPayload]
```

Get all agent payloads

<a id="packages.valory.skills.abstract_round_abci.base.CollectionRound.payload_values_count"></a>

#### payload`_`values`_`count

```python
@property
def payload_values_count() -> Counter
```

Get count of payload values.

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
class _CollectUntilAllRound(CollectionRound, ABC)
```

_CollectUntilAllRound

This class represents abstract logic for when rounds need to collect payloads from all agents.

This round should only be used when non-BFT behaviour is acceptable.

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
class CollectDifferentUntilAllRound(_CollectUntilAllRound, ABC)
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
class CollectSameUntilAllRound(_CollectUntilAllRound, ABC)
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

<a id="packages.valory.skills.abstract_round_abci.base.CollectSameUntilAllRound.common_payload_values"></a>

#### common`_`payload`_`values

```python
@property
def common_payload_values() -> Tuple[Any, ...]
```

Get the common payload among the agents.

<a id="packages.valory.skills.abstract_round_abci.base.CollectSameUntilThresholdRound"></a>

## CollectSameUntilThresholdRound Objects

```python
class CollectSameUntilThresholdRound(CollectionRound, ABC)
```

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

Get the most voted payload value.

Kept for backward compatibility.

<a id="packages.valory.skills.abstract_round_abci.base.CollectSameUntilThresholdRound.most_voted_payload_values"></a>

#### most`_`voted`_`payload`_`values

```python
@property
def most_voted_payload_values() -> Tuple[Any, ...]
```

Get the most voted payload values.

<a id="packages.valory.skills.abstract_round_abci.base.CollectSameUntilThresholdRound.end_block"></a>

#### end`_`block

```python
def end_block() -> Optional[Tuple[BaseSynchronizedData, Enum]]
```

Process the end of the block.

<a id="packages.valory.skills.abstract_round_abci.base.OnlyKeeperSendsRound"></a>

## OnlyKeeperSendsRound Objects

```python
class OnlyKeeperSendsRound(AbstractRound, ABC)
```

OnlyKeeperSendsRound

This class represents logic for rounds where only one agent sends a
payload.

`done_event` is emitted when a) the keeper payload has been received and b)
the keeper payload has non-empty attributes. In this case all attributes are saved
under `payload_key`.

`fail_event` is emitted when a) the keeper payload has been received and b)
the keeper payload has only empty attributes

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

<a id="packages.valory.skills.abstract_round_abci.base.OnlyKeeperSendsRound.end_block"></a>

#### end`_`block

```python
def end_block() -> Optional[Tuple[BaseSynchronizedData, Enum]]
```

Process the end of the block.

<a id="packages.valory.skills.abstract_round_abci.base.VotingRound"></a>

## VotingRound Objects

```python
class VotingRound(CollectionRound, ABC)
```

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
class CollectDifferentUntilThresholdRound(CollectionRound, ABC)
```

CollectDifferentUntilThresholdRound

This class represents logic for rounds where a round needs to collect
different payloads from k of n agents.

`done_event` is emitted when a) the required block confirmations
have been met, and b) the collection threshold (k of n) is reached. In
this case all payloads are saved under `collection_key`.

Extended `required_block_confirmations` to allow for arrival of more
payloads.

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
class CollectNonEmptyUntilThresholdRound(CollectDifferentUntilThresholdRound,
                                         ABC)
```

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

- `entry_count`: the entry id to remove.

**Raises**:

- `None`: KeyError: if the entry count is not found.

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
def __new__(mcs, name: str, bases: Tuple, namespace: Dict,
            **kwargs: Any) -> Type
```

Initialize the class.

<a id="packages.valory.skills.abstract_round_abci.base.BackgroundAppType"></a>

## BackgroundAppType Objects

```python
class BackgroundAppType(Enum)
```

The type of a background app.

Please note that the values correspond to the priority in which the background apps should be processed
when updating rounds.

<a id="packages.valory.skills.abstract_round_abci.base.BackgroundAppType.correct_types"></a>

#### correct`_`types

```python
@staticmethod
def correct_types() -> Set[str]
```

Return the correct types only.

<a id="packages.valory.skills.abstract_round_abci.base.BackgroundAppConfig"></a>

## BackgroundAppConfig Objects

```python
@dataclass(frozen=True)
class BackgroundAppConfig(Generic[EventType])
```

Necessary configuration for a background app.

For a deeper understanding of the various types of background apps and how the config influences
the generated background app's type, please refer to the `BackgroundApp` class.
The `specify_type` method provides further insight on the subject matter.

<a id="packages.valory.skills.abstract_round_abci.base.BackgroundApp"></a>

## BackgroundApp Objects

```python
class BackgroundApp(Generic[EventType])
```

A background app.

<a id="packages.valory.skills.abstract_round_abci.base.BackgroundApp.__init__"></a>

#### `__`init`__`

```python
def __init__(config: BackgroundAppConfig) -> None
```

Initialize the BackgroundApp.

<a id="packages.valory.skills.abstract_round_abci.base.BackgroundApp.__eq__"></a>

#### `__`eq`__`

```python
def __eq__(other: Any) -> bool
```

Custom equality comparing operator.

<a id="packages.valory.skills.abstract_round_abci.base.BackgroundApp.__hash__"></a>

#### `__`hash`__`

```python
def __hash__() -> int
```

Custom hashing operator

<a id="packages.valory.skills.abstract_round_abci.base.BackgroundApp.specify_type"></a>

#### specify`_`type

```python
def specify_type() -> BackgroundAppType
```

Specify the type of the background app.

<a id="packages.valory.skills.abstract_round_abci.base.BackgroundApp.setup"></a>

#### setup

```python
def setup(initial_synchronized_data: BaseSynchronizedData,
          context: SkillContext) -> None
```

Set up the background round.

<a id="packages.valory.skills.abstract_round_abci.base.BackgroundApp.background_round"></a>

#### background`_`round

```python
@property
def background_round() -> AbstractRound
```

Get the background round.

<a id="packages.valory.skills.abstract_round_abci.base.BackgroundApp.process_transaction"></a>

#### process`_`transaction

```python
def process_transaction(transaction: Transaction, dry: bool = False) -> bool
```

Process a transaction.

<a id="packages.valory.skills.abstract_round_abci.base.TransitionBackup"></a>

## TransitionBackup Objects

```python
@dataclass
class TransitionBackup()
```

Holds transition related information as a backup in case we want to transition back from a background app.

<a id="packages.valory.skills.abstract_round_abci.base.AbciApp"></a>

## AbciApp Objects

```python
class AbciApp(Generic[EventType], ABC, metaclass=_MetaAbciApp)
```

Base class for ABCI apps.

Concrete classes of this class implement the ABCI App.

<a id="packages.valory.skills.abstract_round_abci.base.AbciApp.__init__"></a>

#### `__`init`__`

```python
def __init__(synchronized_data: BaseSynchronizedData, logger: logging.Logger,
             context: SkillContext)
```

Initialize the AbciApp.

<a id="packages.valory.skills.abstract_round_abci.base.AbciApp.is_abstract"></a>

#### is`_`abstract

```python
@classmethod
def is_abstract(cls) -> bool
```

Return if the abci app is abstract.

<a id="packages.valory.skills.abstract_round_abci.base.AbciApp.add_background_app"></a>

#### add`_`background`_`app

```python
@classmethod
def add_background_app(cls, config: BackgroundAppConfig) -> Type["AbciApp"]
```

Sets the background related class variables.

For a deeper understanding of the various types of background apps and how the inputs of this method influence
the generated background app's type, please refer to the `BackgroundApp` class.
The `specify_type` method provides further insight on the subject matter.

**Arguments**:

- `config`: the background app's configuration.

**Returns**:

the `AbciApp` with the new background app contained in the `background_apps` set.

<a id="packages.valory.skills.abstract_round_abci.base.AbciApp.synchronized_data"></a>

#### synchronized`_`data

```python
@property
def synchronized_data() -> BaseSynchronizedData
```

Return the current synchronized data.

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
def get_all_round_classes(
        cls,
        bg_round_cls: Set[Type[AbstractRound]],
        include_background_rounds: bool = False) -> Set[AppState]
```

Get all round classes.

<a id="packages.valory.skills.abstract_round_abci.base.AbciApp.bg_apps_prioritized"></a>

#### bg`_`apps`_`prioritized

```python
@property
def bg_apps_prioritized() -> Tuple[List[BackgroundApp], ...]
```

Get the background apps grouped and prioritized by their types.

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

<a id="packages.valory.skills.abstract_round_abci.base.AbciApp.schedule_round"></a>

#### schedule`_`round

```python
def schedule_round(round_cls: AppState) -> None
```

Schedule a round class.

this means:
- cancel timeout events belonging to the current round;
- instantiate the new round class and set it as current round;
- create new timeout events and schedule them according to the latest
  timestamp.

**Arguments**:

- `round_cls`: the class of the new round.

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

<a id="packages.valory.skills.abstract_round_abci.base.AbciApp.cleanup_timeouts"></a>

#### cleanup`_`timeouts

```python
def cleanup_timeouts() -> None
```

Remove all timeouts.

Note that this is method is meant to be used only when performing recovery.
Calling it in normal execution will result in unexpected behaviour.

<a id="packages.valory.skills.abstract_round_abci.base.AbciApp.check_transaction"></a>

#### check`_`transaction

```python
def check_transaction(transaction: Transaction) -> None
```

Check a transaction.

<a id="packages.valory.skills.abstract_round_abci.base.AbciApp.process_transaction"></a>

#### process`_`transaction

```python
def process_transaction(transaction: Transaction, dry: bool = False) -> None
```

Process a transaction.

The background rounds run concurrently with other (normal) rounds.
First we check if the transaction is meant for a background round,
if not we forward it to the current round object.

**Arguments**:

- `transaction`: the transaction.
- `dry`: whether the transaction should only be checked and not processed.

<a id="packages.valory.skills.abstract_round_abci.base.AbciApp.process_event"></a>

#### process`_`event

```python
def process_event(event: EventType,
                  result: Optional[BaseSynchronizedData] = None) -> None
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
def cleanup(cleanup_history_depth: int,
            cleanup_history_depth_current: Optional[int] = None) -> None
```

Clear data.

<a id="packages.valory.skills.abstract_round_abci.base.AbciApp.cleanup_current_histories"></a>

#### cleanup`_`current`_`histories

```python
def cleanup_current_histories(cleanup_history_depth_current: int) -> None
```

Reset the parameter histories for the current entry (period), keeping only the latest values for each parameter.

<a id="packages.valory.skills.abstract_round_abci.base.OffenseType"></a>

## OffenseType Objects

```python
class OffenseType(Enum)
```

The types of offenses.

The values of the enum represent the seriousness of the offence.
Offense types with values >1000 are considered serious.
See also `is_light_offence` and `is_serious_offence` functions.

<a id="packages.valory.skills.abstract_round_abci.base.is_light_offence"></a>

#### is`_`light`_`offence

```python
def is_light_offence(offence_type: OffenseType) -> bool
```

Check if an offence type is light.

<a id="packages.valory.skills.abstract_round_abci.base.is_serious_offence"></a>

#### is`_`serious`_`offence

```python
def is_serious_offence(offence_type: OffenseType) -> bool
```

Check if an offence type is serious.

<a id="packages.valory.skills.abstract_round_abci.base.light_offences"></a>

#### light`_`offences

```python
def light_offences() -> Iterator[OffenseType]
```

Get the light offences.

<a id="packages.valory.skills.abstract_round_abci.base.serious_offences"></a>

#### serious`_`offences

```python
def serious_offences() -> Iterator[OffenseType]
```

Get the serious offences.

<a id="packages.valory.skills.abstract_round_abci.base.AvailabilityWindow"></a>

## AvailabilityWindow Objects

```python
class AvailabilityWindow()
```

A cyclic array with a maximum length that holds boolean values.

When an element is added to the array and the maximum length has been reached,
the oldest element is removed. Two attributes `num_positive` and `num_negative`
reflect the number of positive and negative elements in the AvailabilityWindow,
they are updated every time a new element is added.

<a id="packages.valory.skills.abstract_round_abci.base.AvailabilityWindow.__init__"></a>

#### `__`init`__`

```python
def __init__(max_length: int) -> None
```

Initializes the `AvailabilityWindow` instance.

**Arguments**:

- `max_length`: the maximum length of the cyclic array.

<a id="packages.valory.skills.abstract_round_abci.base.AvailabilityWindow.__eq__"></a>

#### `__`eq`__`

```python
def __eq__(other: Any) -> bool
```

Compare `AvailabilityWindow` objects.

<a id="packages.valory.skills.abstract_round_abci.base.AvailabilityWindow.has_bad_availability_rate"></a>

#### has`_`bad`_`availability`_`rate

```python
def has_bad_availability_rate(threshold: float = 0.95) -> bool
```

Whether the agent on which the window belongs to has a bad availability rate or not.

<a id="packages.valory.skills.abstract_round_abci.base.AvailabilityWindow.add"></a>

#### add

```python
def add(value: bool) -> None
```

Adds a new boolean value to the cyclic array.

If the maximum length has been reached, the oldest element is removed.

**Arguments**:

- `value`: The boolean value to add to the cyclic array.

<a id="packages.valory.skills.abstract_round_abci.base.AvailabilityWindow.to_dict"></a>

#### to`_`dict

```python
def to_dict() -> Dict[str, int]
```

Returns a dictionary representation of the `AvailabilityWindow` instance.

<a id="packages.valory.skills.abstract_round_abci.base.AvailabilityWindow.from_dict"></a>

#### from`_`dict

```python
@classmethod
def from_dict(cls, data: Dict[str, int]) -> "AvailabilityWindow"
```

Initializes an `AvailabilityWindow` instance from a dictionary.

<a id="packages.valory.skills.abstract_round_abci.base.OffenceStatus"></a>

## OffenceStatus Objects

```python
@dataclass
class OffenceStatus()
```

A class that holds information about offence status for an agent.

<a id="packages.valory.skills.abstract_round_abci.base.OffenceStatus.slash_amount"></a>

#### slash`_`amount

```python
def slash_amount(light_unit_amount: int, serious_unit_amount: int) -> int
```

Get the slash amount of the current status.

<a id="packages.valory.skills.abstract_round_abci.base.OffenseStatusEncoder"></a>

## OffenseStatusEncoder Objects

```python
class OffenseStatusEncoder(json.JSONEncoder)
```

A custom JSON encoder for the offence status dictionary.

<a id="packages.valory.skills.abstract_round_abci.base.OffenseStatusEncoder.default"></a>

#### default

```python
def default(o: Any) -> Any
```

The default JSON encoder.

<a id="packages.valory.skills.abstract_round_abci.base.OffenseStatusDecoder"></a>

## OffenseStatusDecoder Objects

```python
class OffenseStatusDecoder(json.JSONDecoder)
```

A custom JSON decoder for the offence status dictionary.

<a id="packages.valory.skills.abstract_round_abci.base.OffenseStatusDecoder.__init__"></a>

#### `__`init`__`

```python
def __init__(*args: Any, **kwargs: Any) -> None
```

Initialize the custom JSON decoder.

<a id="packages.valory.skills.abstract_round_abci.base.OffenseStatusDecoder.hook"></a>

#### hook

```python
@staticmethod
def hook(
    data: Dict[str, Any]
) -> Union[AvailabilityWindow, OffenceStatus, Dict[str, OffenceStatus]]
```

Perform the custom decoding.

<a id="packages.valory.skills.abstract_round_abci.base.PendingOffense"></a>

## PendingOffense Objects

```python
@dataclass(frozen=True, eq=True)
class PendingOffense()
```

A dataclass to represent offences that need to be addressed.

<a id="packages.valory.skills.abstract_round_abci.base.PendingOffense.__post_init__"></a>

#### `__`post`_`init`__`

```python
def __post_init__() -> None
```

Post initialization for offence type conversion in case it is given as an `int`.

<a id="packages.valory.skills.abstract_round_abci.base.SlashingNotConfiguredError"></a>

## SlashingNotConfiguredError Objects

```python
class SlashingNotConfiguredError(Exception)
```

Custom exception raised when slashing configuration is requested but is not available.

<a id="packages.valory.skills.abstract_round_abci.base.DEFAULT_PENDING_OFFENCE_TTL"></a>

#### DEFAULT`_`PENDING`_`OFFENCE`_`TTL

1 hour

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
def __init__(context: SkillContext, abci_app_cls: Type[AbciApp])
```

Initialize the round.

<a id="packages.valory.skills.abstract_round_abci.base.RoundSequence.enable_slashing"></a>

#### enable`_`slashing

```python
def enable_slashing() -> None
```

Enable slashing.

<a id="packages.valory.skills.abstract_round_abci.base.RoundSequence.validator_to_agent"></a>

#### validator`_`to`_`agent

```python
@property
def validator_to_agent() -> Dict[str, str]
```

Get the mapping of the validators' addresses to their agent addresses.

<a id="packages.valory.skills.abstract_round_abci.base.RoundSequence.validator_to_agent"></a>

#### validator`_`to`_`agent

```python
@validator_to_agent.setter
def validator_to_agent(validator_to_agent: Dict[str, str]) -> None
```

Set the mapping of the validators' addresses to their agent addresses.

<a id="packages.valory.skills.abstract_round_abci.base.RoundSequence.offence_status"></a>

#### offence`_`status

```python
@property
def offence_status() -> Dict[str, OffenceStatus]
```

Get the mapping of the agents' addresses to their offence status.

<a id="packages.valory.skills.abstract_round_abci.base.RoundSequence.offence_status"></a>

#### offence`_`status

```python
@offence_status.setter
def offence_status(offence_status: Dict[str, OffenceStatus]) -> None
```

Set the mapping of the agents' addresses to their offence status.

<a id="packages.valory.skills.abstract_round_abci.base.RoundSequence.add_pending_offence"></a>

#### add`_`pending`_`offence

```python
def add_pending_offence(pending_offence: PendingOffense) -> None
```

Add a pending offence to the set of pending offences.

Pending offences are offences that have been detected, but not yet agreed upon by the consensus.
A pending offence is removed from the set of pending offences and added to the OffenceStatus of a validator
when the majority of the agents agree on it.

**Arguments**:

- `pending_offence`: the pending offence to add

**Returns**:

None

<a id="packages.valory.skills.abstract_round_abci.base.RoundSequence.sync_db_and_slashing"></a>

#### sync`_`db`_`and`_`slashing

```python
def sync_db_and_slashing(serialized_db_state: str) -> None
```

Sync the database and the slashing configuration.

<a id="packages.valory.skills.abstract_round_abci.base.RoundSequence.serialized_offence_status"></a>

#### serialized`_`offence`_`status

```python
def serialized_offence_status() -> str
```

Serialize the offence status.

<a id="packages.valory.skills.abstract_round_abci.base.RoundSequence.store_offence_status"></a>

#### store`_`offence`_`status

```python
def store_offence_status() -> None
```

Store the serialized offence status.

<a id="packages.valory.skills.abstract_round_abci.base.RoundSequence.get_agent_address"></a>

#### get`_`agent`_`address

```python
def get_agent_address(validator: Validator) -> str
```

Get corresponding agent address from a `Validator` instance.

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

<a id="packages.valory.skills.abstract_round_abci.base.RoundSequence.blockchain"></a>

#### blockchain

```python
@property
def blockchain() -> Blockchain
```

Get the Blockchain instance.

<a id="packages.valory.skills.abstract_round_abci.base.RoundSequence.blockchain"></a>

#### blockchain

```python
@blockchain.setter
def blockchain(_blockchain: Blockchain) -> None
```

Get the Blockchain instance.

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

This is going to be the database's hash.
In this way, the app hash will be reflecting our application's state,
and will guarantee that all the agents on the chain apply the changes of the arriving blocks in the same way.

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

<a id="packages.valory.skills.abstract_round_abci.base.RoundSequence.block_stall_deadline_expired"></a>

#### block`_`stall`_`deadline`_`expired

```python
@property
def block_stall_deadline_expired() -> bool
```

Get if the deadline for not having received any begin block requests from the Tendermint node has expired.

<a id="packages.valory.skills.abstract_round_abci.base.RoundSequence.set_block_stall_deadline"></a>

#### set`_`block`_`stall`_`deadline

```python
def set_block_stall_deadline() -> None
```

Use the local time of the agent and a predefined tolerance, to specify the expiration of the deadline.

<a id="packages.valory.skills.abstract_round_abci.base.RoundSequence.init_chain"></a>

#### init`_`chain

```python
def init_chain(initial_height: int) -> None
```

Init chain.

<a id="packages.valory.skills.abstract_round_abci.base.RoundSequence.begin_block"></a>

#### begin`_`block

```python
def begin_block(header: Header, evidences: Evidences,
                last_commit_info: LastCommitInfo) -> None
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

- `transaction`: the transaction.

**Raises**:

- `None`: an Error otherwise.

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
def reset_blockchain(is_replay: bool = False, is_init: bool = False) -> None
```

Reset blockchain after tendermint reset.

**Arguments**:

- `is_replay`: whether we are resetting the blockchain while replaying blocks.
- `is_init`: whether to process blocks before receiving an init_chain req from tendermint.

<a id="packages.valory.skills.abstract_round_abci.base.RoundSequence.reset_state"></a>

#### reset`_`state

```python
def reset_state(restart_from_round: str,
                round_count: int,
                serialized_db_state: Optional[str] = None) -> None
```

This method resets the state of RoundSequence to the beginning of the period.

Note: This is intended to be used for agent <-> tendermint communication recovery only!

**Arguments**:

- `restart_from_round`: from which round to restart the abci.
This round should be the first round in the last period.
- `round_count`: the round count at the beginning of the period -1.
- `serialized_db_state`: the state of the database at the beginning of the period.
If provided, the database will be reset to this state.

<a id="packages.valory.skills.abstract_round_abci.base.PendingOffencesPayload"></a>

## PendingOffencesPayload Objects

```python
@dataclass(frozen=True)
class PendingOffencesPayload(BaseTxPayload)
```

Represent a transaction payload for pending offences.

<a id="packages.valory.skills.abstract_round_abci.base.PendingOffencesRound"></a>

## PendingOffencesRound Objects

```python
class PendingOffencesRound(CollectSameUntilThresholdRound)
```

Defines the pending offences background round, which runs concurrently with other rounds to sync the offences.

<a id="packages.valory.skills.abstract_round_abci.base.PendingOffencesRound.__init__"></a>

#### `__`init`__`

```python
def __init__(*args: Any, **kwargs: Any) -> None
```

Initialize the `PendingOffencesRound`.

<a id="packages.valory.skills.abstract_round_abci.base.PendingOffencesRound.offence_status"></a>

#### offence`_`status

```python
@property
def offence_status() -> Dict[str, OffenceStatus]
```

Get the offence status from the round sequence.

<a id="packages.valory.skills.abstract_round_abci.base.PendingOffencesRound.end_block"></a>

#### end`_`block

```python
def end_block() -> None
```

Process the end of the block for the pending offences background round.

It is important to note that this is a non-standard type of round, meaning it does not emit any events.
Instead, it continuously runs in the background.
The objective of this round is to consistently monitor the received pending offences
and achieve a consensus among the agents.

