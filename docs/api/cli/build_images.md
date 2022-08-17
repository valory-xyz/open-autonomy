<a id="autonomy.cli.build_images"></a>

# autonomy.cli.build`_`images

Build images.

<a id="autonomy.cli.build_images.build_images"></a>

#### build`_`images

```python
@click.command(name="build-images")
@click.argument(
    "agent",
    type=PublicIdParameter(),
    required=False,
)
@click.option(
    "--build-dir",
    type=click.Path(dir_okay=True),
    help="Path to build dir.",
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
def build_images(agent: Optional[PublicId], build_dir: Optional[Path], skaffold_dir: Optional[Path], version: str, push: bool, profile: str) -> None
```

Build image using skaffold.

