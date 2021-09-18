<a id="packages.valory.protocols.abci.serialization"></a>

# packages.valory.protocols.abci.serialization

Serialization module for abci protocol.

<a id="packages.valory.protocols.abci.serialization.AbciSerializer"></a>

## AbciSerializer Objects

```python
class AbciSerializer(Serializer)
```

Serialization for the 'abci' protocol.

<a id="packages.valory.protocols.abci.serialization.AbciSerializer.encode"></a>

#### encode

```python
@staticmethod
def encode(msg: Message) -> bytes
```

Encode a 'Abci' message into bytes.

**Arguments**:

- `msg`: the message object.

**Returns**:

the bytes.

<a id="packages.valory.protocols.abci.serialization.AbciSerializer.decode"></a>

#### decode

```python
@staticmethod
def decode(obj: bytes) -> Message
```

Decode bytes into a 'Abci' message.

**Arguments**:

- `obj`: the bytes object.

**Returns**:

the 'Abci' message.

