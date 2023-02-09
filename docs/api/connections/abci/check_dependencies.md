<a id="packages.valory.connections.abci.check_dependencies"></a>

# packages.valory.connections.abci.check`_`dependencies

Check dependencies.

<a id="packages.valory.connections.abci.check_dependencies.nth"></a>

#### nth

```python
def nth(iterable: Iterable, index: int, default: int = 0) -> int
```

Returns the item at position 'index' or a default value

<a id="packages.valory.connections.abci.check_dependencies.get_version"></a>

#### get`_`version

```python
def get_version(*args: int) -> VERSION
```

Get the version from a list of arguments.

Set to '0' if there are not enough arguments.

**Arguments**:

- `args`: positional arguments

**Returns**:

the version

<a id="packages.valory.connections.abci.check_dependencies.version_to_string"></a>

#### version`_`to`_`string

```python
def version_to_string(version: VERSION) -> str
```

Transform version to string.

**Arguments**:

- `version`: the version.

**Returns**:

the string representation.

<a id="packages.valory.connections.abci.check_dependencies.print_ok_message"></a>

#### print`_`ok`_`message

```python
def print_ok_message(binary_name: str, actual_version: VERSION,
                     version_lower_bound: VERSION) -> None
```

Print OK message.

**Arguments**:

- `binary_name`: the binary binary_name.
- `actual_version`: the actual version.
- `version_lower_bound`: the version lower bound.

<a id="packages.valory.connections.abci.check_dependencies.check_binary"></a>

#### check`_`binary

```python
def check_binary(binary_name: str,
                 args: List[str],
                 version_regex: Pattern,
                 version_lower_bound: VERSION,
                 only_warning: bool = False) -> None
```

Check a binary is accessible from the terminal.

It breaks down in:
1) check if the binary is reachable from the system path;
2) check that the version number is higher or equal than the minimum required version.

**Arguments**:

- `binary_name`: the name of the binary.
- `args`: the arguments to provide to the binary to retrieve the version.
- `version_regex`: the regex used to extract the version from the output.
- `version_lower_bound`: the minimum required version.
- `only_warning`: if True, don't raise error but print a warning message

<a id="packages.valory.connections.abci.check_dependencies.check_versions"></a>

#### check`_`versions

```python
def check_versions() -> None
```

Check versions.

<a id="packages.valory.connections.abci.check_dependencies.main"></a>

#### main

```python
def main() -> None
```

The main entrypoint of the script.

