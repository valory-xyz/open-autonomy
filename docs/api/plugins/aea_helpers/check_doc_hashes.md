<a id="plugins.aea-helpers.aea_helpers.check_doc_hashes"></a>

# plugins.aea-helpers.aea`_`helpers.check`_`doc`_`hashes

Tools for autoupdating IPFS hashes in the documentation.

<a id="plugins.aea-helpers.aea_helpers.check_doc_hashes.read_file"></a>

#### read`_`file

```python
def read_file(filepath: str) -> str
```

Loads a file into a string

<a id="plugins.aea-helpers.aea_helpers.check_doc_hashes.get_packages"></a>

#### get`_`packages

```python
def get_packages() -> Dict[str, str]
```

Get packages.

<a id="plugins.aea-helpers.aea_helpers.check_doc_hashes.get_packages_from_repository"></a>

#### get`_`packages`_`from`_`repository

```python
def get_packages_from_repository(repo_url: str) -> Dict[str, str]
```

Retrieve packages.json from the latest release from a repository.

<a id="plugins.aea-helpers.aea_helpers.check_doc_hashes.Package"></a>

## Package Objects

```python
class Package()
```

Class that represents a package in packages.json

<a id="plugins.aea-helpers.aea_helpers.check_doc_hashes.Package.__init__"></a>

#### `__`init`__`

```python
def __init__(package_id_str: str,
             package_hash: str,
             root_dir: Path,
             ignore_file_load_errors: bool = False) -> None
```

Constructor

<a id="plugins.aea-helpers.aea_helpers.check_doc_hashes.Package.get_command"></a>

#### get`_`command

```python
def get_command(cmd: str,
                include_version: bool = True,
                flags: str = "") -> str
```

Get the corresponding command.

**Arguments**:

- `cmd`: the command
- `include_version`: whether or not to include the version
- `flags`: command flags

**Returns**:

the full command

<a id="plugins.aea-helpers.aea_helpers.check_doc_hashes.PackageHashManager"></a>

## PackageHashManager Objects

```python
class PackageHashManager()
```

Class that represents the packages in packages.json

<a id="plugins.aea-helpers.aea_helpers.check_doc_hashes.PackageHashManager.__init__"></a>

#### `__`init`__`

```python
def __init__(root_dir: Path,
             skip_hashes: Optional[List[str]] = None,
             package_json_urls: Optional[List[str]] = None) -> None
```

Constructor

<a id="plugins.aea-helpers.aea_helpers.check_doc_hashes.PackageHashManager.get_package_by_hash"></a>

#### get`_`package`_`by`_`hash

```python
def get_package_by_hash(package_hash: str) -> Optional[Package]
```

Get a package given its hash

<a id="plugins.aea-helpers.aea_helpers.check_doc_hashes.PackageHashManager.get_hash_by_package_line"></a>

#### get`_`hash`_`by`_`package`_`line

```python
def get_hash_by_package_line(package_line: str,
                             target_file: str) -> Optional[str]
```

Get a hash given its package line

<a id="plugins.aea-helpers.aea_helpers.check_doc_hashes.PackageHashManager.get_hash_by_attributes"></a>

#### get`_`hash`_`by`_`attributes

```python
def get_hash_by_attributes(package_type: str, vendor: str,
                           package_name: str) -> Optional[str]
```

Get a package hash give the package information

<a id="plugins.aea-helpers.aea_helpers.check_doc_hashes.check_ipfs_hashes"></a>

#### check`_`ipfs`_`hashes

```python
def check_ipfs_hashes(root_dir: Path,
                      paths: Optional[List[Path]] = None,
                      fix: bool = False,
                      skip_hashes: Optional[List[str]] = None,
                      package_json_urls: Optional[List[str]] = None) -> None
```

Fix ipfs hashes in the docs

<a id="plugins.aea-helpers.aea_helpers.check_doc_hashes.check_doc_hashes"></a>

#### check`_`doc`_`hashes

```python
@click.command(name="check-doc-hashes")
@click.option("--fix", is_flag=True, help="Fix mismatched hashes in-place.")
@click.option(
    "--skip-hash",
    multiple=True,
    help="IPFS hashes to skip (repeatable).",
)
@click.option(
    "-p",
    "--doc-path",
    "doc_paths",
    type=click.Path(exists=True),
    multiple=True,
    help="Documentation directories to scan (default: docs).",
)
@click.option(
    "--package-json-url",
    "package_json_urls",
    multiple=True,
    help="URLs of remote repos to fetch packages.json from (repeatable).",
)
def check_doc_hashes(fix: bool, skip_hash: tuple, doc_paths: tuple,
                     package_json_urls: tuple) -> None
```

Check and optionally fix IPFS hashes in documentation files.

