<a id="autonomy.cli.utils.click_utils"></a>

# autonomy.cli.utils.click`_`utils

Usefule click utils.

<a id="autonomy.cli.utils.click_utils.image_profile_flag"></a>

#### image`_`profile`_`flag

```python
def image_profile_flag(default: str = ImageProfiles.PRODUCTION,
                       mark_default: bool = True) -> Callable
```

Choice of one flag between: '--local/--remote'.

<a id="autonomy.cli.utils.click_utils.abci_spec_format_flag"></a>

#### abci`_`spec`_`format`_`flag

```python
def abci_spec_format_flag(
        default: str = FSMSpecificationLoader.OutputFormats.YAML,
        mark_default: bool = True) -> Callable
```

Flags for abci spec outputs formats.

<a id="autonomy.cli.utils.click_utils.chain_selection_flag"></a>

#### chain`_`selection`_`flag

```python
def chain_selection_flag(
    default: ChainType = ChainType.LOCAL,
    mark_default: bool = True,
    help_string_format:
    str = "To use {} chain profile to interact with the contracts"
) -> Callable
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
def convert(value: Any, param: Optional[click.Parameter],
            ctx: Optional[click.Context]) -> Optional[Path]
```

Convert path string to `pathlib.Path`

<a id="autonomy.cli.utils.click_utils.NFTArgument"></a>

## NFTArgument Objects

```python
class NFTArgument(click.ParamType)
```

NFT parameter for minting tools.

<a id="autonomy.cli.utils.click_utils.NFTArgument.get_metavar"></a>

#### get`_`metavar

```python
def get_metavar(param: click.Parameter) -> str
```

Get metavar

<a id="autonomy.cli.utils.click_utils.NFTArgument.convert"></a>

#### convert

```python
def convert(value: Any, param: Optional[click.Parameter],
            ctx: Optional[click.Context]) -> Optional[Union[Path, IPFSHash]]
```

Convert path string to `pathlib.Path`

<a id="autonomy.cli.utils.click_utils.image_author_option"></a>

#### image`_`author`_`option

```python
def image_author_option(fn: Callable) -> Callable
```

Wrap function with clik option for image-author

