<a id="plugins.aea-test-autonomy.aea_test_autonomy.docker.ganache"></a>

# plugins.aea-test-autonomy.aea`_`test`_`autonomy.docker.ganache

Ganache Docker Image.

<a id="plugins.aea-test-autonomy.aea_test_autonomy.docker.ganache.GanacheDockerImage"></a>

## GanacheDockerImage Objects

```python
class GanacheDockerImage(DockerImage)
```

Wrapper to Ganache Docker image.

<a id="plugins.aea-test-autonomy.aea_test_autonomy.docker.ganache.GanacheDockerImage.__init__"></a>

#### `__`init`__`

```python
def __init__(client: DockerClient,
             addr: str,
             port: int,
             config: Optional[Dict] = None,
             gas_limit: str = "0x9184e72a000")
```

Initialize the Ganache Docker image.

**Arguments**:

- `client`: the Docker client.
- `addr`: the address.
- `port`: the port.
- `config`: optional configuration to command line.
- `gas_limit`: the gas limit for blocks.

<a id="plugins.aea-test-autonomy.aea_test_autonomy.docker.ganache.GanacheDockerImage.image"></a>

#### image

```python
@property
def image() -> str
```

Get the image name.

<a id="plugins.aea-test-autonomy.aea_test_autonomy.docker.ganache.GanacheDockerImage.create"></a>

#### create

```python
def create() -> Container
```

Create the container.

<a id="plugins.aea-test-autonomy.aea_test_autonomy.docker.ganache.GanacheDockerImage.create_many"></a>

#### create`_`many

```python
def create_many(nb_containers: int) -> List[Container]
```

Instantiate the image in many containers, parametrized.

<a id="plugins.aea-test-autonomy.aea_test_autonomy.docker.ganache.GanacheDockerImage.wait"></a>

#### wait

```python
def wait(max_attempts: int = 15, sleep_rate: float = 1.0) -> bool
```

Wait until the image is up.

<a id="plugins.aea-test-autonomy.aea_test_autonomy.docker.ganache.GanacheForkDockerImage"></a>

## GanacheForkDockerImage Objects

```python
class GanacheForkDockerImage(GanacheDockerImage)
```

Extends GanacheDockerImage to enable forking

