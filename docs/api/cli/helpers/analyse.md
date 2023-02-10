<a id="autonomy.cli.helpers.analyse"></a>

# autonomy.cli.helpers.analyse

Helpers for analyse command

<a id="autonomy.cli.helpers.analyse.load_package_tree"></a>

#### load`_`package`_`tree

```python
def load_package_tree(packages_dir: Path) -> None
```

Load package tree.

<a id="autonomy.cli.helpers.analyse.list_all_skill_yaml_files"></a>

#### list`_`all`_`skill`_`yaml`_`files

```python
def list_all_skill_yaml_files(registry_path: Path) -> List[Path]
```

List all skill yaml files in a local registry

<a id="autonomy.cli.helpers.analyse.run_dialogues_check"></a>

#### run`_`dialogues`_`check

```python
def run_dialogues_check(packages_dir: Path, ignore: List[str], dialogues: List[str]) -> None
```

Run dialogues check.

<a id="autonomy.cli.helpers.analyse.check_service_readiness"></a>

#### check`_`service`_`readiness

```python
def check_service_readiness(token_id: Optional[int], service_id: PackageId, chain_type: ChainType, packages_dir: Path) -> None
```

Check deployment readiness of a service.

