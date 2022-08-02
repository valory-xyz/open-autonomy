<a id="autonomy.test_tools.fixture_helpers"></a>

# autonomy.test`_`tools.fixture`_`helpers

This module contains helper classes/functions for fixtures.

<a id="autonomy.test_tools.fixture_helpers.UseTendermint"></a>

## UseTendermint Objects

```python
@pytest.mark.integration
class UseTendermint()
```

Inherit from this class to use Tendermint.

<a id="autonomy.test_tools.fixture_helpers.UseTendermint.abci_host"></a>

#### abci`_`host

```python
@property
def abci_host() -> str
```

Get the abci host address.

<a id="autonomy.test_tools.fixture_helpers.UseTendermint.abci_port"></a>

#### abci`_`port

```python
@property
def abci_port() -> int
```

Get the abci port.

<a id="autonomy.test_tools.fixture_helpers.UseTendermint.node_address"></a>

#### node`_`address

```python
@property
def node_address() -> str
```

Get the node address.

<a id="autonomy.test_tools.fixture_helpers.UseFlaskTendermintNode"></a>

## UseFlaskTendermintNode Objects

```python
@pytest.mark.integration
class UseFlaskTendermintNode()
```

Inherit from this class to use flask server with Tendermint.

<a id="autonomy.test_tools.fixture_helpers.UseFlaskTendermintNode.p2p_seeds"></a>

#### p2p`_`seeds

```python
@property
def p2p_seeds() -> List[str]
```

Get the p2p seeds.

<a id="autonomy.test_tools.fixture_helpers.UseFlaskTendermintNode.get_node_name"></a>

#### get`_`node`_`name

```python
def get_node_name(i: int) -> str
```

Get the node's name.

<a id="autonomy.test_tools.fixture_helpers.UseFlaskTendermintNode.get_abci_port"></a>

#### get`_`abci`_`port

```python
def get_abci_port(i: int) -> int
```

Get the ith rpc port.

<a id="autonomy.test_tools.fixture_helpers.UseFlaskTendermintNode.get_port"></a>

#### get`_`port

```python
def get_port(i: int) -> int
```

Get the ith port.

<a id="autonomy.test_tools.fixture_helpers.UseFlaskTendermintNode.get_com_port"></a>

#### get`_`com`_`port

```python
def get_com_port(i: int) -> int
```

Get the ith com port.

<a id="autonomy.test_tools.fixture_helpers.UseFlaskTendermintNode.get_laddr"></a>

#### get`_`laddr

```python
def get_laddr(i: int, p2p: bool = False) -> str
```

Get the ith rpc port.

<a id="autonomy.test_tools.fixture_helpers.UseFlaskTendermintNode.health_check"></a>

#### health`_`check

```python
def health_check(**kwargs: Any) -> None
```

Perform a health check.

<a id="autonomy.test_tools.fixture_helpers.UseGnosisSafeHardHatNet"></a>

## UseGnosisSafeHardHatNet Objects

```python
@pytest.mark.integration
class UseGnosisSafeHardHatNet()
```

Inherit from this class to use HardHat local net with Gnosis-Safe deployed.

<a id="autonomy.test_tools.fixture_helpers.UseGanache"></a>

## UseGanache Objects

```python
@pytest.mark.integration
class UseGanache()
```

Inherit from this class to use Ganache.

<a id="autonomy.test_tools.fixture_helpers.UseACNNode"></a>

## UseACNNode Objects

```python
@pytest.mark.integration
class UseACNNode()
```

Inherit from this class to use an ACNNode for a client connection

<a id="autonomy.test_tools.fixture_helpers.ACNNodeBaseTest"></a>

## ACNNodeBaseTest Objects

```python
class ACNNodeBaseTest(DockerBaseTest)
```

Base pytest class for Ganache.

<a id="autonomy.test_tools.fixture_helpers.ACNNodeBaseTest.setup_class_kwargs"></a>

#### setup`_`class`_`kwargs

```python
@classmethod
def setup_class_kwargs(cls) -> Dict[str, Any]
```

Get kwargs for _setup_class call.

<a id="autonomy.test_tools.fixture_helpers.ACNNodeBaseTest.url"></a>

#### url

```python
@classmethod
def url(cls) -> str
```

Get the url under which the image is reachable.

<a id="autonomy.test_tools.fixture_helpers.GanacheBaseTest"></a>

## GanacheBaseTest Objects

```python
class GanacheBaseTest(DockerBaseTest)
```

Base pytest class for Ganache.

<a id="autonomy.test_tools.fixture_helpers.GanacheBaseTest.setup_class_kwargs"></a>

#### setup`_`class`_`kwargs

```python
@classmethod
def setup_class_kwargs(cls) -> Dict[str, Any]
```

Get kwargs for _setup_class call.

<a id="autonomy.test_tools.fixture_helpers.GanacheBaseTest.key_pairs"></a>

#### key`_`pairs

```python
@classmethod
def key_pairs(cls) -> List[Tuple[str, str]]
```

Get the key pairs which are funded.

<a id="autonomy.test_tools.fixture_helpers.GanacheBaseTest.url"></a>

#### url

```python
@classmethod
def url(cls) -> str
```

Get the url under which the image is reachable.

<a id="autonomy.test_tools.fixture_helpers.HardHatBaseTest"></a>

## HardHatBaseTest Objects

```python
class HardHatBaseTest(DockerBaseTest)
```

Base pytest class for HardHat.

<a id="autonomy.test_tools.fixture_helpers.HardHatBaseTest.setup_class_kwargs"></a>

#### setup`_`class`_`kwargs

```python
@classmethod
def setup_class_kwargs(cls) -> Dict[str, Any]
```

Get kwargs for _setup_class call.

<a id="autonomy.test_tools.fixture_helpers.HardHatBaseTest.key_pairs"></a>

#### key`_`pairs

```python
@classmethod
def key_pairs(cls) -> List[Tuple[str, str]]
```

Get the key pairs which are funded.

<a id="autonomy.test_tools.fixture_helpers.HardHatBaseTest.url"></a>

#### url

```python
@classmethod
def url(cls) -> str
```

Get the url under which the image is reachable.

<a id="autonomy.test_tools.fixture_helpers.HardHatGnosisBaseTest"></a>

## HardHatGnosisBaseTest Objects

```python
class HardHatGnosisBaseTest(HardHatBaseTest)
```

Base pytest class for HardHat with Gnosis deployed.

<a id="autonomy.test_tools.fixture_helpers.HardHatAMMBaseTest"></a>

## HardHatAMMBaseTest Objects

```python
class HardHatAMMBaseTest(HardHatBaseTest)
```

Base pytest class for HardHat with Gnosis and Uniswap deployed.

