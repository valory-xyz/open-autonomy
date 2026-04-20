# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2026 Valory AG
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
# ------------------------------------------------------------------------------

"""Unit tests for MockServerChannel."""

# pylint: skip-file

import asyncio
import hashlib
import json
import socket
import urllib.error
import urllib.request
from typing import AsyncGenerator, Dict, List, Tuple, cast

import pytest
import pytest_asyncio

from packages.valory.connections.abci.connection import MockServerChannel
from packages.valory.protocols.abci import AbciMessage

MOCK_RPC_PORT = 37657  # avoid conflicts with real TM


def _http_get(url: str) -> Tuple[int, Dict]:
    """Make a GET request and return (status_code, json_body).

    :param url: the URL to request.
    :return: tuple of HTTP status code and parsed JSON body.
    """
    try:
        with urllib.request.urlopen(url) as resp:  # nosec
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


@pytest.fixture()
def free_port() -> int:
    """Get a free port to avoid conflicts between parallel tests."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))  # nosec
        return s.getsockname()[1]


@pytest.fixture()
def channel(free_port: int) -> MockServerChannel:
    """Create a MockServerChannel instance."""
    return MockServerChannel(
        rpc_host="127.0.0.1",
        rpc_port=free_port,
        block_time=10.0,  # long block time so blocks don't auto-produce during tests
    )


@pytest_asyncio.fixture()
async def connected_channel(
    channel: MockServerChannel,
) -> AsyncGenerator[MockServerChannel, None]:
    """Create and connect a MockServerChannel."""
    loop = asyncio.get_event_loop()
    await channel.connect(loop)
    yield channel
    await channel.disconnect()


# --- ABCI message sequencing tests ---


class TestABCIMessageSequencing:
    """Test the ABCI block lifecycle message sequence."""

    @pytest.mark.asyncio
    async def test_first_message_is_request_info(
        self, connected_channel: MockServerChannel
    ) -> None:
        """The first message produced should be REQUEST_INFO."""
        envelope = await asyncio.wait_for(connected_channel.get_message(), timeout=2.0)
        message = cast(AbciMessage, envelope.message)
        assert message.performative == AbciMessage.Performative.REQUEST_INFO

    @pytest.mark.asyncio
    async def test_init_chain_after_info_response(
        self, connected_channel: MockServerChannel
    ) -> None:
        """After responding to INFO, the next message should be REQUEST_INIT_CHAIN."""
        # get and respond to info
        envelope = await asyncio.wait_for(connected_channel.get_message(), timeout=2.0)
        info_msg = cast(AbciMessage, envelope.message)
        assert info_msg.performative == AbciMessage.Performative.REQUEST_INFO

        # respond — the mock only checks that the future is resolved
        await connected_channel.send(envelope)

        # next should be init_chain
        envelope = await asyncio.wait_for(connected_channel.get_message(), timeout=2.0)
        message = cast(AbciMessage, envelope.message)
        assert message.performative == AbciMessage.Performative.REQUEST_INIT_CHAIN

    @pytest.mark.asyncio
    async def test_full_block_lifecycle(
        self, connected_channel: MockServerChannel
    ) -> None:
        """Test the full sequence: info -> init_chain -> begin_block -> end_block -> commit."""
        expected_sequence = [
            AbciMessage.Performative.REQUEST_INFO,
            AbciMessage.Performative.REQUEST_INIT_CHAIN,
            AbciMessage.Performative.REQUEST_BEGIN_BLOCK,
            AbciMessage.Performative.REQUEST_END_BLOCK,
            AbciMessage.Performative.REQUEST_COMMIT,
        ]

        received: List[AbciMessage.Performative] = []
        for _ in range(len(expected_sequence)):
            envelope = await asyncio.wait_for(
                connected_channel.get_message(), timeout=2.0
            )
            msg = cast(AbciMessage, envelope.message)
            received.append(msg.performative)
            # send() just resolves the future; content doesn't matter for sequencing
            await connected_channel.send(envelope)

        assert received == expected_sequence

    @pytest.mark.asyncio
    async def test_deliver_tx_in_block(
        self, connected_channel: MockServerChannel
    ) -> None:
        """Test that a submitted tx appears as REQUEST_DELIVER_TX in the next block."""

        async def drain_and_respond(
            ch: MockServerChannel,
        ) -> AbciMessage.Performative:
            """Get next message and immediately respond to unblock the producer."""
            env = await asyncio.wait_for(ch.get_message(), timeout=2.0)
            msg = cast(AbciMessage, env.message)
            await ch.send(env)
            return msg.performative

        # drain info, init_chain, first empty block (begin, end, commit)
        for _ in range(5):
            await drain_and_respond(connected_channel)

        # now submit a tx via HTTP
        tx_data = b'{"test": "payload"}'
        url = f"http://127.0.0.1:{connected_channel.rpc_port}/broadcast_tx_sync?tx=0x{tx_data.hex()}"
        status, _ = await asyncio.to_thread(_http_get, url)
        assert status == 200

        # the tx event wakes the producer for the next block
        # expect: begin_block, deliver_tx, end_block, commit
        perfs = []
        for _ in range(4):
            p = await drain_and_respond(connected_channel)
            perfs.append(p)

        assert perfs == [
            AbciMessage.Performative.REQUEST_BEGIN_BLOCK,
            AbciMessage.Performative.REQUEST_DELIVER_TX,
            AbciMessage.Performative.REQUEST_END_BLOCK,
            AbciMessage.Performative.REQUEST_COMMIT,
        ]


# --- RPC HTTP handler tests ---


class TestRPCHandlers:
    """Test the mock Tendermint RPC HTTP endpoints."""

    @pytest.mark.asyncio
    async def test_broadcast_tx_sync(
        self, connected_channel: MockServerChannel
    ) -> None:
        """Test /broadcast_tx_sync returns hash and code 0."""
        tx_data = b"hello"
        expected_hash = hashlib.sha256(tx_data).hexdigest().upper()
        url = f"http://127.0.0.1:{connected_channel.rpc_port}/broadcast_tx_sync?tx=0x{tx_data.hex()}"
        status, body = await asyncio.to_thread(_http_get, url)
        assert status == 200
        assert body["result"]["code"] == 0
        assert body["result"]["hash"] == expected_hash

    @pytest.mark.asyncio
    async def test_tx_query_not_found(
        self, connected_channel: MockServerChannel
    ) -> None:
        """Test /tx?hash=... returns 500 when tx not yet delivered."""
        url = f"http://127.0.0.1:{connected_channel.rpc_port}/tx?hash=0xABCD1234"
        status, body = await asyncio.to_thread(_http_get, url)
        assert status == 500
        assert body["error"]["code"] == -32603
        assert "not found" in body["error"]["data"]

    @pytest.mark.asyncio
    async def test_tx_query_found(self, connected_channel: MockServerChannel) -> None:
        """Test /tx?hash=... returns 200 with tx_result after delivery."""
        tx_data = b"test_tx_found"
        tx_hash = hashlib.sha256(tx_data).hexdigest().upper()
        connected_channel._delivered_txs.add(tx_hash)
        url = f"http://127.0.0.1:{connected_channel.rpc_port}/tx?hash=0x{tx_hash}"
        status, body = await asyncio.to_thread(_http_get, url)
        assert status == 200
        assert body["result"]["tx_result"]["code"] == 0

    @pytest.mark.asyncio
    async def test_status_returns_height(
        self, connected_channel: MockServerChannel
    ) -> None:
        """Test /status returns current block height."""
        connected_channel._height = 42
        url = f"http://127.0.0.1:{connected_channel.rpc_port}/status"
        status, body = await asyncio.to_thread(_http_get, url)
        assert status == 200
        assert body["result"]["sync_info"]["latest_block_height"] == "42"

    @pytest.mark.asyncio
    async def test_net_info(self, connected_channel: MockServerChannel) -> None:
        """Test /net_info returns valid response."""
        url = f"http://127.0.0.1:{connected_channel.rpc_port}/net_info"
        status, body = await asyncio.to_thread(_http_get, url)
        assert status == 200
        assert body["result"]["n_peers"] == "0"

    @pytest.mark.asyncio
    async def test_hard_reset(self, connected_channel: MockServerChannel) -> None:
        """Test /hard_reset returns 200 (no-op)."""
        url = f"http://127.0.0.1:{connected_channel.rpc_port}/hard_reset"
        status, _ = await asyncio.to_thread(_http_get, url)
        assert status == 200

    @pytest.mark.asyncio
    async def test_gentle_reset(self, connected_channel: MockServerChannel) -> None:
        """Test /gentle_reset returns 200 (no-op)."""
        url = f"http://127.0.0.1:{connected_channel.rpc_port}/gentle_reset"
        status, _ = await asyncio.to_thread(_http_get, url)
        assert status == 200


# --- Connect/disconnect lifecycle tests ---


class TestLifecycle:
    """Test connect and disconnect behaviour."""

    @pytest.mark.asyncio
    async def test_connect_sets_state(self, channel: MockServerChannel) -> None:
        """Test that connect initialises internal state."""
        assert channel.is_stopped
        loop = asyncio.get_event_loop()
        await channel.connect(loop)
        assert not channel.is_stopped
        assert channel._request_queue is not None
        assert channel._block_producer_task is not None
        assert channel._rpc_server is not None
        await channel.disconnect()

    @pytest.mark.asyncio
    async def test_disconnect_cleans_up(self, channel: MockServerChannel) -> None:
        """Test that disconnect tears down all resources."""
        loop = asyncio.get_event_loop()
        await channel.connect(loop)
        await channel.disconnect()
        assert channel.is_stopped
        assert channel._block_producer_task is None
        assert channel._rpc_server is None
        assert channel._request_queue is None

    @pytest.mark.asyncio
    async def test_double_connect_is_noop(self, channel: MockServerChannel) -> None:
        """Test that connecting twice doesn't raise."""
        loop = asyncio.get_event_loop()
        await channel.connect(loop)
        await channel.connect(loop)  # should be a no-op
        assert not channel.is_stopped
        await channel.disconnect()

    @pytest.mark.asyncio
    async def test_double_disconnect_is_noop(self, channel: MockServerChannel) -> None:
        """Test that disconnecting twice doesn't raise."""
        loop = asyncio.get_event_loop()
        await channel.connect(loop)
        await channel.disconnect()
        await channel.disconnect()  # should be a no-op
        assert channel.is_stopped

    @pytest.mark.asyncio
    async def test_height_increments(
        self, connected_channel: MockServerChannel
    ) -> None:
        """Test that block height increments after a full block cycle."""
        assert connected_channel._height == 0

        async def drain(ch: MockServerChannel) -> None:
            env = await asyncio.wait_for(ch.get_message(), timeout=2.0)
            await ch.send(env)

        # drain info, init_chain, begin_block, end_block, commit = 1 full block
        for _ in range(5):
            await drain(connected_channel)

        assert connected_channel._height == 1

    @pytest.mark.asyncio
    async def test_connect_rollback_on_port_conflict(self, free_port: int) -> None:
        """Test that connect rolls back state if the port is already bound."""
        import socket as sock

        # occupy the port
        blocker = sock.socket(sock.AF_INET, sock.SOCK_STREAM)
        blocker.setsockopt(sock.SOL_SOCKET, sock.SO_REUSEADDR, 1)
        blocker.bind(("127.0.0.1", free_port))  # nosec
        blocker.listen(1)
        try:
            ch = MockServerChannel(
                rpc_host="127.0.0.1", rpc_port=free_port, block_time=10.0
            )
            with pytest.raises(OSError):
                await ch.connect(asyncio.get_event_loop())
            assert ch.is_stopped
            assert ch._request_queue is None
        finally:
            blocker.close()

    @pytest.mark.asyncio
    async def test_get_message_raises_on_producer_error(
        self, channel: MockServerChannel
    ) -> None:
        """Test that get_message raises ConnectionError after producer dies."""
        # manually set up just the queue (no producer) to test sentinel handling
        channel._is_stopped = False
        channel._request_queue = asyncio.Queue()
        await channel._request_queue.put(None)
        with pytest.raises(ConnectionError):
            await channel.get_message()
        channel._is_stopped = True

    @pytest.mark.asyncio
    async def test_broadcast_tx_invalid_hex(
        self, connected_channel: MockServerChannel
    ) -> None:
        """Test /broadcast_tx_sync with invalid hex returns 400."""
        url = (
            f"http://127.0.0.1:{connected_channel.rpc_port}/broadcast_tx_sync?tx=0xZZZZ"
        )
        status, body = await asyncio.to_thread(_http_get, url)
        assert status == 400
        assert body["error"]["code"] == -32602

    @pytest.mark.asyncio
    async def test_unknown_route_returns_404(
        self, connected_channel: MockServerChannel
    ) -> None:
        """Test that an unknown path returns 404."""
        url = f"http://127.0.0.1:{connected_channel.rpc_port}/nonexistent"
        status, body = await asyncio.to_thread(_http_get, url)
        assert status == 404
