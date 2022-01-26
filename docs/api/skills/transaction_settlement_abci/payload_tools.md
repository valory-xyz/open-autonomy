<a id="packages.valory.skills.transaction_settlement_abci.payload_tools"></a>

# packages.valory.skills.transaction`_`settlement`_`abci.payload`_`tools

Tools for payload serialization and deserialization.

<a id="packages.valory.skills.transaction_settlement_abci.payload_tools.VerificationStatus"></a>

## VerificationStatus Objects

```python
class VerificationStatus(Enum)
```

Tx verification status enumeration.

<a id="packages.valory.skills.transaction_settlement_abci.payload_tools.PayloadDeserializationError"></a>

## PayloadDeserializationError Objects

```python
class PayloadDeserializationError(Exception)
```

Exception for payload deserialization errors.

<a id="packages.valory.skills.transaction_settlement_abci.payload_tools.PayloadDeserializationError.__init__"></a>

#### `__`init`__`

```python
def __init__(*args: Any) -> None
```

Initialize the exception.

**Arguments**:

- `args`: extra arguments to pass to the constructor of `Exception`.

<a id="packages.valory.skills.transaction_settlement_abci.payload_tools.tx_hist_payload_to_hex"></a>

#### tx`_`hist`_`payload`_`to`_`hex

```python
def tx_hist_payload_to_hex(verification: VerificationStatus, tx_hash: Optional[str] = None) -> str
```

Serialise history payload to a hex string.

<a id="packages.valory.skills.transaction_settlement_abci.payload_tools.tx_hist_hex_to_payload"></a>

#### tx`_`hist`_`hex`_`to`_`payload

```python
def tx_hist_hex_to_payload(payload: str) -> Tuple[VerificationStatus, str]
```

Decode history payload.

<a id="packages.valory.skills.transaction_settlement_abci.payload_tools.skill_input_hex_to_payload"></a>

#### skill`_`input`_`hex`_`to`_`payload

```python
def skill_input_hex_to_payload(payload: str) -> Tuple[str, int, int, str, bytes]
```

Decode payload.

