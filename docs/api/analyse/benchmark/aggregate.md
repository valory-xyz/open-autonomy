<a id="aea_swarm.analyse.benchmark.aggregate"></a>

# aea`_`swarm.analyse.benchmark.aggregate

Tools for aggregating benchmark results.

<a id="aea_swarm.analyse.benchmark.aggregate.BlockTypes"></a>

## BlockTypes Objects

```python
class BlockTypes()
```

Block types.

<a id="aea_swarm.analyse.benchmark.aggregate.read_benchmark_data"></a>

#### read`_`benchmark`_`data

```python
def read_benchmark_data(path: Path) -> List[Dict]
```

Returns logs.

<a id="aea_swarm.analyse.benchmark.aggregate.create_dataframe"></a>

#### create`_`dataframe

```python
def create_dataframe(data: List[Dict]) -> pd.DataFrame
```

Create pandas.DataFrame object from benchmark data.

<a id="aea_swarm.analyse.benchmark.aggregate.format_output"></a>

#### format`_`output

```python
def format_output(df: pd.DataFrame, period: int, block_type: str) -> str
```

Format output from given dataframe and parameters

<a id="aea_swarm.analyse.benchmark.aggregate.aggregate"></a>

#### aggregate

```python
def aggregate(path: Path, block_type: str, period: int, output: Path) -> None
```

Benchmark Aggregator.

