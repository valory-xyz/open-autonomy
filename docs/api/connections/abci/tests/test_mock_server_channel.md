<a id="packages.valory.connections.abci.tests.test_mock_server_channel"></a>

# packages.valory.connections.abci.tests.test`_`mock`_`server`_`channel

Unit tests for MockServerChannel.

<a id="packages.valory.connections.abci.tests.test_mock_server_channel.MOCK_RPC_PORT"></a>

#### MOCK`_`RPC`_`PORT

avoid conflicts with real TM

<a id="packages.valory.connections.abci.tests.test_mock_server_channel.free_port"></a>

#### free`_`port

```python
@pytest.fixture()
def free_port() -> int
```

Get a free port to avoid conflicts between parallel tests.

<a id="packages.valory.connections.abci.tests.test_mock_server_channel.channel"></a>

#### channel

```python
@pytest.fixture()
def channel(free_port: int) -> MockServerChannel
```

Create a MockServerChannel instance.

<a id="packages.valory.connections.abci.tests.test_mock_server_channel.connected_channel"></a>

#### connected`_`channel

```python
@pytest_asyncio.fixture()
async def connected_channel(
        channel: MockServerChannel) -> AsyncGenerator[MockServerChannel, None]
```

Create and connect a MockServerChannel.

<a id="packages.valory.connections.abci.tests.test_mock_server_channel.TestABCIMessageSequencing"></a>

## TestABCIMessageSequencing Objects

```python
class TestABCIMessageSequencing()
```

Test the ABCI block lifecycle message sequence.

<a id="packages.valory.connections.abci.tests.test_mock_server_channel.TestABCIMessageSequencing.test_first_message_is_request_info"></a>

#### test`_`first`_`message`_`is`_`request`_`info

```python
@pytest.mark.asyncio
async def test_first_message_is_request_info(
        connected_channel: MockServerChannel) -> None
```

The first message produced should be REQUEST_INFO.

<a id="packages.valory.connections.abci.tests.test_mock_server_channel.TestABCIMessageSequencing.test_init_chain_after_info_response"></a>

#### test`_`init`_`chain`_`after`_`info`_`response

```python
@pytest.mark.asyncio
async def test_init_chain_after_info_response(
        connected_channel: MockServerChannel) -> None
```

After responding to INFO, the next message should be REQUEST_INIT_CHAIN.

<a id="packages.valory.connections.abci.tests.test_mock_server_channel.TestABCIMessageSequencing.test_full_block_lifecycle"></a>

#### test`_`full`_`block`_`lifecycle

```python
@pytest.mark.asyncio
async def test_full_block_lifecycle(
        connected_channel: MockServerChannel) -> None
```

Test the full sequence: info -> init_chain -> begin_block -> end_block -> commit.

<a id="packages.valory.connections.abci.tests.test_mock_server_channel.TestABCIMessageSequencing.test_deliver_tx_in_block"></a>

#### test`_`deliver`_`tx`_`in`_`block

```python
@pytest.mark.asyncio
async def test_deliver_tx_in_block(
        connected_channel: MockServerChannel) -> None
```

Test that a submitted tx appears as REQUEST_DELIVER_TX in the next block.

<a id="packages.valory.connections.abci.tests.test_mock_server_channel.TestRPCHandlers"></a>

## TestRPCHandlers Objects

```python
class TestRPCHandlers()
```

Test the mock Tendermint RPC HTTP endpoints.

<a id="packages.valory.connections.abci.tests.test_mock_server_channel.TestRPCHandlers.test_broadcast_tx_sync"></a>

#### test`_`broadcast`_`tx`_`sync

```python
@pytest.mark.asyncio
async def test_broadcast_tx_sync(connected_channel: MockServerChannel) -> None
```

Test /broadcast_tx_sync returns hash and code 0.

<a id="packages.valory.connections.abci.tests.test_mock_server_channel.TestRPCHandlers.test_tx_query_not_found"></a>

#### test`_`tx`_`query`_`not`_`found

```python
@pytest.mark.asyncio
async def test_tx_query_not_found(
        connected_channel: MockServerChannel) -> None
```

Test /tx?hash=... returns 500 when tx not yet delivered.

<a id="packages.valory.connections.abci.tests.test_mock_server_channel.TestRPCHandlers.test_tx_query_found"></a>

#### test`_`tx`_`query`_`found

```python
@pytest.mark.asyncio
async def test_tx_query_found(connected_channel: MockServerChannel) -> None
```

Test /tx?hash=... returns 200 with tx_result after delivery.

<a id="packages.valory.connections.abci.tests.test_mock_server_channel.TestRPCHandlers.test_status_returns_height"></a>

#### test`_`status`_`returns`_`height

```python
@pytest.mark.asyncio
async def test_status_returns_height(
        connected_channel: MockServerChannel) -> None
```

Test /status returns current block height.

<a id="packages.valory.connections.abci.tests.test_mock_server_channel.TestRPCHandlers.test_net_info"></a>

#### test`_`net`_`info

```python
@pytest.mark.asyncio
async def test_net_info(connected_channel: MockServerChannel) -> None
```

Test /net_info returns valid response.

<a id="packages.valory.connections.abci.tests.test_mock_server_channel.TestRPCHandlers.test_hard_reset"></a>

#### test`_`hard`_`reset

```python
@pytest.mark.asyncio
async def test_hard_reset(connected_channel: MockServerChannel) -> None
```

Test /hard_reset returns 200 (no-op).

<a id="packages.valory.connections.abci.tests.test_mock_server_channel.TestRPCHandlers.test_gentle_reset"></a>

#### test`_`gentle`_`reset

```python
@pytest.mark.asyncio
async def test_gentle_reset(connected_channel: MockServerChannel) -> None
```

Test /gentle_reset returns 200 (no-op).

<a id="packages.valory.connections.abci.tests.test_mock_server_channel.TestLifecycle"></a>

## TestLifecycle Objects

```python
class TestLifecycle()
```

Test connect and disconnect behaviour.

<a id="packages.valory.connections.abci.tests.test_mock_server_channel.TestLifecycle.test_connect_sets_state"></a>

#### test`_`connect`_`sets`_`state

```python
@pytest.mark.asyncio
async def test_connect_sets_state(channel: MockServerChannel) -> None
```

Test that connect initialises internal state.

<a id="packages.valory.connections.abci.tests.test_mock_server_channel.TestLifecycle.test_disconnect_cleans_up"></a>

#### test`_`disconnect`_`cleans`_`up

```python
@pytest.mark.asyncio
async def test_disconnect_cleans_up(channel: MockServerChannel) -> None
```

Test that disconnect tears down all resources.

<a id="packages.valory.connections.abci.tests.test_mock_server_channel.TestLifecycle.test_double_connect_is_noop"></a>

#### test`_`double`_`connect`_`is`_`noop

```python
@pytest.mark.asyncio
async def test_double_connect_is_noop(channel: MockServerChannel) -> None
```

Test that connecting twice doesn't raise.

<a id="packages.valory.connections.abci.tests.test_mock_server_channel.TestLifecycle.test_double_disconnect_is_noop"></a>

#### test`_`double`_`disconnect`_`is`_`noop

```python
@pytest.mark.asyncio
async def test_double_disconnect_is_noop(channel: MockServerChannel) -> None
```

Test that disconnecting twice doesn't raise.

<a id="packages.valory.connections.abci.tests.test_mock_server_channel.TestLifecycle.test_height_increments"></a>

#### test`_`height`_`increments

```python
@pytest.mark.asyncio
async def test_height_increments(connected_channel: MockServerChannel) -> None
```

Test that block height starts at 0 and is incremented by the block producer.

