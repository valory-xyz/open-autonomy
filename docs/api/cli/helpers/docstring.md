<a id="autonomy.cli.helpers.docstring"></a>

# autonomy.cli.helpers.docstring

Helper for docstring analyser.

<a id="autonomy.cli.helpers.docstring.import_rounds_module"></a>

#### import`_`rounds`_`module

```python
def import_rounds_module(module_path: Path,
                         packages_dir: Optional[Path] = None) -> ModuleType
```

Import module using importlib.import_module

<a id="autonomy.cli.helpers.docstring.analyse_docstrings"></a>

#### analyse`_`docstrings

```python
def analyse_docstrings(module_path: Path,
                       update: bool = False,
                       packages_dir: Optional[Path] = None) -> bool
```

Process module.

**Arguments**:

- `module_path`: Path to the rounds module
- `update`: whether to update the content if required
- `packages_dir`: Path to packages directory

**Returns**:

boolean specifying whether the update is needed or not

