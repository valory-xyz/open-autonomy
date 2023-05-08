<a id="plugins.aea-test-autonomy.aea_test_autonomy.docker.tendermint"></a>

# plugins.aea-test-autonomy.aea`_`test`_`autonomy.docker.tendermint

Tendermint Docker image.

<a id="plugins.aea-test-autonomy.aea_test_autonomy.docker.tendermint.TendermintDockerImage"></a>

## TendermintDockerImage Objects

```python
class TendermintDockerImage(DockerImage)
```

Tendermint Docker image.

<a id="plugins.aea-test-autonomy.aea_test_autonomy.docker.tendermint.TendermintDockerImage.__init__"></a>

#### `__`init`__`

```python
def __init__(client: docker.DockerClient,
             abci_host: str = DEFAULT_ABCI_HOST,
             abci_port: int = DEFAULT_ABCI_PORT,
             port: int = DEFAULT_TENDERMINT_PORT,
             p2p_port: int = DEFAULT_P2P_PORT,
             com_port: int = DEFAULT_TENDERMINT_COM_PORT)
```

Initialize.

<a id="plugins.aea-test-autonomy.aea_test_autonomy.docker.tendermint.TendermintDockerImage.image"></a>

#### image

```python
@property
def image() -> str
```

Get the image name.

<a id="plugins.aea-test-autonomy.aea_test_autonomy.docker.tendermint.TendermintDockerImage.create"></a>

#### create

```python
def create() -> Container
```

Create the container.

<a id="plugins.aea-test-autonomy.aea_test_autonomy.docker.tendermint.TendermintDockerImage.create_many"></a>

#### create`_`many

```python
def create_many(nb_containers: int) -> List[Container]
```

Instantiate the image in many containers, parametrized.

<a id="plugins.aea-test-autonomy.aea_test_autonomy.docker.tendermint.TendermintDockerImage.wait"></a>

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

<a id="plugins.aea-test-autonomy.aea_test_autonomy.docker.tendermint.FlaskTendermintDockerImage"></a>

## FlaskTendermintDockerImage Objects

```python
class FlaskTendermintDockerImage(TendermintDockerImage)
```

Flask app with Tendermint Docker image.

<a id="plugins.aea-test-autonomy.aea_test_autonomy.docker.tendermint.FlaskTendermintDockerImage.__init__"></a>

#### `__`init`__`

```python
def __init__(client: docker.DockerClient,
             abci_host: str = DEFAULT_ABCI_HOST,
             abci_port: int = DEFAULT_ABCI_PORT,
             port: int = DEFAULT_TENDERMINT_PORT,
             p2p_port: int = DEFAULT_P2P_PORT,
             com_port: int = DEFAULT_TENDERMINT_COM_PORT + 2)
```

Initialize.

<a id="plugins.aea-test-autonomy.aea_test_autonomy.docker.tendermint.FlaskTendermintDockerImage.image"></a>

#### image

```python
@property
def image() -> str
```

Get the image name.

<a id="plugins.aea-test-autonomy.aea_test_autonomy.docker.tendermint.FlaskTendermintDockerImage.get_node_name"></a>

#### get`_`node`_`name

```python
@staticmethod
def get_node_name(i: int) -> str
```

Get the ith node's name.

<a id="plugins.aea-test-autonomy.aea_test_autonomy.docker.tendermint.FlaskTendermintDockerImage.get_port"></a>

#### get`_`port

```python
def get_port(i: int) -> int
```

Get the ith port.

<a id="plugins.aea-test-autonomy.aea_test_autonomy.docker.tendermint.FlaskTendermintDockerImage.get_com_port"></a>

#### get`_`com`_`port

```python
def get_com_port(i: int) -> int
```

Get the ith com port.

<a id="plugins.aea-test-autonomy.aea_test_autonomy.docker.tendermint.FlaskTendermintDockerImage.get_p2p_port"></a>

#### get`_`p2p`_`port

```python
def get_p2p_port(i: int) -> int
```

Get the ith p2p port.

<a id="plugins.aea-test-autonomy.aea_test_autonomy.docker.tendermint.FlaskTendermintDockerImage.get_abci_port"></a>

#### get`_`abci`_`port

```python
def get_abci_port(i: int) -> int
```

Get the ith abci port.

<a id="plugins.aea-test-autonomy.aea_test_autonomy.docker.tendermint.FlaskTendermintDockerImage.get_addr"></a>

#### get`_`addr

```python
def get_addr(prefix: str, i: int, p2p: bool = False) -> str
```

Get a node's address.

<a id="plugins.aea-test-autonomy.aea_test_autonomy.docker.tendermint.FlaskTendermintDockerImage.p2p_seeds"></a>

#### p2p`_`seeds

```python
@property
def p2p_seeds() -> List[str]
```

Get p2p seeds.

<a id="plugins.aea-test-autonomy.aea_test_autonomy.docker.tendermint.FlaskTendermintDockerImage.create_many"></a>

#### create`_`many

```python
def create_many(nb_containers: int) -> List[Container]
```

Create a list of node containers.

<a id="plugins.aea-test-autonomy.aea_test_autonomy.docker.tendermint.FlaskTendermintDockerImage.health_check"></a>

#### health`_`check

```python
def health_check(**kwargs: Any) -> None
```

Do a health-check of the Tendermint network.

<a id="plugins.aea-test-autonomy.aea_test_autonomy.docker.tendermint.FlaskTendermintDockerImage.cleanup"></a>

#### cleanup

```python
@staticmethod
def cleanup(nb_containers: int) -> None
```

Cleanup dangling containers.

