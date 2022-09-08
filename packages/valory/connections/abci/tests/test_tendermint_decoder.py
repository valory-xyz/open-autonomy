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

"""Tests for valory/abci connection, tendermint_decoder module."""

# pylint: skip-file

from packages.valory.connections.abci.dialogues import AbciDialogue, AbciDialogues
from packages.valory.connections.abci.tendermint.abci.types_pb2 import (  # type: ignore
    Request,
    RequestApplySnapshotChunk,
    RequestEcho,
    RequestListSnapshots,
    RequestLoadSnapshotChunk,
    RequestOfferSnapshot,
    RequestSetOption,
    Snapshot,
)
from packages.valory.connections.abci.tendermint_decoder import (
    _TendermintProtocolDecoder,
)
from packages.valory.protocols.abci import AbciMessage


class TestTendermintProtocolDecoder:
    """Test for the Tendermint protocol decoder."""

    def test_request_echo(self) -> None:
        """Test decoding of a request echo."""
        dialogues = AbciDialogues()
        request = Request()
        echo = RequestEcho()
        echo.message = ""
        request.echo.CopyFrom(echo)
        message, dialogue = _TendermintProtocolDecoder.request_echo(
            request, dialogues, "counterparty"
        )
        assert isinstance(message, AbciMessage)
        assert isinstance(dialogue, AbciDialogue)

    def test_request_set_option(self) -> None:
        """Test decoding of a request set-option."""
        dialogues = AbciDialogues()
        request = Request()
        set_option = RequestSetOption()
        set_option.key = ""
        set_option.value = ""
        request.set_option.CopyFrom(set_option)
        message, dialogue = _TendermintProtocolDecoder.request_set_option(
            request, dialogues, "counterparty"
        )
        assert isinstance(message, AbciMessage)
        assert isinstance(dialogue, AbciDialogue)

    def test_request_list_snapshots(self) -> None:
        """Test decoding of a request list-snapshots."""
        dialogues = AbciDialogues()
        request = Request()
        list_snapshots = RequestListSnapshots()
        request.list_snapshots.CopyFrom(list_snapshots)
        message, dialogue = _TendermintProtocolDecoder.request_list_snapshots(
            request, dialogues, "counterparty"
        )
        assert isinstance(message, AbciMessage)
        assert isinstance(dialogue, AbciDialogue)

    def test_request_offer_snapshot(self) -> None:
        """Test decoding of a request offer-snapshot."""
        dialogues = AbciDialogues()
        request = Request()
        offer_snapshot = RequestOfferSnapshot()
        snapshot = Snapshot()
        offer_snapshot.snapshot.CopyFrom(snapshot)
        offer_snapshot.app_hash = b""
        request.offer_snapshot.CopyFrom(offer_snapshot)
        message, dialogue = _TendermintProtocolDecoder.request_offer_snapshot(
            request, dialogues, "counterparty"
        )
        assert isinstance(message, AbciMessage)
        assert isinstance(dialogue, AbciDialogue)

    def test_request_load_snapshot_chunk(self) -> None:
        """Test decoding of a request load-snapshot-chunk."""
        dialogues = AbciDialogues()
        request = Request()
        load_snapshot_chunk = RequestLoadSnapshotChunk()
        request.load_snapshot_chunk.CopyFrom(load_snapshot_chunk)
        message, dialogue = _TendermintProtocolDecoder.request_load_snapshot_chunk(
            request, dialogues, "counterparty"
        )
        assert isinstance(message, AbciMessage)
        assert isinstance(dialogue, AbciDialogue)

    def test_request_apply_snapshot_chunk(self) -> None:
        """Test decoding of a request load-snapshot-chunk."""
        dialogues = AbciDialogues()
        request = Request()
        apply_snapshot_chunk = RequestApplySnapshotChunk()
        request.apply_snapshot_chunk.CopyFrom(apply_snapshot_chunk)
        message, dialogue = _TendermintProtocolDecoder.request_apply_snapshot_chunk(
            request, dialogues, "counterparty"
        )
        assert isinstance(message, AbciMessage)
        assert isinstance(dialogue, AbciDialogue)
