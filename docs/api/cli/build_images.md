<a id="autonomy.cli.build_images"></a>

# autonomy.cli.build`_`images

Build images.

<a id="autonomy.cli.build_images.build_image"></a>

#### build`_`image

```python
@click.command(name="build-image")
@click.argument(
    "agent",
    type=PublicIdParameter(),
    required=False,
)
@click.option(
    "--service-dir",
    type=click.Path(dir_okay=True),
    help="Path to service dir.",
)
@click.option(
    "-e",
    "--extra-dependency",
    "extra_dependencies",
    type=PyPiDependency(),
    help="Provide extra dependency.",
    multiple=True,
)
@click.option("--version", type=str, help="Specify tag version for the image.")
@click.option("--dev",
              is_flag=True,
              help="Build development image.",
              default=False)
@click.option("--pull",
              is_flag=True,
              help="Pull latest dependencies.",
              default=False)
@click.option(
    "-f",
    "--dockerfile",
    type=click.Path(
        file_okay=True,
        dir_okay=False,
        exists=False,
    ),
    help="Specify custom dockerfile for building the agent",
)
@click.option(
    "--platform",
    type=str,
    help="Specify the target architecture platform for the image.",
)
@click.option(
    "--builder",
    type=str,
    help='Override the configured docker builder instance (default "default").',
)
@click.option("--push",
              is_flag=True,
              help="Push image to docker hub.",
              default=False)
@click.option(
    "--pre-install-command",
    type=str,
    help="Run the command before installing dependencies.",
    default=None,
)
@image_author_option
def build_image(agent: Optional[PublicId],
                service_dir: Optional[Path],
                dockerfile: Optional[Path],
                extra_dependencies: Tuple[Dependency, ...],
                pull: bool = False,
                dev: bool = False,
                version: Optional[str] = None,
                image_author: Optional[str] = None,
                platform: Optional[str] = None,
                push: bool = False,
                builder: Optional[str] = None,
                pre_install_command: Optional[str] = None) -> None
```

Build runtime images for autonomous agents.

