<a id="packages.valory.protocols.abci.custom_types"></a>

# packages.valory.protocols.abci.custom`_`types

This module contains class representations corresponding to every custom type in the protocol specification.

<a id="packages.valory.protocols.abci.custom_types.BlockParams"></a>

## BlockParams Objects

```python
class BlockParams()
```

This class represents an instance of BlockParams.

<a id="packages.valory.protocols.abci.custom_types.BlockParams.__init__"></a>

#### `__`init`__`

```python
def __init__(max_bytes: int, max_gas: int)
```

Initialise an instance of BlockParams.

<a id="packages.valory.protocols.abci.custom_types.BlockParams.encode"></a>

#### encode

```python
@staticmethod
def encode(block_params_protobuf_object,
           block_params_object: "BlockParams") -> None
```

Encode an instance of this class into the protocol buffer object.

The protocol buffer object in the block_params_protobuf_object argument is matched with the instance of this class in the 'block_params_object' argument.

**Arguments**:

- `block_params_protobuf_object`: the protocol buffer object whose type corresponds with this class.
- `block_params_object`: an instance of this class to be encoded in the protocol buffer object.

<a id="packages.valory.protocols.abci.custom_types.BlockParams.decode"></a>

#### decode

```python
@classmethod
def decode(cls, block_params_protobuf_object) -> "BlockParams"
```

Decode a protocol buffer object that corresponds with this class into an instance of this class.

A new instance of this class is created that matches the protocol buffer object in the 'block_params_protobuf_object' argument.

**Arguments**:

- `block_params_protobuf_object`: the protocol buffer object whose type corresponds with this class.

**Returns**:

A new instance of this class that matches the protocol buffer object in the 'block_params_protobuf_object' argument.

<a id="packages.valory.protocols.abci.custom_types.BlockParams.__eq__"></a>

#### `__`eq`__`

```python
def __eq__(other) -> bool
```

Compare with another object.

<a id="packages.valory.protocols.abci.custom_types.Duration"></a>

## Duration Objects

```python
class Duration()
```

This class represents an instance of Duration.

<a id="packages.valory.protocols.abci.custom_types.Duration.__init__"></a>

#### `__`init`__`

```python
def __init__(seconds: int, nanos: int)
```

Initialise an instance of Duration.

**Arguments**:

- `seconds`: Signed seconds of the span of time.
Must be from -315,576,000,000 to +315,576,000,000 inclusive.
- `nanos`: Signed fractions of a second at nanosecond resolution of the span of time.
Durations less than one second are represented with a 0 seconds field and
a positive or negative nanos field. For durations of one second or more,
a non-zero value for the nanos field must be of the same sign as the seconds field.
Must be from -999,999,999 to +999,999,999 inclusive.

<a id="packages.valory.protocols.abci.custom_types.Duration.encode"></a>

#### encode

```python
@staticmethod
def encode(duration_protobuf_object, duration_object: "Duration") -> None
```

Encode an instance of this class into the protocol buffer object.

The protocol buffer object in the duration_protobuf_object argument is matched with the instance of this class in the 'duration_object' argument.

**Arguments**:

- `duration_protobuf_object`: the protocol buffer object whose type corresponds with this class.
- `duration_object`: an instance of this class to be encoded in the protocol buffer object.

<a id="packages.valory.protocols.abci.custom_types.Duration.decode"></a>

#### decode

```python
@classmethod
def decode(cls, duration_protobuf_object) -> "Duration"
```

Decode a protocol buffer object that corresponds with this class into an instance of this class.

A new instance of this class is created that matches the protocol buffer object in the 'duration_protobuf_object' argument.

**Arguments**:

- `duration_protobuf_object`: the protocol buffer object whose type corresponds with this class.

**Returns**:

A new instance of this class that matches the protocol buffer object in the 'duration_protobuf_object' argument.

<a id="packages.valory.protocols.abci.custom_types.Duration.__eq__"></a>

#### `__`eq`__`

```python
def __eq__(other) -> bool
```

Compare with another object.

<a id="packages.valory.protocols.abci.custom_types.EvidenceParams"></a>

## EvidenceParams Objects

```python
class EvidenceParams()
```

This class represents an instance of EvidenceParams.

<a id="packages.valory.protocols.abci.custom_types.EvidenceParams.__init__"></a>

#### `__`init`__`

```python
def __init__(max_age_num_blocks: int, max_age_duration: Duration,
             max_bytes: int)
```

Initialise an instance of BlockParams.

<a id="packages.valory.protocols.abci.custom_types.EvidenceParams.encode"></a>

#### encode

```python
@staticmethod
def encode(evidence_params_protobuf_object,
           evidence_params_object: "EvidenceParams") -> None
```

Encode an instance of this class into the protocol buffer object.

The protocol buffer object in the evidence_params_protobuf_object argument is matched with the instance of this class in the 'evidence_params_object' argument.

**Arguments**:

- `evidence_params_protobuf_object`: the protocol buffer object whose type corresponds with this class.
- `evidence_params_object`: an instance of this class to be encoded in the protocol buffer object.

<a id="packages.valory.protocols.abci.custom_types.EvidenceParams.decode"></a>

#### decode

```python
@classmethod
def decode(cls, evidence_params_protobuf_object) -> "EvidenceParams"
```

Decode a protocol buffer object that corresponds with this class into an instance of this class.

A new instance of this class is created that matches the protocol buffer object in the 'evidence_params_protobuf_object' argument.

**Arguments**:

- `evidence_params_protobuf_object`: the protocol buffer object whose type corresponds with this class.

**Returns**:

A new instance of this class that matches the protocol buffer object in the 'evidence_params_protobuf_object' argument.

<a id="packages.valory.protocols.abci.custom_types.EvidenceParams.__eq__"></a>

#### `__`eq`__`

```python
def __eq__(other) -> bool
```

Compare with another object.

<a id="packages.valory.protocols.abci.custom_types.ValidatorParams"></a>

## ValidatorParams Objects

```python
class ValidatorParams()
```

This class represents an instance of ValidatorParams.

<a id="packages.valory.protocols.abci.custom_types.ValidatorParams.__init__"></a>

#### `__`init`__`

```python
def __init__(pub_key_types: List[str])
```

Initialise an instance of BlockParams.

<a id="packages.valory.protocols.abci.custom_types.ValidatorParams.encode"></a>

#### encode

```python
@staticmethod
def encode(validator_params_protobuf_object,
           validator_params_object: "ValidatorParams") -> None
```

Encode an instance of this class into the protocol buffer object.

The protocol buffer object in the validator_params_protobuf_object argument is matched with the instance of this class in the 'validator_params_object' argument.

**Arguments**:

- `validator_params_protobuf_object`: the protocol buffer object whose type corresponds with this class.
- `validator_params_object`: an instance of this class to be encoded in the protocol buffer object.

<a id="packages.valory.protocols.abci.custom_types.ValidatorParams.decode"></a>

#### decode

```python
@classmethod
def decode(cls, validator_params_protobuf_object) -> "ValidatorParams"
```

Decode a protocol buffer object that corresponds with this class into an instance of this class.

A new instance of this class is created that matches the protocol buffer object in the 'validator_params_protobuf_object' argument.

**Arguments**:

- `validator_params_protobuf_object`: the protocol buffer object whose type corresponds with this class.

**Returns**:

A new instance of this class that matches the protocol buffer object in the 'validator_params_protobuf_object' argument.

<a id="packages.valory.protocols.abci.custom_types.ValidatorParams.__eq__"></a>

#### `__`eq`__`

```python
def __eq__(other) -> bool
```

Compare with another object.

<a id="packages.valory.protocols.abci.custom_types.VersionParams"></a>

## VersionParams Objects

```python
class VersionParams()
```

This class represents an instance of VersionParams.

<a id="packages.valory.protocols.abci.custom_types.VersionParams.__init__"></a>

#### `__`init`__`

```python
def __init__(app_version: int)
```

Initialise an instance of BlockParams.

<a id="packages.valory.protocols.abci.custom_types.VersionParams.encode"></a>

#### encode

```python
@staticmethod
def encode(version_params_protobuf_object,
           version_params_object: "VersionParams") -> None
```

Encode an instance of this class into the protocol buffer object.

The protocol buffer object in the version_params_protobuf_object argument is matched with the instance of this class in the 'version_params_object' argument.

**Arguments**:

- `version_params_protobuf_object`: the protocol buffer object whose type corresponds with this class.
- `version_params_object`: an instance of this class to be encoded in the protocol buffer object.

<a id="packages.valory.protocols.abci.custom_types.VersionParams.decode"></a>

#### decode

```python
@classmethod
def decode(cls, version_params_protobuf_object) -> "VersionParams"
```

Decode a protocol buffer object that corresponds with this class into an instance of this class.

A new instance of this class is created that matches the protocol buffer object in the 'version_params_protobuf_object' argument.

**Arguments**:

- `version_params_protobuf_object`: the protocol buffer object whose type corresponds with this class.

**Returns**:

A new instance of this class that matches the protocol buffer object in the 'version_params_protobuf_object' argument.

<a id="packages.valory.protocols.abci.custom_types.VersionParams.__eq__"></a>

#### `__`eq`__`

```python
def __eq__(other) -> bool
```

Compare with another object.

<a id="packages.valory.protocols.abci.custom_types.ConsensusParams"></a>

## ConsensusParams Objects

```python
class ConsensusParams()
```

This class represents an instance of ConsensusParams.

<a id="packages.valory.protocols.abci.custom_types.ConsensusParams.__init__"></a>

#### `__`init`__`

```python
def __init__(block: "BlockParams", evidence_params: "EvidenceParams",
             validator_params: "ValidatorParams",
             version_params: "VersionParams")
```

Initialise an instance of ConsensusParams.

<a id="packages.valory.protocols.abci.custom_types.ConsensusParams.encode"></a>

#### encode

```python
@staticmethod
def encode(consensus_params_protobuf_object,
           consensus_params_object: Optional["ConsensusParams"]) -> None
```

Encode an instance of this class into the protocol buffer object.

The protocol buffer object in the consensus_params_protobuf_object argument is matched with the instance of this class in the 'consensus_params_object' argument.

**Arguments**:

- `consensus_params_protobuf_object`: the protocol buffer object whose type corresponds with this class.
- `consensus_params_object`: an instance of this class to be encoded in the protocol buffer object.

<a id="packages.valory.protocols.abci.custom_types.ConsensusParams.decode"></a>

#### decode

```python
@classmethod
def decode(cls, consensus_params_protobuf_object) -> "ConsensusParams"
```

Decode a protocol buffer object that corresponds with this class into an instance of this class.

A new instance of this class is created that matches the protocol buffer object in the 'consensus_params_protobuf_object' argument.

**Arguments**:

- `consensus_params_protobuf_object`: the protocol buffer object whose type corresponds with this class.

**Returns**:

A new instance of this class that matches the protocol buffer object in the 'consensus_params_protobuf_object' argument.

<a id="packages.valory.protocols.abci.custom_types.ConsensusParams.__eq__"></a>

#### `__`eq`__`

```python
def __eq__(other)
```

Compare with another object.

<a id="packages.valory.protocols.abci.custom_types.EventAttribute"></a>

## EventAttribute Objects

```python
class EventAttribute()
```

This class represents an instance of EventAttribute.

<a id="packages.valory.protocols.abci.custom_types.EventAttribute.__init__"></a>

#### `__`init`__`

```python
def __init__(key: bytes, value: bytes, index: bool)
```

Initialise an instance of EventAttribute.

<a id="packages.valory.protocols.abci.custom_types.EventAttribute.encode"></a>

#### encode

```python
@staticmethod
def encode(event_attribute_protobuf_object,
           event_attribute_object: "EventAttribute") -> None
```

Encode an instance of this class into the protocol buffer object.

The protocol buffer object in the event_attribute_protobuf_object argument is matched with the instance of this class in the 'event_attribute_object' argument.

**Arguments**:

- `event_attribute_protobuf_object`: the protocol buffer object whose type corresponds with this class.
- `event_attribute_object`: an instance of this class to be encoded in the protocol buffer object.

<a id="packages.valory.protocols.abci.custom_types.EventAttribute.decode"></a>

#### decode

```python
@classmethod
def decode(cls, event_attribute_protobuf_object) -> "EventAttribute"
```

Decode a protocol buffer object that corresponds with this class into an instance of this class.

A new instance of this class is created that matches the protocol buffer object in the 'event_attribute_protobuf_object' argument.

**Arguments**:

- `event_attribute_protobuf_object`: the protocol buffer object whose type corresponds with this class.

**Returns**:

A new instance of this class that matches the protocol buffer object in the 'event_attribute_protobuf_object' argument.

<a id="packages.valory.protocols.abci.custom_types.EventAttribute.__eq__"></a>

#### `__`eq`__`

```python
def __eq__(other)
```

Compare with another object.

<a id="packages.valory.protocols.abci.custom_types.Event"></a>

## Event Objects

```python
class Event()
```

This class represents an instance of Event.

<a id="packages.valory.protocols.abci.custom_types.Event.__init__"></a>

#### `__`init`__`

```python
def __init__(type_: str, attributes: List[EventAttribute])
```

Initialise an instance of Event.

<a id="packages.valory.protocols.abci.custom_types.Event.encode"></a>

#### encode

```python
@staticmethod
def encode(event_protobuf_object, event_object: "Event") -> None
```

Encode an instance of this class into the protocol buffer object.

The protocol buffer object in the event_protobuf_object argument is matched with the instance of this class in the 'event_object' argument.

**Arguments**:

- `event_protobuf_object`: the protocol buffer object whose type corresponds with this class.
- `event_object`: an instance of this class to be encoded in the protocol buffer object.

<a id="packages.valory.protocols.abci.custom_types.Event.decode"></a>

#### decode

```python
@classmethod
def decode(cls, event_protobuf_object) -> "Event"
```

Decode a protocol buffer object that corresponds with this class into an instance of this class.

A new instance of this class is created that matches the protocol buffer object in the 'event_protobuf_object' argument.

**Arguments**:

- `event_protobuf_object`: the protocol buffer object whose type corresponds with this class.

**Returns**:

A new instance of this class that matches the protocol buffer object in the 'event_protobuf_object' argument.

<a id="packages.valory.protocols.abci.custom_types.Event.__eq__"></a>

#### `__`eq`__`

```python
def __eq__(other)
```

Compare with another object.

<a id="packages.valory.protocols.abci.custom_types.Events"></a>

## Events Objects

```python
class Events()
```

This class represents an instance of Events.

<a id="packages.valory.protocols.abci.custom_types.Events.__init__"></a>

#### `__`init`__`

```python
def __init__(events: List[Event])
```

Initialise an instance of Events.

<a id="packages.valory.protocols.abci.custom_types.Events.encode"></a>

#### encode

```python
@staticmethod
def encode(events_protobuf_object, events_object: "Events") -> None
```

Encode an instance of this class into the protocol buffer object.

The protocol buffer object in the events_protobuf_object argument is matched with the instance of this class in the 'events_object' argument.

**Arguments**:

- `events_protobuf_object`: the protocol buffer object whose type corresponds with this class.
- `events_object`: an instance of this class to be encoded in the protocol buffer object.

<a id="packages.valory.protocols.abci.custom_types.Events.decode"></a>

#### decode

```python
@classmethod
def decode(cls, events_protobuf_object) -> "Events"
```

Decode a protocol buffer object that corresponds with this class into an instance of this class.

A new instance of this class is created that matches the protocol buffer object in the 'events_protobuf_object' argument.

**Arguments**:

- `events_protobuf_object`: the protocol buffer object whose type corresponds with this class.

**Returns**:

A new instance of this class that matches the protocol buffer object in the 'events_protobuf_object' argument.

<a id="packages.valory.protocols.abci.custom_types.Events.__eq__"></a>

#### `__`eq`__`

```python
def __eq__(other)
```

Compare with another object.

<a id="packages.valory.protocols.abci.custom_types.EvidenceType"></a>

## EvidenceType Objects

```python
class EvidenceType(Enum)
```

This class represent an instance of EvidenceType.

<a id="packages.valory.protocols.abci.custom_types.Evidence"></a>

## Evidence Objects

```python
class Evidence()
```

This class represent an instance of Evidence.

<a id="packages.valory.protocols.abci.custom_types.Evidence.__init__"></a>

#### `__`init`__`

```python
def __init__(evidence_type: EvidenceType, validator: "Validator", height: int,
             time: "Timestamp", total_voting_power: int)
```

Initialise an instance of Evidences.

<a id="packages.valory.protocols.abci.custom_types.Evidence.encode"></a>

#### encode

```python
@staticmethod
def encode(evidence_protobuf_object, evidence_object: "Evidence") -> None
```

Encode an instance of this class into the protocol buffer object.

The protocol buffer object in the evidence_protobuf_object argument is matched with the instance of this class in the 'evidence_object' argument.

**Arguments**:

- `evidence_protobuf_object`: the protocol buffer object whose type corresponds with this class.
- `evidence_object`: an instance of this class to be encoded in the protocol buffer object.

<a id="packages.valory.protocols.abci.custom_types.Evidence.decode"></a>

#### decode

```python
@classmethod
def decode(cls, evidence_protobuf_object) -> "Evidence"
```

Decode a protocol buffer object that corresponds with this class into an instance of this class.

A new instance of this class is created that matches the protocol buffer object in the 'evidence_protobuf_object' argument.

**Arguments**:

- `evidence_protobuf_object`: the protocol buffer object whose type corresponds with this class.

**Returns**:

A new instance of this class that matches the protocol buffer object in the 'evidence_protobuf_object' argument.

<a id="packages.valory.protocols.abci.custom_types.Evidence.__eq__"></a>

#### `__`eq`__`

```python
def __eq__(other)
```

Compare with another object.

<a id="packages.valory.protocols.abci.custom_types.Evidences"></a>

## Evidences Objects

```python
class Evidences()
```

This class represents an instance of Evidences.

<a id="packages.valory.protocols.abci.custom_types.Evidences.__init__"></a>

#### `__`init`__`

```python
def __init__(byzantine_validators: List[Evidence])
```

Initialise an instance of Evidences.

<a id="packages.valory.protocols.abci.custom_types.Evidences.encode"></a>

#### encode

```python
@staticmethod
def encode(evidences_protobuf_object, evidences_object: "Evidences") -> None
```

Encode an instance of this class into the protocol buffer object.

The protocol buffer object in the evidences_protobuf_object argument is matched with the instance of this class in the 'evidences_object' argument.

**Arguments**:

- `evidences_protobuf_object`: the protocol buffer object whose type corresponds with this class.
- `evidences_object`: an instance of this class to be encoded in the protocol buffer object.

<a id="packages.valory.protocols.abci.custom_types.Evidences.decode"></a>

#### decode

```python
@classmethod
def decode(cls, evidences_protobuf_object) -> "Evidences"
```

Decode a protocol buffer object that corresponds with this class into an instance of this class.

A new instance of this class is created that matches the protocol buffer object in the 'evidences_protobuf_object' argument.

**Arguments**:

- `evidences_protobuf_object`: the protocol buffer object whose type corresponds with this class.

**Returns**:

A new instance of this class that matches the protocol buffer object in the 'evidences_protobuf_object' argument.

<a id="packages.valory.protocols.abci.custom_types.Evidences.__eq__"></a>

#### `__`eq`__`

```python
def __eq__(other)
```

Compare with another object.

<a id="packages.valory.protocols.abci.custom_types.CheckTxTypeEnum"></a>

## CheckTxTypeEnum Objects

```python
class CheckTxTypeEnum(Enum)
```

CheckTxTypeEnum for tx check.

<a id="packages.valory.protocols.abci.custom_types.CheckTxType"></a>

## CheckTxType Objects

```python
class CheckTxType()
```

This class represents an instance of CheckTxType.

<a id="packages.valory.protocols.abci.custom_types.CheckTxType.__init__"></a>

#### `__`init`__`

```python
def __init__(check_tx_type: CheckTxTypeEnum)
```

Initialise an instance of CheckTxType.

<a id="packages.valory.protocols.abci.custom_types.CheckTxType.encode"></a>

#### encode

```python
@staticmethod
def encode(check_tx_type_protobuf_object,
           check_tx_type_object: "CheckTxType") -> None
```

Encode an instance of this class into the protocol buffer object.

The protocol buffer object in the check_tx_type_protobuf_object argument is matched with the instance of this class in the 'check_tx_type_object' argument.

**Arguments**:

- `check_tx_type_protobuf_object`: the protocol buffer object whose type corresponds with this class.
- `check_tx_type_object`: an instance of this class to be encoded in the protocol buffer object.

<a id="packages.valory.protocols.abci.custom_types.CheckTxType.decode"></a>

#### decode

```python
@classmethod
def decode(cls, check_tx_type_protobuf_object) -> "CheckTxType"
```

Decode a protocol buffer object that corresponds with this class into an instance of this class.

A new instance of this class is created that matches the protocol buffer object in the 'check_tx_type_protobuf_object' argument.

**Arguments**:

- `check_tx_type_protobuf_object`: the protocol buffer object whose type corresponds with this class.

**Returns**:

A new instance of this class that matches the protocol buffer object in the 'check_tx_type_protobuf_object' argument.

<a id="packages.valory.protocols.abci.custom_types.CheckTxType.__eq__"></a>

#### `__`eq`__`

```python
def __eq__(other)
```

Compare with another object.

<a id="packages.valory.protocols.abci.custom_types.ConsensusVersion"></a>

## ConsensusVersion Objects

```python
class ConsensusVersion()
```

This class represents an instance of ConsensusVersion.

<a id="packages.valory.protocols.abci.custom_types.ConsensusVersion.__init__"></a>

#### `__`init`__`

```python
def __init__(block: int, app: int)
```

Initialise an instance of ConsensusVersion.

<a id="packages.valory.protocols.abci.custom_types.ConsensusVersion.encode"></a>

#### encode

```python
@staticmethod
def encode(consensus_version_protobuf_object,
           consensus_version_object: "ConsensusVersion") -> None
```

Encode an instance of this class into the protocol buffer object.

The protocol buffer object in the consensus_version_protobuf_object argument is matched with the instance of this class in the 'consensus_version_object' argument.

**Arguments**:

- `consensus_version_protobuf_object`: the protocol buffer object whose type corresponds with this class.
- `consensus_version_object`: an instance of this class to be encoded in the protocol buffer object.

<a id="packages.valory.protocols.abci.custom_types.ConsensusVersion.decode"></a>

#### decode

```python
@classmethod
def decode(cls, consensus_version_protobuf_object) -> "ConsensusVersion"
```

Decode a protocol buffer object that corresponds with this class into an instance of this class.

A new instance of this class is created that matches the protocol buffer object in the 'consensus_version_protobuf_object' argument.

**Arguments**:

- `consensus_version_protobuf_object`: the protocol buffer object whose type corresponds with this class.

**Returns**:

A new instance of this class that matches the protocol buffer object in the 'consensus_version_protobuf_object' argument.

<a id="packages.valory.protocols.abci.custom_types.ConsensusVersion.__eq__"></a>

#### `__`eq`__`

```python
def __eq__(other)
```

Compare with another object.

<a id="packages.valory.protocols.abci.custom_types.PartSetHeader"></a>

## PartSetHeader Objects

```python
class PartSetHeader()
```

This class represents an instance of PartSetHeader.

<a id="packages.valory.protocols.abci.custom_types.PartSetHeader.__init__"></a>

#### `__`init`__`

```python
def __init__(total: int, hash_: bytes)
```

Initialise an instance of PartSetHeader.

<a id="packages.valory.protocols.abci.custom_types.PartSetHeader.encode"></a>

#### encode

```python
@staticmethod
def encode(part_set_header_protobuf_object,
           part_set_header_object: "PartSetHeader") -> None
```

Encode an instance of this class into the protocol buffer object.

The protocol buffer object in the part_set_header_protobuf_object argument is matched with the instance of this class in the 'part_set_header_object' argument.

**Arguments**:

- `part_set_header_protobuf_object`: the protocol buffer object whose type corresponds with this class.
- `part_set_header_object`: an instance of this class to be encoded in the protocol buffer object.

<a id="packages.valory.protocols.abci.custom_types.PartSetHeader.decode"></a>

#### decode

```python
@classmethod
def decode(cls, part_set_header_protobuf_object) -> "PartSetHeader"
```

Decode a protocol buffer object that corresponds with this class into an instance of this class.

A new instance of this class is created that matches the protocol buffer object in the 'part_set_header_protobuf_object' argument.

**Arguments**:

- `part_set_header_protobuf_object`: the protocol buffer object whose type corresponds with this class.

**Returns**:

A new instance of this class that matches the protocol buffer object in the 'part_set_header_protobuf_object' argument.

<a id="packages.valory.protocols.abci.custom_types.PartSetHeader.__eq__"></a>

#### `__`eq`__`

```python
def __eq__(other)
```

Compare with another object.

<a id="packages.valory.protocols.abci.custom_types.BlockID"></a>

## BlockID Objects

```python
class BlockID()
```

This class represents an instance of BlockID.

<a id="packages.valory.protocols.abci.custom_types.BlockID.__init__"></a>

#### `__`init`__`

```python
def __init__(hash_: bytes, part_set_header: PartSetHeader)
```

Initialise an instance of BlockID.

<a id="packages.valory.protocols.abci.custom_types.BlockID.encode"></a>

#### encode

```python
@staticmethod
def encode(block_id_protobuf_object, block_id_object: "BlockID") -> None
```

Encode an instance of this class into the protocol buffer object.

The protocol buffer object in the block_id_protobuf_object argument is matched with the instance of this class in the 'block_id_object' argument.

**Arguments**:

- `block_id_protobuf_object`: the protocol buffer object whose type corresponds with this class.
- `block_id_object`: an instance of this class to be encoded in the protocol buffer object.

<a id="packages.valory.protocols.abci.custom_types.BlockID.decode"></a>

#### decode

```python
@classmethod
def decode(cls, block_id_protobuf_object) -> "BlockID"
```

Decode a protocol buffer object that corresponds with this class into an instance of this class.

A new instance of this class is created that matches the protocol buffer object in the 'block_id_protobuf_object' argument.

**Arguments**:

- `block_id_protobuf_object`: the protocol buffer object whose type corresponds with this class.

**Returns**:

A new instance of this class that matches the protocol buffer object in the 'block_id_protobuf_object' argument.

<a id="packages.valory.protocols.abci.custom_types.BlockID.__eq__"></a>

#### `__`eq`__`

```python
def __eq__(other)
```

Compare with another object.

<a id="packages.valory.protocols.abci.custom_types.Header"></a>

## Header Objects

```python
class Header()
```

This class represents an instance of Header.

<a id="packages.valory.protocols.abci.custom_types.Header.__init__"></a>

#### `__`init`__`

```python
def __init__(version: ConsensusVersion, chain_id: str, height: int,
             time: "Timestamp", last_block_id: BlockID,
             last_commit_hash: bytes, data_hash: bytes, validators_hash: bytes,
             next_validators_hash: bytes, consensus_hash: bytes,
             app_hash: bytes, last_results_hash: bytes, evidence_hash: bytes,
             proposer_address: bytes)
```

Initialise an instance of Header.

<a id="packages.valory.protocols.abci.custom_types.Header.timestamp"></a>

#### timestamp

```python
@property
def timestamp() -> datetime.datetime
```

Get the block timestamp.

<a id="packages.valory.protocols.abci.custom_types.Header.encode"></a>

#### encode

```python
@staticmethod
def encode(header_protobuf_object, header_object: "Header") -> None
```

Encode an instance of this class into the protocol buffer object.

The protocol buffer object in the header_protobuf_object argument is matched with the instance of this class in the 'header_object' argument.

**Arguments**:

- `header_protobuf_object`: the protocol buffer object whose type corresponds with this class.
- `header_object`: an instance of this class to be encoded in the protocol buffer object.

<a id="packages.valory.protocols.abci.custom_types.Header.decode"></a>

#### decode

```python
@classmethod
def decode(cls, header_protobuf_object) -> "Header"
```

Decode a protocol buffer object that corresponds with this class into an instance of this class.

A new instance of this class is created that matches the protocol buffer object in the 'header_protobuf_object' argument.

**Arguments**:

- `header_protobuf_object`: the protocol buffer object whose type corresponds with this class.

**Returns**:

A new instance of this class that matches the protocol buffer object in the 'header_protobuf_object' argument.

<a id="packages.valory.protocols.abci.custom_types.Header.__eq__"></a>

#### `__`eq`__`

```python
def __eq__(other)
```

Compare with another object.

<a id="packages.valory.protocols.abci.custom_types.Validator"></a>

## Validator Objects

```python
class Validator()
```

This class represents an instance of Validator.

<a id="packages.valory.protocols.abci.custom_types.Validator.__init__"></a>

#### `__`init`__`

```python
def __init__(address: bytes, power: int)
```

Initialise an instance of Validator.

<a id="packages.valory.protocols.abci.custom_types.Validator.encode"></a>

#### encode

```python
@staticmethod
def encode(validator_protobuf_object, validator_object: "Validator") -> None
```

Encode an instance of this class into the protocol buffer object.

The protocol buffer object in the validator_protobuf_object argument is matched with the instance of this class in the 'validator_object' argument.

**Arguments**:

- `validator_protobuf_object`: the protocol buffer object whose type corresponds with this class.
- `validator_object`: an instance of this class to be encoded in the protocol buffer object.

<a id="packages.valory.protocols.abci.custom_types.Validator.decode"></a>

#### decode

```python
@classmethod
def decode(cls, validator_protobuf_object) -> "Validator"
```

Decode a protocol buffer object that corresponds with this class into an instance of this class.

A new instance of this class is created that matches the protocol buffer object in the 'validator_protobuf_object' argument.

**Arguments**:

- `validator_protobuf_object`: the protocol buffer object whose type corresponds with this class.

**Returns**:

A new instance of this class that matches the protocol buffer object in the 'validator_protobuf_object' argument.

<a id="packages.valory.protocols.abci.custom_types.Validator.__eq__"></a>

#### `__`eq`__`

```python
def __eq__(other)
```

Compare with another object.

<a id="packages.valory.protocols.abci.custom_types.VoteInfo"></a>

## VoteInfo Objects

```python
class VoteInfo()
```

This class represents an instance of VoteInfo.

<a id="packages.valory.protocols.abci.custom_types.VoteInfo.__init__"></a>

#### `__`init`__`

```python
def __init__(validator: Validator, signed_last_block: bool)
```

Initialise an instance of Validator.

<a id="packages.valory.protocols.abci.custom_types.VoteInfo.encode"></a>

#### encode

```python
@staticmethod
def encode(vote_info_protobuf_object, vote_info_object: "VoteInfo") -> None
```

Encode an instance of this class into the protocol buffer object.

The protocol buffer object in the vote_info_protobuf_object argument is matched with the instance of this class in the 'vote_info_object' argument.

**Arguments**:

- `vote_info_protobuf_object`: the protocol buffer object whose type corresponds with this class.
- `vote_info_object`: an instance of this class to be encoded in the protocol buffer object.

<a id="packages.valory.protocols.abci.custom_types.VoteInfo.decode"></a>

#### decode

```python
@classmethod
def decode(cls, vote_info_protobuf_object) -> "VoteInfo"
```

Decode a protocol buffer object that corresponds with this class into an instance of this class.

A new instance of this class is created that matches the protocol buffer object in the 'vote_info_protobuf_object' argument.

**Arguments**:

- `vote_info_protobuf_object`: the protocol buffer object whose type corresponds with this class.

**Returns**:

A new instance of this class that matches the protocol buffer object in the 'vote_info_protobuf_object' argument.

<a id="packages.valory.protocols.abci.custom_types.VoteInfo.__eq__"></a>

#### `__`eq`__`

```python
def __eq__(other)
```

Compare with another object.

<a id="packages.valory.protocols.abci.custom_types.LastCommitInfo"></a>

## LastCommitInfo Objects

```python
class LastCommitInfo()
```

This class represents an instance of LastCommitInfo.

<a id="packages.valory.protocols.abci.custom_types.LastCommitInfo.__init__"></a>

#### `__`init`__`

```python
def __init__(round_: int, votes: List[VoteInfo])
```

Initialise an instance of LastCommitInfo.

<a id="packages.valory.protocols.abci.custom_types.LastCommitInfo.encode"></a>

#### encode

```python
@staticmethod
def encode(last_commit_info_protobuf_object,
           last_commit_info_object: "LastCommitInfo") -> None
```

Encode an instance of this class into the protocol buffer object.

The protocol buffer object in the last_commit_info_protobuf_object argument is matched with the instance of this class in the 'last_commit_info_object' argument.

**Arguments**:

- `last_commit_info_protobuf_object`: the protocol buffer object whose type corresponds with this class.
- `last_commit_info_object`: an instance of this class to be encoded in the protocol buffer object.

<a id="packages.valory.protocols.abci.custom_types.LastCommitInfo.decode"></a>

#### decode

```python
@classmethod
def decode(cls, last_commit_info_protobuf_object) -> "LastCommitInfo"
```

Decode a protocol buffer object that corresponds with this class into an instance of this class.

A new instance of this class is created that matches the protocol buffer object in the 'last_commit_info_protobuf_object' argument.

**Arguments**:

- `last_commit_info_protobuf_object`: the protocol buffer object whose type corresponds with this class.

**Returns**:

A new instance of this class that matches the protocol buffer object in the 'last_commit_info_protobuf_object' argument.

<a id="packages.valory.protocols.abci.custom_types.LastCommitInfo.__eq__"></a>

#### `__`eq`__`

```python
def __eq__(other)
```

Compare with another object.

<a id="packages.valory.protocols.abci.custom_types.ProofOp"></a>

## ProofOp Objects

```python
class ProofOp()
```

This class represents an instance of ProofOp.

<a id="packages.valory.protocols.abci.custom_types.ProofOp.__init__"></a>

#### `__`init`__`

```python
def __init__(type_: str, key: bytes, data: bytes)
```

Initialise an instance of ProofOp.

ProofOp defines an operation used for calculating Merkle root
The data could be arbitrary format, providing necessary data
for example neighbouring node hash.

**Arguments**:

- `type_`: the type
- `key`: the key
- `data`: the data

<a id="packages.valory.protocols.abci.custom_types.ProofOp.encode"></a>

#### encode

```python
@staticmethod
def encode(proof_op_protobuf_object, proof_op_object: "ProofOp") -> None
```

Encode an instance of this class into the protocol buffer object.

The protocol buffer object in the proof_op_protobuf_object argument is matched with the instance of this class in the 'proof_op_object' argument.

**Arguments**:

- `proof_op_protobuf_object`: the protocol buffer object whose type corresponds with this class.
- `proof_op_object`: an instance of this class to be encoded in the protocol buffer object.

<a id="packages.valory.protocols.abci.custom_types.ProofOp.decode"></a>

#### decode

```python
@classmethod
def decode(cls, proof_op_protobuf_object) -> "ProofOp"
```

Decode a protocol buffer object that corresponds with this class into an instance of this class.

A new instance of this class is created that matches the protocol buffer object in the 'proof_op_protobuf_object' argument.

**Arguments**:

- `proof_op_protobuf_object`: the protocol buffer object whose type corresponds with this class.

**Returns**:

A new instance of this class that matches the protocol buffer object in the 'proof_op_protobuf_object' argument.

<a id="packages.valory.protocols.abci.custom_types.ProofOp.__eq__"></a>

#### `__`eq`__`

```python
def __eq__(other)
```

Compare with another object.

<a id="packages.valory.protocols.abci.custom_types.ProofOps"></a>

## ProofOps Objects

```python
class ProofOps()
```

This class represents an instance of ProofOps.

<a id="packages.valory.protocols.abci.custom_types.ProofOps.__init__"></a>

#### `__`init`__`

```python
def __init__(proof_ops: List[ProofOp])
```

Initialise an instance of ProofOps.

**Arguments**:

- `proof_ops`: a list of ProofOp instances.

<a id="packages.valory.protocols.abci.custom_types.ProofOps.encode"></a>

#### encode

```python
@staticmethod
def encode(proof_ops_protobuf_object, proof_ops_object: "ProofOps") -> None
```

Encode an instance of this class into the protocol buffer object.

The protocol buffer object in the proof_ops_protobuf_object argument is matched with the instance of this class in the 'proof_ops_object' argument.

**Arguments**:

- `proof_ops_protobuf_object`: the protocol buffer object whose type corresponds with this class.
- `proof_ops_object`: an instance of this class to be encoded in the protocol buffer object.

<a id="packages.valory.protocols.abci.custom_types.ProofOps.decode"></a>

#### decode

```python
@classmethod
def decode(cls, proof_ops_protobuf_object) -> "ProofOps"
```

Decode a protocol buffer object that corresponds with this class into an instance of this class.

A new instance of this class is created that matches the protocol buffer object in the 'proof_ops_protobuf_object' argument.

**Arguments**:

- `proof_ops_protobuf_object`: the protocol buffer object whose type corresponds with this class.

**Returns**:

A new instance of this class that matches the protocol buffer object in the 'proof_ops_protobuf_object' argument.

<a id="packages.valory.protocols.abci.custom_types.ProofOps.__eq__"></a>

#### `__`eq`__`

```python
def __eq__(other)
```

Compare with another object.

<a id="packages.valory.protocols.abci.custom_types.ResultType"></a>

## ResultType Objects

```python
class ResultType(Enum)
```

This class represents an instance of ResultType.

<a id="packages.valory.protocols.abci.custom_types.ResultType.UNKNOWN"></a>

#### UNKNOWN

Unknown result, abort all snapshot restoration

<a id="packages.valory.protocols.abci.custom_types.ResultType.ACCEPT"></a>

#### ACCEPT

Snapshot accepted, apply chunks

<a id="packages.valory.protocols.abci.custom_types.ResultType.ABORT"></a>

#### ABORT

Abort all snapshot restoration

<a id="packages.valory.protocols.abci.custom_types.ResultType.REJECT"></a>

#### REJECT

Reject this specific snapshot, try others

<a id="packages.valory.protocols.abci.custom_types.ResultType.REJECT_FORMAT"></a>

#### REJECT`_`FORMAT

Reject all snapshots of this format, try others

<a id="packages.valory.protocols.abci.custom_types.ResultType.REJECT_SENDER"></a>

#### REJECT`_`SENDER

Reject all snapshots from the sender(s), try others

<a id="packages.valory.protocols.abci.custom_types.Result"></a>

## Result Objects

```python
class Result()
```

This class represents an instance of Result.

<a id="packages.valory.protocols.abci.custom_types.Result.__init__"></a>

#### `__`init`__`

```python
def __init__(result_type: ResultType)
```

Initialise an instance of Result.

<a id="packages.valory.protocols.abci.custom_types.Result.encode"></a>

#### encode

```python
@staticmethod
def encode(result_protobuf_object, result_object: "Result") -> None
```

Encode an instance of this class into the protocol buffer object.

The protocol buffer object in the result_protobuf_object argument is matched with the instance of this class in the 'result_object' argument.

**Arguments**:

- `result_protobuf_object`: the protocol buffer object whose type corresponds with this class.
- `result_object`: an instance of this class to be encoded in the protocol buffer object.

<a id="packages.valory.protocols.abci.custom_types.Result.decode"></a>

#### decode

```python
@classmethod
def decode(cls, result_protobuf_object) -> "Result"
```

Decode a protocol buffer object that corresponds with this class into an instance of this class.

A new instance of this class is created that matches the protocol buffer object in the 'result_protobuf_object' argument.

**Arguments**:

- `result_protobuf_object`: the protocol buffer object whose type corresponds with this class.

**Returns**:

A new instance of this class that matches the protocol buffer object in the 'result_protobuf_object' argument.

<a id="packages.valory.protocols.abci.custom_types.Result.__eq__"></a>

#### `__`eq`__`

```python
def __eq__(other)
```

Compare with another object.

<a id="packages.valory.protocols.abci.custom_types.Snapshot"></a>

## Snapshot Objects

```python
class Snapshot()
```

This class represents an instance of Snapshot.

<a id="packages.valory.protocols.abci.custom_types.Snapshot.__init__"></a>

#### `__`init`__`

```python
def __init__(height: int, format_: int, chunks: int, hash_: bytes,
             metadata: bytes)
```

Initialise an instance of Snapshot.

<a id="packages.valory.protocols.abci.custom_types.Snapshot.encode"></a>

#### encode

```python
@staticmethod
def encode(snapshot_protobuf_object, snapshot_object: "Snapshot") -> None
```

Encode an instance of this class into the protocol buffer object.

The protocol buffer object in the snapshot_protobuf_object argument is matched with the instance of this class in the 'snapshot_object' argument.

**Arguments**:

- `snapshot_protobuf_object`: the protocol buffer object whose type corresponds with this class.
- `snapshot_object`: an instance of this class to be encoded in the protocol buffer object.

<a id="packages.valory.protocols.abci.custom_types.Snapshot.decode"></a>

#### decode

```python
@classmethod
def decode(cls, snapshot_protobuf_object) -> "Snapshot"
```

Decode a protocol buffer object that corresponds with this class into an instance of this class.

A new instance of this class is created that matches the protocol buffer object in the 'snapshot_protobuf_object' argument.

**Arguments**:

- `snapshot_protobuf_object`: the protocol buffer object whose type corresponds with this class.

**Returns**:

A new instance of this class that matches the protocol buffer object in the 'snapshot_protobuf_object' argument.

<a id="packages.valory.protocols.abci.custom_types.Snapshot.__eq__"></a>

#### `__`eq`__`

```python
def __eq__(other)
```

Compare with another object.

<a id="packages.valory.protocols.abci.custom_types.SnapShots"></a>

## SnapShots Objects

```python
class SnapShots()
```

This class represents an instance of SnapShots.

<a id="packages.valory.protocols.abci.custom_types.SnapShots.__init__"></a>

#### `__`init`__`

```python
def __init__(snapshots: List[Snapshot])
```

Initialise an instance of SnapShots.

<a id="packages.valory.protocols.abci.custom_types.SnapShots.encode"></a>

#### encode

```python
@staticmethod
def encode(snapshots_protobuf_object, snapshots_object: "SnapShots") -> None
```

Encode an instance of this class into the protocol buffer object.

The protocol buffer object in the snapshots_protobuf_object argument is matched with the instance of this class in the 'snapshots_object' argument.

**Arguments**:

- `snapshots_protobuf_object`: the protocol buffer object whose type corresponds with this class.
- `snapshots_object`: an instance of this class to be encoded in the protocol buffer object.

<a id="packages.valory.protocols.abci.custom_types.SnapShots.decode"></a>

#### decode

```python
@classmethod
def decode(cls, snapshots_protobuf_object) -> "SnapShots"
```

Decode a protocol buffer object that corresponds with this class into an instance of this class.

A new instance of this class is created that matches the protocol buffer object in the 'snapshots_protobuf_object' argument.

**Arguments**:

- `snapshots_protobuf_object`: the protocol buffer object whose type corresponds with this class.

**Returns**:

A new instance of this class that matches the protocol buffer object in the 'snapshots_protobuf_object' argument.

<a id="packages.valory.protocols.abci.custom_types.SnapShots.__eq__"></a>

#### `__`eq`__`

```python
def __eq__(other)
```

Compare with another object.

<a id="packages.valory.protocols.abci.custom_types.Timestamp"></a>

## Timestamp Objects

```python
class Timestamp()
```

This class represents an instance of Timestamp.

<a id="packages.valory.protocols.abci.custom_types.Timestamp.__init__"></a>

#### `__`init`__`

```python
def __init__(seconds: int, nanos: int)
```

Initialise an instance of Timestamp.

**Arguments**:

- `seconds`: Represents seconds of UTC time since Unix epoch
1970-01-01T00:00:00Z. Must be from 0001-01-01T00:00:00Z to
9999-12-31T23:59:59Z inclusive.
- `nanos`: Non-negative fractions of a second at nanosecond resolution.
Negative second values with fractions must still have non-negative nanos values
that count forward in time. Must be from 0 to 999,999,999 inclusive.

<a id="packages.valory.protocols.abci.custom_types.Timestamp.encode"></a>

#### encode

```python
@staticmethod
def encode(timestamp_protobuf_object, timestamp_object: "Timestamp") -> None
```

Encode an instance of this class into the protocol buffer object.

The protocol buffer object in the timestamp_protobuf_object argument is matched with the instance of this class in the 'timestamp_object' argument.

**Arguments**:

- `timestamp_protobuf_object`: the protocol buffer object whose type corresponds with this class.
- `timestamp_object`: an instance of this class to be encoded in the protocol buffer object.

<a id="packages.valory.protocols.abci.custom_types.Timestamp.decode"></a>

#### decode

```python
@classmethod
def decode(cls, timestamp_protobuf_object) -> "Timestamp"
```

Decode a protocol buffer object that corresponds with this class into an instance of this class.

A new instance of this class is created that matches the protocol buffer object in the 'timestamp_protobuf_object' argument.

**Arguments**:

- `timestamp_protobuf_object`: the protocol buffer object whose type corresponds with this class.

**Returns**:

A new instance of this class that matches the protocol buffer object in the 'timestamp_protobuf_object' argument.

<a id="packages.valory.protocols.abci.custom_types.Timestamp.__eq__"></a>

#### `__`eq`__`

```python
def __eq__(other) -> bool
```

Compare with another object.

<a id="packages.valory.protocols.abci.custom_types.PublicKey"></a>

## PublicKey Objects

```python
class PublicKey()
```

This class represents an instance of PublicKey.

<a id="packages.valory.protocols.abci.custom_types.PublicKey.PublicKeyType"></a>

## PublicKeyType Objects

```python
class PublicKeyType(Enum)
```

Enumeration of public key types supported by Tendermint.

<a id="packages.valory.protocols.abci.custom_types.PublicKey.__init__"></a>

#### `__`init`__`

```python
def __init__(data: bytes, key_type: PublicKeyType) -> None
```

Initialize the public key object.

**Arguments**:

- `data`: the data of the public key.
- `key_type`: the type of the public key.

<a id="packages.valory.protocols.abci.custom_types.PublicKey.encode"></a>

#### encode

```python
@staticmethod
def encode(public_key_protobuf_object, public_key_object: "PublicKey") -> None
```

Encode an instance of this class into the protocol buffer object.

The protocol buffer object in the public_key_protobuf_object argument is matched with the instance of this class in the 'public_key_object' argument.

**Arguments**:

- `public_key_protobuf_object`: the protocol buffer object whose type corresponds with this class.
- `public_key_object`: an instance of this class to be encoded in the protocol buffer object.

<a id="packages.valory.protocols.abci.custom_types.PublicKey.decode"></a>

#### decode

```python
@classmethod
def decode(cls, public_key_protobuf_object) -> "PublicKey"
```

Decode a protocol buffer object that corresponds with this class into an instance of this class.

A new instance of this class is created that matches the protocol buffer object in the 'public_key_protobuf_object' argument.

**Arguments**:

- `public_key_protobuf_object`: the protocol buffer object whose type corresponds with this class.

**Returns**:

A new instance of this class that matches the protocol buffer object in the 'public_key_protobuf_object' argument.

<a id="packages.valory.protocols.abci.custom_types.PublicKey.__eq__"></a>

#### `__`eq`__`

```python
def __eq__(other)
```

Compare with another object.

<a id="packages.valory.protocols.abci.custom_types.ValidatorUpdate"></a>

## ValidatorUpdate Objects

```python
class ValidatorUpdate()
```

This class represents an instance of ValidatorUpdate.

<a id="packages.valory.protocols.abci.custom_types.ValidatorUpdate.__init__"></a>

#### `__`init`__`

```python
def __init__(pub_key: PublicKey, power: int)
```

Initialise an instance of ValidatorUpdate.

<a id="packages.valory.protocols.abci.custom_types.ValidatorUpdate.encode"></a>

#### encode

```python
@staticmethod
def encode(validator_update_protobuf_object,
           validator_update_object: "ValidatorUpdate") -> None
```

Encode an instance of this class into the protocol buffer object.

The protocol buffer object in the validator_update_protobuf_object argument is matched with the instance of this class in the 'validator_update_object' argument.

**Arguments**:

- `validator_update_protobuf_object`: the protocol buffer object whose type corresponds with this class.
- `validator_update_object`: an instance of this class to be encoded in the protocol buffer object.

<a id="packages.valory.protocols.abci.custom_types.ValidatorUpdate.decode"></a>

#### decode

```python
@classmethod
def decode(cls, validator_update_protobuf_object) -> "ValidatorUpdate"
```

Decode a protocol buffer object that corresponds with this class into an instance of this class.

A new instance of this class is created that matches the protocol buffer object in the 'validator_update_protobuf_object' argument.

**Arguments**:

- `validator_update_protobuf_object`: the protocol buffer object whose type corresponds with this class.

**Returns**:

A new instance of this class that matches the protocol buffer object in the 'validator_update_protobuf_object' argument.

<a id="packages.valory.protocols.abci.custom_types.ValidatorUpdate.__eq__"></a>

#### `__`eq`__`

```python
def __eq__(other)
```

Compare with another object.

<a id="packages.valory.protocols.abci.custom_types.ValidatorUpdates"></a>

## ValidatorUpdates Objects

```python
class ValidatorUpdates()
```

This class represents an instance of ValidatorUpdates.

<a id="packages.valory.protocols.abci.custom_types.ValidatorUpdates.__init__"></a>

#### `__`init`__`

```python
def __init__(validator_updates: List[ValidatorUpdate])
```

Initialise an instance of ValidatorUpdates.

<a id="packages.valory.protocols.abci.custom_types.ValidatorUpdates.encode"></a>

#### encode

```python
@staticmethod
def encode(validator_updates_protobuf_object,
           validator_updates_object: "ValidatorUpdates") -> None
```

Encode an instance of this class into the protocol buffer object.

The protocol buffer object in the validator_updates_protobuf_object argument is matched with the instance of this class in the 'validator_updates_object' argument.

**Arguments**:

- `validator_updates_protobuf_object`: the protocol buffer object whose type corresponds with this class.
- `validator_updates_object`: an instance of this class to be encoded in the protocol buffer object.

<a id="packages.valory.protocols.abci.custom_types.ValidatorUpdates.decode"></a>

#### decode

```python
@classmethod
def decode(cls, validator_updates_protobuf_object) -> "ValidatorUpdates"
```

Decode a protocol buffer object that corresponds with this class into an instance of this class.

A new instance of this class is created that matches the protocol buffer object in the 'validator_updates_protobuf_object' argument.

**Arguments**:

- `validator_updates_protobuf_object`: the protocol buffer object whose type corresponds with this class.

**Returns**:

A new instance of this class that matches the protocol buffer object in the 'validator_updates_protobuf_object' argument.

<a id="packages.valory.protocols.abci.custom_types.ValidatorUpdates.__eq__"></a>

#### `__`eq`__`

```python
def __eq__(other)
```

Compare with another object.

