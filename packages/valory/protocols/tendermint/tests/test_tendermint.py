# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
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

"""Tests package for the 'valory/tendermint' protocol."""
import logging
from typing import Type
from unittest import mock

import pytest
from _pytest.logging import LogCaptureFixture  # type: ignore
from aea.common import Address
from aea.mail.base import Envelope
from aea.protocols.base import Message
from aea.protocols.dialogue.base import Dialogue as BaseDialogue
from aea.protocols.dialogue.base import DialogueLabel

from packages.valory.protocols.tendermint.custom_types import ErrorCode
from packages.valory.protocols.tendermint.dialogues import (
    TendermintDialogue,
    TendermintDialogues,
)
from packages.valory.protocols.tendermint.message import (
    TendermintMessage,
    _default_logger,
)


@pytest.mark.parametrize(
    "msg",
    [
        TendermintMessage(
            performative=TendermintMessage.Performative.GET_GENESIS_INFO,  # type: ignore
            query="",
        ),
        TendermintMessage(
            performative=TendermintMessage.Performative.GET_RECOVERY_PARAMS,  # type: ignore
            query="",
        ),
        TendermintMessage(
            performative=TendermintMessage.Performative.GENESIS_INFO,  # type: ignore
            info="",
        ),
        TendermintMessage(
            performative=TendermintMessage.Performative.RECOVERY_PARAMS,  # type: ignore
            params="",
        ),
        TendermintMessage(
            performative=TendermintMessage.Performative.ERROR,  # type: ignore
            error_code=ErrorCode.INVALID_REQUEST,
            error_msg="",
            error_data=dict(message="dummy"),
        ),
    ],
)
def test_serialization(msg: TendermintMessage) -> None:
    """Test the serialization of Tendermint speech-act messages."""

    msg.to = "receiver"
    envelope = Envelope(
        to=msg.to,
        sender="sender",
        message=msg,
    )
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

    actual_msg = TendermintMessage.serializer.decode(actual_envelope.message)
    actual_msg.to = actual_envelope.to
    actual_msg.sender = actual_envelope.sender
    expected_msg = msg
    assert expected_msg == actual_msg


def test_incorrect_error_data_logged(caplog: LogCaptureFixture) -> None:
    """Test incorrect error_data is logged"""

    expected = "Invalid type for dictionary values in content 'error_data'. Expected 'str'. Found '<class 'int'>'."
    with caplog.at_level(logging.ERROR, logger=_default_logger.name):
        TendermintMessage(
            performative=TendermintMessage.Performative.ERROR,  # type: ignore
            error_code=ErrorCode.INVALID_REQUEST,
            error_msg="",
            error_data=dict(message=1),  # incorrect type
        )
        assert expected in caplog.text


def test_serialization_performative_not_valid() -> None:
    """Test serialization performative not valid"""

    msg = TendermintMessage(
        performative=TendermintMessage.Performative.GET_GENESIS_INFO,  # type: ignore
        query="",
    )
    encoded_msg = msg.encode()

    with mock.patch.object(TendermintMessage, "Performative"):
        with pytest.raises(ValueError, match="Performative not valid: "):
            msg.encode()
        with pytest.raises(ValueError, match="Performative not valid: "):
            msg.decode(encoded_msg)


class AgentDialogue(TendermintDialogue):
    """The dialogue class maintains state of a dialogue and manages it."""

    def __init__(
        self,
        dialogue_label: DialogueLabel,
        self_address: Address,
        role: BaseDialogue.Role,
        message_class: Type[TendermintMessage],
    ) -> None:
        """
        Initialize a dialogue.

        :param dialogue_label: the identifier of the dialogue
        :param self_address: the address of the entity for whom this dialogue is maintained
        :param role: the role of the agent this dialogue is maintained for
        :param message_class: the message class
        """
        TendermintDialogue.__init__(
            self,
            dialogue_label=dialogue_label,
            self_address=self_address,
            role=role,
            message_class=message_class,
        )


class AgentDialogues(TendermintDialogues):
    """The dialogues class keeps track of all dialogues."""

    def __init__(self, self_address: Address) -> None:
        """
        Initialize dialogues.

        :param self_address: the address of the entity for whom this dialogue is maintained
        """

        def role_from_first_message(  # pylint: disable=unused-argument
            message: Message,  # pylint: disable=redefined-outer-name
            receiver_address: Address,
        ) -> BaseDialogue.Role:
            """Infer the role of the agent from an incoming/outgoing first message

            :param message: an incoming/outgoing first message
            :param receiver_address: the address of the receiving agent
            :return: The role of the agent
            """
            return TendermintDialogue.Role.AGENT

        TendermintDialogues.__init__(
            self,
            self_address=self_address,
            role_from_first_message=role_from_first_message,
            dialogue_class=AgentDialogue,
        )


class TestDialogues:
    """Tests abci dialogues."""

    agent_dialogues: AgentDialogues

    @classmethod
    def setup_class(cls) -> None:
        """Setup test class"""

        cls.agent_dialogues = AgentDialogues("agent_address")

    def test_create_self_initiated(self) -> None:
        """Test the self initialisation of a dialogue."""

        result = self.agent_dialogues._create_self_initiated(  # pylint: disable=protected-access
            dialogue_opponent_addr="dummy_address",
            dialogue_reference=(str(0), ""),
            role=TendermintDialogue.Role.AGENT,
        )
        assert isinstance(result, TendermintDialogue)
        assert result.role == TendermintDialogue.Role.AGENT, "The role must be agent."

    def test_create_opponent_initiated(self) -> None:
        """Test the opponent initialisation of a dialogue."""

        result = self.agent_dialogues._create_opponent_initiated(  # pylint: disable=protected-access
            dialogue_opponent_addr="dummy_address",
            dialogue_reference=(str(0), ""),
            role=TendermintDialogue.Role.AGENT,
        )
        assert isinstance(result, TendermintDialogue)
        assert result.role == TendermintDialogue.Role.AGENT, "The role must be agent."
