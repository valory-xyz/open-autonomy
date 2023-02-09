<a id="packages.valory.protocols.abci.message"></a>

# packages.valory.protocols.abci.message

This module contains abci's message definition.

<a id="packages.valory.protocols.abci.message.AbciMessage"></a>

## AbciMessage Objects

```python
class AbciMessage(Message)
```

A protocol for ABCI requests and responses.

<a id="packages.valory.protocols.abci.message.AbciMessage.Performative"></a>

## Performative Objects

```python
class Performative(Message.Performative)
```

Performatives for the abci protocol.

<a id="packages.valory.protocols.abci.message.AbciMessage.Performative.__str__"></a>

#### `__`str`__`

```python
def __str__() -> str
```

Get the string representation.

<a id="packages.valory.protocols.abci.message.AbciMessage.__init__"></a>

#### `__`init`__`

```python
def __init__(performative: Performative,
             dialogue_reference: Tuple[str, str] = ("", ""),
             message_id: int = 1,
             target: int = 0,
             **kwargs: Any)
```

Initialise an instance of AbciMessage.

**Arguments**:

- `message_id`: the message id.
- `dialogue_reference`: the dialogue reference.
- `target`: the message target.
- `performative`: the message performative.
- `**kwargs`: extra options.

<a id="packages.valory.protocols.abci.message.AbciMessage.valid_performatives"></a>

#### valid`_`performatives

```python
@property
def valid_performatives() -> Set[str]
```

Get valid performatives.

<a id="packages.valory.protocols.abci.message.AbciMessage.dialogue_reference"></a>

#### dialogue`_`reference

```python
@property
def dialogue_reference() -> Tuple[str, str]
```

Get the dialogue_reference of the message.

<a id="packages.valory.protocols.abci.message.AbciMessage.message_id"></a>

#### message`_`id

```python
@property
def message_id() -> int
```

Get the message_id of the message.

<a id="packages.valory.protocols.abci.message.AbciMessage.performative"></a>

#### performative

```python
@property
def performative() -> Performative
```

Get the performative of the message.

<a id="packages.valory.protocols.abci.message.AbciMessage.target"></a>

#### target

```python
@property
def target() -> int
```

Get the target of the message.

<a id="packages.valory.protocols.abci.message.AbciMessage.app_hash"></a>

#### app`_`hash

```python
@property
def app_hash() -> bytes
```

Get the 'app_hash' content from the message.

<a id="packages.valory.protocols.abci.message.AbciMessage.app_state_bytes"></a>

#### app`_`state`_`bytes

```python
@property
def app_state_bytes() -> bytes
```

Get the 'app_state_bytes' content from the message.

<a id="packages.valory.protocols.abci.message.AbciMessage.app_version"></a>

#### app`_`version

```python
@property
def app_version() -> int
```

Get the 'app_version' content from the message.

<a id="packages.valory.protocols.abci.message.AbciMessage.block_version"></a>

#### block`_`version

```python
@property
def block_version() -> int
```

Get the 'block_version' content from the message.

<a id="packages.valory.protocols.abci.message.AbciMessage.byzantine_validators"></a>

#### byzantine`_`validators

```python
@property
def byzantine_validators() -> CustomEvidences
```

Get the 'byzantine_validators' content from the message.

<a id="packages.valory.protocols.abci.message.AbciMessage.chain_id"></a>

#### chain`_`id

```python
@property
def chain_id() -> str
```

Get the 'chain_id' content from the message.

<a id="packages.valory.protocols.abci.message.AbciMessage.chunk"></a>

#### chunk

```python
@property
def chunk() -> bytes
```

Get the 'chunk' content from the message.

<a id="packages.valory.protocols.abci.message.AbciMessage.chunk_index"></a>

#### chunk`_`index

```python
@property
def chunk_index() -> int
```

Get the 'chunk_index' content from the message.

<a id="packages.valory.protocols.abci.message.AbciMessage.chunk_sender"></a>

#### chunk`_`sender

```python
@property
def chunk_sender() -> str
```

Get the 'chunk_sender' content from the message.

<a id="packages.valory.protocols.abci.message.AbciMessage.code"></a>

#### code

```python
@property
def code() -> int
```

Get the 'code' content from the message.

<a id="packages.valory.protocols.abci.message.AbciMessage.codespace"></a>

#### codespace

```python
@property
def codespace() -> str
```

Get the 'codespace' content from the message.

<a id="packages.valory.protocols.abci.message.AbciMessage.consensus_param_updates"></a>

#### consensus`_`param`_`updates

```python
@property
def consensus_param_updates() -> Optional[CustomConsensusParams]
```

Get the 'consensus_param_updates' content from the message.

<a id="packages.valory.protocols.abci.message.AbciMessage.consensus_params"></a>

#### consensus`_`params

```python
@property
def consensus_params() -> Optional[CustomConsensusParams]
```

Get the 'consensus_params' content from the message.

<a id="packages.valory.protocols.abci.message.AbciMessage.data"></a>

#### data

```python
@property
def data() -> bytes
```

Get the 'data' content from the message.

<a id="packages.valory.protocols.abci.message.AbciMessage.dummy_consensus_params"></a>

#### dummy`_`consensus`_`params

```python
@property
def dummy_consensus_params() -> CustomConsensusParams
```

Get the 'dummy_consensus_params' content from the message.

<a id="packages.valory.protocols.abci.message.AbciMessage.error"></a>

#### error

```python
@property
def error() -> str
```

Get the 'error' content from the message.

<a id="packages.valory.protocols.abci.message.AbciMessage.events"></a>

#### events

```python
@property
def events() -> CustomEvents
```

Get the 'events' content from the message.

<a id="packages.valory.protocols.abci.message.AbciMessage.format"></a>

#### format

```python
@property
def format() -> int
```

Get the 'format' content from the message.

<a id="packages.valory.protocols.abci.message.AbciMessage.gas_used"></a>

#### gas`_`used

```python
@property
def gas_used() -> int
```

Get the 'gas_used' content from the message.

<a id="packages.valory.protocols.abci.message.AbciMessage.gas_wanted"></a>

#### gas`_`wanted

```python
@property
def gas_wanted() -> int
```

Get the 'gas_wanted' content from the message.

<a id="packages.valory.protocols.abci.message.AbciMessage.hash"></a>

#### hash

```python
@property
def hash() -> bytes
```

Get the 'hash' content from the message.

<a id="packages.valory.protocols.abci.message.AbciMessage.header"></a>

#### header

```python
@property
def header() -> CustomHeader
```

Get the 'header' content from the message.

<a id="packages.valory.protocols.abci.message.AbciMessage.height"></a>

#### height

```python
@property
def height() -> int
```

Get the 'height' content from the message.

<a id="packages.valory.protocols.abci.message.AbciMessage.index"></a>

#### index

```python
@property
def index() -> int
```

Get the 'index' content from the message.

<a id="packages.valory.protocols.abci.message.AbciMessage.info"></a>

#### info

```python
@property
def info() -> str
```

Get the 'info' content from the message.

<a id="packages.valory.protocols.abci.message.AbciMessage.info_data"></a>

#### info`_`data

```python
@property
def info_data() -> str
```

Get the 'info_data' content from the message.

<a id="packages.valory.protocols.abci.message.AbciMessage.initial_height"></a>

#### initial`_`height

```python
@property
def initial_height() -> int
```

Get the 'initial_height' content from the message.

<a id="packages.valory.protocols.abci.message.AbciMessage.key"></a>

#### key

```python
@property
def key() -> bytes
```

Get the 'key' content from the message.

<a id="packages.valory.protocols.abci.message.AbciMessage.last_block_app_hash"></a>

#### last`_`block`_`app`_`hash

```python
@property
def last_block_app_hash() -> bytes
```

Get the 'last_block_app_hash' content from the message.

<a id="packages.valory.protocols.abci.message.AbciMessage.last_block_height"></a>

#### last`_`block`_`height

```python
@property
def last_block_height() -> int
```

Get the 'last_block_height' content from the message.

<a id="packages.valory.protocols.abci.message.AbciMessage.last_commit_info"></a>

#### last`_`commit`_`info

```python
@property
def last_commit_info() -> CustomLastCommitInfo
```

Get the 'last_commit_info' content from the message.

<a id="packages.valory.protocols.abci.message.AbciMessage.log"></a>

#### log

```python
@property
def log() -> str
```

Get the 'log' content from the message.

<a id="packages.valory.protocols.abci.message.AbciMessage.message"></a>

#### message

```python
@property
def message() -> str
```

Get the 'message' content from the message.

<a id="packages.valory.protocols.abci.message.AbciMessage.option_key"></a>

#### option`_`key

```python
@property
def option_key() -> str
```

Get the 'option_key' content from the message.

<a id="packages.valory.protocols.abci.message.AbciMessage.option_value"></a>

#### option`_`value

```python
@property
def option_value() -> str
```

Get the 'option_value' content from the message.

<a id="packages.valory.protocols.abci.message.AbciMessage.p2p_version"></a>

#### p2p`_`version

```python
@property
def p2p_version() -> int
```

Get the 'p2p_version' content from the message.

<a id="packages.valory.protocols.abci.message.AbciMessage.path"></a>

#### path

```python
@property
def path() -> str
```

Get the 'path' content from the message.

<a id="packages.valory.protocols.abci.message.AbciMessage.proof_ops"></a>

#### proof`_`ops

```python
@property
def proof_ops() -> CustomProofOps
```

Get the 'proof_ops' content from the message.

<a id="packages.valory.protocols.abci.message.AbciMessage.prove"></a>

#### prove

```python
@property
def prove() -> bool
```

Get the 'prove' content from the message.

<a id="packages.valory.protocols.abci.message.AbciMessage.query_data"></a>

#### query`_`data

```python
@property
def query_data() -> bytes
```

Get the 'query_data' content from the message.

<a id="packages.valory.protocols.abci.message.AbciMessage.refetch_chunks"></a>

#### refetch`_`chunks

```python
@property
def refetch_chunks() -> Tuple[int, ...]
```

Get the 'refetch_chunks' content from the message.

<a id="packages.valory.protocols.abci.message.AbciMessage.reject_senders"></a>

#### reject`_`senders

```python
@property
def reject_senders() -> Tuple[str, ...]
```

Get the 'reject_senders' content from the message.

<a id="packages.valory.protocols.abci.message.AbciMessage.result"></a>

#### result

```python
@property
def result() -> CustomResult
```

Get the 'result' content from the message.

<a id="packages.valory.protocols.abci.message.AbciMessage.retain_height"></a>

#### retain`_`height

```python
@property
def retain_height() -> int
```

Get the 'retain_height' content from the message.

<a id="packages.valory.protocols.abci.message.AbciMessage.snapshot"></a>

#### snapshot

```python
@property
def snapshot() -> CustomSnapshot
```

Get the 'snapshot' content from the message.

<a id="packages.valory.protocols.abci.message.AbciMessage.snapshots"></a>

#### snapshots

```python
@property
def snapshots() -> CustomSnapShots
```

Get the 'snapshots' content from the message.

<a id="packages.valory.protocols.abci.message.AbciMessage.time"></a>

#### time

```python
@property
def time() -> CustomTimestamp
```

Get the 'time' content from the message.

<a id="packages.valory.protocols.abci.message.AbciMessage.tx"></a>

#### tx

```python
@property
def tx() -> bytes
```

Get the 'tx' content from the message.

<a id="packages.valory.protocols.abci.message.AbciMessage.type"></a>

#### type

```python
@property
def type() -> CustomCheckTxType
```

Get the 'type' content from the message.

<a id="packages.valory.protocols.abci.message.AbciMessage.validator_updates"></a>

#### validator`_`updates

```python
@property
def validator_updates() -> CustomValidatorUpdates
```

Get the 'validator_updates' content from the message.

<a id="packages.valory.protocols.abci.message.AbciMessage.validators"></a>

#### validators

```python
@property
def validators() -> CustomValidatorUpdates
```

Get the 'validators' content from the message.

<a id="packages.valory.protocols.abci.message.AbciMessage.value"></a>

#### value

```python
@property
def value() -> bytes
```

Get the 'value' content from the message.

<a id="packages.valory.protocols.abci.message.AbciMessage.version"></a>

#### version

```python
@property
def version() -> str
```

Get the 'version' content from the message.

