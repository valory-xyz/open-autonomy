<a id="packages.valory.connections.abci.tests.test_fuzz.mock_node.channels.grpc_channel"></a>

# packages.valory.connections.abci.tests.test`_`fuzz.mock`_`node.channels.grpc`_`channel

GrpcChannel for MockNode

<a id="packages.valory.connections.abci.tests.test_fuzz.mock_node.channels.grpc_channel.GrpcChannel"></a>

## GrpcChannel Objects

```python
class GrpcChannel(BaseChannel)
```

Implements BaseChannel to use gRPC

<a id="packages.valory.connections.abci.tests.test_fuzz.mock_node.channels.grpc_channel.GrpcChannel.__init__"></a>

#### `__`init`__`

```python
def __init__(**kwargs: Dict) -> None
```

Initializes a GrpcChannel

:param: kwargs:
    - host: the host of the ABCI app (localhost by default)
    - port: the port of the ABCI app (26658 by default)


<a id="packages.valory.connections.abci.tests.test_fuzz.mock_node.channels.grpc_channel.GrpcChannel.send_info"></a>

#### send`_`info

```python
def send_info(request: abci_types.RequestInfo) -> abci_types.ResponseInfo
```

Sends an info request.

:param: request: RequestInfo pb object
:return: ResponseInfo pb object


<a id="packages.valory.connections.abci.tests.test_fuzz.mock_node.channels.grpc_channel.GrpcChannel.send_echo"></a>

#### send`_`echo

```python
def send_echo(request: abci_types.RequestEcho) -> abci_types.ResponseEcho
```

Sends an echo request.

:param: request: RequestEcho pb object
:return: ResponseEcho pb object


<a id="packages.valory.connections.abci.tests.test_fuzz.mock_node.channels.grpc_channel.GrpcChannel.send_flush"></a>

#### send`_`flush

```python
def send_flush(request: abci_types.RequestFlush) -> abci_types.ResponseFlush
```

Sends an flush request.

:param: request: RequestFlush pb object
:return: ResponseFlush pb object


<a id="packages.valory.connections.abci.tests.test_fuzz.mock_node.channels.grpc_channel.GrpcChannel.send_set_option"></a>

#### send`_`set`_`option

```python
def send_set_option(
        request: abci_types.RequestSetOption) -> abci_types.ResponseSetOption
```

Sends an setOption request.

:param: request: RequestSetOption pb object
:return: ResponseSetOption pb object


<a id="packages.valory.connections.abci.tests.test_fuzz.mock_node.channels.grpc_channel.GrpcChannel.send_deliver_tx"></a>

#### send`_`deliver`_`tx

```python
def send_deliver_tx(
        request: abci_types.RequestDeliverTx) -> abci_types.ResponseDeliverTx
```

Sends an deliverTx request.

:param: request: RequestDeliverTx pb object
:return: ResponseDeliverTx pb object


<a id="packages.valory.connections.abci.tests.test_fuzz.mock_node.channels.grpc_channel.GrpcChannel.send_check_tx"></a>

#### send`_`check`_`tx

```python
def send_check_tx(
        request: abci_types.RequestCheckTx) -> abci_types.ResponseCheckTx
```

Sends an checkTx request.

:param: request: RequestCheckTx pb object
:return: ResponseCheckTx pb object


<a id="packages.valory.connections.abci.tests.test_fuzz.mock_node.channels.grpc_channel.GrpcChannel.send_query"></a>

#### send`_`query

```python
def send_query(request: abci_types.RequestQuery) -> abci_types.ResponseQuery
```

Sends an query request.

:param: request: RequestQuery pb object
:return: ResponseQuery pb object


<a id="packages.valory.connections.abci.tests.test_fuzz.mock_node.channels.grpc_channel.GrpcChannel.send_commit"></a>

#### send`_`commit

```python
def send_commit(
        request: abci_types.RequestCommit) -> abci_types.ResponseCommit
```

Sends an commit request.

:param: request: RequestCommit pb object
:return: ResponseCommit pb object


<a id="packages.valory.connections.abci.tests.test_fuzz.mock_node.channels.grpc_channel.GrpcChannel.send_init_chain"></a>

#### send`_`init`_`chain

```python
def send_init_chain(
        request: abci_types.RequestInitChain) -> abci_types.ResponseInitChain
```

Sends an initChain request.

:param: request: RequestInitChain pb object
:return: ResponseInitChain pb object


<a id="packages.valory.connections.abci.tests.test_fuzz.mock_node.channels.grpc_channel.GrpcChannel.send_begin_block"></a>

#### send`_`begin`_`block

```python
def send_begin_block(
        request: abci_types.RequestBeginBlock
) -> abci_types.ResponseBeginBlock
```

Sends an beginBlock request.

:param: request: RequestBeginBlock pb object
:return: ResponseBeginBlock pb object


<a id="packages.valory.connections.abci.tests.test_fuzz.mock_node.channels.grpc_channel.GrpcChannel.send_end_block"></a>

#### send`_`end`_`block

```python
def send_end_block(
        request: abci_types.RequestEndBlock) -> abci_types.ResponseEndBlock
```

Sends an endBlock request.

:param: request: RequestEndBlock pb object
:return: ResponseEndBlock pb object


<a id="packages.valory.connections.abci.tests.test_fuzz.mock_node.channels.grpc_channel.GrpcChannel.send_list_snapshots"></a>

#### send`_`list`_`snapshots

```python
def send_list_snapshots(
    request: abci_types.RequestListSnapshots
) -> abci_types.ResponseListSnapshots
```

Sends an listSnapshots request.

:param: request: RequestListSnapshots pb object
:return: ResponseListSnapshots pb object


<a id="packages.valory.connections.abci.tests.test_fuzz.mock_node.channels.grpc_channel.GrpcChannel.send_offer_snapshot"></a>

#### send`_`offer`_`snapshot

```python
def send_offer_snapshot(
    request: abci_types.RequestOfferSnapshot
) -> abci_types.ResponseOfferSnapshot
```

Sends an offerSnapshot request.

:param: request: RequestOfferSnapshot pb object
:return: ResponseOfferSnapshot pb object


<a id="packages.valory.connections.abci.tests.test_fuzz.mock_node.channels.grpc_channel.GrpcChannel.send_load_snapshot_chunk"></a>

#### send`_`load`_`snapshot`_`chunk

```python
def send_load_snapshot_chunk(
    request: abci_types.RequestLoadSnapshotChunk
) -> abci_types.ResponseLoadSnapshotChunk
```

Sends an loadSnapshotChunk request.

:param: request: RequestLoadSnapshotChunk pb object
:return: ResponseLoadSnapshotChunk pb object


<a id="packages.valory.connections.abci.tests.test_fuzz.mock_node.channels.grpc_channel.GrpcChannel.send_apply_snapshot_chunk"></a>

#### send`_`apply`_`snapshot`_`chunk

```python
def send_apply_snapshot_chunk(
    request: abci_types.RequestApplySnapshotChunk
) -> abci_types.ResponseApplySnapshotChunk
```

Sends an applySnapshotChunk request.

:param: request: RequestApplySnapshotChunk pb object
:return: ResponseApplySnapshotChunk pb object


