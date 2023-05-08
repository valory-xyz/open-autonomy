<a id="plugins.aea-test-autonomy.aea_test_autonomy.fixture_helpers"></a>

# plugins.aea-test-autonomy.aea`_`test`_`autonomy.fixture`_`helpers

This module contains helper classes/functions for fixtures.

<a id="plugins.aea-test-autonomy.aea_test_autonomy.fixture_helpers.tendermint_port"></a>

#### tendermint`_`port

```python
@pytest.fixture(scope="session")
def tendermint_port() -> int
```

Get the Tendermint port

<a id="plugins.aea-test-autonomy.aea_test_autonomy.fixture_helpers.abci_host"></a>

#### abci`_`host

```python
@pytest.fixture(scope="session")
def abci_host() -> str
```

Get the ABCI host

<a id="plugins.aea-test-autonomy.aea_test_autonomy.fixture_helpers.abci_port"></a>

#### abci`_`port

```python
@pytest.fixture(scope="session")
def abci_port() -> int
```

Get the ABCI port

<a id="plugins.aea-test-autonomy.aea_test_autonomy.fixture_helpers.tendermint"></a>

#### tendermint

```python
@pytest.fixture(scope="class")
def tendermint(tendermint_port: int,
               abci_host: str,
               abci_port: int,
               timeout: float = 2.0,
               max_attempts: int = 10) -> Generator
```

Launch the Ganache image.

<a id="plugins.aea-test-autonomy.aea_test_autonomy.fixture_helpers.UseTendermint"></a>

## UseTendermint Objects

```python
@pytest.mark.integration
class UseTendermint()
```

Inherit from this class to use Tendermint.

<a id="plugins.aea-test-autonomy.aea_test_autonomy.fixture_helpers.UseTendermint.abci_host"></a>

#### abci`_`host

```python
@property
def abci_host() -> str
```

Get the abci host address.

<a id="plugins.aea-test-autonomy.aea_test_autonomy.fixture_helpers.UseTendermint.abci_port"></a>

#### abci`_`port

```python
@property
def abci_port() -> int
```

Get the abci port.

<a id="plugins.aea-test-autonomy.aea_test_autonomy.fixture_helpers.UseTendermint.node_address"></a>

#### node`_`address

```python
@property
def node_address() -> str
```

Get the node address.

<a id="plugins.aea-test-autonomy.aea_test_autonomy.fixture_helpers.nb_nodes"></a>

#### nb`_`nodes

```python
@pytest.fixture
def nb_nodes(request: Any) -> int
```

Get a parametrized number of nodes.

<a id="plugins.aea-test-autonomy.aea_test_autonomy.fixture_helpers.flask_tendermint"></a>

#### flask`_`tendermint

```python
@pytest.fixture
def flask_tendermint(
    tendermint_port: int,
    nb_nodes: int,
    abci_host: str,
    abci_port: int,
    timeout: float = 2.0,
    max_attempts: int = 10
) -> Generator[FlaskTendermintDockerImage, None, None]
```

Launch the Flask server with Tendermint container.

<a id="plugins.aea-test-autonomy.aea_test_autonomy.fixture_helpers.UseFlaskTendermintNode"></a>

## UseFlaskTendermintNode Objects

```python
@pytest.mark.integration
class UseFlaskTendermintNode()
```

Inherit from this class to use flask server with Tendermint.

<a id="plugins.aea-test-autonomy.aea_test_autonomy.fixture_helpers.UseFlaskTendermintNode.p2p_seeds"></a>

#### p2p`_`seeds

```python
@property
def p2p_seeds() -> List[str]
```

Get the p2p seeds.

<a id="plugins.aea-test-autonomy.aea_test_autonomy.fixture_helpers.UseFlaskTendermintNode.get_node_name"></a>

#### get`_`node`_`name

```python
def get_node_name(i: int) -> str
```

Get the node's name.

<a id="plugins.aea-test-autonomy.aea_test_autonomy.fixture_helpers.UseFlaskTendermintNode.get_abci_port"></a>

#### get`_`abci`_`port

```python
def get_abci_port(i: int) -> int
```

Get the ith rpc port.

<a id="plugins.aea-test-autonomy.aea_test_autonomy.fixture_helpers.UseFlaskTendermintNode.get_port"></a>

#### get`_`port

```python
def get_port(i: int) -> int
```

Get the ith port.

<a id="plugins.aea-test-autonomy.aea_test_autonomy.fixture_helpers.UseFlaskTendermintNode.get_com_port"></a>

#### get`_`com`_`port

```python
def get_com_port(i: int) -> int
```

Get the ith com port.

<a id="plugins.aea-test-autonomy.aea_test_autonomy.fixture_helpers.UseFlaskTendermintNode.get_laddr"></a>

#### get`_`laddr

```python
def get_laddr(i: int, p2p: bool = False) -> str
```

Get the ith rpc port.

<a id="plugins.aea-test-autonomy.aea_test_autonomy.fixture_helpers.UseFlaskTendermintNode.health_check"></a>

#### health`_`check

```python
def health_check(**kwargs: Any) -> None
```

Perform a health check.

<a id="plugins.aea-test-autonomy.aea_test_autonomy.fixture_helpers.ganache_addr"></a>

#### ganache`_`addr

```python
@pytest.fixture(scope="session")
def ganache_addr() -> str
```

HTTP address to the Ganache node.

<a id="plugins.aea-test-autonomy.aea_test_autonomy.fixture_helpers.ganache_port"></a>

#### ganache`_`port

```python
@pytest.fixture(scope="session")
def ganache_port() -> int
```

Port of the connection to the Ganache Node to use during the tests.

<a id="plugins.aea-test-autonomy.aea_test_autonomy.fixture_helpers.ganache_configuration"></a>

#### ganache`_`configuration

```python
@pytest.fixture(scope="session")
def ganache_configuration() -> Dict
```

Get the Ganache configuration for testing purposes.

<a id="plugins.aea-test-autonomy.aea_test_autonomy.fixture_helpers.ganache_scope_function"></a>

#### ganache`_`scope`_`function

```python
@pytest.fixture(scope="function")
def ganache_scope_function(ganache_configuration: Dict,
                           ganache_addr: str,
                           ganache_port: int,
                           timeout: float = 2.0,
                           max_attempts: int = 10) -> Generator
```

Launch the Ganache image. This fixture is scoped to a function which means it will destroyed at the end of the test.

<a id="plugins.aea-test-autonomy.aea_test_autonomy.fixture_helpers.ganache_scope_class"></a>

#### ganache`_`scope`_`class

```python
@pytest.fixture(scope="class")
def ganache_scope_class(ganache_configuration: Dict,
                        ganache_addr: str,
                        ganache_port: int,
                        timeout: float = 2.0,
                        max_attempts: int = 10) -> Generator
```

Launch the Ganache image. This fixture is scoped to a class which means it will destroyed after running every test in a class.

<a id="plugins.aea-test-autonomy.aea_test_autonomy.fixture_helpers.ammnet_scope_class"></a>

#### ammnet`_`scope`_`class

```python
@pytest.fixture(scope="class")
def ammnet_scope_class(timeout: float = 2.0,
                       max_attempts: int = 26) -> Generator
```

Launch the Ganache image. This fixture is scoped to a class which means it will destroyed after running every test in a class.

<a id="plugins.aea-test-autonomy.aea_test_autonomy.fixture_helpers.UseGanache"></a>

## UseGanache Objects

```python
@pytest.mark.integration
class UseGanache()
```

Inherit from this class to use Ganache.

<a id="plugins.aea-test-autonomy.aea_test_autonomy.fixture_helpers.GanacheBaseTest"></a>

## GanacheBaseTest Objects

```python
class GanacheBaseTest(DockerBaseTest)
```

Base pytest class for Ganache.

<a id="plugins.aea-test-autonomy.aea_test_autonomy.fixture_helpers.GanacheBaseTest.setup_class_kwargs"></a>

#### setup`_`class`_`kwargs

```python
@classmethod
def setup_class_kwargs(cls) -> Dict[str, Any]
```

Get kwargs for _setup_class call.

<a id="plugins.aea-test-autonomy.aea_test_autonomy.fixture_helpers.GanacheBaseTest.key_pairs"></a>

#### key`_`pairs

```python
@classmethod
def key_pairs(cls) -> List[Tuple[str, str]]
```

Get the key pairs which are funded.

<a id="plugins.aea-test-autonomy.aea_test_autonomy.fixture_helpers.GanacheBaseTest.url"></a>

#### url

```python
@classmethod
def url(cls) -> str
```

Get the url under which the image is reachable.

<a id="plugins.aea-test-autonomy.aea_test_autonomy.fixture_helpers.acn_config"></a>

#### acn`_`config

```python
@pytest.fixture(scope="session")
def acn_config() -> Dict
```

ACN node configuration.

<a id="plugins.aea-test-autonomy.aea_test_autonomy.fixture_helpers.acn_node"></a>

#### acn`_`node

```python
@pytest.fixture(scope="function")
def acn_node(acn_config: Dict,
             timeout: float = 2.0,
             max_attempts: int = 10) -> Generator
```

Launch the Ganache image.

<a id="plugins.aea-test-autonomy.aea_test_autonomy.fixture_helpers.UseACNNode"></a>

## UseACNNode Objects

```python
@pytest.mark.integration
class UseACNNode()
```

Inherit from this class to use an ACNNode for a client connection

<a id="plugins.aea-test-autonomy.aea_test_autonomy.fixture_helpers.ACNNodeBaseTest"></a>

## ACNNodeBaseTest Objects

```python
class ACNNodeBaseTest(DockerBaseTest)
```

Base pytest class for Ganache.

<a id="plugins.aea-test-autonomy.aea_test_autonomy.fixture_helpers.ACNNodeBaseTest.setup_class_kwargs"></a>

#### setup`_`class`_`kwargs

```python
@classmethod
def setup_class_kwargs(cls) -> Dict[str, Any]
```

Get kwargs for _setup_class call.

<a id="plugins.aea-test-autonomy.aea_test_autonomy.fixture_helpers.ACNNodeBaseTest.url"></a>

#### url

```python
@classmethod
def url(cls) -> str
```

Get the url under which the image is reachable.

<a id="plugins.aea-test-autonomy.aea_test_autonomy.fixture_helpers.hardhat_addr"></a>

#### hardhat`_`addr

```python
@pytest.fixture(scope="session")
def hardhat_addr() -> str
```

Get the hardhat addr

<a id="plugins.aea-test-autonomy.aea_test_autonomy.fixture_helpers.hardhat_port"></a>

#### hardhat`_`port

```python
@pytest.fixture(scope="session")
def hardhat_port() -> int
```

Get the hardhat port

<a id="plugins.aea-test-autonomy.aea_test_autonomy.fixture_helpers.key_pairs"></a>

#### key`_`pairs

```python
@pytest.fixture(scope="session")
def key_pairs() -> List[Tuple[str, str]]
```

Get the default key paris for hardhat.

<a id="plugins.aea-test-autonomy.aea_test_autonomy.fixture_helpers.HardHatBaseTest"></a>

## HardHatBaseTest Objects

```python
class HardHatBaseTest(DockerBaseTest)
```

Base pytest class for HardHat.

<a id="plugins.aea-test-autonomy.aea_test_autonomy.fixture_helpers.HardHatBaseTest.setup_class_kwargs"></a>

#### setup`_`class`_`kwargs

```python
@classmethod
def setup_class_kwargs(cls) -> Dict[str, Any]
```

Get kwargs for _setup_class call.

<a id="plugins.aea-test-autonomy.aea_test_autonomy.fixture_helpers.HardHatBaseTest.key_pairs"></a>

#### key`_`pairs

```python
@classmethod
def key_pairs(cls) -> List[Tuple[str, str]]
```

Get the key pairs which are funded.

<a id="plugins.aea-test-autonomy.aea_test_autonomy.fixture_helpers.HardHatBaseTest.url"></a>

#### url

```python
@classmethod
def url(cls) -> str
```

Get the url under which the image is reachable.

<a id="plugins.aea-test-autonomy.aea_test_autonomy.fixture_helpers.registries_scope_class"></a>

#### registries`_`scope`_`class

```python
@pytest.fixture(scope="class")
def registries_scope_class(timeout: float = 2.0,
                           max_attempts: int = 20) -> Generator
```

Launch the Registry contracts image. This fixture is scoped to a class which means it will destroyed after running every test in a class.

<a id="plugins.aea-test-autonomy.aea_test_autonomy.fixture_helpers.UseRegistries"></a>

## UseRegistries Objects

```python
@pytest.mark.integration
class UseRegistries()
```

Inherit from this class to use a local Ethereum network with deployed registry contracts

<a id="plugins.aea-test-autonomy.aea_test_autonomy.fixture_helpers.gnosis_safe_hardhat_scope_function"></a>

#### gnosis`_`safe`_`hardhat`_`scope`_`function

```python
@pytest.fixture(scope="function")
def gnosis_safe_hardhat_scope_function(hardhat_addr: str,
                                       hardhat_port: int,
                                       timeout: float = 3.0,
                                       max_attempts: int = 40) -> Generator
```

Launch the HardHat node with Gnosis Safe contracts deployed. This fixture is scoped to a function which means it will destroyed at the end of the test.

<a id="plugins.aea-test-autonomy.aea_test_autonomy.fixture_helpers.gnosis_safe_hardhat_scope_class"></a>

#### gnosis`_`safe`_`hardhat`_`scope`_`class

```python
@pytest.fixture(scope="class")
def gnosis_safe_hardhat_scope_class(hardhat_addr: str,
                                    hardhat_port: int,
                                    timeout: float = 3.0,
                                    max_attempts: int = 40) -> Generator
```

Launch the HardHat node with Gnosis Safe contracts deployed.This fixture is scoped to a class which means it will destroyed after running every test in a class.

<a id="plugins.aea-test-autonomy.aea_test_autonomy.fixture_helpers.UseGnosisSafeHardHatNet"></a>

## UseGnosisSafeHardHatNet Objects

```python
@pytest.mark.integration
class UseGnosisSafeHardHatNet()
```

Inherit from this class to use HardHat local net with Gnosis-Safe deployed.

<a id="plugins.aea-test-autonomy.aea_test_autonomy.fixture_helpers.HardHatGnosisBaseTest"></a>

## HardHatGnosisBaseTest Objects

```python
class HardHatGnosisBaseTest(HardHatBaseTest)
```

Base pytest class for HardHat with Gnosis deployed.

<a id="plugins.aea-test-autonomy.aea_test_autonomy.fixture_helpers.HardHatAMMBaseTest"></a>

## HardHatAMMBaseTest Objects

```python
class HardHatAMMBaseTest(HardHatBaseTest)
```

Base pytest class for HardHat with Gnosis and Uniswap deployed.

<a id="plugins.aea-test-autonomy.aea_test_autonomy.fixture_helpers.RegistriesBaseTest"></a>

## RegistriesBaseTest Objects

```python
class RegistriesBaseTest(HardHatBaseTest)
```

Base pytest class for component registries.

<a id="plugins.aea-test-autonomy.aea_test_autonomy.fixture_helpers.ipfs_daemon"></a>

#### ipfs`_`daemon

```python
@pytest.fixture(scope="class")
def ipfs_daemon() -> Iterator[bool]
```

Starts an IPFS daemon for the tests.

<a id="plugins.aea-test-autonomy.aea_test_autonomy.fixture_helpers.ipfs_domain"></a>

#### ipfs`_`domain

```python
@pytest.fixture(scope="session")
def ipfs_domain() -> str
```

Get the ipfs domain

<a id="plugins.aea-test-autonomy.aea_test_autonomy.fixture_helpers.UseLocalIpfs"></a>

## UseLocalIpfs Objects

```python
class UseLocalIpfs()
```

Use local IPFS daemon.

