<a id="aea_swarm.cli.deploy"></a>

# aea`_`swarm.cli.deploy

Deploy CLI module.

<a id="aea_swarm.cli.deploy.deploy_group"></a>

#### deploy`_`group

```python
@click.group(name="deploy")
def deploy_group() -> None
```

Deploy an AEA project.

<a id="aea_swarm.cli.deploy.build_deployment"></a>

#### build`_`deployment

```python
@deploy_group.command(name="build")
@click.argument(
    "deployment-file-path", type=click.Path(exists=True, file_okay=True, dir_okay=False)
)
@click.argument("keys_file", type=str, required=True)
@click.option(
    "--o",
    "output_dir",
    type=click.Path(exists=False, dir_okay=True),
    default=Path.cwd(),
)
@click.option(
    "--docker",
    "deployment_type",
    flag_value=DockerComposeGenerator.deployment_type,
    default=True,
)
@click.option(
    "--kubernetes",
    "deployment_type",
    flag_value=KubernetesGenerator.deployment_type,
)
@click.option("--dev", "dev_mode", is_flag=True, default=False)
@click.option("--force", "force_overwrite", is_flag=True, default=False)
def build_deployment(deployment_file_path: Path, keys_file: Path, deployment_type: str, output_dir: Path, dev_mode: bool, force_overwrite: bool) -> None
```

Build the agent and its components.

