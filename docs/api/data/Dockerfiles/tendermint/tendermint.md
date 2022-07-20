<a id="autonomy.data.Dockerfiles.tendermint.tendermint"></a>

# autonomy.data.Dockerfiles.tendermint.tendermint

Tendermint manager.

<a id="autonomy.data.Dockerfiles.tendermint.tendermint.StoppableThread"></a>

## StoppableThread Objects

```python
class StoppableThread(Thread)
```

Thread class with a stop() method.

<a id="autonomy.data.Dockerfiles.tendermint.tendermint.StoppableThread.__init__"></a>

#### `__`init`__`

```python
def __init__(*args: Any, **kwargs: Any) -> None
```

Initialise the thread.

<a id="autonomy.data.Dockerfiles.tendermint.tendermint.StoppableThread.stop"></a>

#### stop

```python
def stop() -> None
```

Set the stop event.

<a id="autonomy.data.Dockerfiles.tendermint.tendermint.StoppableThread.stopped"></a>

#### stopped

```python
def stopped() -> bool
```

Check if the thread is stopped.

<a id="autonomy.data.Dockerfiles.tendermint.tendermint.TendermintParams"></a>

## TendermintParams Objects

```python
class TendermintParams()
```

Tendermint node parameters.

<a id="autonomy.data.Dockerfiles.tendermint.tendermint.TendermintParams.__init__"></a>

#### `__`init`__`

```python
def __init__(proxy_app: str, rpc_laddr: str = DEFAULT_RPC_LISTEN_ADDRESS, p2p_laddr: str = DEFAULT_P2P_LISTEN_ADDRESS, p2p_seeds: Optional[List[str]] = None, consensus_create_empty_blocks: bool = True, home: Optional[str] = None)
```

Initialize the parameters to the Tendermint node.

**Arguments**:

- `proxy_app`: ABCI address.
- `rpc_laddr`: RPC address.
- `p2p_laddr`: P2P address.
- `p2p_seeds`: P2P seeds.
- `consensus_create_empty_blocks`: if true, Tendermint node creates empty blocks.
- `home`: Tendermint's home directory.

<a id="autonomy.data.Dockerfiles.tendermint.tendermint.TendermintParams.__str__"></a>

#### `__`str`__`

```python
def __str__() -> str
```

Get the string representation.

<a id="autonomy.data.Dockerfiles.tendermint.tendermint.TendermintNode"></a>

## TendermintNode Objects

```python
class TendermintNode()
```

A class to manage a Tendermint node.

<a id="autonomy.data.Dockerfiles.tendermint.tendermint.TendermintNode.__init__"></a>

#### `__`init`__`

```python
def __init__(params: TendermintParams, logger: Optional[Logger] = None)
```

Initialize a Tendermint node.

**Arguments**:

- `params`: the parameters.
- `logger`: the logger.

<a id="autonomy.data.Dockerfiles.tendermint.tendermint.TendermintNode.init"></a>

#### init

```python
def init() -> None
```

Initialize Tendermint node.

<a id="autonomy.data.Dockerfiles.tendermint.tendermint.TendermintNode.start"></a>

#### start

```python
def start(start_monitoring: bool = False) -> None
```

Start a Tendermint node process.

<a id="autonomy.data.Dockerfiles.tendermint.tendermint.TendermintNode.stop"></a>

#### stop

```python
def stop() -> None
```

Stop a Tendermint node process.

<a id="autonomy.data.Dockerfiles.tendermint.tendermint.TendermintNode.prune_blocks"></a>

#### prune`_`blocks

```python
def prune_blocks() -> int
```

Prune blocks from the Tendermint state

<a id="autonomy.data.Dockerfiles.tendermint.tendermint.TendermintNode.write_line"></a>

#### write`_`line

```python
def write_line(line: str) -> None
```

Open and write a line to the log file.

<a id="autonomy.data.Dockerfiles.tendermint.tendermint.TendermintNode.check_server_status"></a>

#### check`_`server`_`status

```python
def check_server_status() -> None
```

Check server status.

<a id="autonomy.data.Dockerfiles.tendermint.tendermint.TendermintNode.reset_genesis_file"></a>

#### reset`_`genesis`_`file

```python
def reset_genesis_file(genesis_time: str, initial_height: str) -> None
```

Reset genesis file.

