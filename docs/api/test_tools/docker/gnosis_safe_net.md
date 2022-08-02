<a id="autonomy.test_tools.docker.gnosis_safe_net"></a>

# autonomy.test`_`tools.docker.gnosis`_`safe`_`net

Tendermint Docker image.

<a id="autonomy.test_tools.docker.gnosis_safe_net.GnosisSafeNetDockerImage"></a>

## GnosisSafeNetDockerImage Objects

```python
class GnosisSafeNetDockerImage(DockerImage)
```

Spawn a local Ethereum network with deployed Gnosis Safe contracts, using HardHat.

<a id="autonomy.test_tools.docker.gnosis_safe_net.GnosisSafeNetDockerImage.__init__"></a>

#### `__`init`__`

```python
def __init__(client: docker.DockerClient, addr: str = DEFAULT_HARDHAT_ADDR, port: int = DEFAULT_HARDHAT_PORT)
```

Initialize.

<a id="autonomy.test_tools.docker.gnosis_safe_net.GnosisSafeNetDockerImage.tag"></a>

#### tag

```python
@property
def tag() -> str
```

Get the tag.

<a id="autonomy.test_tools.docker.gnosis_safe_net.GnosisSafeNetDockerImage.create"></a>

#### create

```python
def create() -> Container
```

Create the container.

<a id="autonomy.test_tools.docker.gnosis_safe_net.GnosisSafeNetDockerImage.create_many"></a>

#### create`_`many

```python
def create_many(nb_containers: int) -> List[Container]
```

Instantiate the image in many containers, parametrized.

<a id="autonomy.test_tools.docker.gnosis_safe_net.GnosisSafeNetDockerImage.wait"></a>

#### wait

```python
def wait(max_attempts: int = 15, sleep_rate: float = 1.0) -> bool
```

Wait until the image is running.

**Arguments**:

- `max_attempts`: max number of attempts.
- `sleep_rate`: the amount of time to sleep between different requests.

**Returns**:

True if the wait was successful, False otherwise.

