<a id="packages.valory.skills.abstract_round_abci.serializer"></a>

# packages.valory.skills.abstract`_`round`_`abci.serializer

Serialize nested dictionaries to bytes using google.protobuf.Struct.

Prerequisites:
- All keys must be of type: str
- Values must be of type: bool, int, float, str, bytes, dict
- Strings must be unicode, as google.protobuf.Struct does not support bytes

The following encoding is required and performed,
and sentinel values are added for decoding:
- bytes to string
- integer to string

<a id="packages.valory.skills.abstract_round_abci.serializer.to_bytes"></a>

#### to`_`bytes

```python
def to_bytes(data: Dict[str, Any]) -> bytes
```

Serialize to bytes using protobuf. Adds extra data for type-casting.

<a id="packages.valory.skills.abstract_round_abci.serializer.from_bytes"></a>

#### from`_`bytes

```python
def from_bytes(buffer: bytes) -> Dict[str, Any]
```

Deserialize patched-up python dict from protobuf bytes.

<a id="packages.valory.skills.abstract_round_abci.serializer.patch"></a>

#### patch

```python
def patch(data: Dict[str, Any]) -> Dict[str, Any]
```

Patch for protobuf serialization. In-place operation.

<a id="packages.valory.skills.abstract_round_abci.serializer.unpatch"></a>

#### unpatch

```python
def unpatch(data: Dict[str, Any]) -> Dict[str, Any]
```

Unpatch for protobuf deserialization. In-place operation.

<a id="packages.valory.skills.abstract_round_abci.serializer.DictProtobufStructSerializer"></a>

## DictProtobufStructSerializer Objects

```python
class DictProtobufStructSerializer()
```

Class to keep backwards compatibility

