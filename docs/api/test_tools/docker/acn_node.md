<a id="autonomy.test_tools.docker.acn_node"></a>

# autonomy.test`_`tools.docker.acn`_`node

ACN Docker Image.

<a id="autonomy.test_tools.docker.acn_node.ACNNodeDockerImage"></a>

## ACNNodeDockerImage Objects

```python
class ACNNodeDockerImage(DockerImage)
```

Wrapper to ACNNode Docker image.

<a id="autonomy.test_tools.docker.acn_node.ACNNodeDockerImage.__init__"></a>

#### `__`init`__`

```python
def __init__(client: DockerClient, config: Optional[Dict] = None)
```

Initialize the ACNNode Docker image.

**Arguments**:

- `client`: the Docker client.
- `config`: optional configuration to command line.

<a id="autonomy.test_tools.docker.acn_node.ACNNodeDockerImage.tag"></a>

#### tag

```python
@property
def tag() -> str
```

Get the image tag.

<a id="autonomy.test_tools.docker.acn_node.ACNNodeDockerImage.create"></a>

#### create

```python
def create() -> Container
```

Create the container.

<a id="autonomy.test_tools.docker.acn_node.ACNNodeDockerImage.create_many"></a>

#### create`_`many

```python
def create_many(nb_containers: int) -> List[Container]
```

Instantiate the image in many containers, parametrized.

<a id="autonomy.test_tools.docker.acn_node.ACNNodeDockerImage.wait"></a>

#### wait

```python
def wait(max_attempts: int = 15, sleep_rate: float = 1.0) -> bool
```

Wait until the image is up.

