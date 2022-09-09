<a id="packages.valory.protocols.abci.tests.test_abci"></a>

# packages.valory.protocols.abci.tests.test`_`abci

Tests package for the 'valory/abci' protocol.

<a id="packages.valory.protocols.abci.tests.test_abci.BaseTestMessageConstruction"></a>

## BaseTestMessageConstruction Objects

```python
class BaseTestMessageConstruction()
```

Base class to test message construction for the ABCI protocol.

<a id="packages.valory.protocols.abci.tests.test_abci.BaseTestMessageConstruction.build_message"></a>

#### build`_`message

```python
@abstractmethod
def build_message() -> AbciMessage
```

Build the message to be used for testing.

<a id="packages.valory.protocols.abci.tests.test_abci.BaseTestMessageConstruction.test_run"></a>

#### test`_`run

```python
def test_run() -> None
```

Run the test.

<a id="packages.valory.protocols.abci.tests.test_abci.TestRequestEcho"></a>

## TestRequestEcho Objects

```python
class TestRequestEcho(BaseTestMessageConstruction)
```

Test ABCI request abci.

<a id="packages.valory.protocols.abci.tests.test_abci.TestRequestEcho.build_message"></a>

#### build`_`message

```python
def build_message() -> AbciMessage
```

Build the message.

<a id="packages.valory.protocols.abci.tests.test_abci.TestResponseEcho"></a>

## TestResponseEcho Objects

```python
class TestResponseEcho(BaseTestMessageConstruction)
```

Test ABCI response abci.

<a id="packages.valory.protocols.abci.tests.test_abci.TestResponseEcho.build_message"></a>

#### build`_`message

```python
def build_message() -> AbciMessage
```

Build the message.

<a id="packages.valory.protocols.abci.tests.test_abci.TestRequestFlush"></a>

## TestRequestFlush Objects

```python
class TestRequestFlush(BaseTestMessageConstruction)
```

Test ABCI request flush.

<a id="packages.valory.protocols.abci.tests.test_abci.TestRequestFlush.build_message"></a>

#### build`_`message

```python
def build_message() -> AbciMessage
```

Build the message.

<a id="packages.valory.protocols.abci.tests.test_abci.TestResponseFlush"></a>

## TestResponseFlush Objects

```python
class TestResponseFlush(BaseTestMessageConstruction)
```

Test ABCI response flush.

<a id="packages.valory.protocols.abci.tests.test_abci.TestResponseFlush.build_message"></a>

#### build`_`message

```python
def build_message() -> AbciMessage
```

Build the message.

<a id="packages.valory.protocols.abci.tests.test_abci.TestRequestInfo"></a>

## TestRequestInfo Objects

```python
class TestRequestInfo(BaseTestMessageConstruction)
```

Test ABCI request info.

<a id="packages.valory.protocols.abci.tests.test_abci.TestRequestInfo.build_message"></a>

#### build`_`message

```python
def build_message() -> AbciMessage
```

Build the message.

<a id="packages.valory.protocols.abci.tests.test_abci.TestResponseInfo"></a>

## TestResponseInfo Objects

```python
class TestResponseInfo(BaseTestMessageConstruction)
```

Test ABCI response info.

<a id="packages.valory.protocols.abci.tests.test_abci.TestResponseInfo.build_message"></a>

#### build`_`message

```python
def build_message() -> AbciMessage
```

Build the message.

<a id="packages.valory.protocols.abci.tests.test_abci.TestRequestInitChain"></a>

## TestRequestInitChain Objects

```python
class TestRequestInitChain(BaseTestMessageConstruction)
```

Test ABCI request init chain.

<a id="packages.valory.protocols.abci.tests.test_abci.TestRequestInitChain.build_message"></a>

#### build`_`message

```python
def build_message() -> AbciMessage
```

Build the message.

<a id="packages.valory.protocols.abci.tests.test_abci.TestResponseInitChain"></a>

## TestResponseInitChain Objects

```python
class TestResponseInitChain(BaseTestMessageConstruction)
```

Test ABCI response init chain.

<a id="packages.valory.protocols.abci.tests.test_abci.TestResponseInitChain.build_message"></a>

#### build`_`message

```python
def build_message() -> AbciMessage
```

Build the message.

<a id="packages.valory.protocols.abci.tests.test_abci.TestRequestQuery"></a>

## TestRequestQuery Objects

```python
class TestRequestQuery(BaseTestMessageConstruction)
```

Test ABCI response query.

<a id="packages.valory.protocols.abci.tests.test_abci.TestRequestQuery.build_message"></a>

#### build`_`message

```python
def build_message() -> AbciMessage
```

Build the message.

<a id="packages.valory.protocols.abci.tests.test_abci.TestResponseQuery"></a>

## TestResponseQuery Objects

```python
class TestResponseQuery(BaseTestMessageConstruction)
```

Test ABCI response query.

<a id="packages.valory.protocols.abci.tests.test_abci.TestResponseQuery.build_message"></a>

#### build`_`message

```python
def build_message() -> AbciMessage
```

Build the message.

<a id="packages.valory.protocols.abci.tests.test_abci.TestRequestBeginBlock"></a>

## TestRequestBeginBlock Objects

```python
class TestRequestBeginBlock(BaseTestMessageConstruction)
```

Test ABCI request begin block.

<a id="packages.valory.protocols.abci.tests.test_abci.TestRequestBeginBlock.build_message"></a>

#### build`_`message

```python
def build_message() -> AbciMessage
```

Build the message.

<a id="packages.valory.protocols.abci.tests.test_abci.TestResponseBeginBlock"></a>

## TestResponseBeginBlock Objects

```python
class TestResponseBeginBlock(BaseTestMessageConstruction)
```

Test ABCI response begin block.

<a id="packages.valory.protocols.abci.tests.test_abci.TestResponseBeginBlock.build_message"></a>

#### build`_`message

```python
def build_message() -> AbciMessage
```

Build the message.

<a id="packages.valory.protocols.abci.tests.test_abci.TestRequestCheckTx"></a>

## TestRequestCheckTx Objects

```python
class TestRequestCheckTx(BaseTestMessageConstruction)
```

Test ABCI request check tx.

<a id="packages.valory.protocols.abci.tests.test_abci.TestRequestCheckTx.build_message"></a>

#### build`_`message

```python
def build_message() -> AbciMessage
```

Build the message.

<a id="packages.valory.protocols.abci.tests.test_abci.TestResponseCheckTx"></a>

## TestResponseCheckTx Objects

```python
class TestResponseCheckTx(BaseTestMessageConstruction)
```

Test ABCI response check tx.

<a id="packages.valory.protocols.abci.tests.test_abci.TestResponseCheckTx.build_message"></a>

#### build`_`message

```python
def build_message() -> AbciMessage
```

Build the message.

<a id="packages.valory.protocols.abci.tests.test_abci.TestRequestDeliverTx"></a>

## TestRequestDeliverTx Objects

```python
class TestRequestDeliverTx(BaseTestMessageConstruction)
```

Test ABCI request deliver tx.

<a id="packages.valory.protocols.abci.tests.test_abci.TestRequestDeliverTx.build_message"></a>

#### build`_`message

```python
def build_message() -> AbciMessage
```

Build the message.

<a id="packages.valory.protocols.abci.tests.test_abci.TestResponseDeliverTx"></a>

## TestResponseDeliverTx Objects

```python
class TestResponseDeliverTx(BaseTestMessageConstruction)
```

Test ABCI response deliver tx.

<a id="packages.valory.protocols.abci.tests.test_abci.TestResponseDeliverTx.build_message"></a>

#### build`_`message

```python
def build_message() -> AbciMessage
```

Build the message.

<a id="packages.valory.protocols.abci.tests.test_abci.TestRequestEndBlock"></a>

## TestRequestEndBlock Objects

```python
class TestRequestEndBlock(BaseTestMessageConstruction)
```

Test ABCI request end block.

<a id="packages.valory.protocols.abci.tests.test_abci.TestRequestEndBlock.build_message"></a>

#### build`_`message

```python
def build_message() -> AbciMessage
```

Build the message.

<a id="packages.valory.protocols.abci.tests.test_abci.TestRequestSetOption"></a>

## TestRequestSetOption Objects

```python
class TestRequestSetOption(BaseTestMessageConstruction)
```

Test ABCI request end block.

<a id="packages.valory.protocols.abci.tests.test_abci.TestRequestSetOption.build_message"></a>

#### build`_`message

```python
def build_message() -> AbciMessage
```

Build the message.

<a id="packages.valory.protocols.abci.tests.test_abci.TestResponseEndBlock"></a>

## TestResponseEndBlock Objects

```python
class TestResponseEndBlock(BaseTestMessageConstruction)
```

Test ABCI response end block.

<a id="packages.valory.protocols.abci.tests.test_abci.TestResponseEndBlock.build_message"></a>

#### build`_`message

```python
def build_message() -> AbciMessage
```

Build the message.

<a id="packages.valory.protocols.abci.tests.test_abci.TestRequestCommit"></a>

## TestRequestCommit Objects

```python
class TestRequestCommit(BaseTestMessageConstruction)
```

Test ABCI request commit.

<a id="packages.valory.protocols.abci.tests.test_abci.TestRequestCommit.build_message"></a>

#### build`_`message

```python
def build_message() -> AbciMessage
```

Build the message.

<a id="packages.valory.protocols.abci.tests.test_abci.TestResponseCommit"></a>

## TestResponseCommit Objects

```python
class TestResponseCommit(BaseTestMessageConstruction)
```

Test ABCI response commit.

<a id="packages.valory.protocols.abci.tests.test_abci.TestResponseCommit.build_message"></a>

#### build`_`message

```python
def build_message() -> AbciMessage
```

Build the message.

<a id="packages.valory.protocols.abci.tests.test_abci.TestRequestListSnapshots"></a>

## TestRequestListSnapshots Objects

```python
class TestRequestListSnapshots(BaseTestMessageConstruction)
```

Test ABCI request list snapshots.

<a id="packages.valory.protocols.abci.tests.test_abci.TestRequestListSnapshots.build_message"></a>

#### build`_`message

```python
def build_message() -> AbciMessage
```

Build the message.

<a id="packages.valory.protocols.abci.tests.test_abci.TestResponseListSnapshots"></a>

## TestResponseListSnapshots Objects

```python
class TestResponseListSnapshots(BaseTestMessageConstruction)
```

Test ABCI response list snapshots.

<a id="packages.valory.protocols.abci.tests.test_abci.TestResponseListSnapshots.build_message"></a>

#### build`_`message

```python
def build_message() -> AbciMessage
```

Build the message.

<a id="packages.valory.protocols.abci.tests.test_abci.TestRequestOfferSnapshot"></a>

## TestRequestOfferSnapshot Objects

```python
class TestRequestOfferSnapshot(BaseTestMessageConstruction)
```

Test ABCI request offer snapshot.

<a id="packages.valory.protocols.abci.tests.test_abci.TestRequestOfferSnapshot.build_message"></a>

#### build`_`message

```python
def build_message() -> AbciMessage
```

Build the message.

<a id="packages.valory.protocols.abci.tests.test_abci.TestResponseOfferSnapshot"></a>

## TestResponseOfferSnapshot Objects

```python
class TestResponseOfferSnapshot(BaseTestMessageConstruction)
```

Test ABCI response offer snapshot.

<a id="packages.valory.protocols.abci.tests.test_abci.TestResponseOfferSnapshot.build_message"></a>

#### build`_`message

```python
def build_message() -> AbciMessage
```

Build the message.

<a id="packages.valory.protocols.abci.tests.test_abci.TestRequestLoadSnapshotChunk"></a>

## TestRequestLoadSnapshotChunk Objects

```python
class TestRequestLoadSnapshotChunk(BaseTestMessageConstruction)
```

Test ABCI request load snapshot chunk.

<a id="packages.valory.protocols.abci.tests.test_abci.TestRequestLoadSnapshotChunk.build_message"></a>

#### build`_`message

```python
def build_message() -> AbciMessage
```

Build the message.

<a id="packages.valory.protocols.abci.tests.test_abci.TestResponseLoadSnapshotChunk"></a>

## TestResponseLoadSnapshotChunk Objects

```python
class TestResponseLoadSnapshotChunk(BaseTestMessageConstruction)
```

Test ABCI response load snapshot chunk.

<a id="packages.valory.protocols.abci.tests.test_abci.TestResponseLoadSnapshotChunk.build_message"></a>

#### build`_`message

```python
def build_message() -> AbciMessage
```

Build the message.

<a id="packages.valory.protocols.abci.tests.test_abci.TestRequestApplySnapshotChunk"></a>

## TestRequestApplySnapshotChunk Objects

```python
class TestRequestApplySnapshotChunk(BaseTestMessageConstruction)
```

Test ABCI request load snapshot chunk.

<a id="packages.valory.protocols.abci.tests.test_abci.TestRequestApplySnapshotChunk.build_message"></a>

#### build`_`message

```python
def build_message() -> AbciMessage
```

Build the message.

<a id="packages.valory.protocols.abci.tests.test_abci.TestResponseApplySnapshotChunk"></a>

## TestResponseApplySnapshotChunk Objects

```python
class TestResponseApplySnapshotChunk(BaseTestMessageConstruction)
```

Test ABCI response apply snapshot chunk.

<a id="packages.valory.protocols.abci.tests.test_abci.TestResponseApplySnapshotChunk.build_message"></a>

#### build`_`message

```python
def build_message() -> AbciMessage
```

Build the message.

<a id="packages.valory.protocols.abci.tests.test_abci.TestDummy"></a>

## TestDummy Objects

```python
class TestDummy(BaseTestMessageConstruction)
```

Test ABCI request abci.

<a id="packages.valory.protocols.abci.tests.test_abci.TestDummy.build_message"></a>

#### build`_`message

```python
def build_message() -> AbciMessage
```

Build the message.

<a id="packages.valory.protocols.abci.tests.test_abci.TestResponseException"></a>

## TestResponseException Objects

```python
class TestResponseException(BaseTestMessageConstruction)
```

Test ABCI request abci.

<a id="packages.valory.protocols.abci.tests.test_abci.TestResponseException.build_message"></a>

#### build`_`message

```python
def build_message() -> AbciMessage
```

Build the message.

<a id="packages.valory.protocols.abci.tests.test_abci.TestResponseSetOption"></a>

## TestResponseSetOption Objects

```python
class TestResponseSetOption(BaseTestMessageConstruction)
```

Test ABCI request end block.

<a id="packages.valory.protocols.abci.tests.test_abci.TestResponseSetOption.build_message"></a>

#### build`_`message

```python
def build_message() -> AbciMessage
```

Build the message.

<a id="packages.valory.protocols.abci.tests.test_abci.test_incorrect_message"></a>

#### test`_`incorrect`_`message

```python
@mock.patch.object(
    message,
    "enforce",
    side_effect=AEAEnforceError("some error"),
)
def test_incorrect_message(mocked_enforce: Callable) -> None
```

Test that we raise an exception when the message is incorrect.

<a id="packages.valory.protocols.abci.tests.test_abci.test_performative_string_value"></a>

#### test`_`performative`_`string`_`value

```python
def test_performative_string_value() -> None
```

Test the string valoe of performatives.

<a id="packages.valory.protocols.abci.tests.test_abci.test_encoding_unknown_performative"></a>

#### test`_`encoding`_`unknown`_`performative

```python
def test_encoding_unknown_performative() -> None
```

Test that we raise an exception when the performative is unknown during encoding.

<a id="packages.valory.protocols.abci.tests.test_abci.test_decoding_unknown_performative"></a>

#### test`_`decoding`_`unknown`_`performative

```python
def test_decoding_unknown_performative() -> None
```

Test that we raise an exception when the performative is unknown during encoding.

<a id="packages.valory.protocols.abci.tests.test_abci.AgentDialogue"></a>

## AgentDialogue Objects

```python
class AgentDialogue(AbciDialogue)
```

The dialogue class maintains state of a dialogue and manages it.

<a id="packages.valory.protocols.abci.tests.test_abci.AgentDialogue.__init__"></a>

#### `__`init`__`

```python
def __init__(dialogue_label: DialogueLabel, self_address: Address, role: BaseDialogue.Role, message_class: Type[AbciMessage]) -> None
```

Initialize a dialogue.

**Arguments**:

- `dialogue_label`: the identifier of the dialogue
- `self_address`: the address of the entity for whom this dialogue is maintained
- `role`: the role of the agent this dialogue is maintained for
- `message_class`: the message class

<a id="packages.valory.protocols.abci.tests.test_abci.AgentDialogues"></a>

## AgentDialogues Objects

```python
class AgentDialogues(AbciDialogues)
```

The dialogues class keeps track of all dialogues.

<a id="packages.valory.protocols.abci.tests.test_abci.AgentDialogues.__init__"></a>

#### `__`init`__`

```python
def __init__(self_address: Address) -> None
```

Initialize dialogues.

**Arguments**:

- `self_address`: the address of the entity for whom this dialogue is maintained

<a id="packages.valory.protocols.abci.tests.test_abci.ServerDialogue"></a>

## ServerDialogue Objects

```python
class ServerDialogue(AbciDialogue)
```

The dialogue class maintains state of a dialogue and manages it.

<a id="packages.valory.protocols.abci.tests.test_abci.ServerDialogue.__init__"></a>

#### `__`init`__`

```python
def __init__(dialogue_label: DialogueLabel, self_address: Address, role: BaseDialogue.Role, message_class: Type[AbciMessage]) -> None
```

Initialize a dialogue.

**Arguments**:

- `dialogue_label`: the identifier of the dialogue
- `self_address`: the address of the entity for whom this dialogue is maintained
- `role`: the role of the agent this dialogue is maintained for
- `message_class`: the message class

<a id="packages.valory.protocols.abci.tests.test_abci.ServerDialogues"></a>

## ServerDialogues Objects

```python
class ServerDialogues(AbciDialogues)
```

The dialogues class keeps track of all dialogues.

<a id="packages.valory.protocols.abci.tests.test_abci.ServerDialogues.__init__"></a>

#### `__`init`__`

```python
def __init__(self_address: Address) -> None
```

Initialize dialogues.

**Arguments**:

- `self_address`: the address of the entity for whom this dialogue is maintained

<a id="packages.valory.protocols.abci.tests.test_abci.TestDialogues"></a>

## TestDialogues Objects

```python
class TestDialogues()
```

Tests abci dialogues.

<a id="packages.valory.protocols.abci.tests.test_abci.TestDialogues.setup_class"></a>

#### setup`_`class

```python
@classmethod
def setup_class(cls) -> None
```

Set up the test.

<a id="packages.valory.protocols.abci.tests.test_abci.TestDialogues.test_create_self_initiated"></a>

#### test`_`create`_`self`_`initiated

```python
def test_create_self_initiated() -> None
```

Test the self initialisation of a dialogue.

<a id="packages.valory.protocols.abci.tests.test_abci.TestDialogues.test_create_opponent_initiated"></a>

#### test`_`create`_`opponent`_`initiated

```python
def test_create_opponent_initiated() -> None
```

Test the opponent initialisation of a dialogue.

