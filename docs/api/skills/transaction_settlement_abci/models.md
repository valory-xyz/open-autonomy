<a id="packages.valory.skills.transaction_settlement_abci.models"></a>

# packages.valory.skills.transaction`_`settlement`_`abci.models

Custom objects for the transaction settlement ABCI application.

<a id="packages.valory.skills.transaction_settlement_abci.models.SharedState"></a>

## SharedState Objects

```python
class SharedState(BaseSharedState)
```

Keep the current shared state of the skill.

<a id="packages.valory.skills.transaction_settlement_abci.models.MutableParams"></a>

## MutableParams Objects

```python
@dataclass
class MutableParams(TypeCheckMixin)
```

Collection for the mutable parameters.

<a id="packages.valory.skills.transaction_settlement_abci.models.GasParams"></a>

## GasParams Objects

```python
@dataclass
class GasParams(BaseParams)
```

Gas parameters.

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

We keep track of the nonce and tip across rounds and periods.
We reuse it each time a new raw transaction is generated. If
at the time of the new raw transaction being generated the nonce
on the ledger does not match the nonce on the skill, then we ignore
the skill nonce and tip (effectively we price fresh). Otherwise, we
are in a re-submission scenario where we need to take account of the
old tip.

**Arguments**:

- `args`: positional arguments
- `kwargs`: keyword arguments

