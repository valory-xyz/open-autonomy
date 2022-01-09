# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2022 Valory AG
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
import logging
import signal
import subprocess  # nosec
from asyncio import AbstractEventLoop, AbstractServer, CancelledError, Task
from io import BytesIO
from logging import Logger
from typing import Any, Dict, Generator, List, Optional, Tuple, Type, cast

from aea.configurations.base import PublicId
from aea.connections.base import Connection, ConnectionStates
from aea.mail.base import Envelope
from aea.protocols.dialogue.base import DialogueLabel
from google.protobuf.message import DecodeError

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

LOCALHOST = "127.0.0.1"
DEFAULT_ABCI_PORT = 26658
DEFAULT_P2P_PORT = 26656
DEFAULT_RPC_PORT = 26657
DEFAULT_LISTEN_ADDRESS = "0.0.0.0"  # nosec
DEFAULT_P2P_LISTEN_ADDRESS = f"tcp://{DEFAULT_LISTEN_ADDRESS}:{DEFAULT_P2P_PORT}"
DEFAULT_RPC_LISTEN_ADDRESS = f"tcp://{LOCALHOST}:{DEFAULT_RPC_PORT}"
MAX_READ_IN_BYTES = 64 * 1024  # Max we'll consume on a read stream


class DecodeVarintError(Exception):
    """This exception is raised when an error occurs while decoding a varint."""


class ShortBufferLengthError(Exception):
    """This exception is raised when the buffer length is shorter than expected."""


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
        """
        Decode a number from its varint coding.

        :param buffer: the buffer to read from.
        :return: the decoded int.

        :raise: DecodeVarintError if the varint could not be decoded.
        """
        shift = 0
        result = 0
        success = False
        byte = cls._read_one(buffer)
        while byte is not None:
            result |= (byte & 0x7F) << shift
            shift += 7
            if not byte & 0x80:
                success = True
                break
            byte = cls._read_one(buffer)
        if not success:
            raise DecodeVarintError("could not decode varint")
        return result >> 1

    @classmethod
    def _read_one(cls, buffer: BytesIO) -> Optional[int]:
        """
        Read one byte to decode a varint.

        :param buffer: the buffer to read from.
        :return: the next character, or None if EOF is reached.
        """
        character = buffer.read(1)
        if character == b"":
            return None
        return ord(character)

    @classmethod
    def write_message(cls, message: Response) -> bytes:
        """Write a message in a buffer."""
        buffer = BytesIO(b"")
        protobuf_bytes = message.SerializeToString()
        encoded = cls.encode_varint(len(protobuf_bytes))
        buffer.write(encoded)
        buffer.write(protobuf_bytes)
        return buffer.getvalue()

    @classmethod
    def read_messages(
        cls, buffer: BytesIO, message_cls: Type
    ) -> Generator[Request, None, None]:
        """
        Return an iterator over the messages found in the `reader` buffer.

        :param: buffer: the buffer to read messages from.
        :param: message_cls: the message class to instantiate.
        :yield: a new message.

        :raise: DecodeVarintError if the varint cannot be decoded correctly.
        :raise: ShortBufferLengthError if the buffer length is shorter than expected.
        :raise: google.protobuf.message.DecodeError if the Protobuf decoding fails.
        """
        total_length = buffer.getbuffer().nbytes
        while buffer.tell() < total_length:
            length = cls.decode_varint(buffer)
            data = buffer.read(length)
            if len(data) < length:
                raise ShortBufferLengthError(
                    f"expected buffer of length {length}, got {len(data)}"
                )
            message = message_cls()
            message.ParseFromString(data)
            yield message


class TcpServerChannel:  # pylint: disable=too-many-instance-attributes
    """TCP server channel to handle incoming communication from the Tendermint node."""

    def __init__(
        self,
        target_skill_id: PublicId,
        address: str,
        port: int,
        logger: Optional[Logger] = None,
    ):
        """
        Initialize the TCP server.

        :param target_skill_id: the public id of the target skill.
        :param address: the listen address.
        :param port: the port to listen from.
        :param logger: the logger.
        """
        self.target_skill_id = target_skill_id
        self.address = address
        self.port = port
        self.logger = logger or logging.getLogger()

        # channel state
        self._loop: Optional[AbstractEventLoop] = None
        self._dialogues = AbciDialogues()
        self._is_stopped: bool = True
        self.queue: Optional[asyncio.Queue] = None
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
        if not self._is_stopped:  # pragma: nocover
            return
        self._loop = loop
        self._is_stopped = False
        self.queue = asyncio.Queue()
        self._server = await asyncio.start_server(
            self.receive_messages, host=self.address, port=self.port, loop=self._loop
        )

    async def disconnect(self) -> None:
        """Disconnect the channel"""
        if self.is_stopped:  # pragma: nocover
            return
        self._is_stopped = True
        self._server = cast(AbstractServer, self._server)
        self._server.close()
        await self._server.wait_closed()

        self.queue = None
        self._server = None
        self._streams_by_socket = {}
        self._request_id_to_socket = {}

    async def receive_messages(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        """Receive incoming messages."""
        self.logger = cast(Logger, self.logger)
        self.queue = cast(asyncio.Queue, self.queue)
        ip_address, socket, *_ = writer.get_extra_info("peername")
        peer_name = f"{ip_address}:{socket}"
        self._streams_by_socket[peer_name] = (reader, writer)
        self.logger.debug(f"Connection with Tendermint @ {peer_name}")

        while not self.is_stopped:
            data = BytesIO()

            try:
                bits = await reader.read(MAX_READ_IN_BYTES)
            except CancelledError:  # pragma: nocover
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
            message_iterator: Generator[
                Request, None, None
            ] = _TendermintABCISerializer.read_messages(data, Request)
            end_of_message_iterator = False
            sentinel = object()
            while not self.is_stopped:
                try:
                    message = next(message_iterator, sentinel)
                except (
                    DecodeVarintError,
                    ShortBufferLengthError,
                    DecodeError,
                ) as e:  # pragma: nocover
                    self.logger.error(
                        f"an error occurred while reading a message: "
                        f"{type(e).__name__}: {e}. "
                        f"The message will be ignored."
                    )
                    continue

                if message == sentinel:
                    # we reached the end of the iterator
                    end_of_message_iterator = True
                    break
                await self._handle_message(message, peer_name)

            # check whether we exited the loop because of the end of the iterator
            # or because the reading loop has been stopped prematurely
            if not end_of_message_iterator:
                self.logger.warning(
                    "prematurely interrupting the message reading loop; "
                    "there may be some unread messages that will be lost"
                )

    async def _handle_message(self, message: Request, peer_name: str) -> None:
        """Handle a single message from a peer."""
        req_type = message.WhichOneof("value")
        self.logger.debug(f"Received message of type: {req_type}")
        result = _TendermintProtocolDecoder.process(
            message, self._dialogues, str(self.target_skill_id)
        )
        if result is not None:
            request, dialogue = result
            # associate request to peer, so we remember who to reply to
            self._request_id_to_socket[dialogue.incomplete_dialogue_label] = peer_name
            envelope = Envelope(to=request.to, sender=request.sender, message=request)
            await cast(asyncio.Queue, self.queue).put(envelope)
        else:  # pragma: nocover
            self.logger.warning(f"Decoded request {req_type} was not a match.")

    async def get_message(self) -> Envelope:
        """Get a message from the queue."""
        return await cast(asyncio.Queue, self.queue).get()

    async def send(self, envelope: Envelope) -> None:
        """Send a message."""
        self.logger = cast(Logger, self.logger)
        message = cast(AbciMessage, envelope.message)
        dialogue = self._dialogues.update(message)
        if dialogue is None:  # pragma: nocover
            self.logger.warning(f"Could not create dialogue for message={message}")
            return

        peer_name = self._request_id_to_socket[dialogue.incomplete_dialogue_label]
        _reader, writer = self._streams_by_socket[peer_name]
        protobuf_message = _TendermintProtocolEncoder.process(message)
        data = _TendermintABCISerializer.write_message(protobuf_message)
        self.logger.debug(f"Writing {len(data)} bytes")
        writer.write(data)


class TendermintParams:  # pylint: disable=too-few-public-methods
    """Tendermint node parameters."""

    def __init__(  # pylint: disable=too-many-arguments
        self,
        proxy_app: str,
        rpc_laddr: str,
        p2p_laddr: str,
        p2p_seeds: List[str],
        consensus_create_empty_blocks: bool,
        home: Optional[str] = None,
    ):
        """
        Initialize the parameters to the Tendermint node.

        :param proxy_app: ABCI address.
        :param rpc_laddr: RPC address.
        :param p2p_laddr: P2P address.
        :param p2p_seeds: P2P seeds.
        :param consensus_create_empty_blocks: if true, Tendermint node creates empty blocks.
        :param home: Tendermint's home directory.
        """
        self.proxy_app = proxy_app
        self.rpc_laddr = rpc_laddr
        self.p2p_laddr = p2p_laddr
        self.p2p_seeds = p2p_seeds
        self.consensus_create_empty_blocks = consensus_create_empty_blocks
        self.home = home

    def __str__(self) -> str:
        """Get the string representation."""
        return (
            f"{self.__class__.__name__}("
            f"    proxy_app={self.proxy_app},\n"
            f"    rpc_laddr={self.rpc_laddr},\n"
            f"    p2p_laddr={self.p2p_laddr},\n"
            f"    p2p_seeds={self.p2p_seeds},\n"
            f"    consensus_create_empty_blocks={self.consensus_create_empty_blocks},\n"
            f"    home={self.home},\n"
            ")"
        )


class TendermintNode:
    """A class to manage a Tendermint node."""

    def __init__(self, params: TendermintParams, logger: Optional[Logger] = None):
        """
        Initialize a Tendermint node.

        :param params: the parameters.
        :param logger: the logger.
        """
        self.params = params
        self.logger = logger or logging.getLogger()

        self._process: Optional[subprocess.Popen] = None

    def _build_init_command(self) -> List[str]:
        """Build the 'init' command."""
        cmd = [
            "tendermint",
            "init",
        ]
        if self.params.home is not None:  # pragma: nocover
            cmd += ["--home", self.params.home]
        return cmd

    def _build_node_command(self) -> List[str]:
        """Build the 'node' command."""
        cmd = [
            "tendermint",
            "node",
            f"--proxy_app={self.params.proxy_app}",
            f"--rpc.laddr={self.params.rpc_laddr}",
            f"--p2p.laddr={self.params.p2p_laddr}",
            f"--p2p.seeds={','.join(self.params.p2p_seeds)}",
            f"--consensus.create_empty_blocks={str(self.params.consensus_create_empty_blocks).lower()}",
        ]
        if self.params.home is not None:  # pragma: nocover
            cmd += ["--home", self.params.home]
        return cmd

    def init(self) -> None:
        """Initialize Tendermint node."""
        cmd = self._build_init_command()
        subprocess.call(cmd)  # nosec

    def start(self) -> None:
        """Start a Tendermint node process."""
        if self._process is not None:  # pragma: nocover
            return
        cmd = self._build_node_command()
        self._process = subprocess.Popen(  # nosec # pylint: disable=consider-using-with
            cmd
        )

    def stop(self) -> None:
        """Stop a Tendermint node process."""
        if self._process is None:  # pragma: nocover
            return
        self._process.send_signal(signal.SIGTERM)
        self._process.wait(timeout=30)
        poll = self._process.poll()
        if poll is None:  # pragma: nocover
            self._process.terminate()
            self._process.wait(2)
        self._process = None


class ABCIServerConnection(Connection):  # pylint: disable=too-many-instance-attributes
    """ABCI server."""

    connection_id = PUBLIC_ID
    params: Optional[TendermintParams] = None
    node: Optional[TendermintNode] = None

    def __init__(self, **kwargs: Any) -> None:
        """
        Initialize the connection.

        :param kwargs: keyword arguments passed to component base
        """
        super().__init__(**kwargs)  # pragma: no cover

        self._process_connection_params()
        self._process_tendermint_params()

    def _process_connection_params(self) -> None:
        """
        Process the connection parameters.

        The parameters to process are:
        - host
        - port
        - target_skill_id
        """
        self.host = cast(str, self.configuration.config.get("host"))
        self.port = cast(int, self.configuration.config.get("port"))
        target_skill_id_string = cast(
            Optional[str], self.configuration.config.get("target_skill_id")
        )

        if (
            self.host is None or self.port is None or target_skill_id_string is None
        ):  # pragma: no cover
            raise ValueError("host and port and target_skill_id must be set!")
        target_skill_id = PublicId.try_from_str(target_skill_id_string)
        if target_skill_id is None:  # pragma: no cover
            raise ValueError("Provided target_skill_id is not a valid public id.")
        self.target_skill_id = target_skill_id

        self.channel = TcpServerChannel(
            self.target_skill_id, address=self.host, port=self.port, logger=self.logger
        )

    def _process_tendermint_params(self) -> None:
        """
        Process the Tendermint parameters.

        In particular, if use_tendermint is False, do nothing.
        Else, process the following parameters:
        - rpc_laddr: the listening address for RPC communication
        - p2p_laddr: the listening address for P2P communication
        - p2p_seeds: a comma-separated list of IP addresses and ports
        """
        self.use_tendermint = cast(
            bool, self.configuration.config.get("use_tendermint")
        )
        if not self.use_tendermint:
            return
        tendermint_config = self.configuration.config.get("tendermint_config", {})
        rpc_laddr = cast(str, tendermint_config.get("rpc_laddr", DEFAULT_RPC_PORT))
        p2p_laddr = cast(
            str, tendermint_config.get("p2p_laddr", DEFAULT_P2P_LISTEN_ADDRESS)
        )
        p2p_seeds = cast(List[str], tendermint_config.get("p2p_seeds", []))
        home = cast(Optional[str], tendermint_config.get("home", None))
        consensus_create_empty_blocks = cast(
            bool, tendermint_config.get("consensus_create_empty_blocks", True)
        )
        proxy_app = f"tcp://{self.host}:{self.port}"
        self.params = TendermintParams(
            proxy_app,
            rpc_laddr,
            p2p_laddr,
            p2p_seeds,
            consensus_create_empty_blocks,
            home,
        )
        self.logger.debug(f"Tendermint parameters: {self.params}")
        self.node = TendermintNode(self.params, self.logger)

    async def connect(self) -> None:
        """
        Set up the connection.

        In the implementation, remember to update 'connection_status' accordingly.
        """
        if self.is_connected:  # pragma: no cover
            return

        self.state = ConnectionStates.connecting
        if self.use_tendermint:
            self.node = cast(TendermintNode, self.node)
            self.node.init()
            self.node.start()
        self.channel.logger = self.logger
        await self.channel.connect(loop=self.loop)
        if self.channel.is_stopped:  # pragma: no cover
            self.state = ConnectionStates.disconnected
            return
        self.state = ConnectionStates.connected

    async def disconnect(self) -> None:
        """
        Tear down the connection.

        In the implementation, remember to update 'connection_status' accordingly.
        """
        if self.is_disconnected:  # pragma: no cover
            return

        self.state = ConnectionStates.disconnecting
        await self.channel.disconnect()
        if self.use_tendermint:
            self.node = cast(TendermintNode, self.node)
            self.node.stop()
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
