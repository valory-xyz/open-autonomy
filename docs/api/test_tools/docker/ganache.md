<a id="autonomy.test_tools.docker.ganache"></a>

# autonomy.test`_`tools.docker.ganache

Ganache Docker Image.

<a id="autonomy.test_tools.docker.ganache.GanacheDockerImage"></a>

## GanacheDockerImage Objects

```python
class GanacheDockerImage(DockerImage)
```

Wrapper to Ganache Docker image.

<a id="autonomy.test_tools.docker.ganache.GanacheDockerImage.__init__"></a>

#### `__`init`__`

```python
def __init__(client: DockerClient, addr: str, port: int, config: Optional[Dict] = None, gas_limit: str = "0x9184e72a000")
```

Initialize the Ganache Docker image.

**Arguments**:

- `client`: the Docker client.
- `addr`: the address.
- `port`: the port.
- `config`: optional configuration to command line.
- `gas_limit`: the gas limit for blocks.

<a id="autonomy.test_tools.docker.ganache.GanacheDockerImage.tag"></a>

#### tag

```python
@property
def tag() -> str
```

Get the image tag.

<a id="autonomy.test_tools.docker.ganache.GanacheDockerImage.create"></a>

#### create

```python
def create() -> Container
```

Create the container.

<a id="autonomy.test_tools.docker.ganache.GanacheDockerImage.create_many"></a>

#### create`_`many

```python
def create_many(nb_containers: int) -> List[Container]
```

Instantiate the image in many containers, parametrized.

<a id="autonomy.test_tools.docker.ganache.GanacheDockerImage.wait"></a>

#### wait

```python
def wait(max_attempts: int = 15, sleep_rate: float = 1.0) -> bool
```

Wait until the image is up.

<a id="autonomy.test_tools.docker.ganache.GanacheForkDockerImage"></a>

## GanacheForkDockerImage Objects

```python
class GanacheForkDockerImage(GanacheDockerImage)
```

Extends GanacheDockerImage to enable forking

