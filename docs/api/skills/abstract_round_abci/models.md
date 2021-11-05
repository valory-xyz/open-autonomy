<a id="packages.valory.skills.abstract_round_abci.models"></a>

# packages.valory.skills.abstract`_`round`_`abci.models

This module contains the shared state for the price estimation ABCI application.

<a id="packages.valory.skills.abstract_round_abci.models.BaseParams"></a>

## BaseParams Objects

```python
class BaseParams(Model)
```

Parameters.

<a id="packages.valory.skills.abstract_round_abci.models.BaseParams.__init__"></a>

#### `__`init`__`

```python
def __init__(*args: Any, **kwargs: Any) -> None
```

Initialize the parameters object.

<a id="packages.valory.skills.abstract_round_abci.models.SharedState"></a>

## SharedState Objects

```python
class SharedState(Model)
```

Keep the current shared state of the skill.

<a id="packages.valory.skills.abstract_round_abci.models.SharedState.__init__"></a>

#### `__`init`__`

```python
def __init__(*args: Any, *, abci_app_cls: Type[AbciApp], **kwargs: Any) -> None
```

Initialize the state.

<a id="packages.valory.skills.abstract_round_abci.models.SharedState.setup"></a>

#### setup

```python
def setup() -> None
```

Set up the model.

<a id="packages.valory.skills.abstract_round_abci.models.SharedState.period_state"></a>

#### period`_`state

```python
@property
def period_state() -> BasePeriodState
```

Get the period state if available.

<a id="packages.valory.skills.abstract_round_abci.models.Requests"></a>

## Requests Objects

```python
class Requests(Model)
```

Keep the current pending requests.

<a id="packages.valory.skills.abstract_round_abci.models.Requests.__init__"></a>

#### `__`init`__`

```python
def __init__(*args: Any, **kwargs: Any) -> None
```

Initialize the state.

