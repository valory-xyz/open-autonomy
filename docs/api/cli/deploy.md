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
    "service-id",
    type=PublicIdParameter(),
)
@click.argument("keys_file", type=str, required=True)
@click.option(
    "--o",
    "output_dir",
    type=click.Path(exists=False, dir_okay=True),
    default=Path.cwd(),
    help="Path to output dir.",
)
@click.option(
    "--docker",
    "deployment_type",
    flag_value=DockerComposeGenerator.deployment_type,
    default=True,
    help="Use docker as a backend.",
)
@click.option(
    "--kubernetes",
    "deployment_type",
    flag_value=KubernetesGenerator.deployment_type,
    help="Use docker as a kubernetes.",
)
@click.option(
    "--package-dir",
    type=click.Path(exists=False, dir_okay=True),
    default=Path.cwd() / PACKAGES,
    help="Path to packages folder (For local usage).",
)
@click.option(
    "--dev",
    "dev_mode",
    is_flag=True,
    default=False,
    help="Create development environment.",
)
@click.option(
    "--force",
    "force_overwrite",
    is_flag=True,
    default=False,
    help="Remove existing build and overwrite with new one.",
)
def build_deployment(service_id: PublicId, keys_file: Path, deployment_type: str, output_dir: Path, package_dir: Path, dev_mode: bool, force_overwrite: bool) -> None
```

Build the agent and its components.

