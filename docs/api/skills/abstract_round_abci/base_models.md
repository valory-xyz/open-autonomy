<a id="packages.valory.skills.abstract_round_abci.base_models"></a>

# packages.valory.skills.abstract`_`round`_`abci.base`_`models

This module contains the base classes for the models classes of the skill.

<a id="packages.valory.skills.abstract_round_abci.base_models._MetaPayload"></a>

## `_`MetaPayload Objects

```python
class _MetaPayload(ABCMeta)
```

Payload metaclass.

The purpose of this metaclass is to remember the association
between the type of a payload and the payload class to build it.
This is necessary to recover the right payload class to instantiate
at decoding time.

Each class that has this class as metaclass must have a class
attribute 'transaction_type', which for simplicity is required
to be convertible to string, for serialization purposes.

<a id="packages.valory.skills.abstract_round_abci.base_models._MetaPayload.__new__"></a>

#### `__`new`__`

```python
def __new__(mcs, name: str, bases: Tuple, namespace: Dict, **kwargs: Any) -> Type
```

Create a new class object.

<a id="packages.valory.skills.abstract_round_abci.base_models.BaseTxPayload"></a>

## BaseTxPayload Objects

```python
class BaseTxPayload(ABC, metaclass=_MetaPayload)
```

This class represents a base class for transaction payload classes.

<a id="packages.valory.skills.abstract_round_abci.base_models.BaseTxPayload.__init__"></a>

#### `__`init`__`

```python
def __init__(sender: str) -> None
```

Initialize a transaction payload.

**Arguments**:

- `sender`: the sender (Ethereum) address

<a id="packages.valory.skills.abstract_round_abci.base_models.BaseTxPayload.encode"></a>

#### encode

```python
def encode() -> bytes
```

Encode the payload.

<a id="packages.valory.skills.abstract_round_abci.base_models.BaseTxPayload.decode"></a>

#### decode

```python
@classmethod
def decode(cls, obj: bytes) -> "BaseTxPayload"
```

Decode the payload.

<a id="packages.valory.skills.abstract_round_abci.base_models.BaseTxPayload.from_json"></a>

#### from`_`json

```python
@classmethod
def from_json(cls, obj: Dict) -> "BaseTxPayload"
```

Decode the payload.

<a id="packages.valory.skills.abstract_round_abci.base_models.BaseTxPayload.json"></a>

#### json

```python
@property
def json() -> Dict
```

Get the JSON representation of the payload.

<a id="packages.valory.skills.abstract_round_abci.base_models.BaseTxPayload.data"></a>

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

<a id="packages.valory.skills.abstract_round_abci.base_models.BaseTxPayload.__eq__"></a>

#### `__`eq`__`

```python
def __eq__(other: Any) -> bool
```

Check equality.

<a id="packages.valory.skills.abstract_round_abci.base_models.Transaction"></a>

## Transaction Objects

```python
class Transaction(ABC)
```

Class to represent a transaction.

<a id="packages.valory.skills.abstract_round_abci.base_models.Transaction.__init__"></a>

#### `__`init`__`

```python
def __init__(payload: BaseTxPayload, signature: str) -> None
```

Initialize a transaction object.

<a id="packages.valory.skills.abstract_round_abci.base_models.Transaction.encode"></a>

#### encode

```python
def encode() -> bytes
```

Encode the transaction.

<a id="packages.valory.skills.abstract_round_abci.base_models.Transaction.decode"></a>

#### decode

```python
@classmethod
def decode(cls, obj: bytes) -> "Transaction"
```

Decode the transaction.

<a id="packages.valory.skills.abstract_round_abci.base_models.Transaction.verify"></a>

#### verify

```python
def verify() -> None
```

Verify the signature is correct.

<a id="packages.valory.skills.abstract_round_abci.base_models.Transaction.__eq__"></a>

#### `__`eq`__`

```python
def __eq__(other: Any) -> bool
```

Check equality.

<a id="packages.valory.skills.abstract_round_abci.base_models.Block"></a>

## Block Objects

```python
class Block()
```

Class to represent (a subset of) data of a Tendermint block.

<a id="packages.valory.skills.abstract_round_abci.base_models.Block.__init__"></a>

#### `__`init`__`

```python
def __init__(header: Header, transactions: Sequence[Transaction]) -> None
```

Initialize the block.

<a id="packages.valory.skills.abstract_round_abci.base_models.Block.transactions"></a>

#### transactions

```python
@property
def transactions() -> Tuple[Transaction, ...]
```

Get the transactions.

<a id="packages.valory.skills.abstract_round_abci.base_models.Blockchain"></a>

## Blockchain Objects

```python
class Blockchain()
```

Class to represent a (naive) Tendermint blockchain.

The consistency of the data in the blocks is guaranteed by Tendermint.

<a id="packages.valory.skills.abstract_round_abci.base_models.Blockchain.__init__"></a>

#### `__`init`__`

```python
def __init__() -> None
```

Initialize the blockchain.

<a id="packages.valory.skills.abstract_round_abci.base_models.Blockchain.add_block"></a>

#### add`_`block

```python
def add_block(block: Block) -> None
```

Add a block to the list.

<a id="packages.valory.skills.abstract_round_abci.base_models.Blockchain.height"></a>

#### height

```python
@property
def height() -> int
```

Get the height.

<a id="packages.valory.skills.abstract_round_abci.base_models.Blockchain.length"></a>

#### length

```python
@property
def length() -> int
```

Get the blockchain length.

<a id="packages.valory.skills.abstract_round_abci.base_models.Blockchain.get_block"></a>

#### get`_`block

```python
def get_block(height: int) -> Block
```

Get the ith block.

<a id="packages.valory.skills.abstract_round_abci.base_models.BlockBuilder"></a>

## BlockBuilder Objects

```python
class BlockBuilder()
```

Helper class to build a block.

<a id="packages.valory.skills.abstract_round_abci.base_models.BlockBuilder.__init__"></a>

#### `__`init`__`

```python
def __init__() -> None
```

Initialize the block builder.

<a id="packages.valory.skills.abstract_round_abci.base_models.BlockBuilder.reset"></a>

#### reset

```python
def reset() -> None
```

Reset the temporary data structures.

<a id="packages.valory.skills.abstract_round_abci.base_models.BlockBuilder.header"></a>

#### header

```python
@property
def header() -> Header
```

Get the block header.

**Returns**:

the block header

<a id="packages.valory.skills.abstract_round_abci.base_models.BlockBuilder.header"></a>

#### header

```python
@header.setter
def header(header: Header) -> None
```

Set the header.

<a id="packages.valory.skills.abstract_round_abci.base_models.BlockBuilder.transactions"></a>

#### transactions

```python
@property
def transactions() -> Tuple[Transaction, ...]
```

Get the sequence of transactions.

<a id="packages.valory.skills.abstract_round_abci.base_models.BlockBuilder.add_transaction"></a>

#### add`_`transaction

```python
def add_transaction(transaction: Transaction) -> None
```

Add a transaction.

<a id="packages.valory.skills.abstract_round_abci.base_models.BlockBuilder.get_block"></a>

#### get`_`block

```python
def get_block() -> Block
```

Get the block.

<a id="packages.valory.skills.abstract_round_abci.base_models.ConsensusParams"></a>

## ConsensusParams Objects

```python
class ConsensusParams()
```

Represent the consensus parameters.

<a id="packages.valory.skills.abstract_round_abci.base_models.ConsensusParams.__init__"></a>

#### `__`init`__`

```python
def __init__(max_participants: int)
```

Initialize the consensus parameters.

<a id="packages.valory.skills.abstract_round_abci.base_models.ConsensusParams.max_participants"></a>

#### max`_`participants

```python
@property
def max_participants() -> int
```

Get the maximum number of participants.

<a id="packages.valory.skills.abstract_round_abci.base_models.ConsensusParams.two_thirds_threshold"></a>

#### two`_`thirds`_`threshold

```python
@property
def two_thirds_threshold() -> int
```

Get the 2/3 threshold.

<a id="packages.valory.skills.abstract_round_abci.base_models.ConsensusParams.from_json"></a>

#### from`_`json

```python
@classmethod
def from_json(cls, obj: Dict) -> "ConsensusParams"
```

Get from JSON.

<a id="packages.valory.skills.abstract_round_abci.base_models.BasePeriodState"></a>

## BasePeriodState Objects

```python
class BasePeriodState()
```

Class to represent a period state.

<a id="packages.valory.skills.abstract_round_abci.base_models.BasePeriodState.__init__"></a>

#### `__`init`__`

```python
def __init__(participants: Optional[FrozenSet[str]] = None) -> None
```

Initialize a period state.

<a id="packages.valory.skills.abstract_round_abci.base_models.BasePeriodState.participants"></a>

#### participants

```python
@property
def participants() -> FrozenSet[str]
```

Get the participants.

<a id="packages.valory.skills.abstract_round_abci.base_models.BasePeriodState.update"></a>

#### update

```python
@classmethod
def update(cls, state: "BasePeriodState", **kwargs: Any) -> "BasePeriodState"
```

Copy and update the state.

<a id="packages.valory.skills.abstract_round_abci.base_models.AbstractRound"></a>

## AbstractRound Objects

```python
class AbstractRound(ABC)
```

This class represents an abstract round.

A round is a state of a period. It usually involves
interactions between participants in the period,
although this is not enforced at this level of abstraction.

<a id="packages.valory.skills.abstract_round_abci.base_models.AbstractRound.__init__"></a>

#### `__`init`__`

```python
def __init__(state: BasePeriodState, consensus_params: ConsensusParams) -> None
```

Initialize the round.

<a id="packages.valory.skills.abstract_round_abci.base_models.AbstractRound.state"></a>

#### state

```python
@property
def state() -> BasePeriodState
```

Get the period state.

<a id="packages.valory.skills.abstract_round_abci.base_models.AbstractRound.check_transaction"></a>

#### check`_`transaction

```python
def check_transaction(transaction: Transaction) -> bool
```

Check transaction against the current state.

By convention, the payload handler should be a method
of the class that is named 'check_{payload_name}'.

**Arguments**:

- `transaction`: the transaction

**Returns**:

True if the transaction can be applied to the current

<a id="packages.valory.skills.abstract_round_abci.base_models.AbstractRound.add_transaction"></a>

#### add`_`transaction

```python
def add_transaction(transaction: Transaction) -> None
```

Process a transaction.

By convention, the payload handler should be a method
of the class that is named '{payload_name}'.

**Arguments**:

- `transaction`: the transaction.

<a id="packages.valory.skills.abstract_round_abci.base_models.AbstractRound.end_block"></a>

#### end`_`block

```python
@abstractmethod
def end_block() -> Optional[Tuple[Any, Optional["AbstractRound"]]]
```

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

<a id="packages.valory.skills.abstract_round_abci.base_models.Period"></a>

## Period Objects

```python
class Period()
```

This class represents a period (i.e. a sequence of rounds)

<a id="packages.valory.skills.abstract_round_abci.base_models.Period.__init__"></a>

#### `__`init`__`

```python
def __init__(starting_round_cls: Type[AbstractRound])
```

Initialize the round.

<a id="packages.valory.skills.abstract_round_abci.base_models.Period.setup"></a>

#### setup

```python
def setup(*args: Any, **kwargs: Any) -> None
```

Set up the period.

**Arguments**:

- `args`: the arguments to pass to the round constructor.
- `kwargs`: the keyword-arguments to pass to the round constructor.

<a id="packages.valory.skills.abstract_round_abci.base_models.Period.is_finished"></a>

#### is`_`finished

```python
@property
def is_finished() -> bool
```

Check if a period has finished.

<a id="packages.valory.skills.abstract_round_abci.base_models.Period.check_is_finished"></a>

#### check`_`is`_`finished

```python
def check_is_finished() -> None
```

Check if a period has finished.

<a id="packages.valory.skills.abstract_round_abci.base_models.Period.current_round_id"></a>

#### current`_`round`_`id

```python
@property
def current_round_id() -> Optional[str]
```

Get the current round id.

<a id="packages.valory.skills.abstract_round_abci.base_models.Period.latest_result"></a>

#### latest`_`result

```python
@property
def latest_result() -> Optional[Any]
```

Get the latest result of the round.

<a id="packages.valory.skills.abstract_round_abci.base_models.Period.begin_block"></a>

#### begin`_`block

```python
def begin_block(header: Header) -> None
```

Begin block.

<a id="packages.valory.skills.abstract_round_abci.base_models.Period.deliver_tx"></a>

#### deliver`_`tx

```python
def deliver_tx(transaction: Transaction) -> bool
```

Deliver a transaction.

Appends the transaction to build the block on 'end_block' later.

**Arguments**:

- `transaction`: the transaction.

**Returns**:

True if the transaction delivery was successful, False otherwise.

<a id="packages.valory.skills.abstract_round_abci.base_models.Period.end_block"></a>

#### end`_`block

```python
def end_block() -> None
```

Process the 'end_block' request.

<a id="packages.valory.skills.abstract_round_abci.base_models.Period.commit"></a>

#### commit

```python
def commit() -> None
```

Process the 'commit' request.

