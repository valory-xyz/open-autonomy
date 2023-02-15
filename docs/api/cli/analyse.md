<a id="autonomy.cli.analyse"></a>

# autonomy.cli.analyse

Analyse CLI module.

<a id="autonomy.cli.analyse.analyse_group"></a>

#### analyse`_`group

```python
@click.group(name="analyse")
def analyse_group() -> None
```

Analyse an agent service.

<a id="autonomy.cli.analyse.abci_app_specs"></a>

#### abci`_`app`_`specs

```python
@analyse_group.command(name="fsm-specs")
@click.option("--package", type=PathArgument())
@click.option("--app-class", type=str)
@click.option("--update",
              is_flag=True,
              help="Update FSM definition if check fails.")
@abci_spec_format_flag()
@pass_ctx
def abci_app_specs(ctx: Context, package: Optional[Path],
                   app_class: Optional[str], spec_format: str,
                   update: bool) -> None
```

Generate ABCI app specs.

<a id="autonomy.cli.analyse.docstrings"></a>

#### docstrings

```python
@analyse_group.command(name="docstrings")
@click.option(
    "--update",
    is_flag=True,
    default=False,
    help="Update docstrings if required.",
)
@pass_ctx
def docstrings(ctx: Context, update: bool) -> None
```

Analyse ABCI docstring definitions.

<a id="autonomy.cli.analyse.run_handler_check"></a>

#### run`_`handler`_`check

```python
@analyse_group.command(name="handlers")
@pass_ctx
@click.option(
    "--common-handlers",
    "-h",
    type=str,
    default=[
        "abci",
    ],
    help=
    "Specify which handlers to check. Eg. -h handler_a -h handler_b -h handler_c",
    multiple=True,
)
@click.option(
    "--ignore",
    "-i",
    type=str,
    default=[
        "abstract_abci",
    ],
    help="Specify which skills to skip. Eg. -i skill_0 -i skill_1 -i skill_2",
    multiple=True,
)
def run_handler_check(ctx: Context, ignore: List[str],
                      common_handlers: List[str]) -> None
```

Check handler definitions.

<a id="autonomy.cli.analyse.benchmark"></a>

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
    type=click.Choice(choices=(*BlockTypes.types, BlockTypes.ALL),
                      case_sensitive=True),
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
    default=BENCHMARKS_DIR,
)
def benchmark(path: Path, block_type: str, period: int, output: Path) -> None
```

Benchmark aggregator.

