<a id="autonomy.replay.utils"></a>

# autonomy.replay.utils

Utils module.

<a id="autonomy.replay.utils.fix_address_books"></a>

#### fix`_`address`_`books

```python
def fix_address_books(build_dir: Path) -> None
```

Update address books in data dump to use them in replays.

Malformed individual peer entries (missing ``addr``/``ip`` keys or
a non-dotted IP) are skipped with a warning so a single bad entry
does not leave the addrbook half-rewritten and abort the sweep of
the remaining files.

**Arguments**:

- `build_dir`: build directory containing the tendermint state dump.

<a id="autonomy.replay.utils.fix_config_files"></a>

#### fix`_`config`_`files

```python
def fix_config_files(build_dir: Path) -> None
```

Update config.toml in data dump to use them in replays.

**Arguments**:

- `build_dir`: build directory containing the tendermint state dump.

<a id="autonomy.replay.utils.load_docker_config"></a>

#### load`_`docker`_`config

```python
def load_docker_config(file_path: Path) -> Dict[str, Any]
```

Load docker config.

**Arguments**:

- `file_path`: docker-compose YAML path.

**Raises**:

- `ValueError`: if the top-level YAML node is not a mapping.

**Returns**:

parsed mapping.

