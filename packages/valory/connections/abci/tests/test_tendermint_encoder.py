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

"""Tests for valory/abci connection, tendermint_encoder module."""

# pylint: skip-file

from packages.valory.connections.abci.tendermint.abci.types_pb2 import (  # type: ignore
    ResponseListSnapshots,
)
from packages.valory.connections.abci.tendermint_encoder import (
    _TendermintProtocolEncoder,
)
from packages.valory.protocols.abci import AbciMessage
from packages.valory.protocols.abci.custom_types import Result, ResultType, SnapShots
from packages.valory.protocols.abci.custom_types import Snapshot as CustomSnapshot


class TestTendermintProtocolEncoder:
    """Test for the Tendermint protocol encoder."""

    def test_response_exception(self) -> None:
        """Test decoding of a response exception."""
        expected_error = "error"
        abci_message = AbciMessage(
            performative=AbciMessage.Performative.RESPONSE_EXCEPTION,  # type: ignore
            error=expected_error,
        )
        message = _TendermintProtocolEncoder.response_exception(abci_message)
        assert message.exception.error == expected_error

    def test_response_echo(self) -> None:
        """Test decoding of a response echo."""
        expected_message = "message"
        abci_message = AbciMessage(
            performative=AbciMessage.Performative.RESPONSE_ECHO,  # type: ignore
            message=expected_message,
        )
        message = _TendermintProtocolEncoder.response_echo(abci_message)
        assert message.echo.message == expected_message

    def test_response_set_option(self) -> None:
        """Test decoding of a response set-option."""
        expected_code = 0
        expected_log = "log"
        expected_info = "info"
        abci_message = AbciMessage(
            performative=AbciMessage.Performative.RESPONSE_SET_OPTION,  # type: ignore
            code=expected_code,
            log=expected_log,
            info=expected_info,
        )
        message = _TendermintProtocolEncoder.response_set_option(abci_message)
        assert message.set_option.code == expected_code
        assert message.set_option.log == expected_log
        assert message.set_option.info == expected_info

    def test_response_list_snapshots(self) -> None:
        """Test decoding of a response list-snapshots."""
        snapshot = CustomSnapshot(0, 0, 0, b"", b"")
        snapshots = SnapShots([snapshot])

        # expected snapshots object
        list_snapshots = ResponseListSnapshots()
        snapshots_pb = [
            _TendermintProtocolEncoder._encode_snapshot(snapshot)
            for snapshot in snapshots.snapshots
        ]
        list_snapshots.snapshots.extend(snapshots_pb)

        abci_message = AbciMessage(
            performative=AbciMessage.Performative.RESPONSE_LIST_SNAPSHOTS,  # type: ignore
            snapshots=snapshots,
        )
        message = _TendermintProtocolEncoder.response_list_snapshots(abci_message)
        assert message.list_snapshots == list_snapshots

    def test_response_offer_snapshot(self) -> None:
        """Test decoding of a response offer-snapshot."""
        expected_result = Result(ResultType.ACCEPT)
        abci_message = AbciMessage(
            performative=AbciMessage.Performative.RESPONSE_OFFER_SNAPSHOT,  # type: ignore
            result=expected_result,
        )
        message = _TendermintProtocolEncoder.response_offer_snapshot(abci_message)
        assert message.offer_snapshot.result == expected_result.result_type.value

    def test_response_load_snapshot_chunk(self) -> None:
        """Test decoding of a response load-snapshot-chunk."""
        expected_chunk = b"chunk"
        abci_message = AbciMessage(
            performative=AbciMessage.Performative.RESPONSE_LOAD_SNAPSHOT_CHUNK,  # type: ignore
            chunk=expected_chunk,
        )
        message = _TendermintProtocolEncoder.response_load_snapshot_chunk(abci_message)
        assert message.load_snapshot_chunk.chunk == expected_chunk

    def test_response_apply_snapshot_chunk(self) -> None:
        """Test decoding of a response apply-snapshot-chunk."""
        result = Result(ResultType.ACCEPT)
        abci_message = AbciMessage(
            performative=AbciMessage.Performative.RESPONSE_APPLY_SNAPSHOT_CHUNK,  # type: ignore
            result=result,
            refetch_chunks=tuple(),
            reject_senders=tuple(),
        )
        message = _TendermintProtocolEncoder.response_apply_snapshot_chunk(abci_message)
        assert message.apply_snapshot_chunk.result == result.result_type.value
