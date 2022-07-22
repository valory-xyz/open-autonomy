<a id="autonomy.deploy.image"></a>

# autonomy.deploy.image

Image building.

<a id="autonomy.deploy.image.check_kubeconfig_vars"></a>

#### check`_`kubeconfig`_`vars

```python
def check_kubeconfig_vars() -> bool
```

Check if kubeconfig variables are set properly.

<a id="autonomy.deploy.image.ImageProfiles"></a>

## ImageProfiles Objects

```python
class ImageProfiles()
```

Image build profiles.

<a id="autonomy.deploy.image.build_image"></a>

#### build`_`image

```python
def build_image(agent: PublicId, profile: str, skaffold_dir: Path, version: str, push: bool = False, build_concurrency: int = 0) -> None
```

Command to build images from for skaffold deployment.

