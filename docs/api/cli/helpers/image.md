<a id="autonomy.cli.helpers.image"></a>

# autonomy.cli.helpers.image

Image helpers.

<a id="autonomy.cli.helpers.image.build_image"></a>

#### build`_`image

```python
def build_image(agent: Optional[PublicId],
                service_dir: Optional[Path],
                pull: bool = False,
                version: Optional[str] = None,
                image_author: Optional[str] = None,
                extra_dependencies: Optional[Tuple[Dependency, ...]] = None,
                dockerfile: Optional[Path] = None) -> None
```

Build agent/service image.

