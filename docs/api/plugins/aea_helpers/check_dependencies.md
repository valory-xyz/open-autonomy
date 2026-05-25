<a id="plugins.aea-helpers.aea_helpers.check_dependencies"></a>

# plugins.aea-helpers.aea`_`helpers.check`_`dependencies

Check that project dependency files are consistent.

Validates that dependencies declared in packages/ match those in
pyproject.toml (or Pipfile) and tox.ini. Supports both check-only
and update modes.

<a id="plugins.aea-helpers.aea_helpers.check_dependencies.PathArgument"></a>

## PathArgument Objects

```python
class PathArgument(click.Path)
```

Path parameter for CLI.

<a id="plugins.aea-helpers.aea_helpers.check_dependencies.PathArgument.convert"></a>

#### convert

```python
def convert(value: Any, param: Optional[click.Parameter],
            ctx: Optional[click.Context]) -> Optional[Path]
```

Convert path string to `pathlib.Path`

<a id="plugins.aea-helpers.aea_helpers.check_dependencies.PipfileConfig"></a>

## PipfileConfig Objects

```python
class PipfileConfig()
```

Class to represent Pipfile config.

<a id="plugins.aea-helpers.aea_helpers.check_dependencies.PipfileConfig.__init__"></a>

#### `__`init`__`

```python
def __init__(sources: List[str],
             packages: OrderedDictType[str, Dependency],
             dev_packages: OrderedDictType[str, Dependency],
             file: Path,
             exclude: Optional[List[str]] = None) -> None
```

Initialize object.

<a id="plugins.aea-helpers.aea_helpers.check_dependencies.PipfileConfig.__iter__"></a>

#### `__`iter`__`

```python
def __iter__() -> Iterator[Dependency]
```

Iterate dependencies.

<a id="plugins.aea-helpers.aea_helpers.check_dependencies.PipfileConfig.update"></a>

#### update

```python
def update(dependency: Dependency) -> None
```

Update dependency specifier.

<a id="plugins.aea-helpers.aea_helpers.check_dependencies.PipfileConfig.check"></a>

#### check

```python
def check(dependency: Dependency) -> Tuple[Optional[str], int]
```

Check dependency specifier.

<a id="plugins.aea-helpers.aea_helpers.check_dependencies.PipfileConfig.parse"></a>

#### parse

```python
@classmethod
def parse(
    cls, content: str
) -> Tuple[List[str], OrderedDictType[str, OrderedDictType[str, Dependency]]]
```

Parse from string.

<a id="plugins.aea-helpers.aea_helpers.check_dependencies.PipfileConfig.compile"></a>

#### compile

```python
def compile() -> str
```

Compile to Pipfile string.

<a id="plugins.aea-helpers.aea_helpers.check_dependencies.PipfileConfig.load"></a>

#### load

```python
@classmethod
def load(cls,
         file: Path,
         exclude: Optional[List[str]] = None) -> "PipfileConfig"
```

Load from file.

<a id="plugins.aea-helpers.aea_helpers.check_dependencies.PipfileConfig.dump"></a>

#### dump

```python
def dump() -> None
```

Write to Pipfile.

<a id="plugins.aea-helpers.aea_helpers.check_dependencies.ToxConfig"></a>

## ToxConfig Objects

```python
class ToxConfig()
```

Class to represent tox.ini file.

<a id="plugins.aea-helpers.aea_helpers.check_dependencies.ToxConfig.__init__"></a>

#### `__`init`__`

```python
def __init__(dependencies: Dict[str, Dict[str, Any]],
             file: Path,
             exclude: Optional[List[str]] = None) -> None
```

Initialize object.

<a id="plugins.aea-helpers.aea_helpers.check_dependencies.ToxConfig.__iter__"></a>

#### `__`iter`__`

```python
def __iter__() -> Iterator[Dependency]
```

Iter dependencies.

<a id="plugins.aea-helpers.aea_helpers.check_dependencies.ToxConfig.update"></a>

#### update

```python
def update(dependency: Dependency) -> None
```

Update dependency specifier.

<a id="plugins.aea-helpers.aea_helpers.check_dependencies.ToxConfig.check"></a>

#### check

```python
def check(dependency: Dependency) -> Tuple[Optional[str], int]
```

Check dependency specifier.

<a id="plugins.aea-helpers.aea_helpers.check_dependencies.ToxConfig.parse"></a>

#### parse

```python
@classmethod
def parse(cls, content: str) -> Dict[str, Dict[str, Any]]
```

Parse file content.

<a id="plugins.aea-helpers.aea_helpers.check_dependencies.ToxConfig.load"></a>

#### load

```python
@classmethod
def load(cls, file: Path, exclude: Optional[List[str]] = None) -> "ToxConfig"
```

Load tox.ini file.

<a id="plugins.aea-helpers.aea_helpers.check_dependencies.ToxConfig.write"></a>

#### write

```python
def write() -> None
```

Dump config.

<a id="plugins.aea-helpers.aea_helpers.check_dependencies.PyProjectTomlConfig"></a>

## PyProjectTomlConfig Objects

```python
class PyProjectTomlConfig()
```

Class to represent pyproject.toml file.

<a id="plugins.aea-helpers.aea_helpers.check_dependencies.PyProjectTomlConfig.__init__"></a>

#### `__`init`__`

```python
def __init__(dependencies: OrderedDictType[str, Dependency],
             config: Dict[str, Dict],
             file: Path,
             exclude: Optional[List[str]] = None,
             main_dep_names: Optional[Set[str]] = None,
             string_dep_names: Optional[Set[str]] = None) -> None
```

Initialize object.

<a id="plugins.aea-helpers.aea_helpers.check_dependencies.PyProjectTomlConfig.__iter__"></a>

#### `__`iter`__`

```python
def __iter__() -> Iterator[Dependency]
```

Iterate dependencies.

<a id="plugins.aea-helpers.aea_helpers.check_dependencies.PyProjectTomlConfig.update"></a>

#### update

```python
def update(dependency: Dependency) -> None
```

Update dependency specifier.

<a id="plugins.aea-helpers.aea_helpers.check_dependencies.PyProjectTomlConfig.check"></a>

#### check

```python
def check(dependency: Dependency) -> Tuple[Optional[str], int]
```

Check dependency specifier.

<a id="plugins.aea-helpers.aea_helpers.check_dependencies.PyProjectTomlConfig.load"></a>

#### load

```python
@classmethod
def load(
        cls,
        pyproject_path: Path,
        exclude: Optional[List[str]] = None
) -> Optional["PyProjectTomlConfig"]
```

Load pyproject.toml dependencies.

Reads `[tool.poetry.dependencies]` plus every
`[tool.poetry.group.*.dependencies]` table. Dict-form entries are
treated as declared even when they omit the `extras` key (so
`optional = true` deps are visible), and dev/test-only entries
(e.g. `pytest-asyncio` in the `dev` group) no longer need to be
duplicated into main deps to satisfy the check.

Group-origin entries enter `self.dependencies` for `check()`
lookups but are excluded from `__iter__` / `dump()` so that
cross-validation against `tox.ini` and `--update` rewrites stay
scoped to main runtime deps. See `__init__` for the rationale.

**Arguments**:

- `pyproject_path`: path to the pyproject.toml file.
- `exclude`: package names to omit from iteration / check.

**Returns**:

a `PyProjectTomlConfig` instance, or `None` if the file
has no `[tool.poetry.dependencies]` table (the `except
KeyError` also triggers on a missing `[tool]` /
`[tool.poetry]` parent).

<a id="plugins.aea-helpers.aea_helpers.check_dependencies.PyProjectTomlConfig.dump"></a>

#### dump

```python
def dump() -> None
```

Dump to file.

Only rewrites lines inside ``[tool.poetry.dependencies]`` that
originated from a plain-string spec (e.g. ``requests = "*"``).
Dict-form entries (``docker = { version = "==7.1.0", optional =
true }``) carry metadata that ``Dependency.to_pipfile_string()``
cannot represent, so they pass through verbatim.  Lines in other
TOML sections (``[tool.poetry.extras]``, group tables, etc.) are
never touched.

<a id="plugins.aea-helpers.aea_helpers.check_dependencies.load_packages_dependencies"></a>

#### load`_`packages`_`dependencies

```python
def load_packages_dependencies(
        packages_dir: Path,
        exclude: Optional[List[str]] = None) -> List[Dependency]
```

Returns a list of package dependencies.

<a id="plugins.aea-helpers.aea_helpers.check_dependencies.check_dependencies"></a>

#### check`_`dependencies

```python
@click.command(name="check-dependencies")
@click.option(
    "--check",
    "check_only",
    is_flag=True,
    help="Validate only, do not update files.",
)
@click.option(
    "--strict",
    is_flag=True,
    help="Enable full cross-validation between all dependency files.",
)
@click.option(
    "--exclude",
    multiple=True,
    help="Package names to exclude from checks (repeatable).",
)
@click.option(
    "--packages",
    "packages_dir",
    type=PathArgument(exists=True, file_okay=False, dir_okay=True),
    help="Path of the packages directory.",
)
@click.option(
    "--tox",
    "tox_path",
    type=PathArgument(exists=True, file_okay=True, dir_okay=False),
    help="tox.ini path.",
)
@click.option(
    "--pipfile",
    "pipfile_path",
    type=PathArgument(exists=True, file_okay=True, dir_okay=False),
    help="Pipfile path.",
)
@click.option(
    "--pyproject",
    "pyproject_path",
    type=PathArgument(exists=True, file_okay=True, dir_okay=False),
    help="pyproject.toml path.",
)
def check_dependencies(check_only: bool = False,
                       strict: bool = False,
                       exclude: tuple = (),
                       packages_dir: Optional[Path] = None,
                       tox_path: Optional[Path] = None,
                       pipfile_path: Optional[Path] = None,
                       pyproject_path: Optional[Path] = None) -> None
```

Check dependencies across packages, tox.ini, pyproject.toml and Pipfile.

