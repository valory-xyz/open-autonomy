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

<a id="packages.valory.skills.abstract_round_abci.models.SharedState.round_sequence"></a>

#### round`_`sequence

```python
@property
def round_sequence() -> RoundSequence
```

Get the round_sequence.

<a id="packages.valory.skills.abstract_round_abci.models.SharedState.synchronized_data"></a>

#### synchronized`_`data

```python
@property
def synchronized_data() -> BaseSynchronizedData
```

Get the latest synchronized_data if available.

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

<a id="packages.valory.skills.abstract_round_abci.models.BenchmarkBlockTypes"></a>

## BenchmarkBlockTypes Objects

```python
class BenchmarkBlockTypes()
```

Benchmark block types.

<a id="packages.valory.skills.abstract_round_abci.models.BenchmarkBlock"></a>

## BenchmarkBlock Objects

```python
class BenchmarkBlock()
```

Benchmark

This class represents logic to measure the code block using a
context manager.

<a id="packages.valory.skills.abstract_round_abci.models.BenchmarkBlock.__init__"></a>

#### `__`init`__`

```python
def __init__(block_type: str) -> None
```

Benchmark for single round.

<a id="packages.valory.skills.abstract_round_abci.models.BenchmarkBlock.__enter__"></a>

#### `__`enter`__`

```python
def __enter__() -> None
```

Enter context.

<a id="packages.valory.skills.abstract_round_abci.models.BenchmarkBlock.__exit__"></a>

#### `__`exit`__`

```python
def __exit__(*args: List, **kwargs: Dict) -> None
```

Exit context

<a id="packages.valory.skills.abstract_round_abci.models.BenchmarkBehaviour"></a>

## BenchmarkBehaviour Objects

```python
class BenchmarkBehaviour()
```

BenchmarkBehaviour

This class represents logic to benchmark a single behaviour.

<a id="packages.valory.skills.abstract_round_abci.models.BenchmarkBehaviour.__init__"></a>

#### `__`init`__`

```python
def __init__() -> None
```

Initialize Benchmark behaviour object.

<a id="packages.valory.skills.abstract_round_abci.models.BenchmarkBehaviour.local"></a>

#### local

```python
def local() -> BenchmarkBlock
```

Measure local block.

<a id="packages.valory.skills.abstract_round_abci.models.BenchmarkBehaviour.consensus"></a>

#### consensus

```python
def consensus() -> BenchmarkBlock
```

Measure consensus block.

<a id="packages.valory.skills.abstract_round_abci.models.BenchmarkTool"></a>

## BenchmarkTool Objects

```python
class BenchmarkTool(Model)
```

BenchmarkTool

Tool to benchmark ABCI apps.

<a id="packages.valory.skills.abstract_round_abci.models.BenchmarkTool.__init__"></a>

#### `__`init`__`

```python
def __init__(*args: Any, **kwargs: Any) -> None
```

Benchmark tool for rounds behaviours.

<a id="packages.valory.skills.abstract_round_abci.models.BenchmarkTool.measure"></a>

#### measure

```python
def measure(behaviour: str) -> BenchmarkBehaviour
```

Measure time to complete round.

<a id="packages.valory.skills.abstract_round_abci.models.BenchmarkTool.data"></a>

#### data

```python
@property
def data() -> List
```

Returns formatted data.

<a id="packages.valory.skills.abstract_round_abci.models.BenchmarkTool.save"></a>

#### save

```python
def save(period: int = 0, reset: bool = True) -> None
```

Save logs to a file.

<a id="packages.valory.skills.abstract_round_abci.models.BenchmarkTool.reset"></a>

#### reset

```python
def reset() -> None
```

Reset benchmark data

