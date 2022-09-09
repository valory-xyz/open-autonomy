<a id="packages.valory.connections.abci.tests.test_abci"></a>

# packages.valory.connections.abci.tests.test`_`abci

Tests for valory/abci connection.

<a id="packages.valory.connections.abci.tests.test_abci.hypothesis_cleanup"></a>

#### hypothesis`_`cleanup

```python
@pytest.fixture(scope="session", autouse=True)
def hypothesis_cleanup() -> Generator
```

Fixture to remove hypothesis directory after tests.

<a id="packages.valory.connections.abci.tests.test_abci.AsyncBytesIO"></a>

## AsyncBytesIO Objects

```python
class AsyncBytesIO()
```

Utility class to emulate asyncio.StreamReader.

<a id="packages.valory.connections.abci.tests.test_abci.AsyncBytesIO.__init__"></a>

#### `__`init`__`

```python
def __init__(data: bytes) -> None
```

Initialize the buffer.

<a id="packages.valory.connections.abci.tests.test_abci.AsyncBytesIO.read"></a>

#### read

```python
async def read(n: int) -> bytes
```

Read n bytes.

<a id="packages.valory.connections.abci.tests.test_abci.ABCIAppTest"></a>

## ABCIAppTest Objects

```python
class ABCIAppTest()
```

A dummy ABCI application for testing purposes.

<a id="packages.valory.connections.abci.tests.test_abci.ABCIAppTest.AbciDialogues"></a>

## AbciDialogues Objects

```python
class AbciDialogues(BaseAbciDialogues)
```

The dialogues class keeps track of all ABCI dialogues.

<a id="packages.valory.connections.abci.tests.test_abci.ABCIAppTest.AbciDialogues.__init__"></a>

#### `__`init`__`

```python
def __init__(address: str) -> None
```

Initialize dialogues.

<a id="packages.valory.connections.abci.tests.test_abci.ABCIAppTest.__init__"></a>

#### `__`init`__`

```python
def __init__(address: str)
```

Initialize.

<a id="packages.valory.connections.abci.tests.test_abci.ABCIAppTest.handle"></a>

#### handle

```python
def handle(request: AbciMessage) -> AbciMessage
```

Process a request.

<a id="packages.valory.connections.abci.tests.test_abci.ABCIAppTest.info"></a>

#### info

```python
def info(request: AbciMessage) -> AbciMessage
```

Process an info request.

<a id="packages.valory.connections.abci.tests.test_abci.ABCIAppTest.flush"></a>

#### flush

```python
def flush(request: AbciMessage) -> AbciMessage
```

Process a flush request.

<a id="packages.valory.connections.abci.tests.test_abci.ABCIAppTest.init_chain"></a>

#### init`_`chain

```python
def init_chain(request: AbciMessage) -> AbciMessage
```

Process an init_chain request.

<a id="packages.valory.connections.abci.tests.test_abci.ABCIAppTest.query"></a>

#### query

```python
def query(request: AbciMessage) -> AbciMessage
```

Process a query request.

<a id="packages.valory.connections.abci.tests.test_abci.ABCIAppTest.check_tx"></a>

#### check`_`tx

```python
def check_tx(request: AbciMessage) -> AbciMessage
```

Process a check_tx request.

<a id="packages.valory.connections.abci.tests.test_abci.ABCIAppTest.deliver_tx"></a>

#### deliver`_`tx

```python
def deliver_tx(request: AbciMessage) -> AbciMessage
```

Process a deliver_tx request.

<a id="packages.valory.connections.abci.tests.test_abci.ABCIAppTest.begin_block"></a>

#### begin`_`block

```python
def begin_block(request: AbciMessage) -> AbciMessage
```

Process a begin_block request.

<a id="packages.valory.connections.abci.tests.test_abci.ABCIAppTest.end_block"></a>

#### end`_`block

```python
def end_block(request: AbciMessage) -> AbciMessage
```

Process an end_block request.

<a id="packages.valory.connections.abci.tests.test_abci.ABCIAppTest.commit"></a>

#### commit

```python
def commit(request: AbciMessage) -> AbciMessage
```

Process a commit request.

<a id="packages.valory.connections.abci.tests.test_abci.ABCIAppTest.set_option"></a>

#### set`_`option

```python
def set_option(request: AbciMessage) -> AbciMessage
```

Process a commit request.

<a id="packages.valory.connections.abci.tests.test_abci.ABCIAppTest.no_match"></a>

#### no`_`match

```python
def no_match(request: AbciMessage) -> None
```

No match.

<a id="packages.valory.connections.abci.tests.test_abci.BaseABCITest"></a>

## BaseABCITest Objects

```python
class BaseABCITest()
```

Base class for ABCI test.

<a id="packages.valory.connections.abci.tests.test_abci.BaseABCITest.make_app"></a>

#### make`_`app

```python
def make_app() -> ABCIAppTest
```

Make an ABCI app.

<a id="packages.valory.connections.abci.tests.test_abci.BaseTestABCITendermintIntegration"></a>

## BaseTestABCITendermintIntegration Objects

```python
@pytest.mark.integration

@pytest.mark.usefixtures("tendermint")
class BaseTestABCITendermintIntegration(BaseThreadedAsyncLoop,  ABC)
```

Integration test between ABCI connection and Tendermint node.

To use this class:

- inherit from this class, and write test methods;
- overwrite the method "make_app". The app must implement a 'handle(message)' method.

<a id="packages.valory.connections.abci.tests.test_abci.BaseTestABCITendermintIntegration.setup"></a>

#### setup

```python
def setup() -> None
```

Set up the test.

<a id="packages.valory.connections.abci.tests.test_abci.BaseTestABCITendermintIntegration.make_app"></a>

#### make`_`app

```python
@abstractmethod
def make_app() -> Any
```

Make an ABCI app.

<a id="packages.valory.connections.abci.tests.test_abci.BaseTestABCITendermintIntegration.health_check"></a>

#### health`_`check

```python
def health_check() -> bool
```

Do a health-check.

<a id="packages.valory.connections.abci.tests.test_abci.BaseTestABCITendermintIntegration.tendermint_url"></a>

#### tendermint`_`url

```python
def tendermint_url() -> str
```

Get the current Tendermint URL.

<a id="packages.valory.connections.abci.tests.test_abci.BaseTestABCITendermintIntegration.teardown"></a>

#### teardown

```python
def teardown() -> None
```

Tear down the test.

<a id="packages.valory.connections.abci.tests.test_abci.BaseTestABCITendermintIntegration.process_incoming_messages"></a>

#### process`_`incoming`_`messages

```python
async def process_incoming_messages() -> None
```

Receive requests and send responses from/to the Tendermint node

<a id="packages.valory.connections.abci.tests.test_abci.TestNoop"></a>

## TestNoop Objects

```python
@skip_docker_tests
class TestNoop(BaseABCITest,  BaseTestABCITendermintIntegration)
```

Test integration between ABCI connection and Tendermint, without txs.

<a id="packages.valory.connections.abci.tests.test_abci.TestNoop.test_run"></a>

#### test`_`run

```python
def test_run() -> None
```

Run the test.

Sleep for N seconds, check Tendermint is still running, and then stop the test.

<a id="packages.valory.connections.abci.tests.test_abci.TestQuery"></a>

## TestQuery Objects

```python
@skip_docker_tests
class TestQuery(BaseABCITest,  BaseTestABCITendermintIntegration)
```

Test integration ABCI-Tendermint with a query.

<a id="packages.valory.connections.abci.tests.test_abci.TestQuery.test_run"></a>

#### test`_`run

```python
def test_run() -> None
```

Run the test.

Send a query request to the Tendermint node, which will trigger
a query request to the ABCI connection.

<a id="packages.valory.connections.abci.tests.test_abci.TestTransaction"></a>

## TestTransaction Objects

```python
@skip_docker_tests
class TestTransaction(BaseABCITest,  BaseTestABCITendermintIntegration)
```

Test integration ABCI-Tendermint by sending a transaction.

<a id="packages.valory.connections.abci.tests.test_abci.TestTransaction.test_run"></a>

#### test`_`run

```python
def test_run() -> None
```

Run the test.

Send a query request to the Tendermint node, which will trigger
a query request to the ABCI connection.

<a id="packages.valory.connections.abci.tests.test_abci.test_connection_standalone_tendermint_setup"></a>

#### test`_`connection`_`standalone`_`tendermint`_`setup

```python
@pytest.mark.asyncio
async def test_connection_standalone_tendermint_setup() -> None
```

Test the setup of the connection configured with Tendermint.

<a id="packages.valory.connections.abci.tests.test_abci.test_ensure_connected_raises_connection_error"></a>

#### test`_`ensure`_`connected`_`raises`_`connection`_`error

```python
def test_ensure_connected_raises_connection_error() -> None
```

Test '_ensure_connected' raises ConnectionError if the channel is not connected.

<a id="packages.valory.connections.abci.tests.test_abci.test_encode_varint_method"></a>

#### test`_`encode`_`varint`_`method

```python
def test_encode_varint_method() -> None
```

Test encode_varint (uint64 Protobuf) method

<a id="packages.valory.connections.abci.tests.test_abci.test_encode_decode_varint"></a>

#### test`_`encode`_`decode`_`varint

```python
@settings(database=database.InMemoryExampleDatabase())
@given(integers(min_value=0, max_value=(1 << 64) - 1))
@pytest.mark.asyncio
async def test_encode_decode_varint(value: int) -> None
```

Test that encoding and decoding works.

<a id="packages.valory.connections.abci.tests.test_abci.test_encoding_raises"></a>

#### test`_`encoding`_`raises

```python
@pytest.mark.parametrize("value", [-1, 1 << 64])
@pytest.mark.asyncio
async def test_encoding_raises(value: int) -> None
```

Test encoding raises

<a id="packages.valory.connections.abci.tests.test_abci.test_decode_varint_raises_exception_when_failing"></a>

#### test`_`decode`_`varint`_`raises`_`exception`_`when`_`failing

```python
@pytest.mark.asyncio
async def test_decode_varint_raises_exception_when_failing() -> None
```

Test that decode_varint raises exception when the decoding fails.

<a id="packages.valory.connections.abci.tests.test_abci.test_decode_varint_raises_eof_error"></a>

#### test`_`decode`_`varint`_`raises`_`eof`_`error

```python
@pytest.mark.asyncio
async def test_decode_varint_raises_eof_error() -> None
```

Test that decode_varint raises exception when the EOF of the stream is reached.

<a id="packages.valory.connections.abci.tests.test_abci.test_dep_util"></a>

#### test`_`dep`_`util

```python
def test_dep_util() -> None
```

Test dependency utils.

<a id="packages.valory.connections.abci.tests.test_abci.test_varint_message_reader"></a>

#### test`_`varint`_`message`_`reader

```python
@pytest.mark.asyncio
async def test_varint_message_reader() -> None
```

Test VarintMessageReader

