<a id="plugins.aea-helpers.aea_helpers.generate_api_docs"></a>

# plugins.aea-helpers.aea`_`helpers.generate`_`api`_`docs

This tool generates the API docs.

<a id="plugins.aea-helpers.aea_helpers.generate_api_docs.check_working_tree_is_dirty"></a>

#### check`_`working`_`tree`_`is`_`dirty

```python
def check_working_tree_is_dirty() -> None
```

Check if the current Git working tree is dirty.

<a id="plugins.aea-helpers.aea_helpers.generate_api_docs.create_subdir"></a>

#### create`_`subdir

```python
def create_subdir(path: str) -> None
```

Create a subdirectory.

**Arguments**:

- `path`: the directory path

<a id="plugins.aea-helpers.aea_helpers.generate_api_docs.replace_underscores"></a>

#### replace`_`underscores

```python
def replace_underscores(text: str) -> str
```

Replace escaped underscores in a text.

**Arguments**:

- `text`: the text

**Returns**:

the processed text

<a id="plugins.aea-helpers.aea_helpers.generate_api_docs.is_relative_to"></a>

#### is`_`relative`_`to

```python
def is_relative_to(path_one: Path, path_two: Path) -> bool
```

Check if a path is relative to another path.

<a id="plugins.aea-helpers.aea_helpers.generate_api_docs.is_not_dir"></a>

#### is`_`not`_`dir

```python
def is_not_dir(path: Path) -> bool
```

Call p.is_dir() method and negate the result.

<a id="plugins.aea-helpers.aea_helpers.generate_api_docs.should_skip"></a>

#### should`_`skip

```python
def should_skip(module_path: Path) -> bool
```

Return true if the file should be skipped.

<a id="plugins.aea-helpers.aea_helpers.generate_api_docs.make_pydoc"></a>

#### make`_`pydoc

```python
def make_pydoc(dotted_path: str, dest_file: Path) -> None
```

Make a PyDoc file.

<a id="plugins.aea-helpers.aea_helpers.generate_api_docs.run_pydoc_markdown"></a>

#### run`_`pydoc`_`markdown

```python
def run_pydoc_markdown(module: str) -> str
```

Run pydoc-markdown.

**Arguments**:

- `module`: the dotted path.

**Returns**:

the PyDoc content (pre-processed).

<a id="plugins.aea-helpers.aea_helpers.generate_api_docs.generate_api_docs"></a>

#### generate`_`api`_`docs

```python
def generate_api_docs() -> None
```

Generate the api docs.

<a id="plugins.aea-helpers.aea_helpers.generate_api_docs.install"></a>

#### install

```python
def install(package: str) -> int
```

Install a PyPI package by calling pip.

**Arguments**:

- `package`: the package name and version specifier.

**Returns**:

the return code.

<a id="plugins.aea-helpers.aea_helpers.generate_api_docs.main"></a>

#### main

```python
def main(check_clean: bool = False) -> None
```

Entry point for API doc generation.

