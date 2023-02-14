<a id="plugins.aea-test-autonomy.aea_test_autonomy.helpers.tendermint_utils"></a>

# plugins.aea-test-autonomy.aea`_`test`_`autonomy.helpers.tendermint`_`utils

Helpers for Tendermint.

<a id="plugins.aea-test-autonomy.aea_test_autonomy.helpers.tendermint_utils.TendermintNodeInfo"></a>

## TendermintNodeInfo Objects

```python
class TendermintNodeInfo()
```

Data class to store Tendermint node info.

<a id="plugins.aea-test-autonomy.aea_test_autonomy.helpers.tendermint_utils.TendermintNodeInfo.__init__"></a>

#### `__`init`__`

```python
def __init__(node_id: str, abci_port: int, rpc_port: int, p2p_port: int,
             home: Path)
```

Initialize Tendermint node info.

<a id="plugins.aea-test-autonomy.aea_test_autonomy.helpers.tendermint_utils.TendermintNodeInfo.rpc_laddr"></a>

#### rpc`_`laddr

```python
@property
def rpc_laddr() -> str
```

Get ith rpc_laddr.

<a id="plugins.aea-test-autonomy.aea_test_autonomy.helpers.tendermint_utils.TendermintNodeInfo.get_http_addr"></a>

#### get`_`http`_`addr

```python
def get_http_addr(host: str) -> str
```

Get ith HTTP RCP address, given the host.

<a id="plugins.aea-test-autonomy.aea_test_autonomy.helpers.tendermint_utils.TendermintNodeInfo.p2p_laddr"></a>

#### p2p`_`laddr

```python
@property
def p2p_laddr() -> str
```

Get ith p2p_laddr.

<a id="plugins.aea-test-autonomy.aea_test_autonomy.helpers.tendermint_utils.TendermintLocalNetworkBuilder"></a>

## TendermintLocalNetworkBuilder Objects

```python
class TendermintLocalNetworkBuilder()
```

Build a local Tendermint network.

<a id="plugins.aea-test-autonomy.aea_test_autonomy.helpers.tendermint_utils.TendermintLocalNetworkBuilder.__init__"></a>

#### `__`init`__`

```python
def __init__(nb_nodes: int,
             directory: Path,
             consensus_create_empty_blocks: bool = True) -> None
```

Initialize the builder.

<a id="plugins.aea-test-autonomy.aea_test_autonomy.helpers.tendermint_utils.TendermintLocalNetworkBuilder.get_p2p_seeds"></a>

#### get`_`p2p`_`seeds

```python
def get_p2p_seeds() -> List[str]
```

Get p2p seeds.

<a id="plugins.aea-test-autonomy.aea_test_autonomy.helpers.tendermint_utils.TendermintLocalNetworkBuilder.get_command"></a>

#### get`_`command

```python
def get_command(i: int) -> List[str]
```

Get command-line command for the ith process.

<a id="plugins.aea-test-autonomy.aea_test_autonomy.helpers.tendermint_utils.TendermintLocalNetworkBuilder.http_rpc_laddrs"></a>

#### http`_`rpc`_`laddrs

```python
@property
def http_rpc_laddrs() -> List[str]
```

Get HTTP RPC listening addresses.

<a id="plugins.aea-test-autonomy.aea_test_autonomy.helpers.tendermint_utils.BaseTendermintTestClass"></a>

## BaseTendermintTestClass Objects

```python
class BaseTendermintTestClass()
```

MixIn class for Pytest classes.

<a id="plugins.aea-test-autonomy.aea_test_autonomy.helpers.tendermint_utils.BaseTendermintTestClass.health_check"></a>

#### health`_`check

```python
@staticmethod
def health_check(tendermint_net: TendermintLocalNetworkBuilder,
                 **kwargs: Any) -> None
```

Do a health-check of the Tendermint network.

