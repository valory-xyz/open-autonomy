<a id="autonomy.test_tools.docker.registries"></a>

# autonomy.test`_`tools.docker.registries

Tendermint Docker image.

<a id="autonomy.test_tools.docker.registries.RegistriesDockerImage"></a>

## RegistriesDockerImage Objects

```python
class RegistriesDockerImage(DockerImage)
```

Spawn a local Ethereum network with deployed registry contracts, using HardHat.

<a id="autonomy.test_tools.docker.registries.RegistriesDockerImage.__init__"></a>

#### `__`init`__`

```python
def __init__(client: docker.DockerClient, third_party_contract_dir: Path, addr: str = DEFAULT_HARDHAT_ADDR, port: int = DEFAULT_HARDHAT_PORT)
```

Initialize.

<a id="autonomy.test_tools.docker.registries.RegistriesDockerImage.tag"></a>

#### tag

```python
@property
def tag() -> str
```

Get the tag.

<a id="autonomy.test_tools.docker.registries.RegistriesDockerImage.create"></a>

#### create

```python
def create() -> Container
```

Create the container.

<a id="autonomy.test_tools.docker.registries.RegistriesDockerImage.create_many"></a>

#### create`_`many

```python
def create_many(nb_containers: int) -> List[Container]
```

Instantiate the image in many containers, parametrized.

<a id="autonomy.test_tools.docker.registries.RegistriesDockerImage.wait"></a>

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

