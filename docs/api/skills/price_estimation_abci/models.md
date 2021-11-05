<a id="packages.valory.skills.price_estimation_abci.models"></a>

# packages.valory.skills.price`_`estimation`_`abci.models

This module contains the shared state for the price estimation ABCI application.

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

<a id="packages.valory.skills.price_estimation_abci.models.SharedState.setup"></a>

#### setup

```python
def setup() -> None
```

Set up.

<a id="packages.valory.skills.price_estimation_abci.models.Params"></a>

## Params Objects

```python
class Params(BaseParams)
```

Parameters.

<a id="packages.valory.skills.price_estimation_abci.models.Params.__init__"></a>

#### `__`init`__`

```python
def __init__(*args: Any, **kwargs: Any) -> None
```

Initialize the parameters object.

<a id="packages.valory.skills.price_estimation_abci.models.Params.is_health_check_timed_out"></a>

#### is`_`health`_`check`_`timed`_`out

```python
def is_health_check_timed_out() -> bool
```

Check if the healthcheck has timed out.

<a id="packages.valory.skills.price_estimation_abci.models.Params.increment_retries"></a>

#### increment`_`retries

```python
def increment_retries() -> None
```

Increment the retries counter.

