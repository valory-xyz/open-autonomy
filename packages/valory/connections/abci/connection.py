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
import json
import logging
import os
import platform
import signal
import subprocess  # nosec
from asyncio import AbstractEventLoop, AbstractServer, CancelledError, Task
from io import BytesIO
from logging import Logger
from pathlib import Path
from threading import Event, Thread
from typing import Any, Dict, List, Optional, Tuple, Union, cast

import grpc  # type: ignore
from aea.configurations.base import PublicId
from aea.connections.base import Connection, ConnectionStates
from aea.exceptions import enforce
from aea.mail.base import Envelope
from aea.protocols.dialogue.base import DialogueLabel
from google.protobuf.message import DecodeError

from packages.valory.connections.abci import PUBLIC_ID as CONNECTION_PUBLIC_ID
from packages.valory.connections.abci.dialogues import AbciDialogues
from packages.valory.connections.abci.tendermint.abci import (  # type: ignore
    types_pb2_grpc,
)
from packages.valory.connections.abci.tendermint.abci.types_pb2 import (  # type: ignore
    Request,
    RequestApplySnapshotChunk,
    RequestBeginBlock,
    RequestCheckTx,
    RequestCommit,
    RequestDeliverTx,
    RequestEcho,
    RequestEndBlock,
    RequestFlush,
    RequestInfo,
    RequestInitChain,
    RequestListSnapshots,
    RequestLoadSnapshotChunk,
    RequestOfferSnapshot,
    RequestQuery,
    RequestSetOption,
    Response,
    ResponseApplySnapshotChunk,
    ResponseBeginBlock,
    ResponseCheckTx,
    ResponseCommit,
    ResponseDeliverTx,
    ResponseEcho,
    ResponseEndBlock,
    ResponseFlush,
    ResponseInfo,
    ResponseInitChain,
    ResponseListSnapshots,
    ResponseLoadSnapshotChunk,
    ResponseOfferSnapshot,
    ResponseQuery,
    ResponseSetOption,
)
from packages.valory.connections.abci.tendermint_decoder import (
    _TendermintProtocolDecoder,
)
from packages.valory.connections.abci.tendermint_encoder import (
    _TendermintProtocolEncoder,
)
from packages.valory.protocols.abci import AbciMessage


PUBLIC_ID = CONNECTION_PUBLIC_ID

ENCODING = "utf-8"
LOCALHOST = "127.0.0.1"
DEFAULT_ABCI_PORT = 26658
DEFAULT_P2P_PORT = 26656
DEFAULT_RPC_PORT = 26657
DEFAULT_LISTEN_ADDRESS = "0.0.0.0"  # nosec
DEFAULT_P2P_LISTEN_ADDRESS = f"tcp://{DEFAULT_LISTEN_ADDRESS}:{DEFAULT_P2P_PORT}"
DEFAULT_RPC_LISTEN_ADDRESS = f"tcp://{LOCALHOST}:{DEFAULT_RPC_PORT}"
MAX_READ_IN_BYTES = 2 ** 20  # Max we'll consume on a read stream (1 MiB)
MAX_VARINT_BYTES = 10  # Max size of varint we support
DEFAULT_TENDERMINT_LOG_FILE = "tendermint.log"


class DecodeVarintError(Exception):
    """This exception is raised when an error occurs while decoding a varint."""


class EncodeVarintError(Exception):
    """This exception is raised when an error occurs while encoding a varint."""


class TooLargeVarint(Exception):
    """This exception is raised when a message with varint exceeding the max size is received."""

    def __init__(self, received_size: int, max_size: int = MAX_READ_IN_BYTES):
        """
        Initialize the exception object.

        :param received_size: the received size.
        :param max_size: the maximum amount the connection supports.
        """
        super().__init__(
            f"The max message size is {max_size}, received message with varint {received_size}."
        )
        self.received_size = received_size
        self.max_size = max_size


class ShortBufferLengthError(Exception):
    """This exception is raised when the buffer length is shorter than expected."""

    def __init__(self, expected_length: int, data: bytes):
        """
        Initialize the exception object.

        :param expected_length: the expected length to be read
        :param data: the data actually read
        """
        super().__init__(
            f"expected bytes of length {expected_length}, got bytes of length {len(data)}"
        )
        self.expected_length = expected_length
        self.data = data


class _TendermintABCISerializer:
    """(stateless) utility class to encode/decode messages for the communication with Tendermint."""

    @classmethod
    def encode_varint(cls, number: int) -> bytes:
        """Encode a number in varint coding."""

        if not 0 <= number < 1 << 64:
            log_msg = "Expecting uint64 from Protobuf"
            raise EncodeVarintError(f"{log_msg}: {number}")

        number <<= 1  # Shift to int64
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
    async def decode_varint(
        cls, buffer: asyncio.StreamReader, max_length: int = MAX_VARINT_BYTES
    ) -> int:
        """
        Decode a number from its varint coding.

        :param buffer: the buffer to read from.
        :param max_length: the max number of bytes that can be read.
        :return: the decoded int.

        :raise: DecodeVarintError if the varint could not be decoded.
        :raise: EOFError if EOF byte is read and the process of decoding a varint has not started.
        """
        enforce(max_length >= 1, "max bytes must be at least one")
        nb_read_bytes = 0
        shift = 0
        result = 0
        success = False
        byte = await cls._read_one(buffer)
        while byte is not None and nb_read_bytes <= max_length:
            nb_read_bytes += 1
            result |= (byte & 0x7F) << shift
            shift += 7
            if not byte & 0x80:
                success = True
                break
            byte = await cls._read_one(buffer)
        # byte is None when EOF is reached
        if byte is None and nb_read_bytes == 0:
            raise EOFError()
        if not success:
            raise DecodeVarintError("could not decode varint")
        return result >> 1

    @classmethod
    async def _read_one(cls, buffer: asyncio.StreamReader) -> Optional[int]:
        """
        Read one byte to decode a varint.

        :param buffer: the buffer to read from.
        :return: the next character, or None if EOF is reached.
        """
        character = await buffer.read(1)
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


class VarintMessageReader:  # pylint: disable=too-few-public-methods
    """Varint message reader."""

    def __init__(self, reader: asyncio.StreamReader) -> None:
        """Initialize the reader."""
        self._reader = reader

    async def read_next_message(self) -> bytes:
        """Read next message."""
        varint = await _TendermintABCISerializer.decode_varint(self._reader)
        if varint > MAX_READ_IN_BYTES:
            raise TooLargeVarint(received_size=varint, max_size=MAX_READ_IN_BYTES)
        message_bytes = await self.read_until(varint)
        if len(message_bytes) < varint:
            raise ShortBufferLengthError(varint, message_bytes)
        return message_bytes

    async def read_until(self, n: int) -> bytes:
        """Wait until n bytes are read from the stream."""
        result = BytesIO(b"")
        read_bytes = 0
        while read_bytes < n:
            data = await self._reader.read(n - read_bytes)
            result.write(data)
            read_bytes += len(data)
        return result.getvalue()


class ABCIApplicationServicer(types_pb2_grpc.ABCIApplicationServicer):
    """Implements the gRPC servicer (handler)"""

    # pylint: disable=invalid-overridden-method, no-member

    def __init__(
        self, request_queue: asyncio.Queue, dialogues: AbciDialogues, target_skill: str
    ):
        """
        Initializes the abci handler.

        :param request_queue: queue holding translated abci messages.
        :param dialogues: dialogues
        :param target_skill: target skill of messages
        """
        super().__init__()
        self._request_queue = request_queue
        self._dialogues = dialogues
        self._target_skill = target_skill
        self._response_queues: Dict[str, asyncio.Queue] = {
            AbciMessage.Performative.RESPONSE_ECHO: asyncio.Queue(),
            AbciMessage.Performative.RESPONSE_FLUSH: asyncio.Queue(),
            AbciMessage.Performative.RESPONSE_INFO: asyncio.Queue(),
            AbciMessage.Performative.RESPONSE_SET_OPTION: asyncio.Queue(),
            AbciMessage.Performative.RESPONSE_DELIVER_TX: asyncio.Queue(),
            AbciMessage.Performative.RESPONSE_CHECK_TX: asyncio.Queue(),
            AbciMessage.Performative.RESPONSE_QUERY: asyncio.Queue(),
            AbciMessage.Performative.RESPONSE_COMMIT: asyncio.Queue(),
            AbciMessage.Performative.RESPONSE_INIT_CHAIN: asyncio.Queue(),
            AbciMessage.Performative.RESPONSE_BEGIN_BLOCK: asyncio.Queue(),
            AbciMessage.Performative.RESPONSE_END_BLOCK: asyncio.Queue(),
            AbciMessage.Performative.RESPONSE_LIST_SNAPSHOTS: asyncio.Queue(),
            AbciMessage.Performative.RESPONSE_OFFER_SNAPSHOT: asyncio.Queue(),
            AbciMessage.Performative.RESPONSE_APPLY_SNAPSHOT_CHUNK: asyncio.Queue(),
            AbciMessage.Performative.RESPONSE_LOAD_SNAPSHOT_CHUNK: asyncio.Queue(),
        }

    async def send(self, envelope: Envelope) -> Response:
        """
        Returns response to the waiting request

        :param: envelope: Envelope to be returned
        """
        message = cast(AbciMessage, envelope.message)
        dialogue = self._dialogues.update(message)
        if dialogue is None:
            return

        await self._response_queues[message.performative].put(envelope)

    async def Echo(
        self, request: RequestEcho, context: grpc.ServicerContext
    ) -> ResponseEcho:
        """
        Handles "Echo" gRPC requests

        :param: request: The request from the Tendermint node
        :param: context: The request context
        :return: the Echo response
        """
        packed_req = Request(echo=request)
        message, _ = _TendermintProtocolDecoder.request_echo(
            packed_req, self._dialogues, self._target_skill
        )
        envelope = Envelope(to=message.to, sender=message.sender, message=message)

        await self._request_queue.put(envelope)
        message = cast(
            AbciMessage,
            (
                await self._response_queues[
                    AbciMessage.Performative.RESPONSE_ECHO
                ].get()
            ).message,
        )

        response = _TendermintProtocolEncoder.response_echo(message)
        context.set_code(grpc.StatusCode.OK)

        return response.echo

    async def Flush(
        self, request: RequestFlush, context: grpc.ServicerContext
    ) -> ResponseFlush:
        """
        Handles "Flush" gRPC requests

        :param: request: The request from the Tendermint node
        :param: context: The request context
        :return: the Echo response
        """
        packed_req = Request(flush=request)
        message, _ = _TendermintProtocolDecoder.request_flush(
            packed_req, self._dialogues, self._target_skill
        )
        envelope = Envelope(to=message.to, sender=message.sender, message=message)

        await self._request_queue.put(envelope)
        message = cast(
            AbciMessage,
            (
                await self._response_queues[
                    AbciMessage.Performative.RESPONSE_FLUSH
                ].get()
            ).message,
        )

        response = _TendermintProtocolEncoder.response_flush(message)
        context.set_code(grpc.StatusCode.OK)

        return response.flush

    async def Info(
        self, request: RequestInfo, context: grpc.ServicerContext
    ) -> ResponseInfo:
        """
        Handles "Info" gRPC requests

        :param: request: The request from the Tendermint node
        :param: context: The request context
        :return: the Echo response
        """
        packed_req = Request(info=request)
        message, _ = _TendermintProtocolDecoder.request_info(
            packed_req, self._dialogues, self._target_skill
        )
        envelope = Envelope(to=message.to, sender=message.sender, message=message)

        await self._request_queue.put(envelope)
        message = cast(
            AbciMessage,
            (
                await self._response_queues[
                    AbciMessage.Performative.RESPONSE_INFO
                ].get()
            ).message,
        )

        response = _TendermintProtocolEncoder.response_info(message)
        context.set_code(grpc.StatusCode.OK)

        return response.info

    async def SetOption(
        self, request: RequestSetOption, context: grpc.ServicerContext
    ) -> ResponseSetOption:
        """
        Handles "SetOption" gRPC requests

        :param: request: The request from the Tendermint node
        :param: context: The request context
        :return: the Echo response
        """
        packed_req = Request(set_option=request)
        message, _ = _TendermintProtocolDecoder.request_set_option(
            packed_req, self._dialogues, self._target_skill
        )
        envelope = Envelope(to=message.to, sender=message.sender, message=message)

        await self._request_queue.put(envelope)
        message = cast(
            AbciMessage,
            (
                await self._response_queues[
                    AbciMessage.Performative.RESPONSE_SET_OPTION
                ].get()
            ).message,
        )

        response = _TendermintProtocolEncoder.response_set_option(message)
        context.set_code(grpc.StatusCode.OK)

        return response.set_option

    async def DeliverTx(
        self, request: RequestDeliverTx, context: grpc.ServicerContext
    ) -> ResponseDeliverTx:
        """
        Handles "DeliverTx" gRPC requests

        :param: request: The request from the Tendermint node
        :param: context: The request context
        :return: the Echo response
        """
        packed_req = Request(deliver_tx=request)
        message, _ = _TendermintProtocolDecoder.request_deliver_tx(
            packed_req, self._dialogues, self._target_skill
        )
        envelope = Envelope(to=message.to, sender=message.sender, message=message)

        await self._request_queue.put(envelope)
        message = cast(
            AbciMessage,
            (
                await self._response_queues[
                    AbciMessage.Performative.RESPONSE_DELIVER_TX
                ].get()
            ).message,
        )

        response = _TendermintProtocolEncoder.response_deliver_tx(message)
        context.set_code(grpc.StatusCode.OK)

        return response.deliver_tx

    async def CheckTx(
        self, request: RequestCheckTx, context: grpc.ServicerContext
    ) -> ResponseCheckTx:
        """
        Handles "CheckTx" gRPC requests

        :param: request: The request from the Tendermint node
        :param: context: The request context
        :return: the Echo response
        """
        packed_req = Request(check_tx=request)
        message, _ = _TendermintProtocolDecoder.request_check_tx(
            packed_req, self._dialogues, self._target_skill
        )
        envelope = Envelope(to=message.to, sender=message.sender, message=message)

        await self._request_queue.put(envelope)
        message = cast(
            AbciMessage,
            (
                await self._response_queues[
                    AbciMessage.Performative.RESPONSE_CHECK_TX
                ].get()
            ).message,
        )

        response = _TendermintProtocolEncoder.response_check_tx(message)
        context.set_code(grpc.StatusCode.OK)

        return response.check_tx

    async def Query(
        self, request: RequestQuery, context: grpc.ServicerContext
    ) -> ResponseQuery:
        """
        Handles "Query" gRPC requests

        :param: request: The request from the Tendermint node
        :param: context: The request context
        :return: the Echo response
        """
        packed_req = Request(query=request)
        message, _ = _TendermintProtocolDecoder.request_query(
            packed_req, self._dialogues, self._target_skill
        )
        envelope = Envelope(to=message.to, sender=message.sender, message=message)

        await self._request_queue.put(envelope)
        message = cast(
            AbciMessage,
            (
                await self._response_queues[
                    AbciMessage.Performative.RESPONSE_QUERY
                ].get()
            ).message,
        )

        response = _TendermintProtocolEncoder.response_query(message)
        context.set_code(grpc.StatusCode.OK)

        return response.query

    async def Commit(
        self, request: RequestCommit, context: grpc.ServicerContext
    ) -> ResponseCommit:
        """
        Handles "Commit" gRPC requests

        :param: request: The request from the Tendermint node
        :param: context: The request context
        :return: the Echo response
        """
        packed_req = Request(commit=request)
        message, _ = _TendermintProtocolDecoder.request_commit(
            packed_req, self._dialogues, self._target_skill
        )
        envelope = Envelope(to=message.to, sender=message.sender, message=message)

        await self._request_queue.put(envelope)
        message = cast(
            AbciMessage,
            (
                await self._response_queues[
                    AbciMessage.Performative.RESPONSE_COMMIT
                ].get()
            ).message,
        )

        response = _TendermintProtocolEncoder.response_commit(message)
        context.set_code(grpc.StatusCode.OK)

        return response.commit

    async def InitChain(
        self, request: RequestInitChain, context: grpc.ServicerContext
    ) -> ResponseInitChain:
        """
        Handles "InitChain" gRPC requests

        :param: request: The request from the Tendermint node
        :param: context: The request context
        :return: the Echo response
        """
        packed_req = Request(init_chain=request)
        message, _ = _TendermintProtocolDecoder.request_init_chain(
            packed_req, self._dialogues, self._target_skill
        )
        envelope = Envelope(to=message.to, sender=message.sender, message=message)

        await self._request_queue.put(envelope)
        message = cast(
            AbciMessage,
            (
                await self._response_queues[
                    AbciMessage.Performative.RESPONSE_INIT_CHAIN
                ].get()
            ).message,
        )

        response = _TendermintProtocolEncoder.response_init_chain(message)
        context.set_code(grpc.StatusCode.OK)

        return response.init_chain

    async def BeginBlock(
        self, request: RequestBeginBlock, context: grpc.ServicerContext
    ) -> ResponseBeginBlock:
        """
        Handles "BeginBlock" gRPC requests

        :param: request: The request from the Tendermint node
        :param: context: The request context
        :return: the Echo response
        """
        packed_req = Request(begin_block=request)
        message, _ = _TendermintProtocolDecoder.request_begin_block(
            packed_req, self._dialogues, self._target_skill
        )
        envelope = Envelope(to=message.to, sender=message.sender, message=message)

        await self._request_queue.put(envelope)
        message = cast(
            AbciMessage,
            (
                await self._response_queues[
                    AbciMessage.Performative.RESPONSE_BEGIN_BLOCK
                ].get()
            ).message,
        )

        response = _TendermintProtocolEncoder.response_begin_block(message)
        context.set_code(grpc.StatusCode.OK)

        return response.begin_block

    async def EndBlock(
        self, request: RequestEndBlock, context: grpc.ServicerContext
    ) -> ResponseEndBlock:
        """
        Handles "EndBlock" gRPC requests

        :param: request: The request from the Tendermint node
        :param: context: The request context
        :return: the Echo response
        """
        packed_req = Request(end_block=request)
        message, _ = _TendermintProtocolDecoder.request_end_block(
            packed_req, self._dialogues, self._target_skill
        )
        envelope = Envelope(to=message.to, sender=message.sender, message=message)

        await self._request_queue.put(envelope)
        message = cast(
            AbciMessage,
            (
                await self._response_queues[
                    AbciMessage.Performative.RESPONSE_END_BLOCK
                ].get()
            ).message,
        )

        response = _TendermintProtocolEncoder.response_end_block(message)
        context.set_code(grpc.StatusCode.OK)

        return response.end_block

    async def ListSnapshots(
        self, request: RequestListSnapshots, context: grpc.ServicerContext
    ) -> ResponseListSnapshots:
        """
        Handles "ListSnapshots" gRPC requests

        :param: request: The request from the Tendermint node
        :param: context: The request context
        :return: the Echo response
        """
        packed_req = Request(list_snapshots=request)
        message, _ = _TendermintProtocolDecoder.request_list_snapshots(
            packed_req, self._dialogues, self._target_skill
        )
        envelope = Envelope(to=message.to, sender=message.sender, message=message)

        await self._request_queue.put(envelope)
        message = cast(
            AbciMessage,
            (
                await self._response_queues[
                    AbciMessage.Performative.RESPONSE_LIST_SNAPSHOTS
                ].get()
            ).message,
        )

        response = _TendermintProtocolEncoder.response_list_snapshots(message)
        context.set_code(grpc.StatusCode.OK)

        return response.list_snapshots

    async def OfferSnapshot(
        self, request: RequestOfferSnapshot, context: grpc.ServicerContext
    ) -> ResponseOfferSnapshot:
        """
        Handles "OfferSnapshot" gRPC requests

        :param: request: The request from the Tendermint node
        :param: context: The request context
        :return: the Echo response
        """
        packed_req = Request(offer_snapshot=request)
        message, _ = _TendermintProtocolDecoder.request_offer_snapshot(
            packed_req, self._dialogues, self._target_skill
        )
        envelope = Envelope(to=message.to, sender=message.sender, message=message)

        await self._request_queue.put(envelope)
        message = cast(
            AbciMessage,
            (
                await self._response_queues[
                    AbciMessage.Performative.RESPONSE_OFFER_SNAPSHOT
                ].get()
            ).message,
        )

        response = _TendermintProtocolEncoder.response_offer_snapshot(message)
        context.set_code(grpc.StatusCode.OK)

        return response.list_snapshots

    async def LoadSnapshotChunk(
        self, request: RequestLoadSnapshotChunk, context: grpc.ServicerContext
    ) -> ResponseLoadSnapshotChunk:
        """
        Handles "LoadSnapshotChunk" gRPC requests

        :param: request: The request from the Tendermint node
        :param: context: The request context
        :return: the Echo response
        """
        packed_req = Request(load_snapshot_chunk=request)
        message, _ = _TendermintProtocolDecoder.request_load_snapshot_chunk(
            packed_req, self._dialogues, self._target_skill
        )
        envelope = Envelope(to=message.to, sender=message.sender, message=message)

        await self._request_queue.put(envelope)
        message = cast(
            AbciMessage,
            (
                await self._response_queues[
                    AbciMessage.Performative.RESPONSE_LOAD_SNAPSHOT_CHUNK
                ].get()
            ).message,
        )

        response = _TendermintProtocolEncoder.response_load_snapshot_chunk(message)
        context.set_code(grpc.StatusCode.OK)

        return response.load_snapshot_chunk

    async def ApplySnapshotChunk(
        self, request: RequestApplySnapshotChunk, context: grpc.ServicerContext
    ) -> ResponseApplySnapshotChunk:
        """
        Handles "ApplySnapshotChunk" gRPC requests

        :param: request: The request from the Tendermint node
        :param: context: The request context
        :return: the Echo response
        """
        packed_req = Request(apply_snapshot_chunk=request)
        message, _ = _TendermintProtocolDecoder.request_apply_snapshot_chunk(
            packed_req, self._dialogues, self._target_skill
        )
        envelope = Envelope(to=message.to, sender=message.sender, message=message)

        await self._request_queue.put(envelope)
        message = cast(
            AbciMessage,
            (
                await self._response_queues[
                    AbciMessage.Performative.RESPONSE_APPLY_SNAPSHOT_CHUNK
                ].get()
            ).message,
        )

        response = _TendermintProtocolEncoder.response_apply_snapshot_chunk(message)
        context.set_code(grpc.StatusCode.OK)

        return response.apply_snapshot_chunk


class GrpcServerChannel:  # pylint: disable=too-many-instance-attributes
    """gRPC server channel to handle incoming communication from the Tendermint node."""

    def __init__(
        self,
        target_skill_id: PublicId,
        address: str,
        port: int,
        logger: Optional[Logger] = None,
    ):
        """
        Initialize the gRPC server.

        :param target_skill_id: the public id of the target skill.
        :param address: the listen address.
        :param port: the port to listen from.
        :param logger: the logger.
        """
        self.target_skill_id = target_skill_id
        self.address = address
        self.port = port
        self.logger = logger

        # channel state
        self._loop: Optional[AbstractEventLoop] = None
        self._dialogues = AbciDialogues()
        self._is_stopped: bool = True
        self.queue: Optional[asyncio.Queue] = None
        self._server: Optional[grpc.Server] = None
        self._server_task: Optional[Task] = None
        self._servicer: Optional[ABCIApplicationServicer] = None

    @property
    def is_stopped(self) -> bool:
        """Check that the channel is stopped."""
        return self._is_stopped

    async def _start_server(self) -> None:
        """Start the gRPC server."""
        self.logger = cast(Logger, self.logger)
        self.queue = cast(asyncio.Queue, self.queue)
        self.logger.info("Starting gRPC server")
        server = grpc.aio.server()
        self._servicer = ABCIApplicationServicer(
            self.queue, self._dialogues, str(self.target_skill_id)
        )
        types_pb2_grpc.add_ABCIApplicationServicer_to_server(self._servicer, server)
        server.add_insecure_port(f"[::]:{self.port}")
        self._server = server
        await self._server.start()
        await self._server.wait_for_termination()

    async def connect(self, loop: AbstractEventLoop) -> None:
        """
        Connect.

        :param loop: asyncio event loop
        """
        if not self._is_stopped:  # pragma: nocover
            return
        self._loop = loop
        self._is_stopped = False
        self.queue = asyncio.Queue()

        asyncio.create_task(self._start_server())

    async def disconnect(self) -> None:
        """Disconnect the channel"""
        if self.is_stopped:  # pragma: nocover
            return
        self._is_stopped = True
        self._server = cast(grpc.Server, self._server)
        await self._server.stop(0)

        self.queue = None
        self._server = None

    async def get_message(self) -> Envelope:
        """Get a message from the queue."""
        return await cast(asyncio.Queue, self.queue).get()

    async def send(self, envelope: Envelope) -> None:
        """Send a message."""
        self._servicer = cast(ABCIApplicationServicer, self._servicer)
        await self._servicer.send(envelope)


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
            self.receive_messages, host=self.address, port=self.port
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

        varint_message_reader = VarintMessageReader(reader)
        while not self.is_stopped:
            try:
                message_bytes = await varint_message_reader.read_next_message()
                if len(message_bytes) == 0:
                    self.logger.error(
                        f"Tendermint node {peer_name} closed connection."
                    )  # pragma: nocover
                    # break to the _stop if the connection stops
                    break  # pragma: nocover
                self.logger.debug(
                    f"Received {len(message_bytes)} bytes from connection {peer_name}"
                )
                message = Request()
                message.ParseFromString(message_bytes)
            except (
                DecodeVarintError,
                DecodeError,
            ) as e:  # pragma: nocover
                self.logger.error(
                    f"an error occurred while reading a message: "
                    f"{type(e).__name__}: {e}. "
                    f"The message will be ignored."
                )
                if reader.at_eof():
                    self.logger.info("connection at EOF, stop receiving loop.")
                    return
                continue
            except TooLargeVarint as e:  # pragma: nocover
                self.logger.error(
                    f"A message exceeding the configured max size was received. "
                    f"{type(e).__name__}: {e} "
                    f"Closing the connection to the node."
                )
                await self.disconnect()
                return
            except EOFError:
                self.logger.info("connection at EOF, stop receiving loop.")
                return
            except CancelledError:  # pragma: nocover
                self.logger.debug(f"Read task for peer {peer_name} cancelled.")
                return
            await self._handle_message(message, peer_name)

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

        # we only deal with atomic request-response cycles, so it is safe to remove the reference
        peer_name = self._request_id_to_socket.pop(dialogue.incomplete_dialogue_label)
        _reader, writer = self._streams_by_socket[peer_name]
        protobuf_message = _TendermintProtocolEncoder.process(message)
        data = _TendermintABCISerializer.write_message(protobuf_message)
        self.logger.debug(f"Writing {len(data)} bytes")
        writer.write(data)


class StoppableThread(Thread):
    """Thread class with a stop() method."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialise the thread."""
        super().__init__(*args, **kwargs)
        self._stop_event = Event()

    def stop(self) -> None:
        """Set the stop event."""
        self._stop_event.set()

    def stopped(self) -> bool:
        """Check if the thread is stopped."""
        return self._stop_event.is_set()


class TendermintParams:  # pylint: disable=too-few-public-methods
    """Tendermint node parameters."""

    def __init__(  # pylint: disable=too-many-arguments
        self,
        proxy_app: str,
        rpc_laddr: str = DEFAULT_RPC_LISTEN_ADDRESS,
        p2p_laddr: str = DEFAULT_P2P_LISTEN_ADDRESS,
        p2p_seeds: Optional[List[str]] = None,
        consensus_create_empty_blocks: bool = True,
        home: Optional[str] = None,
        use_grpc: bool = False,
    ):
        """
        Initialize the parameters to the Tendermint node.

        :param proxy_app: ABCI address.
        :param rpc_laddr: RPC address.
        :param p2p_laddr: P2P address.
        :param p2p_seeds: P2P seeds.
        :param consensus_create_empty_blocks: if true, Tendermint node creates empty blocks.
        :param home: Tendermint's home directory.
        :param use_grpc: Wheter to use a gRPC server, or TSP
        """
        self.proxy_app = proxy_app
        self.rpc_laddr = rpc_laddr
        self.p2p_laddr = p2p_laddr
        self.p2p_seeds = p2p_seeds
        self.consensus_create_empty_blocks = consensus_create_empty_blocks
        self.home = home
        self.use_grpc = use_grpc

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

    def build_node_command(self, debug: bool = False) -> List[str]:
        """Build the 'node' command."""
        p2p_seeds = ",".join(self.p2p_seeds) if self.p2p_seeds else ""
        cmd = [
            "tendermint",
            "node",
            f"--proxy_app={self.proxy_app}",
            f"--rpc.laddr={self.rpc_laddr}",
            f"--p2p.laddr={self.p2p_laddr}",
            f"--p2p.seeds={p2p_seeds}",
            f"--consensus.create_empty_blocks={str(self.consensus_create_empty_blocks).lower()}",
        ]
        if debug:
            cmd.append("--log_level=debug")

        if self.home is not None:  # pragma: nocover
            cmd += ["--home", self.home]
        return cmd

    @staticmethod
    def get_node_command_kwargs(monitoring: bool = False) -> Dict:
        """Get the node command kwargs"""
        kwargs = {
            "bufsize": 1,
            "universal_newlines": True,
        }

        # Only redirect stdout and stderr if we're going to read
        if monitoring:
            kwargs["stdout"] = subprocess.PIPE
            kwargs["stderr"] = subprocess.STDOUT

        if platform.system() == "Windows":  # pragma: nocover
            kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP  # type: ignore
        else:
            kwargs["preexec_fn"] = os.setsid  # type: ignore

        return kwargs


class TendermintNode:
    """A class to manage a Tendermint node."""

    def __init__(self, params: TendermintParams, logger: Optional[Logger] = None):
        """
        Initialize a Tendermint node.

        :param params: the parameters.
        :param logger: the logger.
        """
        self.params = params
        self._process: Optional[subprocess.Popen] = None
        self._monitoring: Optional[StoppableThread] = None
        self.logger = logger or logging.getLogger()
        self.log_file = os.environ.get("LOG_FILE", DEFAULT_TENDERMINT_LOG_FILE)

    def _build_init_command(self) -> List[str]:
        """Build the 'init' command."""
        cmd = [
            "tendermint",
            "init",
        ]
        if self.params.use_grpc:
            cmd += ["--abci=grpc"]
        if self.params.home is not None:  # pragma: nocover
            cmd += ["--home", self.params.home]
        return cmd

    def init(self) -> None:
        """Initialize Tendermint node."""
        cmd = self._build_init_command()
        subprocess.call(cmd)  # nosec

    def start(self, start_monitoring: bool = False, debug: bool = False) -> None:
        """Start a Tendermint node process."""
        self._start_tm_process(start_monitoring, debug)
        if start_monitoring:
            self._start_monitoring_thread()

    def _start_tm_process(self, monitoring: bool = False, debug: bool = False) -> None:
        """Start a Tendermint node process."""
        if self._process is not None:  # pragma: nocover
            return
        cmd = self.params.build_node_command(debug)
        kwargs = self.params.get_node_command_kwargs(monitoring)
        self._process = subprocess.Popen(cmd, **kwargs)  # type: ignore # nosec # pylint: disable=consider-using-with,W1509

        self.write_line("Tendermint process started\n")

    def _start_monitoring_thread(self) -> None:
        """Start a monitoring thread."""
        self._monitoring = StoppableThread(target=self.check_server_status)
        self._monitoring.start()

    def _stop_tm_process(self) -> None:
        """Stop a Tendermint node process."""
        if self._process is None:
            return

        if platform.system() == "Windows":
            os.kill(self._process.pid, signal.CTRL_C_EVENT)  # type: ignore  # pylint: disable=no-member
            try:
                self._process.wait(timeout=5)
            except subprocess.TimeoutExpired:  # nosec
                os.kill(self._process.pid, signal.CTRL_BREAK_EVENT)  # type: ignore  # pylint: disable=no-member
        else:
            self._process.send_signal(signal.SIGTERM)
            self._process.wait(timeout=5)
            poll = self._process.poll()
            if poll is None:  # pragma: nocover
                self._process.terminate()
                self._process.wait(3)

        self._process = None
        self.write_line("Tendermint process stopped\n")

    def _stop_monitoring_thread(self) -> None:
        """Stop a monitoring process."""
        if self._monitoring is not None:
            self._monitoring.stop()  # set stop event
            self._monitoring.join()

    def stop(self) -> None:
        """Stop a Tendermint node process."""
        self._stop_monitoring_thread()
        self._stop_tm_process()

    def prune_blocks(self) -> int:
        """Prune blocks from the Tendermint state"""
        return subprocess.call(  # nosec:
            ["tendermint", "--home", str(self.params.home), "unsafe-reset-all"]
        )

    def write_line(self, line: str) -> None:
        """Open and write a line to the log file."""
        with open(self.log_file, "a", encoding=ENCODING) as file:
            file.write(line)

    def check_server_status(
        self,
    ) -> None:
        """Check server status."""
        self.write_line("Monitoring thread started\n")
        while True:
            try:
                if self._monitoring.stopped():  # type: ignore
                    break  # break from the loop immediately.
                if self._process is not None and self._process.stdout is not None:
                    line = self._process.stdout.readline()
                    self.write_line(line)
                    for trigger in [
                        # this occurs when we lose connection from the tm side
                        "RPC HTTP server stopped",
                        # this occurs when we lose connection from the AEA side.
                        "Stopping abci.socketClient for error: read message: EOF module=abci-client connection=",
                    ]:
                        if line.find(trigger) >= 0:
                            self._stop_tm_process()
                            self._start_tm_process()
                            self.write_line(
                                f"Restarted the HTTP RPC server, as a connection was dropped with message:\n\t\t {line}\n"
                            )
            except Exception as e:  # pylint: disable=broad-except
                self.write_line(f"Error!: {str(e)}")
        self.write_line("Monitoring thread terminated\n")

    def reset_genesis_file(self, genesis_time: str, initial_height: str) -> None:
        """Reset genesis file."""

        genesis_file = Path(str(self.params.home), "config", "genesis.json")
        genesis_config = json.loads(genesis_file.read_text(encoding=ENCODING))
        genesis_config["genesis_time"] = genesis_time
        genesis_config["initial_height"] = initial_height
        genesis_file.write_text(json.dumps(genesis_config, indent=2), encoding=ENCODING)


class ABCIServerConnection(Connection):  # pylint: disable=too-many-instance-attributes
    """ABCI server."""

    connection_id = PUBLIC_ID
    params: Optional[TendermintParams] = None
    node: Optional[TendermintNode] = None
    channel: Optional[Union[TcpServerChannel, GrpcServerChannel]] = None

    def __init__(self, **kwargs: Any) -> None:
        """
        Initialize the connection.

        :param kwargs: keyword arguments passed to component base
        """
        super().__init__(**kwargs)  # pragma: no cover

        self._process_connection_params()
        self._process_tendermint_params()

        if self.use_grpc:
            self.channel = GrpcServerChannel(
                self.target_skill_id,
                address=self.host,
                port=self.port,
                logger=self.logger,
            )
        else:
            self.channel = TcpServerChannel(
                self.target_skill_id,
                address=self.host,
                port=self.port,
                logger=self.logger,
            )

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
        self.use_grpc = cast(bool, self.configuration.config.get("use_grpc"))

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
            self.use_grpc,
        )
        self.logger.debug(f"Tendermint parameters: {self.params}")
        self.node = TendermintNode(self.params, self.logger)

    def _ensure_connected(self) -> None:
        """Ensure that the connection and the channel are ready."""
        super()._ensure_connected()

        self.channel = cast(Union[TcpServerChannel, GrpcServerChannel], self.channel)
        if self.channel.is_stopped:
            raise ConnectionError("The channel is stopped.")

    async def connect(self) -> None:
        """
        Set up the connection.

        In the implementation, remember to update 'connection_status' accordingly.
        """
        if self.is_connected:  # pragma: no cover
            return

        self.state = ConnectionStates.connecting
        self.channel = cast(Union[TcpServerChannel, GrpcServerChannel], self.channel)
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
        self.channel = cast(Union[TcpServerChannel, GrpcServerChannel], self.channel)
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
        self.channel = cast(Union[TcpServerChannel, GrpcServerChannel], self.channel)
        await self.channel.send(envelope)

    async def receive(self, *args: Any, **kwargs: Any) -> Optional[Envelope]:
        """
        Receive an envelope. Blocking.

        :param args: arguments to receive
        :param kwargs: keyword arguments to receive
        :return: the envelope received, if present.  # noqa: DAR202
        """
        self._ensure_connected()
        self.channel = cast(Union[TcpServerChannel, GrpcServerChannel], self.channel)
        try:
            return await self.channel.get_message()
        except CancelledError:  # pragma: no cover
            return None
