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

<a id="autonomy.deploy.image.ImageBuilder"></a>

## ImageBuilder Objects

```python
class ImageBuilder()
```

Class to build images using skaffold.

<a id="autonomy.deploy.image.ImageBuilder.build_images"></a>

#### build`_`images

```python
@classmethod
def build_images(cls, profile: str, deployment_file_path: Path, packages_dir: Path, build_dir: Path, skaffold_dir: Path, version: str, push: bool = False) -> None
```

Build images using the subprocess.

<a id="autonomy.deploy.image.ImageBuilder.get_aea_agent"></a>

#### get`_`aea`_`agent

```python
@staticmethod
def get_aea_agent(deployment_file_path: Path) -> str
```

Validate and retrieve aea agent from spec.

