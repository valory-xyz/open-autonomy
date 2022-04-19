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
def __init__(sender: str, round_id: int, randomness: str, **kwargs: Any) -> None
```

Initialize an 'select_keeper' transaction payload.

**Arguments**:

- `sender`: the sender (Ethereum) address
- `round_id`: the round id
- `randomness`: the randomness
- `kwargs`: the keyword arguments

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
def __init__(sender: str, keepers: str, **kwargs: Any) -> None
```

Initialize a 'select_keeper' transaction payload.

**Arguments**:

- `sender`: the sender (Ethereum) address
- `keepers`: the updated keepers
- `kwargs`: the keyword arguments

<a id="packages.valory.skills.transaction_settlement_abci.payloads.SelectKeeperPayload.keepers"></a>

#### keepers

```python
@property
def keepers() -> str
```

Get the keeper.

<a id="packages.valory.skills.transaction_settlement_abci.payloads.SelectKeeperPayload.data"></a>

#### data

```python
@property
def data() -> Dict[str, str]
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
def __init__(sender: str, vote: Optional[bool] = None, **kwargs: Any) -> None
```

Initialize an 'validate' transaction payload.

**Arguments**:

- `sender`: the sender (Ethereum) address
- `vote`: the vote
- `kwargs`: the keyword arguments

<a id="packages.valory.skills.transaction_settlement_abci.payloads.ValidatePayload.vote"></a>

#### vote

```python
@property
def vote() -> Optional[bool]
```

Get the vote.

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
def __init__(sender: str, verified_res: str, **kwargs: Any) -> None
```

Initialize an 'check' transaction payload.

**Arguments**:

- `sender`: the sender (Ethereum) address
- `verified_res`: the verification result
- `kwargs`: the keyword arguments

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

<a id="packages.valory.skills.transaction_settlement_abci.payloads.SynchronizeLateMessagesPayload"></a>

## SynchronizeLateMessagesPayload Objects

```python
class SynchronizeLateMessagesPayload(BaseTxPayload)
```

Represent a transaction payload of type 'synchronize'.

<a id="packages.valory.skills.transaction_settlement_abci.payloads.SynchronizeLateMessagesPayload.__init__"></a>

#### `__`init`__`

```python
def __init__(sender: str, tx_hashes: str = "", **kwargs: Any) -> None
```

Initialize a 'synchronize' transaction payload.

**Arguments**:

- `sender`: the sender (Ethereum) address
- `tx_hashes`: the late-arriving tx hashes concatenated
- `kwargs`: the keyword arguments

<a id="packages.valory.skills.transaction_settlement_abci.payloads.SynchronizeLateMessagesPayload.tx_hashes"></a>

#### tx`_`hashes

```python
@property
def tx_hashes() -> Optional[str]
```

Get the late-arriving tx hashes.

<a id="packages.valory.skills.transaction_settlement_abci.payloads.SynchronizeLateMessagesPayload.data"></a>

#### data

```python
@property
def data() -> Dict[str, Optional[str]]
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
def __init__(sender: str, signature: str, **kwargs: Any) -> None
```

Initialize an 'signature' transaction payload.

**Arguments**:

- `sender`: the sender (Ethereum) address
- `signature`: the signature
- `kwargs`: the keyword arguments

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
def __init__(sender: str, tx_data: Optional[Dict[str, Union[str, int, bool]]] = None, **kwargs: Any) -> None
```

Initialize an 'finalization' transaction payload.

**Arguments**:

- `sender`: the sender (Ethereum) address
- `tx_data`: the transaction data
- `kwargs`: the keyword arguments

<a id="packages.valory.skills.transaction_settlement_abci.payloads.FinalizationTxPayload.tx_data"></a>

#### tx`_`data

```python
@property
def tx_data() -> Optional[Dict[str, Union[str, int, bool]]]
```

Get the tx_data.

<a id="packages.valory.skills.transaction_settlement_abci.payloads.FinalizationTxPayload.data"></a>

#### data

```python
@property
def data() -> Dict[str, Dict[str, Union[str, int, bool]]]
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
def __init__(sender: str, period_count: int, **kwargs: Any) -> None
```

Initialize an 'reset' transaction payload.

**Arguments**:

- `sender`: the sender (Ethereum) address
- `period_count`: the period count id
- `kwargs`: the keyword arguments

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

