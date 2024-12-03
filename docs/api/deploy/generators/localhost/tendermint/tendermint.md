<a id="autonomy.deploy.generators.localhost.tendermint.tendermint"></a>

# autonomy.deploy.generators.localhost.tendermint.tendermint

Tendermint manager.

<a id="autonomy.deploy.generators.localhost.tendermint.tendermint.StoppableThread"></a>

## StoppableThread Objects

```python
class StoppableThread(Thread)
```

Thread class with a stop() method.

<a id="autonomy.deploy.generators.localhost.tendermint.tendermint.StoppableThread.__init__"></a>

#### `__`init`__`

```python
def __init__(*args: Any, **kwargs: Any) -> None
```

Initialise the thread.

<a id="autonomy.deploy.generators.localhost.tendermint.tendermint.StoppableThread.stop"></a>

#### stop

```python
def stop() -> None
```

Set the stop event.

<a id="autonomy.deploy.generators.localhost.tendermint.tendermint.StoppableThread.stopped"></a>

#### stopped

```python
def stopped() -> bool
```

Check if the thread is stopped.

<a id="autonomy.deploy.generators.localhost.tendermint.tendermint.TendermintParams"></a>

## TendermintParams Objects

```python
class TendermintParams()
```

Tendermint node parameters.

<a id="autonomy.deploy.generators.localhost.tendermint.tendermint.TendermintParams.__init__"></a>

#### `__`init`__`

```python
def __init__(proxy_app: str,
             rpc_laddr: str = DEFAULT_RPC_LISTEN_ADDRESS,
             p2p_laddr: str = DEFAULT_P2P_LISTEN_ADDRESS,
             p2p_seeds: Optional[List[str]] = None,
             consensus_create_empty_blocks: bool = True,
             home: Optional[str] = None,
             use_grpc: bool = False)
```

Initialize the parameters to the Tendermint node.

**Arguments**:

- `proxy_app`: ABCI address.
- `rpc_laddr`: RPC address.
- `p2p_laddr`: P2P address.
- `p2p_seeds`: P2P seeds.
- `consensus_create_empty_blocks`: if true, Tendermint node creates empty blocks.
- `home`: Tendermint's home directory.
- `use_grpc`: Whether to use a gRPC server, or TCP

<a id="autonomy.deploy.generators.localhost.tendermint.tendermint.TendermintParams.__str__"></a>

#### `__`str`__`

```python
def __str__() -> str
```

Get the string representation.

<a id="autonomy.deploy.generators.localhost.tendermint.tendermint.TendermintParams.build_node_command"></a>

#### build`_`node`_`command

```python
def build_node_command(debug: bool = False) -> List[str]
```

Build the 'node' command.

<a id="autonomy.deploy.generators.localhost.tendermint.tendermint.TendermintParams.get_node_command_kwargs"></a>

#### get`_`node`_`command`_`kwargs

```python
@staticmethod
def get_node_command_kwargs() -> Dict
```

Get the node command kwargs

<a id="autonomy.deploy.generators.localhost.tendermint.tendermint.TendermintNode"></a>

## TendermintNode Objects

```python
class TendermintNode()
```

A class to manage a Tendermint node.

<a id="autonomy.deploy.generators.localhost.tendermint.tendermint.TendermintNode.__init__"></a>

#### `__`init`__`

```python
def __init__(params: TendermintParams,
             logger: Optional[Logger] = None,
             write_to_log: bool = False)
```

Initialize a Tendermint node.

**Arguments**:

- `params`: the parameters.
- `logger`: the logger.
- `write_to_log`: Write to log file.

<a id="autonomy.deploy.generators.localhost.tendermint.tendermint.TendermintNode.init"></a>

#### init

```python
def init() -> None
```

Initialize Tendermint node.

<a id="autonomy.deploy.generators.localhost.tendermint.tendermint.TendermintNode.start"></a>

#### start

```python
def start(debug: bool = False) -> None
```

Start a Tendermint node process.

<a id="autonomy.deploy.generators.localhost.tendermint.tendermint.TendermintNode.stop"></a>

#### stop

```python
def stop() -> None
```

Stop a Tendermint node process.

<a id="autonomy.deploy.generators.localhost.tendermint.tendermint.TendermintNode.log"></a>

#### log

```python
def log(line: str) -> None
```

Open and write a line to the log file.

<a id="autonomy.deploy.generators.localhost.tendermint.tendermint.TendermintNode.prune_blocks"></a>

#### prune`_`blocks

```python
def prune_blocks() -> int
```

Prune blocks from the Tendermint state

<a id="autonomy.deploy.generators.localhost.tendermint.tendermint.TendermintNode.reset_genesis_file"></a>

#### reset`_`genesis`_`file

```python
def reset_genesis_file(genesis_time: str, initial_height: str,
                       period_count: str) -> None
```

Reset genesis file.

