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

# pylint: disable=no-member

"""BaseChannel for MockNode"""

from typing import Dict

import packages.valory.connections.abci.tendermint.abci.types_pb2 as abci_types  # type: ignore


class BaseChannel:
    """Defines the interface for other channels to use"""

    def __init__(self, **kwargs: Dict) -> None:
        """Initializes a channel"""

    def connect(self) -> None:
        """
        Set up the channel.

        By default, it is a no-op.
        """

    def disconnect(self) -> None:
        """
        Tear down the channel.

        By default, it is a no-op.
        """

    def send_info(self, request: abci_types.RequestInfo) -> abci_types.ResponseInfo:  # type: ignore
        """
        Sends an info request.

        :param: request: RequestInfo pb object
        """
        raise NotImplementedError

    def send_echo(self, request: abci_types.RequestEcho) -> abci_types.ResponseEcho:  # type: ignore
        """
        Sends an echo request.

        :param: request: RequestEcho pb object
        """
        raise NotImplementedError

    def send_flush(self, request: abci_types.RequestFlush) -> abci_types.ResponseFlush:  # type: ignore
        """
        Sends an flush request.

        :param: request: RequestFlush pb object
        """
        raise NotImplementedError

    def send_set_option(
        self, request: abci_types.RequestSetOption  # type: ignore
    ) -> abci_types.ResponseSetOption:  # type: ignore
        """
        Sends an setOption request.

        :param: request: RequestSetOption pb object
        """
        raise NotImplementedError

    def send_deliver_tx(
        self, request: abci_types.RequestDeliverTx  # type: ignore
    ) -> abci_types.ResponseDeliverTx:  # type: ignore
        """
        Sends an deliverTx request.

        :param: request: RequestDeliverTx pb object
        """
        raise NotImplementedError

    def send_check_tx(
        self, request: abci_types.RequestCheckTx  # type: ignore
    ) -> abci_types.ResponseCheckTx:  # type: ignore
        """
        Sends an checkTx request.

        :param: request: RequestCheckTx pb object
        """
        raise NotImplementedError

    def send_query(self, request: abci_types.RequestQuery) -> abci_types.ResponseQuery:  # type: ignore
        """
        Sends an query request.

        :param: request: RequestQuery pb object
        """
        raise NotImplementedError

    def send_commit(
        self, request: abci_types.RequestCommit  # type: ignore
    ) -> abci_types.ResponseCommit:  # type: ignore
        """
        Sends an commit request.

        :param: request: RequestCommit pb object
        """
        raise NotImplementedError

    def send_init_chain(
        self, request: abci_types.RequestInitChain  # type: ignore
    ) -> abci_types.ResponseInitChain:  # type: ignore
        """
        Sends an initChain request.

        :param: request: RequestInitChain pb object
        """
        raise NotImplementedError

    def send_begin_block(
        self, request: abci_types.RequestBeginBlock  # type: ignore
    ) -> abci_types.ResponseBeginBlock:  # type: ignore
        """
        Sends an beginBlock request.

        :param: request: RequestBeginBlock pb object
        """
        raise NotImplementedError

    def send_end_block(
        self, request: abci_types.RequestEndBlock  # type: ignore
    ) -> abci_types.ResponseEndBlock:  # type: ignore
        """
        Sends an endBlock request.

        :param: request: RequestEndBlock pb object
        """
        raise NotImplementedError

    def send_list_snapshots(
        self, request: abci_types.RequestListSnapshots  # type: ignore
    ) -> abci_types.ResponseListSnapshots:  # type: ignore
        """
        Sends an listSnapshots request.

        :param: request: RequestListSnapshots pb object
        """
        raise NotImplementedError

    def send_offer_snapshot(
        self, request: abci_types.RequestOfferSnapshot  # type: ignore
    ) -> abci_types.ResponseOfferSnapshot:  # type: ignore
        """
        Sends an offerSnapshot request.

        :param: request: RequestOfferSnapshot pb object
        """
        raise NotImplementedError

    def send_load_snapshot_chunk(
        self, request: abci_types.RequestLoadSnapshotChunk  # type: ignore
    ) -> abci_types.ResponseLoadSnapshotChunk:  # type: ignore
        """
        Sends an loadSnapshotChunk request.

        :param: request: RequestLoadSnapshotChunk pb object
        """
        raise NotImplementedError

    def send_apply_snapshot_chunk(
        self, request: abci_types.RequestApplySnapshotChunk  # type: ignore
    ) -> abci_types.ResponseApplySnapshotChunk:  # type: ignore
        """
        Sends an applySnapshotChunk request.

        :param: request: RequestApplySnapshotChunk pb object
        """
        raise NotImplementedError
