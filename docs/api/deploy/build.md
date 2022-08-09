<a id="autonomy.deploy.build"></a>

# autonomy.deploy.build

Script for generating deployment environments.

<a id="autonomy.deploy.build.generate_deployment"></a>

#### generate`_`deployment

```python
def generate_deployment(type_of_deployment: str, private_keys_file_path: Path, service_path: Path, build_dir: Path, number_of_agents: Optional[int] = None, private_keys_password: Optional[str] = None, dev_mode: bool = False, version: Optional[str] = None, packages_dir: Optional[Path] = None, open_aea_dir: Optional[Path] = None, open_autonomy_dir: Optional[Path] = None) -> str
```

Generate the deployment build for the valory app.

