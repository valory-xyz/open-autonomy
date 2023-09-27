# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2023 Valory AG
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
"""TcpChannel for MockNode"""
# pylint: skip-file

import asyncio
import logging
import platform
import socket
from asyncio import AbstractEventLoop
from threading import Thread
from typing import Dict, Optional, cast

from aea.exceptions import enforce

import packages.valory.connections.abci.tendermint.abci.types_pb2 as abci_types  # type: ignore
from packages.valory.connections.abci.connection import (
    VarintMessageReader,
    _TendermintABCISerializer,
)
from packages.valory.connections.abci.tests.test_fuzz.mock_node.channels.base import (
    BaseChannel,
)


_default_logger = logging.getLogger(__name__)

logging.basicConfig()


class TcpChannel(BaseChannel):
    """Implements BaseChannel to use TCP sockets"""

    MAX_READ_IN_BYTES = 64 * 1024  # Max we'll consume on a read stream

    def __init__(self, **kwargs: Dict) -> None:
        """
        Initializes a TcpChannel

        :param: kwargs:
            - host: the host of the ABCI app (localhost by default)
            - port: the port of the ABCI app (26658 by default)
        """
        super().__init__(**kwargs)

        self.host: str = cast(str, kwargs.get("host", "localhost"))
        self.port: int = cast(int, kwargs.get("port", 26658))
        self.logger = _default_logger

        # attributes for the channel state
        self.loop: Optional[AbstractEventLoop] = None
        self.loop_thread: Optional[Thread] = None
        self.message_reader: Optional[VarintMessageReader] = None
        self.reader: Optional[asyncio.StreamReader] = None
        self.writer: Optional[asyncio.StreamWriter] = None

    @property
    def is_connected(self) -> bool:
        """Check whether the channel is connected."""
        return self.loop_thread is not None

    def connect(self) -> None:
        """Set up the channel."""
        if self.is_connected:
            return

        if platform.system() == "Windows":
            self.loop = cast(
                asyncio.AbstractEventLoop,
                asyncio.WindowsSelectorEventLoopPolicy().new_event_loop(),  # type: ignore # windows only
            )
        else:
            self.loop = cast(asyncio.AbstractEventLoop, asyncio.new_event_loop())
        self.loop_thread = Thread(target=self._run_loop_in_thread, args=(self.loop,))
        self.loop_thread.start()

        # set up asyncio connection
        future = asyncio.run_coroutine_threadsafe(
            asyncio.open_connection(self.host, self.port, family=socket.AF_INET),
            self.loop,
        )
        self.reader, self.writer = future.result()
        self.message_reader = VarintMessageReader(self.reader)

    def disconnect(self) -> None:
        """Tear down the channel."""
        if not self.is_connected:
            return

        cast(asyncio.StreamWriter, self.writer).close()

        loop = cast(AbstractEventLoop, self.loop)
        loop.call_soon_threadsafe(loop.stop)
        cast(Thread, self.loop_thread).join(5)

        # restore channel state
        self.loop = None
        self.loop_thread = None
        self.message_reader = None
        self.reader = None
        self.writer = None

    @staticmethod
    def _run_loop_in_thread(loop: AbstractEventLoop) -> None:
        """Run an asyncio loop in the thread of the caller."""
        asyncio.set_event_loop(loop)
        loop.run_forever()

    def _get_response(self) -> abci_types.Response:  # type: ignore
        """
        Gets the response for a request.

        :return: a pb response object

        It assumes that:
            - For every request there's a response.
            - Responses are sent in the same order as the reqs.

        """
        future = asyncio.run_coroutine_threadsafe(
            cast(VarintMessageReader, self.message_reader).read_next_message(),
            cast(AbstractEventLoop, self.loop),
        )
        message_bytes = future.result()
        message = abci_types.Response()  # type: ignore
        message.ParseFromString(message_bytes)
        return message

    def _send_data(self, data: bytes) -> None:
        """Send data over the TCP connection."""
        cast(asyncio.StreamWriter, self.writer).write(data)
        future = asyncio.run_coroutine_threadsafe(
            cast(asyncio.StreamWriter, self.writer).drain(),
            cast(AbstractEventLoop, self.loop),
        )
        future.result()

    def send_info(self, request: abci_types.RequestInfo) -> abci_types.ResponseInfo:  # type: ignore
        """
        Sends an info request.

        :param: request: RequestInfo pb object
        :return: ResponseInfo pb object
        """

        message = abci_types.Request()  # type: ignore
        message.info.CopyFrom(request)

        data = _TendermintABCISerializer.write_message(message)

        self._send_data(data)

        response = self._get_response()
        response_type = response.WhichOneof("value")

        enforce(
            response_type == "info",
            f"expected response of type info, {response_type} was received",
        )

        return response.info

    def send_echo(self, request: abci_types.RequestEcho) -> abci_types.ResponseEcho:  # type: ignore
        """
        Sends an echo request.

        :param: request: RequestEcho pb object
        :return: ResponseEcho pb object
        """
        message = abci_types.Request()  # type: ignore
        message.echo.CopyFrom(request)

        data = _TendermintABCISerializer.write_message(message)

        self._send_data(data)

        response = self._get_response()
        response_type = response.WhichOneof("value")

        enforce(
            response_type == "echo",
            f"expected response of type echo, {response_type} was received",
        )

        return response.echo

    def send_flush(self, request: abci_types.RequestFlush) -> abci_types.ResponseFlush:  # type: ignore
        """
        Sends an flush request.

        :param: request: RequestFlush pb object
        :return: ResponseFlush pb object
        """
        message = abci_types.Request()  # type: ignore
        message.flush.CopyFrom(request)

        data = _TendermintABCISerializer.write_message(message)

        self._send_data(data)

        response = self._get_response()
        response_type = response.WhichOneof("value")

        enforce(
            response_type == "flush",
            f"expected response of type flush, {response_type} was received",
        )

        return response.flush

    def send_set_option(
        self, request: abci_types.RequestSetOption  # type: ignore
    ) -> abci_types.ResponseSetOption:  # type: ignore
        """
        Sends an setOption request.

        :param: request: RequestSetOption pb object
        :return: ResponseSetOption pb object
        """
        message = abci_types.Request()  # type: ignore
        message.set_option.CopyFrom(request)

        data = _TendermintABCISerializer.write_message(message)

        self._send_data(data)

        response = self._get_response()
        response_type = response.WhichOneof("value")

        enforce(
            response_type == "set_option",
            f"expected response of type set_option, {response_type} was received",
        )

        return response.set_option

    def send_deliver_tx(
        self, request: abci_types.RequestDeliverTx  # type: ignore
    ) -> abci_types.ResponseDeliverTx:  # type: ignore
        """
        Sends an deliverTx request.

        :param: request: RequestDeliverTx pb object
        :return: ResponseDeliverTx pb object
        """
        message = abci_types.Request()  # type: ignore
        message.deliver_tx.CopyFrom(request)

        data = _TendermintABCISerializer.write_message(message)

        self._send_data(data)

        response = self._get_response()
        response_type = response.WhichOneof("value")

        enforce(
            response_type == "deliver_tx",
            f"expected response of type deliver_tx, {response_type} was received",
        )

        return response.deliver_tx

    def send_check_tx(
        self, request: abci_types.RequestCheckTx  # type: ignore
    ) -> abci_types.ResponseCheckTx:  # type: ignore
        """
        Sends an checkTx request.

        :param: request: RequestCheckTx pb object
        :return: ResponseCheckTx pb object
        """
        message = abci_types.Request()  # type: ignore
        message.check_tx.CopyFrom(request)

        data = _TendermintABCISerializer.write_message(message)

        self._send_data(data)

        response = self._get_response()
        response_type = response.WhichOneof("value")

        enforce(
            response_type == "check_tx",
            f"expected response of type check_tx, {response_type} was received",
        )

        return response.check_tx

    def send_query(self, request: abci_types.RequestQuery) -> abci_types.ResponseQuery:  # type: ignore
        """
        Sends an query request.

        :param: request: RequestQuery pb object
        :return: ResponseQuery pb object
        """
        message = abci_types.Request()  # type: ignore
        message.query.CopyFrom(request)

        data = _TendermintABCISerializer.write_message(message)

        self._send_data(data)

        response = self._get_response()
        response_type = response.WhichOneof("value")

        enforce(
            response_type == "query",
            f"expected response of type query, {response_type} was received",
        )

        return response.query

    def send_commit(
        self, request: abci_types.RequestCommit  # type: ignore
    ) -> abci_types.ResponseCommit:  # type: ignore
        """
        Sends an commit request.

        :param: request: RequestCommit pb object
        :return: ResponseCommit pb object
        """
        message = abci_types.Request()  # type: ignore
        message.commit.CopyFrom(request)

        data = _TendermintABCISerializer.write_message(message)

        self._send_data(data)

        response = self._get_response()
        response_type = response.WhichOneof("value")

        enforce(
            response_type == "commit",
            f"expected response of type commit, {response_type} was received",
        )

        return response.commit

    def send_init_chain(
        self, request: abci_types.RequestInitChain  # type: ignore
    ) -> abci_types.ResponseInitChain:  # type: ignore
        """
        Sends an initChain request.

        :param: request: RequestInitChain pb object
        :return: ResponseInitChain pb object
        """
        message = abci_types.Request()  # type: ignore
        message.init_chain.CopyFrom(request)

        data = _TendermintABCISerializer.write_message(message)

        self._send_data(data)

        response = self._get_response()
        response_type = response.WhichOneof("value")

        enforce(
            response_type == "init_chain",
            f"expected response of type init_chain, {response_type} was received",
        )

        return response.init_chain

    def send_begin_block(
        self, request: abci_types.RequestBeginBlock  # type: ignore
    ) -> abci_types.ResponseBeginBlock:  # type: ignore
        """
        Sends an beginBlock request.

        :param: request: RequestBeginBlock pb object
        :return: ResponseBeginBlock pb object
        """
        message = abci_types.Request()  # type: ignore
        message.begin_block.CopyFrom(request)

        data = _TendermintABCISerializer.write_message(message)

        self._send_data(data)

        response = self._get_response()
        response_type = response.WhichOneof("value")

        enforce(
            response_type == "begin_block",
            f"expected response of type begin_block, {response_type} was received",
        )

        return response.begin_block

    def send_end_block(
        self, request: abci_types.RequestEndBlock  # type: ignore
    ) -> abci_types.ResponseEndBlock:  # type: ignore
        """
        Sends an endBlock request.

        :param: request: RequestEndBlock pb object
        :return: ResponseEndBlock pb object
        """
        message = abci_types.Request()  # type: ignore
        message.end_block.CopyFrom(request)

        data = _TendermintABCISerializer.write_message(message)

        self._send_data(data)

        response = self._get_response()
        response_type = response.WhichOneof("value")

        enforce(
            response_type == "end_block",
            f"expected response of type end_block, {response_type} was received",
        )

        return response.end_block

    def send_list_snapshots(
        self, request: abci_types.RequestListSnapshots  # type: ignore
    ) -> abci_types.ResponseListSnapshots:  # type: ignore
        """
        Sends an listSnapshots request.

        :param: request: RequestListSnapshots pb object
        :return: ResponseListSnapshots pb object
        """
        message = abci_types.Request()  # type: ignore
        message.list_snapshots.CopyFrom(request)

        data = _TendermintABCISerializer.write_message(message)

        self._send_data(data)

        response = self._get_response()
        response_type = response.WhichOneof("value")

        enforce(
            response_type == "list_snapshots",
            f"expected response of type list_snapshots, {response_type} was received",
        )

        return response.list_snapshots

    def send_offer_snapshot(
        self, request: abci_types.RequestOfferSnapshot  # type: ignore
    ) -> abci_types.ResponseOfferSnapshot:  # type: ignore
        """
        Sends an offerSnapshot request.

        :param: request: RequestOfferSnapshot pb object
        :return: ResponseOfferSnapshot pb object
        """
        message = abci_types.Request()  # type: ignore
        message.offer_snapshot.CopyFrom(request)

        data = _TendermintABCISerializer.write_message(message)

        self._send_data(data)

        response = self._get_response()
        response_type = response.WhichOneof("value")

        enforce(
            response_type == "offer_snapshot",
            f"expected response of type offer_snapshot, {response_type} was received",
        )

        return response.offer_snapshot

    def send_load_snapshot_chunk(
        self, request: abci_types.RequestLoadSnapshotChunk  # type: ignore
    ) -> abci_types.ResponseLoadSnapshotChunk:  # type: ignore
        """
        Sends an loadSnapshotChunk request.

        :param: request: RequestLoadSnapshotChunk pb object
        :return: ResponseLoadSnapshotChunk pb object
        """
        message = abci_types.Request()  # type: ignore
        message.load_snapshot_chunk.CopyFrom(request)

        data = _TendermintABCISerializer.write_message(message)

        self._send_data(data)

        response = self._get_response()
        response_type = response.WhichOneof("value")

        enforce(
            response_type == "load_snapshot_chunk",
            f"expected response of type load_snapshot_chunk, {response_type} was received",
        )

        return response.load_snapshot_chunk

    def send_apply_snapshot_chunk(
        self, request: abci_types.RequestApplySnapshotChunk  # type: ignore
    ) -> abci_types.ResponseApplySnapshotChunk:  # type: ignore
        """
        Sends an applySnapshotChunk request.

        :param: request: RequestApplySnapshotChunk pb object
        :return: ResponseApplySnapshotChunk pb object
        """
        message = abci_types.Request()  # type: ignore
        message.apply_snapshot_chunk.CopyFrom(request)

        data = _TendermintABCISerializer.write_message(message)

        self._send_data(data)

        response = self._get_response()
        response_type = response.WhichOneof("value")

        enforce(
            response_type == "apply_snapshot_chunk",
            f"expected response of type apply_snapshot_chunk, {response_type} was received",
        )

        return response.apply_snapshot_chunk
