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

<a id="autonomy.cli.analyse.abci_group"></a>

#### abci`_`group

```python
@analyse_group.group(name="abci")
def abci_group() -> None
```

Analyse ABCI apps of an agent service.

<a id="autonomy.cli.analyse.generat_abci_app_pecs"></a>

#### generat`_`abci`_`app`_`pecs

```python
@abci_group.command(name="generate-app-specs")
@click.argument("app_class", type=str)
@click.argument("output_file", type=click.Path())
@abci_spec_format_flag()
def generat_abci_app_pecs(app_class: str, output_file: Path, spec_format: str) -> None
```

Generate ABCI app specs.

<a id="autonomy.cli.analyse.check_abci_app_specs"></a>

#### check`_`abci`_`app`_`specs

```python
@abci_group.command(name="check-app-specs")
@click.option(
    "--check-all", type=bool, is_flag=True, help="Check all available definitions."
)
@click.option(
    "--packages-dir",
    type=click.Path(),
    default=Path.cwd() / "packages",
    help="Path to packages directory; Use with `--check-all` flag",
)
@abci_spec_format_flag()
@click.option("--app-class", type=str, help="Dotted path to app definition class.")
@click.option("--infile", type=click.Path(), help="Path to input file.")
def check_abci_app_specs(check_all: bool, packages_dir: Path, spec_format: str, app_class: str, infile: Path) -> None
```

Check ABCI app specs.

<a id="autonomy.cli.analyse.docstrings"></a>

#### docstrings

```python
@abci_group.command(name="docstrings")
@click.argument(
    "packages_dir",
    type=click.Path(dir_okay=True, file_okay=False, exists=True),
    default=Path("packages/"),
)
@click.option("--check", is_flag=True, default=False)
def docstrings(packages_dir: Path, check: bool) -> None
```

Analyse ABCI docstring definitions.

<a id="autonomy.cli.analyse.parse_logs"></a>

#### parse`_`logs

```python
@abci_group.command(name="logs")
@click.argument("file", type=click.Path(file_okay=True, dir_okay=False, exists=True))
def parse_logs(file: Path) -> None
```

Parse logs of an agent service.

<a id="autonomy.cli.analyse.run_handler_check"></a>

#### run`_`handler`_`check

```python
@abci_group.command(name="check-handlers")
@click.argument(
    "packages_dir",
    type=click.Path(dir_okay=True, exists=True),
    default=Path.cwd() / "packages",
)
@click.option(
    "--skip",
    type=str,
    default="abstract_abci",
    help="Specify which skills to skip. Eg. skill_0,skill_1,skill_2",
)
@click.option(
    "--common",
    type=str,
    default="abci",
    help="Specify which handlers to check. Eg. handler_a,handler_b,handler_c",
)
def run_handler_check(packages_dir: Path, skip: str, common: str) -> None
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

Benchmark aggregator.

