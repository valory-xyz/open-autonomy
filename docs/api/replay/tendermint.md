<a id="autonomy.replay.tendermint"></a>

# autonomy.replay.tendermint

Script to build and run tendermint nodes from data dumps.

<a id="autonomy.replay.tendermint.RanOutOfDumpsToReplay"></a>

## RanOutOfDumpsToReplay Objects

```python
class RanOutOfDumpsToReplay(Exception)
```

Error to raise when we run out of dumps to replay.

<a id="autonomy.replay.tendermint.TendermintRunner"></a>

## TendermintRunner Objects

```python
class TendermintRunner()
```

Run tednermint using the dump.

<a id="autonomy.replay.tendermint.TendermintRunner.__init__"></a>

#### `__`init`__`

```python
def __init__(node_id: int, dump_dir: Path, n_periods: int) -> None
```

Initialize object.

<a id="autonomy.replay.tendermint.TendermintRunner.update_period"></a>

#### update`_`period

```python
def update_period() -> None
```

Update period.

<a id="autonomy.replay.tendermint.TendermintRunner.get_last_block_height"></a>

#### get`_`last`_`block`_`height

```python
def get_last_block_height() -> int
```

Returns the last block height before dumping.

<a id="autonomy.replay.tendermint.TendermintRunner.start"></a>

#### start

```python
def start() -> None
```

Start tendermint process.

<a id="autonomy.replay.tendermint.TendermintRunner.stop"></a>

#### stop

```python
def stop() -> None
```

Stop tendermint process.

<a id="autonomy.replay.tendermint.TendermintNetwork"></a>

## TendermintNetwork Objects

```python
class TendermintNetwork()
```

Tendermint network.

<a id="autonomy.replay.tendermint.TendermintNetwork.init"></a>

#### init

```python
def init(dump_dir: Path) -> None
```

Initialize object.

<a id="autonomy.replay.tendermint.TendermintNetwork.update_period"></a>

#### update`_`period

```python
def update_period(node_id: int) -> None
```

Update period for nth node.

<a id="autonomy.replay.tendermint.TendermintNetwork.get_last_block_height"></a>

#### get`_`last`_`block`_`height

```python
def get_last_block_height(node_id: int) -> int
```

Returns last block height before dumping for `node_id`

<a id="autonomy.replay.tendermint.TendermintNetwork.stop_node"></a>

#### stop`_`node

```python
def stop_node(node_id: int) -> None
```

Stop a specific node.

<a id="autonomy.replay.tendermint.TendermintNetwork.start"></a>

#### start

```python
def start() -> None
```

Start networks.

<a id="autonomy.replay.tendermint.TendermintNetwork.stop"></a>

#### stop

```python
def stop() -> None
```

Stop network.

<a id="autonomy.replay.tendermint.TendermintNetwork.run_until_interruption"></a>

#### run`_`until`_`interruption

```python
def run_until_interruption() -> None
```

Run network until interruption.

<a id="autonomy.replay.tendermint.hard_reset"></a>

#### hard`_`reset

```python
@app.route("/<int:node_id>/hard_reset")
def hard_reset(node_id: int) -> Dict
```

Reset tendermint node.

<a id="autonomy.replay.tendermint.status"></a>

#### status

```python
@app.get("/<int:node_id>/status")
def status(node_id: int) -> Dict
```

Status

This endpoint will imitate the tendermint RPC server's /status so the ABCI
app doesn't get blocked in replay mode.

**Arguments**:

- `node_id`: node id

**Returns**:

response

<a id="autonomy.replay.tendermint.broadcast_tx_sync"></a>

#### broadcast`_`tx`_`sync

```python
@app.get("/<int:node_id>/broadcast_tx_sync")
def broadcast_tx_sync(node_id: int) -> Dict
```

Similar as /status

<a id="autonomy.replay.tendermint.tx"></a>

#### tx

```python
@app.get("/<int:node_id>/tx")
def tx(node_id: int) -> Dict
```

Similar as /status

