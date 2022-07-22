<a id="autonomy.cli.deploy"></a>

# autonomy.cli.deploy

Deploy CLI module.

<a id="autonomy.cli.deploy.deploy_group"></a>

#### deploy`_`group

```python
@click.group(name="deploy")
def deploy_group() -> None
```

Deploy an agent service.

<a id="autonomy.cli.deploy.build_group"></a>

#### build`_`group

```python
@deploy_group.group(name="build")
def build_group() -> None
```

Build an agent service deployment.

<a id="autonomy.cli.deploy.build_deployment"></a>

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
    help="Use kubernetes as a backend.",
)
@click.option(
    "--packages-dir",
    type=click.Path(dir_okay=True),
    default=Path.cwd() / PACKAGES,
    help="Path to packages folder (for local usage).",
)
@click.option(
    "--dev",
    "dev_mode",
    is_flag=True,
    default=False,
    help="Create development environment.",
)
@click.option(
    "--version",
    "version",
    help="Specify deployment version.",
)
@click.option(
    "--force",
    "force_overwrite",
    is_flag=True,
    default=False,
    help="Remove existing build and overwrite with new one.",
)
@click.option(
    "--skip-images",
    is_flag=True,
    default=False,
    help="Specify whether to build images or not.",
)
@registry_flag()
@password_option(confirmation_prompt=True)
def build_deployment(service_id: PublicId, keys_file: Path, deployment_type: str, output_dir: Path, packages_dir: Path, dev_mode: bool, force_overwrite: bool, registry: str, number_of_agents: Optional[int] = None, password: Optional[str] = None, version: Optional[str] = None, skip_images: bool = False) -> None
```

Build deployment setup for n agents.

<a id="autonomy.cli.deploy.build_images"></a>

#### build`_`images

```python
@build_group.command(name="image")
@click.option(
    "--build-dir",
    type=click.Path(dir_okay=True),
    help="Path to build dir.",
)
@click.option(
    "--packages-dir",
    type=click.Path(dir_okay=True),
    help="Path to packages folder (for local usage).",
)
@click.option(
    "--skaffold-dir",
    type=click.Path(exists=True, dir_okay=True),
    help="Path to directory containing the skaffold config.",
)
@click.option(
    "--version",
    type=str,
    default=DEFAULT_IMAGE_VERSION,
    help="Image version.",
)
@click.option("--push", is_flag=True, default=False, help="Push image after build.")
@image_profile_flag()
def build_images(profile: str, packages_dir: Optional[Path], build_dir: Optional[Path], skaffold_dir: Optional[Path], version: str, push: bool) -> None
```

Build image using skaffold.

