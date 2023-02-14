<a id="autonomy.deploy.image"></a>

# autonomy.deploy.image

Image building.

<a id="autonomy.deploy.image.ImageProfiles"></a>

## ImageProfiles Objects

```python
class ImageProfiles()
```

Image build profiles.

<a id="autonomy.deploy.image.build_image"></a>

#### build`_`image

```python
def build_image(agent: PublicId,
                pull: bool = False,
                dev: bool = False,
                version: Optional[str] = None,
                image_author: Optional[str] = None) -> None
```

Command to build images from for skaffold deployment.

<a id="autonomy.deploy.image.ImageBuildFailed"></a>

## ImageBuildFailed Objects

```python
class ImageBuildFailed(Exception)
```

Raise when there's an error while building the agent image.

