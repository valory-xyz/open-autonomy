<a id="autonomy.cli.helpers.import_utils"></a>

# autonomy.cli.helpers.import`_`utils

Utilities for importing modules from the local packages registry.

<a id="autonomy.cli.helpers.import_utils.compute_sys_path_root"></a>

#### compute`_`sys`_`path`_`root

```python
def compute_sys_path_root(module_path: Path, module_name: str) -> Path
```

Determine the directory that should be injected into sys.path.

<a id="autonomy.cli.helpers.import_utils.purge_module_cache"></a>

#### purge`_`module`_`cache

```python
def purge_module_cache(module_name: str) -> None
```

Remove cached modules so they can be re-imported from the registry.

<a id="autonomy.cli.helpers.import_utils.import_module_from_path"></a>

#### import`_`module`_`from`_`path

```python
def import_module_from_path(module_name: str,
                            module_file: Path,
                            *,
                            strict_origin: bool = True) -> ModuleType
```

Import a module ensuring it originates from the expected file path.

<a id="autonomy.cli.helpers.import_utils.purge_modules_under_path"></a>

#### purge`_`modules`_`under`_`path

```python
def purge_modules_under_path(base_path: Path) -> None
```

Remove cached modules whose source lives under the provided base path.

