<a id="autonomy.test_tools.docker.amm_net"></a>

# autonomy.test`_`tools.docker.amm`_`net

Tendermint Docker image.

<a id="autonomy.test_tools.docker.amm_net.AMMNetDockerImage"></a>

## AMMNetDockerImage Objects

```python
class AMMNetDockerImage(DockerImage)
```

Spawn a local Ethereum network with deployed Gnosis Safe and Uniswap contracts, using HardHat.

<a id="autonomy.test_tools.docker.amm_net.AMMNetDockerImage.__init__"></a>

#### `__`init`__`

```python
def __init__(client: docker.DockerClient, addr: str = DEFAULT_HARDHAT_ADDR, port: int = DEFAULT_HARDHAT_PORT)
```

Initialize.

<a id="autonomy.test_tools.docker.amm_net.AMMNetDockerImage.tag"></a>

#### tag

```python
@property
def tag() -> str
```

Get the tag.

<a id="autonomy.test_tools.docker.amm_net.AMMNetDockerImage.create"></a>

#### create

```python
def create() -> Container
```

Create the container.

<a id="autonomy.test_tools.docker.amm_net.AMMNetDockerImage.create_many"></a>

#### create`_`many

```python
def create_many(nb_containers: int) -> List[Container]
```

Instantiate the image in many containers, parametrized.

<a id="autonomy.test_tools.docker.amm_net.AMMNetDockerImage.wait"></a>

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

