<a id="packages.valory.skills.price_estimation_abci.payloads"></a>

# packages.valory.skills.price`_`estimation`_`abci.payloads

This module contains the transaction payloads for the price_estimation app.

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

<a id="packages.valory.skills.price_estimation_abci.payloads.BasePriceEstimationPayload"></a>

## BasePriceEstimationPayload Objects

```python
class BasePriceEstimationPayload(BaseTxPayload,  ABC)
```

Base class for the price estimation demo.

<a id="packages.valory.skills.price_estimation_abci.payloads.BasePriceEstimationPayload.__hash__"></a>

#### `__`hash`__`

```python
def __hash__() -> int
```

Hash the payload.

<a id="packages.valory.skills.price_estimation_abci.payloads.RegistrationPayload"></a>

## RegistrationPayload Objects

```python
class RegistrationPayload(BasePriceEstimationPayload)
```

Represent a transaction payload of type 'registration'.

<a id="packages.valory.skills.price_estimation_abci.payloads.RandomnessPayload"></a>

## RandomnessPayload Objects

```python
class RandomnessPayload(BasePriceEstimationPayload)
```

Represent a transaction payload of type 'randomness'.

<a id="packages.valory.skills.price_estimation_abci.payloads.RandomnessPayload.__init__"></a>

#### `__`init`__`

```python
def __init__(sender: str, round_id: int, randomness: str, id_: Optional[str] = None) -> None
```

Initialize an 'select_keeper' transaction payload.

**Arguments**:

- `sender`: the sender (Ethereum) address
- `round_id`: the round id
- `randomness`: the randomness
- `id_`: the id of the transaction

<a id="packages.valory.skills.price_estimation_abci.payloads.RandomnessPayload.round_id"></a>

#### round`_`id

```python
@property
def round_id() -> int
```

Get the round id.

<a id="packages.valory.skills.price_estimation_abci.payloads.RandomnessPayload.randomness"></a>

#### randomness

```python
@property
def randomness() -> str
```

Get the randomness.

<a id="packages.valory.skills.price_estimation_abci.payloads.RandomnessPayload.data"></a>

#### data

```python
@property
def data() -> Dict
```

Get the data.

<a id="packages.valory.skills.price_estimation_abci.payloads.SelectKeeperPayload"></a>

## SelectKeeperPayload Objects

```python
class SelectKeeperPayload(BasePriceEstimationPayload)
```

Represent a transaction payload of type 'select_keeper'.

<a id="packages.valory.skills.price_estimation_abci.payloads.SelectKeeperPayload.__init__"></a>

#### `__`init`__`

```python
def __init__(sender: str, keeper: str, id_: Optional[str] = None) -> None
```

Initialize an 'select_keeper' transaction payload.

**Arguments**:

- `sender`: the sender (Ethereum) address
- `keeper`: the keeper selection
- `id_`: the id of the transaction

<a id="packages.valory.skills.price_estimation_abci.payloads.SelectKeeperPayload.keeper"></a>

#### keeper

```python
@property
def keeper() -> str
```

Get the keeper.

<a id="packages.valory.skills.price_estimation_abci.payloads.SelectKeeperPayload.data"></a>

#### data

```python
@property
def data() -> Dict
```

Get the data.

<a id="packages.valory.skills.price_estimation_abci.payloads.DeploySafePayload"></a>

## DeploySafePayload Objects

```python
class DeploySafePayload(BasePriceEstimationPayload)
```

Represent a transaction payload of type 'deploy_safe'.

<a id="packages.valory.skills.price_estimation_abci.payloads.DeploySafePayload.__init__"></a>

#### `__`init`__`

```python
def __init__(sender: str, safe_contract_address: str, id_: Optional[str] = None) -> None
```

Initialize a 'deploy_safe' transaction payload.

**Arguments**:

- `sender`: the sender (Ethereum) address
- `safe_contract_address`: the Safe contract address
- `id_`: the id of the transaction

<a id="packages.valory.skills.price_estimation_abci.payloads.DeploySafePayload.safe_contract_address"></a>

#### safe`_`contract`_`address

```python
@property
def safe_contract_address() -> str
```

Get the Safe contract address.

<a id="packages.valory.skills.price_estimation_abci.payloads.DeploySafePayload.data"></a>

#### data

```python
@property
def data() -> Dict
```

Get the data.

<a id="packages.valory.skills.price_estimation_abci.payloads.ValidatePayload"></a>

## ValidatePayload Objects

```python
class ValidatePayload(BasePriceEstimationPayload)
```

Represent a transaction payload of type 'validate'.

<a id="packages.valory.skills.price_estimation_abci.payloads.ValidatePayload.__init__"></a>

#### `__`init`__`

```python
def __init__(sender: str, vote: bool, id_: Optional[str] = None) -> None
```

Initialize an 'validate' transaction payload.

**Arguments**:

- `sender`: the sender (Ethereum) address
- `vote`: the vote
- `id_`: the id of the transaction

<a id="packages.valory.skills.price_estimation_abci.payloads.ValidatePayload.vote"></a>

#### vote

```python
@property
def vote() -> bool
```

Get the vote.

<a id="packages.valory.skills.price_estimation_abci.payloads.ValidatePayload.data"></a>

#### data

```python
@property
def data() -> Dict
```

Get the data.

<a id="packages.valory.skills.price_estimation_abci.payloads.ObservationPayload"></a>

## ObservationPayload Objects

```python
class ObservationPayload(BasePriceEstimationPayload)
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
class EstimatePayload(BasePriceEstimationPayload)
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

<a id="packages.valory.skills.price_estimation_abci.payloads.SignaturePayload"></a>

## SignaturePayload Objects

```python
class SignaturePayload(BasePriceEstimationPayload)
```

Represent a transaction payload of type 'signature'.

<a id="packages.valory.skills.price_estimation_abci.payloads.SignaturePayload.__init__"></a>

#### `__`init`__`

```python
def __init__(sender: str, signature: str, id_: Optional[str] = None) -> None
```

Initialize an 'signature' transaction payload.

**Arguments**:

- `sender`: the sender (Ethereum) address
- `signature`: the signature
- `id_`: the id of the transaction

<a id="packages.valory.skills.price_estimation_abci.payloads.SignaturePayload.signature"></a>

#### signature

```python
@property
def signature() -> str
```

Get the signature.

<a id="packages.valory.skills.price_estimation_abci.payloads.SignaturePayload.data"></a>

#### data

```python
@property
def data() -> Dict
```

Get the data.

<a id="packages.valory.skills.price_estimation_abci.payloads.TransactionHashPayload"></a>

## TransactionHashPayload Objects

```python
class TransactionHashPayload(BasePriceEstimationPayload)
```

Represent a transaction payload of type 'tx_hash'.

<a id="packages.valory.skills.price_estimation_abci.payloads.TransactionHashPayload.__init__"></a>

#### `__`init`__`

```python
def __init__(sender: str, tx_hash: str, id_: Optional[str] = None) -> None
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
def tx_hash() -> str
```

Get the tx_hash.

<a id="packages.valory.skills.price_estimation_abci.payloads.TransactionHashPayload.data"></a>

#### data

```python
@property
def data() -> Dict
```

Get the data.

<a id="packages.valory.skills.price_estimation_abci.payloads.FinalizationTxPayload"></a>

## FinalizationTxPayload Objects

```python
class FinalizationTxPayload(BasePriceEstimationPayload)
```

Represent a transaction payload of type 'finalization'.

<a id="packages.valory.skills.price_estimation_abci.payloads.FinalizationTxPayload.__init__"></a>

#### `__`init`__`

```python
def __init__(sender: str, tx_hash: str, id_: Optional[str] = None) -> None
```

Initialize an 'finalization' transaction payload.

**Arguments**:

- `sender`: the sender (Ethereum) address
- `tx_hash`: the 'safe' transaction hash
- `id_`: the id of the transaction

<a id="packages.valory.skills.price_estimation_abci.payloads.FinalizationTxPayload.tx_hash"></a>

#### tx`_`hash

```python
@property
def tx_hash() -> str
```

Get the signature.

<a id="packages.valory.skills.price_estimation_abci.payloads.FinalizationTxPayload.data"></a>

#### data

```python
@property
def data() -> Dict
```

Get the data.

