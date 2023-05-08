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
@click.option("--version", type=str, help="Specify tag version for the image.")
@click.option("--dev",
              is_flag=True,
              help="Build development image.",
              default=False)
@click.option("--pull",
              is_flag=True,
              help="Pull latest dependencies.",
              default=False)
@image_author_option
def build_image(agent: Optional[PublicId],
                service_dir: Optional[Path],
                pull: bool = False,
                dev: bool = False,
                version: Optional[str] = None,
                image_author: Optional[str] = None) -> None
```

Build runtime images for autonomous agents.

