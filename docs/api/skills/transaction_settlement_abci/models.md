<a id="packages.valory.skills.transaction_settlement_abci.models"></a>

# packages.valory.skills.transaction`_`settlement`_`abci.models

Custom objects for the transaction settlement ABCI application.

<a id="packages.valory.skills.transaction_settlement_abci.models.SharedState"></a>

## SharedState Objects

```python
class SharedState(BaseSharedState)
```

Keep the current shared state of the skill.

<a id="packages.valory.skills.transaction_settlement_abci.models.SharedState.__init__"></a>

#### `__`init`__`

```python
def __init__(*args: Any, **kwargs: Any) -> None
```

Initialize the state.

<a id="packages.valory.skills.transaction_settlement_abci.models.TransactionParams"></a>

## TransactionParams Objects

```python
class TransactionParams(BaseParams)
```

Transaction settlement agent-specific parameters.

<a id="packages.valory.skills.transaction_settlement_abci.models.TransactionParams.__init__"></a>

#### `__`init`__`

```python
def __init__(*args: Any, **kwargs: Any) -> None
```

Initialize the parameters object.

<a id="packages.valory.skills.transaction_settlement_abci.models.TransactionParams.reset_tx_params"></a>

#### reset`_`tx`_`params

```python
def reset_tx_params() -> None
```

Reset the transaction-related parameters.

<a id="packages.valory.skills.transaction_settlement_abci.models.RandomnessApi"></a>

## RandomnessApi Objects

```python
class RandomnessApi(ApiSpecs)
```

A model that wraps ApiSpecs for randomness api specifications.

