<a id="packages.valory.connections.abci.connection"></a>

# packages.valory.connections.abci.connection

Connection to interact with an ABCI server.

<a id="packages.valory.connections.abci.connection.DecodeVarintError"></a>

## DecodeVarintError Objects

```python
class DecodeVarintError(Exception)
```

This exception is raised when an error occurs while decoding a varint.

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
async def decode_varint(cls, buffer: asyncio.StreamReader, max_length: int = MAX_VARINT_BYTES) -> int
```

Decode a number from its varint coding.

**Arguments**:

- `buffer`: the buffer to read from.
- `max_length`: the max number of bytes that can be read.

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

<a id="packages.valory.connections.abci.connection.TcpServerChannel"></a>

## TcpServerChannel Objects

```python
class TcpServerChannel()
```

TCP server channel to handle incoming communication from the Tendermint node.

<a id="packages.valory.connections.abci.connection.TcpServerChannel.__init__"></a>

#### `__`init`__`

```python
def __init__(target_skill_id: PublicId, address: str, port: int, logger: Optional[Logger] = None)
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
async def receive_messages(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None
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

<a id="packages.valory.connections.abci.connection.TendermintParams.__str__"></a>

#### `__`str`__`

```python
def __str__() -> str
```

Get the string representation.

<a id="packages.valory.connections.abci.connection.TendermintNode"></a>

## TendermintNode Objects

```python
class TendermintNode()
```

A class to manage a Tendermint node.

<a id="packages.valory.connections.abci.connection.TendermintNode.__init__"></a>

#### `__`init`__`

```python
def __init__(params: TendermintParams, logger: Optional[Logger] = None)
```

Initialize a Tendermint node.

**Arguments**:

- `params`: the parameters.
- `logger`: the logger.

<a id="packages.valory.connections.abci.connection.TendermintNode.init"></a>

#### init

```python
def init() -> None
```

Initialize Tendermint node.

<a id="packages.valory.connections.abci.connection.TendermintNode.start"></a>

#### start

```python
def start(start_monitoring: bool = False) -> None
```

Start a Tendermint node process.

<a id="packages.valory.connections.abci.connection.TendermintNode.stop"></a>

#### stop

```python
def stop() -> None
```

Stop a Tendermint node process.

<a id="packages.valory.connections.abci.connection.TendermintNode.prune_blocks"></a>

#### prune`_`blocks

```python
def prune_blocks() -> None
```

Prune blocks from the Tendermint state

<a id="packages.valory.connections.abci.connection.TendermintNode.write_line"></a>

#### write`_`line

```python
def write_line(line: str) -> None
```

Open and write a line to the log file.

<a id="packages.valory.connections.abci.connection.TendermintNode.check_server_status"></a>

#### check`_`server`_`status

```python
def check_server_status() -> None
```

Check server status.

<a id="packages.valory.connections.abci.connection.TendermintNode.reset_genesis_file"></a>

#### reset`_`genesis`_`file

```python
def reset_genesis_file(genesis_time: str, initial_height: str) -> None
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

