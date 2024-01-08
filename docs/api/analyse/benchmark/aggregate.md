<a id="autonomy.analyse.benchmark.aggregate"></a>

# autonomy.analyse.benchmark.aggregate

Tools for aggregating benchmark results.

<a id="autonomy.analyse.benchmark.aggregate.BlockTypes"></a>

## BlockTypes Objects

```python
class BlockTypes()
```

Block types.

<a id="autonomy.analyse.benchmark.aggregate.read_benchmark_data"></a>

#### read`_`benchmark`_`data

```python
def read_benchmark_data(path: Path,
                        block_type: str = BlockTypes.ALL,
                        period: int = -1) -> Dict[str, Dict[str, List[Dict]]]
```

Returns logs.

<a id="autonomy.analyse.benchmark.aggregate.add_statistic"></a>

#### add`_`statistic

```python
def add_statistic(name: str, aggregator: Callable, behaviours: List[str],
                  behaviour_history: Dict[str, List[float]]) -> str
```

Add a stastic column.

<a id="autonomy.analyse.benchmark.aggregate.add_statistics"></a>

#### add`_`statistics

```python
def add_statistics(behaviours: List[str],
                   behaviour_history: Dict[str, List[float]]) -> str
```

Add statistics.

<a id="autonomy.analyse.benchmark.aggregate.create_table_data"></a>

#### create`_`table`_`data

```python
def create_table_data(
        data: Dict[str, List[Dict]],
        blocks: Tuple[str,
                      ...]) -> Tuple[List[str], List[str], Dict[str, Dict]]
```

Create table data.

<a id="autonomy.analyse.benchmark.aggregate.create_agent_table"></a>

#### create`_`agent`_`table

```python
def create_agent_table(agent: str, data: Dict[str, List[Dict]],
                       blocks: Tuple[str, ...]) -> str
```

Create agent table.

<a id="autonomy.analyse.benchmark.aggregate.aggregate"></a>

#### aggregate

```python
def aggregate(path: Path, block_type: str, period: int, output: Path) -> None
```

Benchmark Aggregator.

