<a id="plugins.aea-test-autonomy.aea_test_autonomy.docker.registries"></a>

# plugins.aea-test-autonomy.aea`_`test`_`autonomy.docker.registries

Tendermint Docker image.

<a id="plugins.aea-test-autonomy.aea_test_autonomy.docker.registries.DEFAULT_ACCOUNT"></a>

#### DEFAULT`_`ACCOUNT

nosec

<a id="plugins.aea-test-autonomy.aea_test_autonomy.docker.registries.COMPONENT_REGISTRY"></a>

#### COMPONENT`_`REGISTRY

nosec

<a id="plugins.aea-test-autonomy.aea_test_autonomy.docker.registries.AGENT_REGISTRY"></a>

#### AGENT`_`REGISTRY

nosec

<a id="plugins.aea-test-autonomy.aea_test_autonomy.docker.registries.REGISTRIES_MANAGER"></a>

#### REGISTRIES`_`MANAGER

nosec

<a id="plugins.aea-test-autonomy.aea_test_autonomy.docker.registries.GNOSIS_SAFE_MULTISIG"></a>

#### GNOSIS`_`SAFE`_`MULTISIG

nosec

<a id="plugins.aea-test-autonomy.aea_test_autonomy.docker.registries.SERVICE_REGISTRY"></a>

#### SERVICE`_`REGISTRY

nosec

<a id="plugins.aea-test-autonomy.aea_test_autonomy.docker.registries.SERVICE_REGISTRY_TOKEN_UTILITY"></a>

#### SERVICE`_`REGISTRY`_`TOKEN`_`UTILITY

nosec

<a id="plugins.aea-test-autonomy.aea_test_autonomy.docker.registries.SERVICE_MANAGER_TOKEN"></a>

#### SERVICE`_`MANAGER`_`TOKEN

nosec

<a id="plugins.aea-test-autonomy.aea_test_autonomy.docker.registries.SERVICE_REGISTRY_L2"></a>

#### SERVICE`_`REGISTRY`_`L2

nosec

<a id="plugins.aea-test-autonomy.aea_test_autonomy.docker.registries.SERVICE_MANAGER"></a>

#### SERVICE`_`MANAGER

nosec

<a id="plugins.aea-test-autonomy.aea_test_autonomy.docker.registries.OPERATOR_WHITELIST"></a>

#### OPERATOR`_`WHITELIST

nosec

<a id="plugins.aea-test-autonomy.aea_test_autonomy.docker.registries.ERC20_TOKEN"></a>

#### ERC20`_`TOKEN

nosec

<a id="plugins.aea-test-autonomy.aea_test_autonomy.docker.registries.GNOSIS_SAFE_MASTER_COPY"></a>

#### GNOSIS`_`SAFE`_`MASTER`_`COPY

nosec

<a id="plugins.aea-test-autonomy.aea_test_autonomy.docker.registries.GNOSIS_SAFE_PROXY_FACTORY"></a>

#### GNOSIS`_`SAFE`_`PROXY`_`FACTORY

nosec

<a id="plugins.aea-test-autonomy.aea_test_autonomy.docker.registries.GNOSIS_SAFE_MULTISEND"></a>

#### GNOSIS`_`SAFE`_`MULTISEND

nosec

<a id="plugins.aea-test-autonomy.aea_test_autonomy.docker.registries.SERVICE_MULTISIG_1"></a>

#### SERVICE`_`MULTISIG`_`1

nosec

<a id="plugins.aea-test-autonomy.aea_test_autonomy.docker.registries.SERVICE_MULTISIG_2"></a>

#### SERVICE`_`MULTISIG`_`2

nosec

<a id="plugins.aea-test-autonomy.aea_test_autonomy.docker.registries.RegistriesDockerImage"></a>

## RegistriesDockerImage Objects

```python
class RegistriesDockerImage(DockerImage)
```

Spawn a local Ethereum network with deployed registry contracts, using HardHat.

<a id="plugins.aea-test-autonomy.aea_test_autonomy.docker.registries.RegistriesDockerImage.__init__"></a>

#### `__`init`__`

```python
def __init__(client: docker.DockerClient,
             addr: str = DEFAULT_HARDHAT_ADDR,
             port: int = DEFAULT_HARDHAT_PORT,
             env_vars: Optional[Dict] = None)
```

Initialize.

<a id="plugins.aea-test-autonomy.aea_test_autonomy.docker.registries.RegistriesDockerImage.image"></a>

#### image

```python
@property
def image() -> str
```

Get the image name.

<a id="plugins.aea-test-autonomy.aea_test_autonomy.docker.registries.RegistriesDockerImage.create"></a>

#### create

```python
def create() -> Container
```

Create the container.

<a id="plugins.aea-test-autonomy.aea_test_autonomy.docker.registries.RegistriesDockerImage.create_many"></a>

#### create`_`many

```python
def create_many(nb_containers: int) -> List[Container]
```

Instantiate the image in many containers, parametrized.

<a id="plugins.aea-test-autonomy.aea_test_autonomy.docker.registries.RegistriesDockerImage.wait"></a>

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

