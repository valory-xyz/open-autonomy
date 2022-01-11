<a id="packages.valory.skills.price_estimation_abci.payloads"></a>

# packages.valory.skills.price`_`estimation`_`abci.payloads

This module contains the transaction payloads for common apps.

<a id="packages.valory.skills.price_estimation_abci.payloads.TransactionType"></a>

## TransactionType Objects

```python
class TransactionType(Enum)
```

Enumeration of transaction types.

<a id="packages.valory.skills.price_estimation_abci.payloads.TransactionType.__str__"></a>

#### `__`str`__`

```python
def __str__() -> str
```

Get the string value of the transaction type.

<a id="packages.valory.skills.price_estimation_abci.payloads.TransactionHashPayload"></a>

## TransactionHashPayload Objects

```python
class TransactionHashPayload(BaseTxPayload)
```

Represent a transaction payload of type 'tx_hash'.

<a id="packages.valory.skills.price_estimation_abci.payloads.TransactionHashPayload.__init__"></a>

#### `__`init`__`

```python
def __init__(sender: str, tx_hash: Optional[str] = None, id_: Optional[str] = None) -> None
```

Initialize an 'tx_hash' transaction payload.

**Arguments**:

- `sender`: the sender (Ethereum) address
- `tx_hash`: the tx_hash
- `id_`: the id of the transaction

<a id="packages.valory.skills.price_estimation_abci.payloads.TransactionHashPayload.tx_hash"></a>

#### tx`_`hash

```python
@property
def tx_hash() -> Optional[str]
```

Get the tx_hash.

<a id="packages.valory.skills.price_estimation_abci.payloads.TransactionHashPayload.data"></a>

#### data

```python
@property
def data() -> Dict
```

Get the data.

<a id="packages.valory.skills.price_estimation_abci.payloads.ObservationPayload"></a>

## ObservationPayload Objects

```python
class ObservationPayload(BaseTxPayload)
```

Represent a transaction payload of type 'observation'.

<a id="packages.valory.skills.price_estimation_abci.payloads.ObservationPayload.__init__"></a>

#### `__`init`__`

```python
def __init__(sender: str, observation: float, id_: Optional[str] = None) -> None
```

Initialize an 'observation' transaction payload.

**Arguments**:

- `sender`: the sender (Ethereum) address
- `observation`: the observation
- `id_`: the id of the transaction

<a id="packages.valory.skills.price_estimation_abci.payloads.ObservationPayload.observation"></a>

#### observation

```python
@property
def observation() -> float
```

Get the observation.

<a id="packages.valory.skills.price_estimation_abci.payloads.ObservationPayload.data"></a>

#### data

```python
@property
def data() -> Dict
```

Get the data.

<a id="packages.valory.skills.price_estimation_abci.payloads.EstimatePayload"></a>

## EstimatePayload Objects

```python
class EstimatePayload(BaseTxPayload)
```

Represent a transaction payload of type 'estimate'.

<a id="packages.valory.skills.price_estimation_abci.payloads.EstimatePayload.__init__"></a>

#### `__`init`__`

```python
def __init__(sender: str, estimate: float, id_: Optional[str] = None) -> None
```

Initialize an 'estimate' transaction payload.

**Arguments**:

- `sender`: the sender (Ethereum) address
- `estimate`: the estimate
- `id_`: the id of the transaction

<a id="packages.valory.skills.price_estimation_abci.payloads.EstimatePayload.estimate"></a>

#### estimate

```python
@property
def estimate() -> float
```

Get the estimate.

<a id="packages.valory.skills.price_estimation_abci.payloads.EstimatePayload.data"></a>

#### data

```python
@property
def data() -> Dict
```

Get the data.

