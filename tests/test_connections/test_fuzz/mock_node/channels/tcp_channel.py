#!/usr/bin/env python3
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
"""TcpChannel for MockNode"""

import logging
import socket
from io import BytesIO
from typing import Dict, Generator

from aea.exceptions import enforce

import packages.valory.connections.abci.tendermint.abci.types_pb2 as abci_types  # type: ignore
from packages.valory.connections.abci.connection import _TendermintABCISerializer

from tests.test_connections.test_fuzz.mock_node.channels.base import BaseChannel


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

        host = kwargs.get("host", "localhost")
        port = kwargs.get("port", 26658)
        self.logger = _default_logger

        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_socket.connect((host, port))

    def _get_response(self) -> abci_types.Response:
        """
        Gets the response for a request.

        :return: a pb response object

        It assumes that:
            - For every request there's a response.
            - Responses are sent in the same order as the reqs.

        """
        data = BytesIO()

        bits = self.tcp_socket.recv(self.MAX_READ_IN_BYTES)

        if len(bits) == 0:
            raise EOFError

        self.logger.debug(f"Received {len(bits)} bytes from abci")
        data.write(bits)
        data.seek(0)

        message_iterator: Generator[
            abci_types.Response, None, None
        ] = _TendermintABCISerializer.read_messages(data, abci_types.Response)
        sentinel = object()
        num_messages = 0
        response = None

        while True:
            message = next(message_iterator, sentinel)
            if response is None:
                response = message

            if message == sentinel:
                # we reached the end of the iterator
                break

            num_messages += 1

        enforce(num_messages == 1, "a single message was expected")

        return response

    def send_info(self, request: abci_types.RequestInfo) -> abci_types.ResponseInfo:
        """
        Sends an info request.

        :param: request: RequestInfo pb object
        :return: ResponseInfo pb object
        """

        message = abci_types.Request()
        message.info.CopyFrom(request)

        data = _TendermintABCISerializer.write_message(message)

        self.tcp_socket.send(data)

        response = self._get_response()
        response_type = response.WhichOneof("value")

        enforce(
            response_type == "info",
            f"expected response of type info, {response_type} was received",
        )

        return response.info

    def send_echo(self, request: abci_types.RequestEcho) -> abci_types.ResponseEcho:
        """
        Sends an echo request.

        :param: request: RequestEcho pb object
        :return: ResponseEcho pb object
        """
        message = abci_types.Request()
        message.echo.CopyFrom(request)

        data = _TendermintABCISerializer.write_message(message)

        self.tcp_socket.send(data)

        response = self._get_response()
        response_type = response.WhichOneof("value")

        enforce(
            response_type == "echo",
            f"expected response of type echo, {response_type} was received",
        )

        return response.echo

    def send_flush(self, request: abci_types.RequestFlush) -> abci_types.ResponseFlush:
        """
        Sends an flush request.

        :param: request: RequestFlush pb object
        :return: ResponseFlush pb object
        """
        message = abci_types.Request()
        message.flush.CopyFrom(request)

        data = _TendermintABCISerializer.write_message(message)

        self.tcp_socket.send(data)

        response = self._get_response()
        response_type = response.WhichOneof("value")

        enforce(
            response_type == "flush",
            f"expected response of type flush, {response_type} was received",
        )

        return response.flush

    def send_set_option(
        self, request: abci_types.RequestSetOption
    ) -> abci_types.ResponseSetOption:
        """
        Sends an setOption request.

        :param: request: RequestSetOption pb object
        :return: ResponseSetOption pb object
        """
        message = abci_types.Request()
        message.set_option.CopyFrom(request)

        data = _TendermintABCISerializer.write_message(message)

        self.tcp_socket.send(data)

        response = self._get_response()
        response_type = response.WhichOneof("value")

        enforce(
            response_type == "set_option",
            f"expected response of type set_option, {response_type} was received",
        )

        return response.set_option

    def send_deliver_tx(
        self, request: abci_types.RequestDeliverTx
    ) -> abci_types.ResponseDeliverTx:
        """
        Sends an deliverTx request.

        :param: request: RequestDeliverTx pb object
        :return: ResponseDeliverTx pb object
        """
        message = abci_types.Request()
        message.deliver_tx.CopyFrom(request)

        data = _TendermintABCISerializer.write_message(message)

        self.tcp_socket.send(data)

        response = self._get_response()
        response_type = response.WhichOneof("value")

        enforce(
            response_type == "deliver_tx",
            f"expected response of type deliver_tx, {response_type} was received",
        )

        return response.deliver_tx

    def send_check_tx(
        self, request: abci_types.RequestCheckTx
    ) -> abci_types.ResponseCheckTx:
        """
        Sends an checkTx request.

        :param: request: RequestCheckTx pb object
        :return: ResponseCheckTx pb object
        """
        message = abci_types.Request()
        message.check_tx.CopyFrom(request)

        data = _TendermintABCISerializer.write_message(message)

        self.tcp_socket.send(data)

        response = self._get_response()
        response_type = response.WhichOneof("value")

        enforce(
            response_type == "check_tx",
            f"expected response of type check_tx, {response_type} was received",
        )

        return response.check_tx

    def send_query(self, request: abci_types.RequestQuery) -> abci_types.ResponseQuery:
        """
        Sends an query request.

        :param: request: RequestQuery pb object
        :return: ResponseQuery pb object
        """
        message = abci_types.Request()
        message.query.CopyFrom(request)

        data = _TendermintABCISerializer.write_message(message)

        self.tcp_socket.send(data)

        response = self._get_response()
        response_type = response.WhichOneof("value")

        enforce(
            response_type == "query",
            f"expected response of type query, {response_type} was received",
        )

        return response.query

    def send_commit(
        self, request: abci_types.RequestCommit
    ) -> abci_types.ResponseCommit:
        """
        Sends an commit request.

        :param: request: RequestCommit pb object
        :return: ResponseCommit pb object
        """
        message = abci_types.Request()
        message.commit.CopyFrom(request)

        data = _TendermintABCISerializer.write_message(message)

        self.tcp_socket.send(data)

        response = self._get_response()
        response_type = response.WhichOneof("value")

        enforce(
            response_type == "commit",
            f"expected response of type commit, {response_type} was received",
        )

        return response.commit

    def send_init_chain(
        self, request: abci_types.RequestInitChain
    ) -> abci_types.ResponseInitChain:
        """
        Sends an initChain request.

        :param: request: RequestInitChain pb object
        :return: ResponseInitChain pb object
        """
        message = abci_types.Request()
        message.init_chain.CopyFrom(request)

        data = _TendermintABCISerializer.write_message(message)

        self.tcp_socket.send(data)

        response = self._get_response()
        response_type = response.WhichOneof("value")

        enforce(
            response_type == "init_chain",
            f"expected response of type init_chain, {response_type} was received",
        )

        return response.init_chain

    def send_begin_block(
        self, request: abci_types.RequestBeginBlock
    ) -> abci_types.ResponseBeginBlock:
        """
        Sends an beginBlock request.

        :param: request: RequestBeginBlock pb object
        :return: ResponseBeginBlock pb object
        """
        message = abci_types.Request()
        message.begin_block.CopyFrom(request)

        data = _TendermintABCISerializer.write_message(message)

        self.tcp_socket.send(data)

        response = self._get_response()
        response_type = response.WhichOneof("value")

        enforce(
            response_type == "begin_block",
            f"expected response of type begin_block, {response_type} was received",
        )

        return response.begin_block

    def send_end_block(
        self, request: abci_types.RequestEndBlock
    ) -> abci_types.ResponseEndBlock:
        """
        Sends an endBlock request.

        :param: request: RequestEndBlock pb object
        :return: ResponseEndBlock pb object
        """
        message = abci_types.Request()
        message.end_block.CopyFrom(request)

        data = _TendermintABCISerializer.write_message(message)

        self.tcp_socket.send(data)

        response = self._get_response()
        response_type = response.WhichOneof("value")

        enforce(
            response_type == "end_block",
            f"expected response of type end_block, {response_type} was received",
        )

        return response.end_block

    def send_list_snapshots(
        self, request: abci_types.RequestListSnapshots
    ) -> abci_types.ResponseListSnapshots:
        """
        Sends an listSnapshots request.

        :param: request: RequestListSnapshots pb object
        :return: ResponseListSnapshots pb object
        """
        message = abci_types.Request()
        message.list_snapshots.CopyFrom(request)

        data = _TendermintABCISerializer.write_message(message)

        self.tcp_socket.send(data)

        response = self._get_response()
        response_type = response.WhichOneof("value")

        enforce(
            response_type == "list_snapshots",
            f"expected response of type list_snapshots, {response_type} was received",
        )

        return response.list_snapshots

    def send_offer_snapshot(
        self, request: abci_types.RequestOfferSnapshot
    ) -> abci_types.ResponseOfferSnapshot:
        """
        Sends an offerSnapshot request.

        :param: request: RequestOfferSnapshot pb object
        :return: ResponseOfferSnapshot pb object
        """
        message = abci_types.Request()
        message.offer_snapshot.CopyFrom(request)

        data = _TendermintABCISerializer.write_message(message)

        self.tcp_socket.send(data)

        response = self._get_response()
        response_type = response.WhichOneof("value")

        enforce(
            response_type == "offer_snapshot",
            f"expected response of type offer_snapshot, {response_type} was received",
        )

        return response.offer_snapshot

    def send_load_snapshot_chunk(
        self, request: abci_types.RequestLoadSnapshotChunk
    ) -> abci_types.ResponseLoadSnapshotChunk:
        """
        Sends an loadSnapshotChunk request.

        :param: request: RequestLoadSnapshotChunk pb object
        :return: ResponseLoadSnapshotChunk pb object
        """
        message = abci_types.Request()
        message.load_snapshot_chunk.CopyFrom(request)

        data = _TendermintABCISerializer.write_message(message)

        self.tcp_socket.send(data)

        response = self._get_response()
        response_type = response.WhichOneof("value")

        enforce(
            response_type == "load_snapshot_chunk",
            f"expected response of type load_snapshot_chunk, {response_type} was received",
        )

        return response.load_snapshot_chunk

    def send_apply_snapshot_chunk(
        self, request: abci_types.RequestApplySnapshotChunk
    ) -> abci_types.ResponseApplySnapshotChunk:
        """
        Sends an applySnapshotChunk request.

        :param: request: RequestApplySnapshotChunk pb object
        :return: ResponseApplySnapshotChunk pb object
        """
        message = abci_types.Request()
        message.apply_snapshot_chunk.CopyFrom(request)

        data = _TendermintABCISerializer.write_message(message)

        self.tcp_socket.send(data)

        response = self._get_response()
        response_type = response.WhichOneof("value")

        enforce(
            response_type == "apply_snapshot_chunk",
            f"expected response of type apply_snapshot_chunk, {response_type} was received",
        )

        return response.apply_snapshot_chunk
