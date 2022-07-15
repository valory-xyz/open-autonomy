<a id="autonomy.cli.hash"></a>

# autonomy.cli.hash

Override for hash command.

<a id="autonomy.cli.hash.load_configuration"></a>

#### load`_`configuration

```python
def load_configuration(package_type: PackageType, package_path: Path) -> PackageConfiguration
```

Load a configuration, knowing the type and the path to the package root.

**Arguments**:

- `package_type`: the package type.
- `package_path`: the path to the package root.

**Returns**:

the configuration object.

<a id="autonomy.cli.hash.update_hashes"></a>

#### update`_`hashes

```python
def update_hashes(packages_dir: Path, no_wrap: bool = False, vendor: Optional[str] = None, config_loader: Callable[
        [PackageType, Path], PackageConfiguration
    ] = load_configuration) -> int
```

Process all AEA packages, update fingerprint, and update hashes.csv files.

<a id="autonomy.cli.hash.hash_group"></a>

#### hash`_`group

```python
@click.group(name="hash")
def hash_group() -> None
```

Hashing utils.

<a id="autonomy.cli.hash.generate_all"></a>

#### generate`_`all

```python
@hash_group.command(name="all")
@click.option(
    "--packages-dir",
    type=click.Path(exists=True, dir_okay=True, file_okay=False),
    default=Path("packages/"),
)
@click.option("--vendor", type=str)
@click.option("--no-wrap", is_flag=True)
@click.option("--check", is_flag=True)
def generate_all(packages_dir: Path, vendor: Optional[str], no_wrap: bool, check: bool) -> None
```

Generate IPFS hashes.

