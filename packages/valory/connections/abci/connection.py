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
from asyncio import AbstractEventLoop, AbstractServer, CancelledError, Task
from io import BytesIO
from logging import Logger
from typing import Any, Dict, Optional, Tuple, Type, cast

from aea.configurations.base import PublicId
from aea.connections.base import Connection, ConnectionStates
from aea.mail.base import Envelope
from aea.protocols.dialogue.base import DialogueLabel

from packages.valory.connections.abci import PUBLIC_ID as CONNECTION_PUBLIC_ID
from packages.valory.connections.abci.dialogues import AbciDialogues
from packages.valory.connections.abci.tendermint.abci.types_pb2 import (  # type: ignore
    Request,
    Response,
)
from packages.valory.connections.abci.tendermint_decoder import (
    _TendermintProtocolDecoder,
)
from packages.valory.connections.abci.tendermint_encoder import (
    _TendermintProtocolEncoder,
)
from packages.valory.protocols.abci import AbciMessage


PUBLIC_ID = CONNECTION_PUBLIC_ID

DEFAULT_LISTEN_ADDRESS = "0.0.0.0"
DEFAULT_ABCI_PORT = 26658
MAX_READ_IN_BYTES = 64 * 1024  # Max we'll consume on a read stream


class _TendermintABCISerializer:
    """(stateless) utility class to encode/decode messages for the communication with Tendermint."""

    @classmethod
    def encode_varint(cls, number: int) -> bytes:
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
    def decode_varint(cls, buffer: BytesIO) -> int:
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
    def _read_one(cls, buffer: BytesIO) -> int:
        """Read one byte to decode a varint."""
        c = buffer.read(1)
        if c == b"":
            raise EOFError("Unexpected EOF while reading bytes")
        return ord(c)

    @classmethod
    def write_message(cls, message: Response) -> bytes:
        """Write a message in a buffer."""
        buffer = BytesIO(b"")
        bz = message.SerializeToString()
        encoded = cls.encode_varint(len(bz))
        buffer.write(encoded)
        buffer.write(bz)
        return buffer.getvalue()

    @classmethod
    def read_messages(cls, buffer: BytesIO, message: Type) -> Request:
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
        target_skill_id: PublicId,
        address: str = DEFAULT_LISTEN_ADDRESS,
        port: int = DEFAULT_ABCI_PORT,
        logger: Optional[Logger] = None,
    ):
        """
        Initialize the TCP server.

        :param connection_address: the connection identity address.
        :param target_skill_id: the public id of the target skill.
        :param address: the listen address.
        :param port: the port to listen from.
        :param logger: the logger.
        """
        self.connection_address = connection_address
        self.target_skill_id = target_skill_id
        self.address = address
        self.port = port
        self.logger = logger

        # channel state
        self._dialogues = AbciDialogues()
        self._is_stopped: bool = True
        self.queue: Optional[asyncio.Queue[Envelope]] = None
        self._server: Optional[AbstractServer] = None
        self._server_task: Optional[Task] = None
        # a single Tendermint opens four concurrent connections:
        # https://docs.tendermint.com/master/spec/abci/apps.html
        # this dictionary keeps track of the reader-writer stream pair
        # by socket name (ip address and port)
        self._streams_by_socket: Dict[
            str, Tuple[asyncio.StreamReader, asyncio.StreamWriter]
        ] = {}
        # this dictionary associates requests to socket name
        # such that responses are sent to the right receiver
        self._request_id_to_socket: Dict[DialogueLabel, str] = {}

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
        self._server = cast(AbstractServer, self._server)
        self._server.close()
        await self._server.wait_closed()

        self.queue = None
        self._server = None
        self._server_task = None
        self._streams_by_socket = {}
        self._request_id_to_socket = {}

    async def receive_messages(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        """Receive incoming messages."""
        self.logger = cast(Logger, self.logger)
        self.queue = cast(asyncio.Queue, self.queue)
        ip, socket, *_ = writer.get_extra_info("peername")
        peer_name = f"{ip}:{socket}"
        self._streams_by_socket[peer_name] = (reader, writer)
        self.logger.info(f"Connection @ {peer_name}")

        while not self.is_stopped:
            data = BytesIO()

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
            data.seek(0)

            # Tendermint prefixes each serialized protobuf message
            # with varint encoded length. We use the 'data' buffer to
            # keep track of where we are in the byte stream and progress
            # based on the length encoding
            for message in _TendermintABCISerializer.read_messages(data, Request):
                if self.is_stopped:
                    break
                req_type = message.WhichOneof("value")
                self.logger.debug(f"Received message of type: {req_type}")
                request, dialogue = _TendermintProtocolDecoder.process(
                    message, self._dialogues, str(self.target_skill_id)
                )
                # associate request to peer, so we remember who to reply to
                self._request_id_to_socket[
                    dialogue.incomplete_dialogue_label
                ] = peer_name
                if request is not None:
                    envelope = Envelope(
                        to=request.to, sender=request.sender, message=request
                    )
                    await self.queue.put(envelope)
                else:
                    self.logger.warning(f"Decoded request {req_type} was None.")

    async def get_message(self) -> Envelope:
        """Get a message from the queue."""
        return await cast(asyncio.Queue, self.queue).get()

    async def send(self, envelope: Envelope) -> None:
        """Send a message."""
        self.logger = cast(Logger, self.logger)
        message = cast(AbciMessage, envelope.message)
        dialogue = self._dialogues.update(message)
        if dialogue is None:
            self.logger.warning(
                "Could not create dialogue for message={}".format(message)
            )
            return

        peer_name = self._request_id_to_socket[dialogue.incomplete_dialogue_label]
        _reader, writer = self._streams_by_socket[peer_name]
        protobuf_message = _TendermintProtocolEncoder.process(message)
        data = _TendermintABCISerializer.write_message(protobuf_message)
        self.logger.debug(f"Writing {len(data)} bytes")
        writer.write(data)


class BaseABCIConnection(Connection, ABC):
    """Base ABCI connection."""

    connection_id = PUBLIC_ID


class ABCIServerConnection(BaseABCIConnection):
    """ABCI server."""

    def __init__(self, **kwargs: Any) -> None:
        """
        Initialize the connection.

        :param kwargs: keyword arguments passed to component base
        """
        super().__init__(**kwargs)  # pragma: no cover
        self.host = cast(str, self.configuration.config.get("host"))
        self.port = cast(int, self.configuration.config.get("port"))
        target_skill_id_string = cast(
            Optional[str], self.configuration.config.get("target_skill_id")
        )
        if (
            self.host is None or self.port is None or target_skill_id_string is None
        ):  # pragma: nocover
            raise ValueError("host and port and target_skill_id must be set!")
        target_skill_id = PublicId.try_from_str(target_skill_id_string)
        if target_skill_id is None:  # pragma: nocover
            raise ValueError("Provided target_skill_id is not a valid public id.")
        self.target_skill_id = target_skill_id
        self.channel = TcpServerChannel(
            self.address, self.target_skill_id, address=self.host, port=self.port
        )

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
