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

<a id="packages.valory.skills.abstract_round_abci.models.ApiSpecs"></a>

## ApiSpecs Objects

```python
class ApiSpecs(Model)
```

A model that wraps APIs to get cryptocurrency prices.

<a id="packages.valory.skills.abstract_round_abci.models.ApiSpecs.__init__"></a>

#### `__`init`__`

```python
def __init__(*args: Any, **kwargs: Any) -> None
```

Initialize ApiSpecsModel.

<a id="packages.valory.skills.abstract_round_abci.models.ApiSpecs.ensure"></a>

#### ensure

```python
def ensure(keyword: str, kwargs: Dict) -> Any
```

Ensure a keyword argument.

<a id="packages.valory.skills.abstract_round_abci.models.ApiSpecs.get_spec"></a>

#### get`_`spec

```python
def get_spec() -> Dict
```

Returns dictionary containing api specifications.

<a id="packages.valory.skills.abstract_round_abci.models.ApiSpecs.process_response"></a>

#### process`_`response

```python
def process_response(response: HttpMessage) -> Any
```

Process response from api.

<a id="packages.valory.skills.abstract_round_abci.models.ApiSpecs.increment_retries"></a>

#### increment`_`retries

```python
def increment_retries() -> None
```

Increment the retries counter.

<a id="packages.valory.skills.abstract_round_abci.models.ApiSpecs.reset_retries"></a>

#### reset`_`retries

```python
def reset_retries() -> None
```

Reset the retries counter.

<a id="packages.valory.skills.abstract_round_abci.models.ApiSpecs.is_retries_exceeded"></a>

#### is`_`retries`_`exceeded

```python
def is_retries_exceeded() -> bool
```

Check if the retries amount has been exceeded.

