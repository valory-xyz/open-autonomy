<a id="aea_swarm.cli.analyse"></a>

# aea`_`swarm.cli.analyse

Analyse CLI module.

<a id="aea_swarm.cli.analyse.analyse_group"></a>

#### analyse`_`group

```python
@click.group(name="analyse")
def analyse_group() -> None
```

Analyse an AEA project.

<a id="aea_swarm.cli.analyse.benchmark"></a>

#### benchmark

```python
@analyse_group.command(name="benchmarks")
@click.argument(
    "path",
    type=click.types.Path(exists=True, dir_okay=True, resolve_path=True),
    required=True,
)
@click.option(
    "--block-type",
    "-b",
    type=click.Choice(choices=(*BlockTypes.types, BlockTypes.ALL), case_sensitive=True),
    default=BlockTypes.ALL,
    required=False,
)
@click.option(
    "--period",
    "-d",
    type=int,
    default=-1,
    required=False,
)
@click.option(
    "--output",
    "-o",
    type=click.types.Path(file_okay=True, dir_okay=False, resolve_path=True),
)
def benchmark(path: Path, block_type: str, period: int, output: Optional[Path]) -> None
```

Benchmark Aggregator.

