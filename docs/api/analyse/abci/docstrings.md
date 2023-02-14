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

<a id="autonomy.analyse.abci.docstrings.compare_docstring_content"></a>

#### compare`_`docstring`_`content

```python
def compare_docstring_content(file_content: str, docstring: str,
                              abci_app_name: str) -> Tuple[bool, str]
```

Update docstrings.

