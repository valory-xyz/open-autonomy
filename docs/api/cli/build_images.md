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
    help="Path to build dir.",
)
def build_image(agent: Optional[PublicId], service_dir: Optional[Path]) -> None
```

Build image using skaffold.

