<a id="packages.valory.skills.transaction_settlement_abci.payloads"></a>

# packages.valory.skills.transaction`_`settlement`_`abci.payloads

This module contains the transaction payloads for common apps.

<a id="packages.valory.skills.transaction_settlement_abci.payloads.TransactionType"></a>

## TransactionType Objects

```python
class TransactionType(Enum)
```

Enumeration of transaction types.

<a id="packages.valory.skills.transaction_settlement_abci.payloads.TransactionType.__str__"></a>

#### `__`str`__`

```python
def __str__() -> str
```

Get the string value of the transaction type.

<a id="packages.valory.skills.transaction_settlement_abci.payloads.RandomnessPayload"></a>

## RandomnessPayload Objects

```python
class RandomnessPayload(BaseTxPayload)
```

Represent a transaction payload of type 'randomness'.

<a id="packages.valory.skills.transaction_settlement_abci.payloads.RandomnessPayload.__init__"></a>

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

<a id="packages.valory.skills.transaction_settlement_abci.payloads.RandomnessPayload.round_id"></a>

#### round`_`id

```python
@property
def round_id() -> int
```

Get the round id.

<a id="packages.valory.skills.transaction_settlement_abci.payloads.RandomnessPayload.randomness"></a>

#### randomness

```python
@property
def randomness() -> str
```

Get the randomness.

<a id="packages.valory.skills.transaction_settlement_abci.payloads.RandomnessPayload.data"></a>

#### data

```python
@property
def data() -> Dict
```

Get the data.

<a id="packages.valory.skills.transaction_settlement_abci.payloads.SelectKeeperPayload"></a>

## SelectKeeperPayload Objects

```python
class SelectKeeperPayload(BaseTxPayload)
```

Represent a transaction payload of type 'select_keeper'.

<a id="packages.valory.skills.transaction_settlement_abci.payloads.SelectKeeperPayload.__init__"></a>

#### `__`init`__`

```python
def __init__(sender: str, keeper: str, id_: Optional[str] = None) -> None
```

Initialize an 'select_keeper' transaction payload.

**Arguments**:

- `sender`: the sender (Ethereum) address
- `keeper`: the keeper selection
- `id_`: the id of the transaction

<a id="packages.valory.skills.transaction_settlement_abci.payloads.SelectKeeperPayload.keeper"></a>

#### keeper

```python
@property
def keeper() -> str
```

Get the keeper.

<a id="packages.valory.skills.transaction_settlement_abci.payloads.SelectKeeperPayload.data"></a>

#### data

```python
@property
def data() -> Dict
```

Get the data.

<a id="packages.valory.skills.transaction_settlement_abci.payloads.ValidatePayload"></a>

## ValidatePayload Objects

```python
class ValidatePayload(BaseTxPayload)
```

Represent a transaction payload of type 'validate'.

<a id="packages.valory.skills.transaction_settlement_abci.payloads.ValidatePayload.__init__"></a>

#### `__`init`__`

```python
def __init__(sender: str, is_settled: Optional[bool] = None, transfers: Optional[List] = None, tx_result: Optional[str] = None, id_: Optional[str] = None) -> None
```

Initialize an 'validate' transaction payload.

**Arguments**:

- `sender`: the sender (Ethereum) address
- `is_settled`: boolean to check whether the transaction is settled
- `transfers`: the transfer events
- `tx_result`: a stringified dict containing is_settled and transfers
- `id_`: the id of the transaction

<a id="packages.valory.skills.transaction_settlement_abci.payloads.ValidatePayload.vote"></a>

#### vote

```python
@property
def vote() -> Optional[bool]
```

Get the vote.

<a id="packages.valory.skills.transaction_settlement_abci.payloads.ValidatePayload.transfers"></a>

#### transfers

```python
@property
def transfers() -> Optional[List]
```

Get the transfers.

<a id="packages.valory.skills.transaction_settlement_abci.payloads.ValidatePayload.tx_result"></a>

#### tx`_`result

```python
@property
def tx_result() -> Optional[str]
```

Get the tx result.

<a id="packages.valory.skills.transaction_settlement_abci.payloads.ValidatePayload.data"></a>

#### data

```python
@property
def data() -> Dict
```

Get the data.

<a id="packages.valory.skills.transaction_settlement_abci.payloads.CheckTransactionHistoryPayload"></a>

## CheckTransactionHistoryPayload Objects

```python
class CheckTransactionHistoryPayload(BaseTxPayload)
```

Represent a transaction payload of type 'check'.

<a id="packages.valory.skills.transaction_settlement_abci.payloads.CheckTransactionHistoryPayload.__init__"></a>

#### `__`init`__`

```python
def __init__(sender: str, verified_res: str, id_: Optional[str] = None) -> None
```

Initialize an 'validate' transaction payload.

**Arguments**:

- `sender`: the sender (Ethereum) address
- `verified_res`: the vote
- `id_`: the id of the transaction

<a id="packages.valory.skills.transaction_settlement_abci.payloads.CheckTransactionHistoryPayload.verified_res"></a>

#### verified`_`res

```python
@property
def verified_res() -> str
```

Get the verified result.

<a id="packages.valory.skills.transaction_settlement_abci.payloads.CheckTransactionHistoryPayload.data"></a>

#### data

```python
@property
def data() -> Dict
```

Get the data.

<a id="packages.valory.skills.transaction_settlement_abci.payloads.SignaturePayload"></a>

## SignaturePayload Objects

```python
class SignaturePayload(BaseTxPayload)
```

Represent a transaction payload of type 'signature'.

<a id="packages.valory.skills.transaction_settlement_abci.payloads.SignaturePayload.__init__"></a>

#### `__`init`__`

```python
def __init__(sender: str, signature: str, id_: Optional[str] = None) -> None
```

Initialize an 'signature' transaction payload.

**Arguments**:

- `sender`: the sender (Ethereum) address
- `signature`: the signature
- `id_`: the id of the transaction

<a id="packages.valory.skills.transaction_settlement_abci.payloads.SignaturePayload.signature"></a>

#### signature

```python
@property
def signature() -> str
```

Get the signature.

<a id="packages.valory.skills.transaction_settlement_abci.payloads.SignaturePayload.data"></a>

#### data

```python
@property
def data() -> Dict
```

Get the data.

<a id="packages.valory.skills.transaction_settlement_abci.payloads.FinalizationTxPayload"></a>

## FinalizationTxPayload Objects

```python
class FinalizationTxPayload(BaseTxPayload)
```

Represent a transaction payload of type 'finalization'.

<a id="packages.valory.skills.transaction_settlement_abci.payloads.FinalizationTxPayload.__init__"></a>

#### `__`init`__`

```python
def __init__(sender: str, tx_data: Optional[Dict[str, Union[str, int, None]]] = None, id_: Optional[str] = None) -> None
```

Initialize an 'finalization' transaction payload.

**Arguments**:

- `sender`: the sender (Ethereum) address
- `tx_data`: the transaction data
- `id_`: the id of the transaction

<a id="packages.valory.skills.transaction_settlement_abci.payloads.FinalizationTxPayload.tx_data"></a>

#### tx`_`data

```python
@property
def tx_data() -> Optional[Dict[str, Union[str, int, None]]]
```

Get the tx_data.

<a id="packages.valory.skills.transaction_settlement_abci.payloads.FinalizationTxPayload.data"></a>

#### data

```python
@property
def data() -> Dict[str, Dict[str, Union[str, int, None]]]
```

Get the data.

<a id="packages.valory.skills.transaction_settlement_abci.payloads.ResetPayload"></a>

## ResetPayload Objects

```python
class ResetPayload(BaseTxPayload)
```

Represent a transaction payload of type 'reset'.

<a id="packages.valory.skills.transaction_settlement_abci.payloads.ResetPayload.__init__"></a>

#### `__`init`__`

```python
def __init__(sender: str, period_count: int, id_: Optional[str] = None) -> None
```

Initialize an 'rest' transaction payload.

**Arguments**:

- `sender`: the sender (Ethereum) address
- `period_count`: the period count id
- `id_`: the id of the transaction

<a id="packages.valory.skills.transaction_settlement_abci.payloads.ResetPayload.period_count"></a>

#### period`_`count

```python
@property
def period_count() -> int
```

Get the period_count.

<a id="packages.valory.skills.transaction_settlement_abci.payloads.ResetPayload.data"></a>

#### data

```python
@property
def data() -> Dict
```

Get the data.

