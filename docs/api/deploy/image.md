<a id="aea_swarm.deploy.image"></a>

# aea`_`swarm.deploy.image

Image building.

<a id="aea_swarm.deploy.image.ImageBuilder"></a>

## ImageBuilder Objects

```python
class ImageBuilder()
```

Class to build images using skaffold.

<a id="aea_swarm.deploy.image.ImageBuilder.get_aea_agent"></a>

#### get`_`aea`_`agent

```python
@staticmethod
def get_aea_agent(deployment_file_path: Optional[str], valory_application: Optional[str]) -> str
```

Validate and retrieve aea agent from spec.

<a id="aea_swarm.deploy.image.ImageBuilder.build_images"></a>

#### build`_`images

```python
def build_images(profile: str, deployment_file_path: Optional[str], valory_application: Optional[str], push: bool = False) -> None
```

Build images using the subprocess.

