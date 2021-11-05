<a id="packages.valory.skills.abstract_round_abci.utils"></a>

# packages.valory.skills.abstract`_`round`_`abci.utils

This module contains utility functions for the 'abstract_round_abci' skill.

<a id="packages.valory.skills.abstract_round_abci.utils.locate"></a>

#### locate

```python
def locate(path: str) -> Any
```

Locate an object by name or dotted save_path, importing as necessary.

<a id="packages.valory.skills.abstract_round_abci.utils.BenchmarkBlockTypes"></a>

## BenchmarkBlockTypes Objects

```python
class BenchmarkBlockTypes()
```

Benchmark block types.

<a id="packages.valory.skills.abstract_round_abci.utils.BenchmarkBlock"></a>

## BenchmarkBlock Objects

```python
class BenchmarkBlock()
```

Benchmark

This class represents logic to measure the code block using a
context manager.

<a id="packages.valory.skills.abstract_round_abci.utils.BenchmarkBlock.__init__"></a>

#### `__`init`__`

```python
def __init__(block_type: str) -> None
```

Benchmark for single round.

<a id="packages.valory.skills.abstract_round_abci.utils.BenchmarkBlock.__enter__"></a>

#### `__`enter`__`

```python
def __enter__() -> None
```

Enter context.

<a id="packages.valory.skills.abstract_round_abci.utils.BenchmarkBlock.__exit__"></a>

#### `__`exit`__`

```python
def __exit__(*args: List, **kwargs: Dict) -> None
```

Exit context

<a id="packages.valory.skills.abstract_round_abci.utils.BenchmarkBehaviour"></a>

## BenchmarkBehaviour Objects

```python
class BenchmarkBehaviour()
```

BenchmarkBehaviour

This class represents logic to benchmark a single behaviour.

<a id="packages.valory.skills.abstract_round_abci.utils.BenchmarkBehaviour.__init__"></a>

#### `__`init`__`

```python
def __init__(behaviour: BaseState) -> None
```

Initialize Benchmark behaviour object.

**Arguments**:

- `behaviour`: behaviour that will be measured.

<a id="packages.valory.skills.abstract_round_abci.utils.BenchmarkBehaviour.local"></a>

#### local

```python
def local() -> BenchmarkBlock
```

Measure local block.

<a id="packages.valory.skills.abstract_round_abci.utils.BenchmarkBehaviour.consensus"></a>

#### consensus

```python
def consensus() -> BenchmarkBlock
```

Measure consensus block.

<a id="packages.valory.skills.abstract_round_abci.utils.BenchmarkTool"></a>

## BenchmarkTool Objects

```python
class BenchmarkTool()
```

BenchmarkTool

Tool to benchmark price estimation agents execution time with
different contexts.

<a id="packages.valory.skills.abstract_round_abci.utils.BenchmarkTool.__init__"></a>

#### `__`init`__`

```python
def __init__() -> None
```

Benchmark tool for rounds behaviours.

<a id="packages.valory.skills.abstract_round_abci.utils.BenchmarkTool.data"></a>

#### data

```python
@property
def data() -> Dict
```

Returns formatted data.

<a id="packages.valory.skills.abstract_round_abci.utils.BenchmarkTool.log"></a>

#### log

```python
def log() -> None
```

Output log.

<a id="packages.valory.skills.abstract_round_abci.utils.BenchmarkTool.save"></a>

#### save

```python
def save() -> None
```

Save logs to a file.

<a id="packages.valory.skills.abstract_round_abci.utils.BenchmarkTool.measure"></a>

#### measure

```python
def measure(behaviour: BaseState) -> BenchmarkBehaviour
```

Measure time to complete round.

