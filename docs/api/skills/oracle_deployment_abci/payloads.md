<a id="packages.valory.skills.oracle_deployment_abci.payloads"></a>

# packages.valory.skills.oracle`_`deployment`_`abci.payloads

This module contains the transaction payloads for the oracle deployment app.

<a id="packages.valory.skills.oracle_deployment_abci.payloads.TransactionType"></a>

## TransactionType Objects

```python
class TransactionType(Enum)
```

Enumeration of transaction types.

<a id="packages.valory.skills.oracle_deployment_abci.payloads.TransactionType.__str__"></a>

#### `__`str`__`

```python
def __str__() -> str
```

Get the string value of the transaction type.

<a id="packages.valory.skills.oracle_deployment_abci.payloads.RandomnessPayload"></a>

## RandomnessPayload Objects

```python
class RandomnessPayload(BaseTxPayload)
```

Represent a transaction payload of type 'randomness'.

<a id="packages.valory.skills.oracle_deployment_abci.payloads.RandomnessPayload.__init__"></a>

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

<a id="packages.valory.skills.oracle_deployment_abci.payloads.RandomnessPayload.round_id"></a>

#### round`_`id

```python
@property
def round_id() -> int
```

Get the round id.

<a id="packages.valory.skills.oracle_deployment_abci.payloads.RandomnessPayload.randomness"></a>

#### randomness

```python
@property
def randomness() -> str
```

Get the randomness.

<a id="packages.valory.skills.oracle_deployment_abci.payloads.RandomnessPayload.data"></a>

#### data

```python
@property
def data() -> Dict
```

Get the data.

<a id="packages.valory.skills.oracle_deployment_abci.payloads.SelectKeeperPayload"></a>

## SelectKeeperPayload Objects

```python
class SelectKeeperPayload(BaseTxPayload)
```

Represent a transaction payload of type 'select_keeper'.

<a id="packages.valory.skills.oracle_deployment_abci.payloads.SelectKeeperPayload.__init__"></a>

#### `__`init`__`

```python
def __init__(sender: str, keeper: str, **kwargs: Any) -> None
```

Initialize an 'select_keeper' transaction payload.

**Arguments**:

- `sender`: the sender (Ethereum) address
- `keeper`: the keeper selection
- `kwargs`: the keyword arguments

<a id="packages.valory.skills.oracle_deployment_abci.payloads.SelectKeeperPayload.keeper"></a>

#### keeper

```python
@property
def keeper() -> str
```

Get the keeper.

<a id="packages.valory.skills.oracle_deployment_abci.payloads.SelectKeeperPayload.data"></a>

#### data

```python
@property
def data() -> Dict
```

Get the data.

<a id="packages.valory.skills.oracle_deployment_abci.payloads.ValidateOraclePayload"></a>

## ValidateOraclePayload Objects

```python
class ValidateOraclePayload(BaseTxPayload)
```

Represent a transaction payload of type 'validate'.

<a id="packages.valory.skills.oracle_deployment_abci.payloads.ValidateOraclePayload.__init__"></a>

#### `__`init`__`

```python
def __init__(sender: str, vote: Optional[bool] = None, **kwargs: Any) -> None
```

Initialize an 'validate' transaction payload.

**Arguments**:

- `sender`: the sender (Ethereum) address
- `vote`: the vote
- `kwargs`: the keyword arguments

<a id="packages.valory.skills.oracle_deployment_abci.payloads.ValidateOraclePayload.vote"></a>

#### vote

```python
@property
def vote() -> Optional[bool]
```

Get the vote.

<a id="packages.valory.skills.oracle_deployment_abci.payloads.ValidateOraclePayload.data"></a>

#### data

```python
@property
def data() -> Dict
```

Get the data.

<a id="packages.valory.skills.oracle_deployment_abci.payloads.DeployOraclePayload"></a>

## DeployOraclePayload Objects

```python
class DeployOraclePayload(BaseTxPayload)
```

Represent a transaction payload of type 'deploy_oracle'.

<a id="packages.valory.skills.oracle_deployment_abci.payloads.DeployOraclePayload.__init__"></a>

#### `__`init`__`

```python
def __init__(sender: str, oracle_contract_address: str, **kwargs: Any) -> None
```

Initialize a 'deploy_safe' transaction payload.

**Arguments**:

- `sender`: the sender (Ethereum) address
- `oracle_contract_address`: the Safe contract address
- `kwargs`: the keyword arguments

<a id="packages.valory.skills.oracle_deployment_abci.payloads.DeployOraclePayload.oracle_contract_address"></a>

#### oracle`_`contract`_`address

```python
@property
def oracle_contract_address() -> str
```

Get the Oracle contract address.

<a id="packages.valory.skills.oracle_deployment_abci.payloads.DeployOraclePayload.data"></a>

#### data

```python
@property
def data() -> Dict
```

Get the data.

