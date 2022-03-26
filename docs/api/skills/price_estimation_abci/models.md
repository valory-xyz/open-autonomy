<a id="packages.valory.skills.price_estimation_abci.models"></a>

# packages.valory.skills.price`_`estimation`_`abci.models

This module contains the shared state for the price estimation app ABCI application.

<a id="packages.valory.skills.price_estimation_abci.models.Params"></a>

## Params Objects

```python
class Params(OracleParams,  TransactionParams)
```

Parameters.

<a id="packages.valory.skills.price_estimation_abci.models.Params.__init__"></a>

#### `__`init`__`

```python
def __init__(*args: Any, **kwargs: Any) -> None
```

Initialize the parameters object.

<a id="packages.valory.skills.price_estimation_abci.models.SharedState"></a>

## SharedState Objects

```python
class SharedState(BaseSharedState)
```

Keep the current shared state of the skill.

<a id="packages.valory.skills.price_estimation_abci.models.SharedState.__init__"></a>

#### `__`init`__`

```python
def __init__(*args: Any, **kwargs: Any) -> None
```

Initialize the state.

<a id="packages.valory.skills.price_estimation_abci.models.RandomnessApi"></a>

## RandomnessApi Objects

```python
class RandomnessApi(ApiSpecs)
```

A model for randomness api specifications.

<a id="packages.valory.skills.price_estimation_abci.models.PriceApi"></a>

## PriceApi Objects

```python
class PriceApi(ApiSpecs)
```

A model for various cryptocurrency price api specifications.

<a id="packages.valory.skills.price_estimation_abci.models.PriceApi.__init__"></a>

#### `__`init`__`

```python
def __init__(*args: Any, **kwargs: Any) -> None
```

Initialize PriceApi.

<a id="packages.valory.skills.price_estimation_abci.models.ServerApi"></a>

## ServerApi Objects

```python
class ServerApi(ApiSpecs)
```

A model for oracle web server api specs

