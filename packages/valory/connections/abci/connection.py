# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021 Valory AG
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
"""Connection to interact with an ABCI server."""
import asyncio
from abc import ABC
from asyncio import AbstractEventLoop, CancelledError, Task
from asyncio.base_events import Server
from io import BytesIO
from logging import Logger
from typing import Any, Dict, Optional, Tuple, Type, cast

from aea.configurations.base import PublicId
from aea.connections.base import Connection, ConnectionStates
from aea.mail.base import Envelope

from packages.valory.connections.abci.tendermint.abci.types_pb2 import Request
from packages.valory.connections.abci.tendermint_decoder import (
    _TendermintProtocolDecoder,
)
from packages.valory.connections.abci.tendermint_encoder import (
    _TendermintProtocolEncoder,
)


PUBLIC_ID = PublicId.from_str("valory/abci:0.1.0")

DEFAULT_LISTEN_ADDRESS = "0.0.0.0"
DEFAULT_ABCI_PORT = 26658
MAX_READ_IN_BYTES = 64 * 1024  # Max we'll consume on a read stream


class _TendermintABCISerializer:
    """(stateless) utility class to encode/decode messages for the communication with Tendermint."""

    @classmethod
    def encode_varint(cls, number: int):
        """Encode a number in varint coding."""
        # Shift to int64
        number = number << 1
        buf = b""
        while True:
            towrite = number & 0x7F
            number >>= 7
            if number:
                buf += bytes((towrite | 0x80,))
            else:
                buf += bytes((towrite,))
                break
        return buf

    @classmethod
    def decode_varint(cls, buffer: BytesIO):
        """Decode a number from its varint coding."""
        shift = 0
        result = 0
        while True:
            i = cls._read_one(buffer)
            result |= (i & 0x7F) << shift
            shift += 7
            if not (i & 0x80):
                break
        return result

    @classmethod
    def _read_one(cls, buffer: BytesIO):
        """Read one byte to decode a varint."""
        c = buffer.read(1)
        if c == b"":
            raise EOFError("Unexpected EOF while reading bytes")
        return ord(c)

    @classmethod
    def write_message(cls, message):
        """Write a message in a buffer."""
        buffer = BytesIO(b"")
        bz = message.SerializeToString()
        encoded = cls.encode_varint(len(bz))
        buffer.write(encoded)
        buffer.write(bz)
        return buffer.getvalue()

    @classmethod
    def read_messages(cls, buffer: BytesIO, message: Type):
        """Return an iterator over the messages found in the `reader` buffer."""
        while True:
            try:
                length = cls.decode_varint(buffer) >> 1
            except EOFError:
                return
            data = buffer.read(length)
            if len(data) < length:
                return
            m = message()
            m.ParseFromString(data)

            yield m


class TcpServerChannel:
    """TCP server channel to handle incoming communication from the Tendermint node."""

    def __init__(
        self,
        connection_address: str,
        address: str = DEFAULT_LISTEN_ADDRESS,
        port: int = DEFAULT_ABCI_PORT,
        logger: Optional[Logger] = None,
    ):
        """

        Initialize the TCP server.

        :param connection_address: the connection identity address.
        :param address: the listen address.
        :param port: the port to listen from.
        :param logger: the logger.
        """
        self.connection_address = connection_address
        self.address = address
        self.port = port
        self.logger = logger

        # channel state
        self._is_stopped: bool = True
        self.queue: Optional[asyncio.Queue[Envelope]] = None
        self._server: Optional[Server] = None
        self._server_task: Optional[Task] = None
        self._streams_by_socket: Dict[
            str, Tuple[asyncio.StreamReader, asyncio.StreamWriter]
        ] = {}

    @property
    def is_stopped(self) -> bool:
        """Check that the channel is stopped."""
        return self._is_stopped

    async def connect(self, loop: AbstractEventLoop) -> None:
        """
        Connect.

        Upon TCP Channel connection, start the TCP Server asynchronously.

        :param loop: asyncio event loop
        """
        if not self._is_stopped:
            return
        self._is_stopped = False
        self.queue = asyncio.Queue()
        self._server = await asyncio.start_server(
            self.receive_messages,
            host=self.address,
            port=self.port,
        )
        self._server_task = loop.create_task(self._server.serve_forever())

    async def disconnect(self) -> None:
        """Disconnect the channel"""
        if self.is_stopped:
            return
        self._is_stopped = True
        self._server_task.cancel()
        self._server.close()
        await self._server.wait_closed()

        self.queue = None
        self._server = None
        self._server_task = None
        self._streams_by_socket = {}

    async def receive_messages(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ):
        """Receive incoming messages."""
        ip, socket, *_ = writer.get_extra_info("peername")
        peer_name = f"{ip}:{socket}"
        self._streams_by_socket[peer_name] = (reader, writer)
        self.logger.info(f"Connection @ {peer_name}")

        data = BytesIO()
        last_pos = 0

        while True:
            if last_pos == data.tell():
                data = BytesIO()
                last_pos = 0

            try:
                bits = await reader.read(MAX_READ_IN_BYTES)
            except CancelledError:
                self.logger.debug(f"Read task for peer {peer_name} cancelled.")
                return
            if len(bits) == 0:
                self.logger.error(f"Tendermint node {peer_name} closed connection.")
                # break to the _stop if the connection stops
                break

            self.logger.debug(f"Received {len(bits)} bytes from connection {peer_name}")
            data.write(bits)
            data.seek(last_pos)

            # Tendermint prefixes each serialized protobuf message
            # with varint encoded length. We use the 'data' buffer to
            # keep track of where we are in the byte stream and progress
            # based on the length encoding
            for message in _TendermintABCISerializer.read_messages(data, Request):
                req_type = message.WhichOneof("value")
                self.logger.debug(f"Received message of type: {req_type}")
                response = _TendermintProtocolDecoder.process(req_type, message)
                if response is not None:
                    envelope = Envelope(
                        to=self.connection_address, sender=peer_name, message=response
                    )
                    await self.queue.put(envelope)
                else:
                    self.logger.warning(f"Decoded request {req_type} was None.")
                last_pos = data.tell()

    async def get_message(self):
        """Get a message from the queue."""
        return await self.queue.get()

    async def send(self, envelope):
        """Send a message."""
        message = envelope.message
        to = envelope.to
        _reader, writer = self._streams_by_socket[to]
        protobuf_message = _TendermintProtocolEncoder.process(message)
        data = _TendermintABCISerializer.write_message(protobuf_message)
        self.logger.debug(f"Writing {len(data)} bytes")
        writer.write(data)


class BaseABCIConnection(Connection, ABC):
    """Base ABCI connection."""

    connection_id = PUBLIC_ID


class ABCIServerConnection(BaseABCIConnection):
    """ABCI server."""

    connection_id = PUBLIC_ID

    def __init__(self, **kwargs: Any) -> None:
        """
        Initialize the connection.

        :param kwargs: keyword arguments passed to component base
        """
        super().__init__(**kwargs)  # pragma: no cover
        self.host = cast(str, self.configuration.config.get("host"))
        self.port = cast(int, self.configuration.config.get("port"))
        if self.host is None or self.port is None:  # pragma: nocover
            raise ValueError("host and port must be set!")

        self.channel = TcpServerChannel(self.address, self.host, self.port)

    async def connect(self) -> None:
        """
        Set up the connection.

        In the implementation, remember to update 'connection_status' accordingly.
        """
        if self.is_connected:
            return

        self.state = ConnectionStates.connecting
        self.channel.logger = self.logger
        await self.channel.connect(loop=self.loop)
        if self.channel.is_stopped:
            self.state = ConnectionStates.disconnected
        else:
            self.state = ConnectionStates.connected

    async def disconnect(self) -> None:
        """
        Tear down the connection.

        In the implementation, remember to update 'connection_status' accordingly.
        """
        if self.is_disconnected:
            return

        self.state = ConnectionStates.disconnecting
        await self.channel.disconnect()
        self.state = ConnectionStates.disconnected

    async def send(self, envelope: Envelope) -> None:
        """
        Send an envelope.

        :param envelope: the envelope to send.
        """
        self._ensure_connected()
        await self.channel.send(envelope)

    async def receive(self, *args: Any, **kwargs: Any) -> Optional[Envelope]:
        """
        Receive an envelope. Blocking.

        :param args: arguments to receive
        :param kwargs: keyword arguments to receive
        :return: the envelope received, if present.  # noqa: DAR202
        """
        self._ensure_connected()
        try:
            return await self.channel.get_message()
        except CancelledError:  # pragma: no cover
            return None
