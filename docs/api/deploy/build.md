<a id="autonomy.deploy.build"></a>

# autonomy.deploy.build

Script for generating deployment environments.

<a id="autonomy.deploy.build.generate_deployment"></a>

#### generate`_`deployment

```python
def generate_deployment(type_of_deployment: str,
                        keys_file: Path,
                        service_path: Path,
                        build_dir: Path,
                        number_of_agents: Optional[int] = None,
                        dev_mode: bool = False,
                        packages_dir: Optional[Path] = None,
                        open_aea_dir: Optional[Path] = None,
                        agent_instances: Optional[List[str]] = None,
                        multisig_address: Optional[str] = None,
                        consensus_threshold: Optional[int] = None,
                        log_level: str = INFO,
                        apply_environment_variables: bool = False,
                        image_version: Optional[str] = None,
                        use_hardhat: bool = False,
                        use_acn: bool = False,
                        use_tm_testnet_setup: bool = False,
                        image_author: Optional[str] = None,
                        resources: Optional[Resources] = None) -> str
```

Generate the deployment for the service.

