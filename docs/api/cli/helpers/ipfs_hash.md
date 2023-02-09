<a id="autonomy.cli.helpers.ipfs_hash"></a>

# autonomy.cli.helpers.ipfs`_`hash

IPFS hash helpers.

<a id="autonomy.cli.helpers.ipfs_hash.load_configuration"></a>

#### load`_`configuration

```python
def load_configuration(package_type: PackageType,
                       package_path: Path) -> PackageConfiguration
```

Load a configuration, knowing the type and the path to the package root.

**Arguments**:

- `package_type`: the package type.
- `package_path`: the path to the package root.

**Returns**:

the configuration object.

<a id="autonomy.cli.helpers.ipfs_hash.update_hashes"></a>

#### update`_`hashes

```python
def update_hashes(
    packages_dir: Path,
    no_wrap: bool = False,
    vendor: Optional[str] = None,
    config_loader: Callable[[PackageType, Path],
                            PackageConfiguration] = load_configuration
) -> int
```

Process all AEA packages, update fingerprint, and update packages.json file.

