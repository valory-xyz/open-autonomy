<a id="packages.valory.connections.abci.connection"></a>

# packages.valory.connections.abci.connection

Connection to interact with an ABCI server.

<a id="packages.valory.connections.abci.connection.DEFAULT_LISTEN_ADDRESS"></a>

#### DEFAULT`_`LISTEN`_`ADDRESS

nosec

<a id="packages.valory.connections.abci.connection.MAX_READ_IN_BYTES"></a>

#### MAX`_`READ`_`IN`_`BYTES

Max we'll consume on a read stream (1 MiB)

<a id="packages.valory.connections.abci.connection.MAX_VARINT_BYTES"></a>

#### MAX`_`VARINT`_`BYTES

Max size of varint we support

<a id="packages.valory.connections.abci.connection.DecodeVarintError"></a>

## DecodeVarintError Objects

```python
class DecodeVarintError(Exception)
```

This exception is raised when an error occurs while decoding a varint.

<a id="packages.valory.connections.abci.connection.EncodeVarintError"></a>

## EncodeVarintError Objects

```python
class EncodeVarintError(Exception)
```

This exception is raised when an error occurs while encoding a varint.

<a id="packages.valory.connections.abci.connection.TooLargeVarint"></a>

## TooLargeVarint Objects

```python
class TooLargeVarint(Exception)
```

This exception is raised when a message with varint exceeding the max size is received.

<a id="packages.valory.connections.abci.connection.TooLargeVarint.__init__"></a>

#### `__`init`__`

```python
def __init__(received_size: int, max_size: int = MAX_READ_IN_BYTES)
```

Initialize the exception object.

**Arguments**:

- `received_size`: the received size.
- `max_size`: the maximum amount the connection supports.

<a id="packages.valory.connections.abci.connection.ShortBufferLengthError"></a>

## ShortBufferLengthError Objects

```python
class ShortBufferLengthError(Exception)
```

This exception is raised when the buffer length is shorter than expected.

<a id="packages.valory.connections.abci.connection.ShortBufferLengthError.__init__"></a>

#### `__`init`__`

```python
def __init__(expected_length: int, data: bytes)
```

Initialize the exception object.

**Arguments**:

- `expected_length`: the expected length to be read
- `data`: the data actually read

<a id="packages.valory.connections.abci.connection._TendermintABCISerializer"></a>

## `_`TendermintABCISerializer Objects

```python
class _TendermintABCISerializer()
```

(stateless) utility class to encode/decode messages for the communication with Tendermint.

<a id="packages.valory.connections.abci.connection._TendermintABCISerializer.encode_varint"></a>

#### encode`_`varint

```python
@classmethod
def encode_varint(cls, number: int) -> bytes
```

Encode a number in varint coding.

<a id="packages.valory.connections.abci.connection._TendermintABCISerializer.decode_varint"></a>

#### decode`_`varint

```python
@classmethod
async def decode_varint(cls,
                        buffer: asyncio.StreamReader,
                        max_length: int = MAX_VARINT_BYTES) -> int
```

Decode a number from its varint coding.

**Arguments**:

- `buffer`: the buffer to read from.
- `max_length`: the max number of bytes that can be read.

**Raises**:

- `None`: DecodeVarintError if the varint could not be decoded.
- `None`: EOFError if EOF byte is read and the process of decoding a varint has not started.

**Returns**:

the decoded int.

<a id="packages.valory.connections.abci.connection._TendermintABCISerializer.write_message"></a>

#### write`_`message

```python
@classmethod
def write_message(cls, message: Response) -> bytes
```

Write a message in a buffer.

<a id="packages.valory.connections.abci.connection.VarintMessageReader"></a>

## VarintMessageReader Objects

```python
class VarintMessageReader()
```

Varint message reader.

<a id="packages.valory.connections.abci.connection.VarintMessageReader.__init__"></a>

#### `__`init`__`

```python
def __init__(reader: asyncio.StreamReader) -> None
```

Initialize the reader.

<a id="packages.valory.connections.abci.connection.VarintMessageReader.read_next_message"></a>

#### read`_`next`_`message

```python
async def read_next_message() -> bytes
```

Read next message.

<a id="packages.valory.connections.abci.connection.VarintMessageReader.read_until"></a>

#### read`_`until

```python
async def read_until(n: int) -> bytes
```

Wait until n bytes are read from the stream.

<a id="packages.valory.connections.abci.connection.ABCIApplicationServicer"></a>

## ABCIApplicationServicer Objects

```python
class ABCIApplicationServicer(types_pb2_grpc.ABCIApplicationServicer)
```

Implements the gRPC servicer (handler)

<a id="packages.valory.connections.abci.connection.ABCIApplicationServicer.__init__"></a>

#### `__`init`__`

```python
def __init__(request_queue: asyncio.Queue, dialogues: AbciDialogues,
             target_skill: str)
```

Initializes the abci handler.

**Arguments**:

- `request_queue`: queue holding translated abci messages.
- `dialogues`: dialogues
- `target_skill`: target skill of messages

<a id="packages.valory.connections.abci.connection.ABCIApplicationServicer.send"></a>

#### send

```python
async def send(envelope: Envelope) -> Response
```

Returns response to the waiting request

:param: envelope: Envelope to be returned


<a id="packages.valory.connections.abci.connection.ABCIApplicationServicer.Echo"></a>

#### Echo

```python
async def Echo(request: RequestEcho,
               context: grpc.ServicerContext) -> ResponseEcho
```

Handles "Echo" gRPC requests

:param: request: The request from the Tendermint node
:param: context: The request context
:return: the Echo response


<a id="packages.valory.connections.abci.connection.ABCIApplicationServicer.Flush"></a>

#### Flush

```python
async def Flush(request: RequestFlush,
                context: grpc.ServicerContext) -> ResponseFlush
```

Handles "Flush" gRPC requests

:param: request: The request from the Tendermint node
:param: context: The request context
:return: the Echo response


<a id="packages.valory.connections.abci.connection.ABCIApplicationServicer.Info"></a>

#### Info

```python
async def Info(request: RequestInfo,
               context: grpc.ServicerContext) -> ResponseInfo
```

Handles "Info" gRPC requests

:param: request: The request from the Tendermint node
:param: context: The request context
:return: the Echo response


<a id="packages.valory.connections.abci.connection.ABCIApplicationServicer.SetOption"></a>

#### SetOption

```python
async def SetOption(request: RequestSetOption,
                    context: grpc.ServicerContext) -> ResponseSetOption
```

Handles "SetOption" gRPC requests

:param: request: The request from the Tendermint node
:param: context: The request context
:return: the Echo response


<a id="packages.valory.connections.abci.connection.ABCIApplicationServicer.DeliverTx"></a>

#### DeliverTx

```python
async def DeliverTx(request: RequestDeliverTx,
                    context: grpc.ServicerContext) -> ResponseDeliverTx
```

Handles "DeliverTx" gRPC requests

:param: request: The request from the Tendermint node
:param: context: The request context
:return: the Echo response


<a id="packages.valory.connections.abci.connection.ABCIApplicationServicer.CheckTx"></a>

#### CheckTx

```python
async def CheckTx(request: RequestCheckTx,
                  context: grpc.ServicerContext) -> ResponseCheckTx
```

Handles "CheckTx" gRPC requests

:param: request: The request from the Tendermint node
:param: context: The request context
:return: the Echo response


<a id="packages.valory.connections.abci.connection.ABCIApplicationServicer.Query"></a>

#### Query

```python
async def Query(request: RequestQuery,
                context: grpc.ServicerContext) -> ResponseQuery
```

Handles "Query" gRPC requests

:param: request: The request from the Tendermint node
:param: context: The request context
:return: the Echo response


<a id="packages.valory.connections.abci.connection.ABCIApplicationServicer.Commit"></a>

#### Commit

```python
async def Commit(request: RequestCommit,
                 context: grpc.ServicerContext) -> ResponseCommit
```

Handles "Commit" gRPC requests

:param: request: The request from the Tendermint node
:param: context: The request context
:return: the Echo response


<a id="packages.valory.connections.abci.connection.ABCIApplicationServicer.InitChain"></a>

#### InitChain

```python
async def InitChain(request: RequestInitChain,
                    context: grpc.ServicerContext) -> ResponseInitChain
```

Handles "InitChain" gRPC requests

:param: request: The request from the Tendermint node
:param: context: The request context
:return: the Echo response


<a id="packages.valory.connections.abci.connection.ABCIApplicationServicer.BeginBlock"></a>

#### BeginBlock

```python
async def BeginBlock(request: RequestBeginBlock,
                     context: grpc.ServicerContext) -> ResponseBeginBlock
```

Handles "BeginBlock" gRPC requests

:param: request: The request from the Tendermint node
:param: context: The request context
:return: the Echo response


<a id="packages.valory.connections.abci.connection.ABCIApplicationServicer.EndBlock"></a>

#### EndBlock

```python
async def EndBlock(request: RequestEndBlock,
                   context: grpc.ServicerContext) -> ResponseEndBlock
```

Handles "EndBlock" gRPC requests

:param: request: The request from the Tendermint node
:param: context: The request context
:return: the Echo response


<a id="packages.valory.connections.abci.connection.ABCIApplicationServicer.ListSnapshots"></a>

#### ListSnapshots

```python
async def ListSnapshots(
        request: RequestListSnapshots,
        context: grpc.ServicerContext) -> ResponseListSnapshots
```

Handles "ListSnapshots" gRPC requests

:param: request: The request from the Tendermint node
:param: context: The request context
:return: the Echo response


<a id="packages.valory.connections.abci.connection.ABCIApplicationServicer.OfferSnapshot"></a>

#### OfferSnapshot

```python
async def OfferSnapshot(
        request: RequestOfferSnapshot,
        context: grpc.ServicerContext) -> ResponseOfferSnapshot
```

Handles "OfferSnapshot" gRPC requests

:param: request: The request from the Tendermint node
:param: context: The request context
:return: the Echo response


<a id="packages.valory.connections.abci.connection.ABCIApplicationServicer.LoadSnapshotChunk"></a>

#### LoadSnapshotChunk

```python
async def LoadSnapshotChunk(
        request: RequestLoadSnapshotChunk,
        context: grpc.ServicerContext) -> ResponseLoadSnapshotChunk
```

Handles "LoadSnapshotChunk" gRPC requests

:param: request: The request from the Tendermint node
:param: context: The request context
:return: the Echo response


<a id="packages.valory.connections.abci.connection.ABCIApplicationServicer.ApplySnapshotChunk"></a>

#### ApplySnapshotChunk

```python
async def ApplySnapshotChunk(
        request: RequestApplySnapshotChunk,
        context: grpc.ServicerContext) -> ResponseApplySnapshotChunk
```

Handles "ApplySnapshotChunk" gRPC requests

:param: request: The request from the Tendermint node
:param: context: The request context
:return: the Echo response


<a id="packages.valory.connections.abci.connection.GrpcServerChannel"></a>

## GrpcServerChannel Objects

```python
class GrpcServerChannel()
```

gRPC server channel to handle incoming communication from the Tendermint node.

<a id="packages.valory.connections.abci.connection.GrpcServerChannel.__init__"></a>

#### `__`init`__`

```python
def __init__(target_skill_id: PublicId,
             address: str,
             port: int,
             logger: Optional[Logger] = None)
```

Initialize the gRPC server.

**Arguments**:

- `target_skill_id`: the public id of the target skill.
- `address`: the listen address.
- `port`: the port to listen from.
- `logger`: the logger.

<a id="packages.valory.connections.abci.connection.GrpcServerChannel.is_stopped"></a>

#### is`_`stopped

```python
@property
def is_stopped() -> bool
```

Check that the channel is stopped.

<a id="packages.valory.connections.abci.connection.GrpcServerChannel.connect"></a>

#### connect

```python
async def connect(loop: AbstractEventLoop) -> None
```

Connect.

**Arguments**:

- `loop`: asyncio event loop

<a id="packages.valory.connections.abci.connection.GrpcServerChannel.disconnect"></a>

#### disconnect

```python
async def disconnect() -> None
```

Disconnect the channel

<a id="packages.valory.connections.abci.connection.GrpcServerChannel.get_message"></a>

#### get`_`message

```python
async def get_message() -> Envelope
```

Get a message from the queue.

<a id="packages.valory.connections.abci.connection.GrpcServerChannel.send"></a>

#### send

```python
async def send(envelope: Envelope) -> None
```

Send a message.

<a id="packages.valory.connections.abci.connection.TcpServerChannel"></a>

## TcpServerChannel Objects

```python
class TcpServerChannel()
```

TCP server channel to handle incoming communication from the Tendermint node.

<a id="packages.valory.connections.abci.connection.TcpServerChannel.__init__"></a>

#### `__`init`__`

```python
def __init__(target_skill_id: PublicId,
             address: str,
             port: int,
             logger: Optional[Logger] = None)
```

Initialize the TCP server.

**Arguments**:

- `target_skill_id`: the public id of the target skill.
- `address`: the listen address.
- `port`: the port to listen from.
- `logger`: the logger.

<a id="packages.valory.connections.abci.connection.TcpServerChannel.is_stopped"></a>

#### is`_`stopped

```python
@property
def is_stopped() -> bool
```

Check that the channel is stopped.

<a id="packages.valory.connections.abci.connection.TcpServerChannel.connect"></a>

#### connect

```python
async def connect(loop: AbstractEventLoop) -> None
```

Connect.

Upon TCP Channel connection, start the TCP Server asynchronously.

**Arguments**:

- `loop`: asyncio event loop

<a id="packages.valory.connections.abci.connection.TcpServerChannel.disconnect"></a>

#### disconnect

```python
async def disconnect() -> None
```

Disconnect the channel

<a id="packages.valory.connections.abci.connection.TcpServerChannel.receive_messages"></a>

#### receive`_`messages

```python
async def receive_messages(reader: asyncio.StreamReader,
                           writer: asyncio.StreamWriter) -> None
```

Receive incoming messages.

<a id="packages.valory.connections.abci.connection.TcpServerChannel.get_message"></a>

#### get`_`message

```python
async def get_message() -> Envelope
```

Get a message from the queue.

<a id="packages.valory.connections.abci.connection.TcpServerChannel.send"></a>

#### send

```python
async def send(envelope: Envelope) -> None
```

Send a message.

<a id="packages.valory.connections.abci.connection.StoppableThread"></a>

## StoppableThread Objects

```python
class StoppableThread(Thread)
```

Thread class with a stop() method.

<a id="packages.valory.connections.abci.connection.StoppableThread.__init__"></a>

#### `__`init`__`

```python
def __init__(*args: Any, **kwargs: Any) -> None
```

Initialise the thread.

<a id="packages.valory.connections.abci.connection.StoppableThread.stop"></a>

#### stop

```python
def stop() -> None
```

Set the stop event.

<a id="packages.valory.connections.abci.connection.StoppableThread.stopped"></a>

#### stopped

```python
def stopped() -> bool
```

Check if the thread is stopped.

<a id="packages.valory.connections.abci.connection.TendermintParams"></a>

## TendermintParams Objects

```python
class TendermintParams()
```

Tendermint node parameters.

<a id="packages.valory.connections.abci.connection.TendermintParams.__init__"></a>

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

<a id="packages.valory.connections.abci.connection.TendermintParams.__str__"></a>

#### `__`str`__`

```python
def __str__() -> str
```

Get the string representation.

<a id="packages.valory.connections.abci.connection.TendermintParams.build_node_command"></a>

#### build`_`node`_`command

```python
def build_node_command(debug: bool = False) -> List[str]
```

Build the 'node' command.

<a id="packages.valory.connections.abci.connection.TendermintParams.get_node_command_kwargs"></a>

#### get`_`node`_`command`_`kwargs

```python
@staticmethod
def get_node_command_kwargs() -> Dict
```

Get the node command kwargs

<a id="packages.valory.connections.abci.connection.TendermintNode"></a>

## TendermintNode Objects

```python
class TendermintNode()
```

A class to manage a Tendermint node.

<a id="packages.valory.connections.abci.connection.TendermintNode.__init__"></a>

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

<a id="packages.valory.connections.abci.connection.TendermintNode.init"></a>

#### init

```python
def init() -> None
```

Initialize Tendermint node.

<a id="packages.valory.connections.abci.connection.TendermintNode.start"></a>

#### start

```python
def start(debug: bool = False) -> None
```

Start a Tendermint node process.

<a id="packages.valory.connections.abci.connection.TendermintNode.stop"></a>

#### stop

```python
def stop() -> None
```

Stop a Tendermint node process.

<a id="packages.valory.connections.abci.connection.TendermintNode.log"></a>

#### log

```python
def log(line: str) -> None
```

Open and write a line to the log file.

<a id="packages.valory.connections.abci.connection.TendermintNode.prune_blocks"></a>

#### prune`_`blocks

```python
def prune_blocks() -> int
```

Prune blocks from the Tendermint state

<a id="packages.valory.connections.abci.connection.TendermintNode.reset_genesis_file"></a>

#### reset`_`genesis`_`file

```python
def reset_genesis_file(genesis_time: str, initial_height: str,
                       period_count: str) -> None
```

Reset genesis file.

<a id="packages.valory.connections.abci.connection.ABCIServerConnection"></a>

## ABCIServerConnection Objects

```python
class ABCIServerConnection(Connection)
```

ABCI server.

<a id="packages.valory.connections.abci.connection.ABCIServerConnection.__init__"></a>

#### `__`init`__`

```python
def __init__(**kwargs: Any) -> None
```

Initialize the connection.

**Arguments**:

- `kwargs`: keyword arguments passed to component base

<a id="packages.valory.connections.abci.connection.ABCIServerConnection.connect"></a>

#### connect

```python
async def connect() -> None
```

Set up the connection.

In the implementation, remember to update 'connection_status' accordingly.

<a id="packages.valory.connections.abci.connection.ABCIServerConnection.disconnect"></a>

#### disconnect

```python
async def disconnect() -> None
```

Tear down the connection.

In the implementation, remember to update 'connection_status' accordingly.

<a id="packages.valory.connections.abci.connection.ABCIServerConnection.send"></a>

#### send

```python
async def send(envelope: Envelope) -> None
```

Send an envelope.

**Arguments**:

- `envelope`: the envelope to send.

<a id="packages.valory.connections.abci.connection.ABCIServerConnection.receive"></a>

#### receive

```python
async def receive(*args: Any, **kwargs: Any) -> Optional[Envelope]
```

Receive an envelope. Blocking.

**Arguments**:

- `args`: arguments to receive
- `kwargs`: keyword arguments to receive

**Returns**:

the envelope received, if present.  # noqa: DAR202

