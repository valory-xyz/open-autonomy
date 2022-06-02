<a id="aea_swarm.deploy.build"></a>

# aea`_`swarm.deploy.build

Script for generating deployment environments.

<a id="aea_swarm.deploy.build.generate_deployment"></a>

#### generate`_`deployment

```python
def generate_deployment(type_of_deployment: str, private_keys_file_path: Path, service_path: Path, packages_dir: Path, build_dir: Path, number_of_agents: Optional[int] = None, dev_mode: bool = False, version: Optional[str] = None) -> str
```

Generate the deployment build for the valory app.

