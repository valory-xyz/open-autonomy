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
def tx_hist_payload_to_hex(verification: VerificationStatus,
                           tx_hash: Optional[str] = None) -> str
```

Serialise history payload to a hex string.

<a id="packages.valory.skills.transaction_settlement_abci.payload_tools.tx_hist_hex_to_payload"></a>

#### tx`_`hist`_`hex`_`to`_`payload

```python
def tx_hist_hex_to_payload(
        payload: str) -> Tuple[VerificationStatus, Optional[str]]
```

Decode history payload.

<a id="packages.valory.skills.transaction_settlement_abci.payload_tools.hash_payload_to_hex"></a>

#### hash`_`payload`_`to`_`hex

```python
def hash_payload_to_hex(safe_tx_hash: str,
                        ether_value: int,
                        safe_tx_gas: int,
                        to_address: str,
                        data: bytes,
                        operation: int = SafeOperation.CALL.value,
                        base_gas: int = 0,
                        safe_gas_price: int = 0,
                        gas_token: str = NULL_ADDRESS,
                        refund_receiver: str = NULL_ADDRESS,
                        use_flashbots: bool = False,
                        gas_limit: int = 0,
                        raise_on_failed_simulation: bool = False) -> str
```

Serialise to a hex string.

<a id="packages.valory.skills.transaction_settlement_abci.payload_tools.skill_input_hex_to_payload"></a>

#### skill`_`input`_`hex`_`to`_`payload

```python
def skill_input_hex_to_payload(payload: str) -> dict
```

Decode payload.

