<a id="plugins.aea-helpers.aea_helpers.check_third_party_hashes"></a>

# plugins.aea-helpers.aea`_`helpers.check`_`third`_`party`_`hashes

Check that third-party package hashes match the open-aea repository.

<a id="plugins.aea-helpers.aea_helpers.check_third_party_hashes.get_open_aea_version"></a>

#### get`_`open`_`aea`_`version

```python
def get_open_aea_version(root_dir: Path) -> str
```

Extract the pinned open-aea version from setup.py.

<a id="plugins.aea-helpers.aea_helpers.check_third_party_hashes.get_remote_packages"></a>

#### get`_`remote`_`packages

```python
def get_remote_packages(version: str,
                        open_aea_repo: str = "valory-xyz/open-aea") -> dict
```

Fetch packages.json from open-aea repo at the tag matching version.

<a id="plugins.aea-helpers.aea_helpers.check_third_party_hashes.get_local_third_party"></a>

#### get`_`local`_`third`_`party

```python
def get_local_third_party(root_dir: Path) -> dict
```

Read third-party packages from local packages.json.

<a id="plugins.aea-helpers.aea_helpers.check_third_party_hashes.main"></a>

#### main

```python
def main(root_dir: Path) -> None
```

Run the check.

<a id="plugins.aea-helpers.aea_helpers.check_third_party_hashes.check_third_party_hashes"></a>

#### check`_`third`_`party`_`hashes

```python
@click.command(name="check-third-party-hashes")
@click.option(
    "--root-dir",
    type=click.Path(exists=True, file_okay=False),
    default=".",
    help="Repository root directory (default: current working directory).",
)
def check_third_party_hashes(root_dir: str) -> None
```

Check that third-party package hashes match the open-aea repository.

