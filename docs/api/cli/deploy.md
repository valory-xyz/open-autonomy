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

<a id="aea_swarm.cli.deploy.build_group"></a>

#### build`_`group

```python
@deploy_group.group(name="build")
def build_group() -> None
```

Build tools

<a id="aea_swarm.cli.deploy.build_deployment"></a>

#### build`_`deployment

```python
@build_group.command(name="deployment")
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
    "--n",
    "number_of_agents",
    type=int,
    default=None,
    help="Number of agents.",
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
    type=click.Path(exists=True, dir_okay=True),
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
@click.option(
    "--keys-password",
    "keys_password",
    default=None,
    help="Optional password for encrypted keys.",
)
def build_deployment(service_id: PublicId, keys_file: Path, deployment_type: str, output_dir: Path, package_dir: Path, dev_mode: bool, force_overwrite: bool, number_of_agents: Optional[int] = None, keys_password: Optional[str] = None) -> None
```

Build deployment setup for n agents.

<a id="aea_swarm.cli.deploy.build_images"></a>

#### build`_`images

```python
@build_group.command(name="image")
@click.argument(
    "service-id",
    type=PublicIdParameter(),
)
@click.option(
    "--package-dir",
    type=click.Path(exists=True, dir_okay=True),
    default=Path.cwd() / PACKAGES,
    help="Path to packages folder (For local usage).",
)
@click.option(
    "--build-dir",
    type=click.Path(exists=True, dir_okay=True),
    default=Path.cwd() / "deployments" / "Dockerfiles" / "open_aea",
    help="Path to build directory.",
)
@click.option(
    "--skaffold-dir",
    type=click.Path(exists=True, dir_okay=True),
    default=Path.cwd(),
    help="Path to directory containing the skaffold config.",
)
@click.option(
    "--version",
    type=str,
    default=DEFAULT_IMAGE_VERSION,
    help="Image version",
)
@click.option("--push", is_flag=True, default=False, help="Push image after build.")
@image_profile_flag()
def build_images(service_id: PublicId, profile: str, package_dir: Path, build_dir: Path, skaffold_dir: Path, version: str, push: bool) -> None
```

Build image using skaffold.

