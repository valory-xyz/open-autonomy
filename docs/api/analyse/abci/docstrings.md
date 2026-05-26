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
def compare_docstring_content(
        file_content: str, docstring: str,
        abci_app_name: str) -> Tuple[Optional[bool], str]
```

Update docstrings.

Three result shapes let the caller distinguish "nothing to do because the
file has no ``AbciApp[Event]`` class header" from "the class was found
but already carries a docstring".

**Arguments**:

- `file_content`: source text of the rounds module.
- `docstring`: expected docstring to insert or compare against.
- `abci_app_name`: class name to substitute into the class header.

**Returns**:

``(True, updated_content)`` when content was rewritten,
``(False, "")`` when a header was found but an existing docstring
sits below it, ``(None, "")`` when no ``AbciApp[Event]`` header
exists in the file.

