<a id="autonomy.cli.utils.click_utils"></a>

# autonomy.cli.utils.click`_`utils

Usefule click utils.

<a id="autonomy.cli.utils.click_utils.image_profile_flag"></a>

#### image`_`profile`_`flag

```python
def image_profile_flag(default: str = ImageProfiles.PRODUCTION, mark_default: bool = True) -> Callable
```

Choice of one flag between: '--local/--remote'.

<a id="autonomy.cli.utils.click_utils.abci_spec_format_flag"></a>

#### abci`_`spec`_`format`_`flag

```python
def abci_spec_format_flag(default: str = FSMSpecificationLoader.OutputFormats.YAML, mark_default: bool = True) -> Callable
```

Flags for abci spec outputs formats.

<a id="autonomy.cli.utils.click_utils.chain_selection_flag"></a>

#### chain`_`selection`_`flag

```python
def chain_selection_flag(default: str = "staging", mark_default: bool = True) -> Callable
```

Flags for abci spec outputs formats.

<a id="autonomy.cli.utils.click_utils.sys_path_patch"></a>

#### sys`_`path`_`patch

```python
@contextlib.contextmanager
def sys_path_patch(path: Path) -> Generator
```

Patch sys.path variable with new import path at highest priority.

<a id="autonomy.cli.utils.click_utils.PathArgument"></a>

## PathArgument Objects

```python
class PathArgument(click.Path)
```

Path parameter for CLI.

<a id="autonomy.cli.utils.click_utils.PathArgument.convert"></a>

#### convert

```python
def convert(value: Any, param: Optional[click.Parameter], ctx: Optional[click.Context]) -> Optional[Path]
```

Convert path string to `pathlib.Path`

