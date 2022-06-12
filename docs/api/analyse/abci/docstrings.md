<a id="autonomy.analyse.abci.docstrings"></a>

# autonomy.analyse.abci.docstrings

Analyse ABCI app definitions for docstrings.

<a id="autonomy.analyse.abci.docstrings.docstring_abci_app"></a>

#### docstring`_`abci`_`app

```python
def docstring_abci_app(abci_app: Any) -> str
```

Generate a docstring for an ABCI app

This ensures that documentation aligns with the actual implementation

**Arguments**:

- `abci_app`: abci app object.

**Returns**:

docstring

<a id="autonomy.analyse.abci.docstrings.update_docstrings"></a>

#### update`_`docstrings

```python
def update_docstrings(module_path: Path, docstring: str, abci_app_name: str, check: bool = False) -> bool
```

Update docstrings.

<a id="autonomy.analyse.abci.docstrings.process_module"></a>

#### process`_`module

```python
def process_module(module_path: Path, check: bool = False) -> bool
```

Process module.

