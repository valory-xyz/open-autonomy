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

"""Tests package for the 'valory/abci' protocol."""

from abc import abstractmethod

from aea.mail.base import Envelope

from packages.valory.protocols.tendermint import TendermintMessage
from packages.valory.protocols.tendermint.message import (
    _default_logger as abci_message_logger,
)


class BaseTestMessageConstruction:
    """Base class to test message construction for the ABCI protocol."""

    @abstractmethod
    def build_message(self) -> TendermintMessage:
        """Build the message to be used for testing."""

    def test_run(self) -> None:
        """Run the test."""
        msg = self.build_message()
        msg.to = "receiver"
        envelope = Envelope(to=msg.to, sender="sender", message=msg)
        envelope_bytes = envelope.encode()

        actual_envelope = Envelope.decode(envelope_bytes)
        expected_envelope = envelope

        assert expected_envelope.to == actual_envelope.to
        assert expected_envelope.sender == actual_envelope.sender
        assert (
            expected_envelope.protocol_specification_id
            == actual_envelope.protocol_specification_id
        )
        assert expected_envelope.message != actual_envelope.message

        actual_msg = TendermintMessage.serializer.decode(actual_envelope.message_bytes)
        actual_msg.to = actual_envelope.to
        actual_msg.sender = actual_envelope.sender
        expected_msg = msg
        assert expected_msg == actual_msg


class TestRequestEcho(BaseTestMessageConstruction):
    """Test ABCI request abci."""

    def build_message(self) -> TendermintMessage:
        """Build the message."""
        return TendermintMessage(
            performative=TendermintMessage.Performative.REQUEST,  # type: ignore
            query="query",
        )
