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

"""Test the handlers.py module of the skill."""

import json
import logging
from typing import Any, cast
from unittest import mock
from unittest.mock import MagicMock

import pytest
from _pytest.logging import LogCaptureFixture
from aea.configurations.data_types import PublicId
from aea.protocols.base import Message

from packages.valory.protocols.abci import AbciMessage
from packages.valory.protocols.abci.custom_types import (
    CheckTxType,
    CheckTxTypeEnum,
    ValidatorUpdates,
)
from packages.valory.protocols.http import HttpMessage
from packages.valory.protocols.tendermint import TendermintMessage
from packages.valory.skills.abstract_round_abci.base import (
    ABCIAppInternalError,
    AddBlockError,
    ERROR_CODE,
    OK_CODE,
    SignatureNotValidError,
)
from packages.valory.skills.abstract_round_abci.dialogues import (
    AbciDialogue,
    AbciDialogues,
    TendermintDialogue,
    TendermintDialogues,
)
from packages.valory.skills.abstract_round_abci.handlers import (
    ABCIRoundHandler,
    AbstractResponseHandler,
    TendermintHandler,
    exception_to_info_msg,
)


def test_exception_to_info_msg() -> None:
    """Test 'exception_to_info_msg' helper function."""
    exception = Exception("exception message")
    expected_string = f"{exception.__class__.__name__}: {str(exception)}"
    actual_string = exception_to_info_msg(exception)
    assert expected_string == actual_string


class TestABCIRoundHandler:
    """Test 'ABCIRoundHandler'."""

    def setup(self) -> None:
        """Set up the tests."""
        self.context = MagicMock(skill_id=PublicId.from_str("dummy/skill:0.1.0"))
        self.dialogues = AbciDialogues(name="", skill_context=self.context)
        self.handler = ABCIRoundHandler(name="", skill_context=self.context)

    def test_info(self) -> None:
        """Test the 'info' handler method."""
        message, dialogue = self.dialogues.create(
            counterparty="",
            performative=AbciMessage.Performative.REQUEST_INFO,
            version="",
            block_version=0,
            p2p_version=0,
        )
        response = self.handler.info(
            cast(AbciMessage, message), cast(AbciDialogue, dialogue)
        )
        assert response.performative == AbciMessage.Performative.RESPONSE_INFO

    @pytest.mark.parametrize("app_hash", (b"", b"test"))
    def test_init_chain(self, app_hash: bytes) -> None:
        """Test the 'init_chain' handler method."""
        message, dialogue = self.dialogues.create(
            counterparty="",
            performative=AbciMessage.Performative.REQUEST_INIT_CHAIN,
            time=MagicMock,
            chain_id="test_chain_id",
            consensus_params=MagicMock(),
            validators=MagicMock(),
            app_state_bytes=b"",
            initial_height=10,
        )
        self.context.state.round_sequence.last_round_transition_root_hash = app_hash
        response = self.handler.init_chain(
            cast(AbciMessage, message), cast(AbciDialogue, dialogue)
        )
        assert response.performative == AbciMessage.Performative.RESPONSE_INIT_CHAIN
        assert response.validators == ValidatorUpdates([])
        assert response.app_hash == app_hash

    def test_begin_block(self) -> None:
        """Test the 'begin_block' handler method."""
        message, dialogue = self.dialogues.create(
            counterparty="",
            performative=AbciMessage.Performative.REQUEST_BEGIN_BLOCK,
            hash=b"",
            header=MagicMock(),
            last_commit_info=MagicMock(),
            byzantine_validators=MagicMock(),
        )
        response = self.handler.begin_block(
            cast(AbciMessage, message), cast(AbciDialogue, dialogue)
        )
        assert response.performative == AbciMessage.Performative.RESPONSE_BEGIN_BLOCK

    @mock.patch("packages.valory.skills.abstract_round_abci.handlers.Transaction")
    def test_check_tx(self, *_: Any) -> None:
        """Test the 'check_tx' handler method."""
        message, dialogue = self.dialogues.create(
            counterparty="",
            performative=AbciMessage.Performative.REQUEST_CHECK_TX,
            tx=b"",
            type=CheckTxType(CheckTxTypeEnum.NEW),
        )
        response = self.handler.check_tx(
            cast(AbciMessage, message), cast(AbciDialogue, dialogue)
        )
        assert response.performative == AbciMessage.Performative.RESPONSE_CHECK_TX
        assert response.code == OK_CODE

    @mock.patch(
        "packages.valory.skills.abstract_round_abci.handlers.Transaction.decode",
        side_effect=SignatureNotValidError,
    )
    def test_check_tx_negative(self, *_: Any) -> None:
        """Test the 'check_tx' handler method, negative case."""
        message, dialogue = self.dialogues.create(
            counterparty="",
            performative=AbciMessage.Performative.REQUEST_CHECK_TX,
            tx=b"",
            type=CheckTxType(CheckTxTypeEnum.NEW),
        )
        response = self.handler.check_tx(
            cast(AbciMessage, message), cast(AbciDialogue, dialogue)
        )
        assert response.performative == AbciMessage.Performative.RESPONSE_CHECK_TX
        assert response.code == ERROR_CODE

    @mock.patch("packages.valory.skills.abstract_round_abci.handlers.Transaction")
    def test_deliver_tx(self, *_: Any) -> None:
        """Test the 'deliver_tx' handler method."""
        message, dialogue = self.dialogues.create(
            counterparty="",
            performative=AbciMessage.Performative.REQUEST_DELIVER_TX,
            tx=b"",
        )
        response = self.handler.deliver_tx(
            cast(AbciMessage, message), cast(AbciDialogue, dialogue)
        )
        assert response.performative == AbciMessage.Performative.RESPONSE_DELIVER_TX
        assert response.code == OK_CODE

    @mock.patch(
        "packages.valory.skills.abstract_round_abci.handlers.Transaction.decode",
        side_effect=SignatureNotValidError,
    )
    def test_deliver_tx_negative(self, *_: Any) -> None:
        """Test the 'deliver_tx' handler method, negative case."""
        message, dialogue = self.dialogues.create(
            counterparty="",
            performative=AbciMessage.Performative.REQUEST_DELIVER_TX,
            tx=b"",
        )
        response = self.handler.deliver_tx(
            cast(AbciMessage, message), cast(AbciDialogue, dialogue)
        )
        assert response.performative == AbciMessage.Performative.RESPONSE_DELIVER_TX
        assert response.code == ERROR_CODE

    @pytest.mark.parametrize("request_height", tuple(range(3)))
    def test_end_block(self, request_height: int) -> None:
        """Test the 'end_block' handler method."""
        message, dialogue = self.dialogues.create(
            counterparty="",
            performative=AbciMessage.Performative.REQUEST_END_BLOCK,
            height=request_height,
        )
        assert isinstance(message, AbciMessage)
        assert isinstance(dialogue, AbciDialogue)
        assert message.height == request_height
        assert self.context.state.round_sequence.tm_height != request_height
        response = self.handler.end_block(message, dialogue)
        assert response.performative == AbciMessage.Performative.RESPONSE_END_BLOCK
        assert self.context.state.round_sequence.tm_height == request_height

    def test_commit(self) -> None:
        """Test the 'commit' handler method."""
        message, dialogue = self.dialogues.create(
            counterparty="",
            performative=AbciMessage.Performative.REQUEST_COMMIT,
        )
        response = self.handler.commit(
            cast(AbciMessage, message), cast(AbciDialogue, dialogue)
        )
        assert response.performative == AbciMessage.Performative.RESPONSE_COMMIT

    def test_commit_negative(self) -> None:
        """Test the 'commit' handler method, negative case."""
        self.context.state.round_sequence.commit.side_effect = AddBlockError()
        message, dialogue = self.dialogues.create(
            counterparty="",
            performative=AbciMessage.Performative.REQUEST_COMMIT,
        )
        with pytest.raises(AddBlockError):
            self.handler.commit(
                cast(AbciMessage, message), cast(AbciDialogue, dialogue)
            )


class ConcreteResponseHandler(AbstractResponseHandler):
    """A concrete response handler for testing purposes."""

    SUPPORTED_PROTOCOL = HttpMessage.protocol_id
    allowed_response_performatives = frozenset({HttpMessage.Performative.RESPONSE})


class TestAbstractResponseHandler:
    """Test 'AbstractResponseHandler'."""

    def setup(self) -> None:
        """Set up the tests."""
        self.context = MagicMock()
        self.handler = ConcreteResponseHandler(name="", skill_context=self.context)

    def test_handle(self) -> None:
        """Test the 'handle' method."""
        callback = MagicMock()
        request_reference = "reference"
        self.context.requests.request_id_to_callback = {}
        self.context.requests.request_id_to_callback[request_reference] = callback
        with mock.patch.object(
            self.handler, "_recover_protocol_dialogues"
        ) as mock_dialogues_fn:
            mock_dialogue = MagicMock()
            mock_dialogue.dialogue_label.dialogue_reference = (request_reference, "")
            mock_dialogues = MagicMock()
            mock_dialogues.update = MagicMock(return_value=mock_dialogue)
            mock_dialogues_fn.return_value = mock_dialogues
            mock_message = MagicMock(performative=HttpMessage.Performative.RESPONSE)
            self.handler.handle(mock_message)
        callback.assert_called()

    @mock.patch.object(
        AbstractResponseHandler, "_recover_protocol_dialogues", return_value=None
    )
    def test_handle_negative_cannot_recover_dialogues(self, *_: Any) -> None:
        """Test the 'handle' method, negative case (cannot recover dialogues)."""
        self.handler.handle(MagicMock())

    @mock.patch.object(AbstractResponseHandler, "_recover_protocol_dialogues")
    def test_handle_negative_cannot_update_dialogues(
        self, mock_dialogues_fn: Any
    ) -> None:
        """Test the 'handle' method, negative case (cannot update dialogues)."""
        mock_dialogues = MagicMock(update=MagicMock(return_value=None))
        mock_dialogues_fn.return_value = mock_dialogues
        self.handler.handle(MagicMock())

    def test_handle_negative_performative_not_allowed(self) -> None:
        """Test the 'handle' method, negative case (performative not allowed)."""
        self.handler.handle(MagicMock())

    def test_handle_negative_cannot_find_callback(self) -> None:
        """Test the 'handle' method, negative case (cannot find callback)."""
        self.context.requests.request_id_to_callback = {}
        with pytest.raises(
            ABCIAppInternalError, match="No callback defined for request with nonce: "
        ):
            self.handler.handle(
                MagicMock(performative=HttpMessage.Performative.RESPONSE)
            )


class TestTendermintHandler:
    """Test Tendermint Handler"""

    def setup(self) -> None:
        """Set up the tests."""
        self.context = MagicMock(skill_id=PublicId.from_str("dummy/skill:0.1.0"))
        self.handler = TendermintHandler(name="dummy", skill_context=self.context)
        self.handler.context.logger = logging.getLogger()
        self.dialogues = TendermintDialogues(name="dummy", skill_context=self.context)

    def test_handle_unidentified_tendermint_dialogue(
        self, caplog: LogCaptureFixture
    ) -> None:
        """Test unidentified tendermint dialogue"""
        message = Message()
        with mock.patch.object(self.handler.dialogues, "update", return_value=None):
            self.handler.handle(message)
            assert "Unidentified Tendermint dialogue: " in caplog.text

    def test_handle_request(self, caplog: LogCaptureFixture) -> None:
        """Test handle request"""
        performative = TendermintMessage.Performative.REQUEST
        message = TendermintMessage(performative)  # type: ignore
        message.sender = "Alice"
        tendermint_address = "http://0.0.0.0:25567"
        registered_addresses = {message.sender: tendermint_address}
        initial_data = {"registered_addresses": registered_addresses}
        self.handler.synchronized_data.db.initial_data = initial_data  # type: ignore
        self.context.agent_address = message.sender
        self.handler.handle(message)
        assert "Sending Tendermint request response: " in caplog.text

    def test_handle_request_no_registered_addresses(
        self, caplog: LogCaptureFixture
    ) -> None:
        """Test handle request no registered addresses"""
        performative = TendermintMessage.Performative.REQUEST
        message = TendermintMessage(performative)  # type: ignore
        message.sender = "Alice"
        self.handler.synchronized_data.db.initial_data = {}  # type: ignore
        self.handler.handle(message)
        error_msg = "No registered addresses retrieved yet"
        assert f"Invalid request, {error_msg}: {message}" in caplog.text

    def test_handle_request_sender_not_in_registered_addresses(
        self, caplog: LogCaptureFixture
    ) -> None:
        """Test handle request sender not in registered addresses"""
        performative = TendermintMessage.Performative.REQUEST
        message = TendermintMessage(performative)  # type: ignore
        message.sender = "Alice"
        self.handler.handle(message)
        error_msg = "Sender not registered for on-chain service"
        assert f"Invalid request, {error_msg}: {message}" in caplog.text

    def test_handle_response_sender_not_in_registered_addresses(
        self, caplog: LogCaptureFixture
    ) -> None:
        """Test handle response sender not in registered addresses"""
        performative = TendermintMessage.Performative.RESPONSE
        message = TendermintMessage(performative, info="info")  # type: ignore
        message.sender = "Alice"
        self.handler.synchronized_data.db.initial_data = {}  # type: ignore
        self.handler.handle(message)
        error_msg = "Response from agent not registered on-chain"
        assert f"Invalid response: {error_msg}\n{message}" in caplog.text

    def test_handle_response_valid_addresses(self, caplog: LogCaptureFixture) -> None:
        """Test handle response valid address"""
        performative = TendermintMessage.Performative.RESPONSE
        info = json.dumps({"tendermint_url": "http://0.0.0.0:25567"})
        message = TendermintMessage(performative, info=info)  # type: ignore
        message.sender = "Alice"
        initial_data = {"registered_addresses": {message.sender: None}}
        self.handler.synchronized_data.db.initial_data = initial_data  # type: ignore
        self.handler.handle(message)
        assert f"Collected Tendermint config info: {message}" in caplog.text

    def test_handle_response_invalid_addresses(self, caplog: LogCaptureFixture) -> None:
        """Test handle response invalid address"""
        performative = TendermintMessage.Performative.RESPONSE
        info = "sudo rm -rf /"
        message = TendermintMessage(performative, info=info)  # type: ignore
        message.sender = "Alice"
        initial_data = {"registered_addresses": {message.sender: None}}
        self.handler.synchronized_data.db.initial_data = initial_data  # type: ignore
        self.handler.handle(message)
        assert "Failed to parse Tendermint address: " in caplog.text

    def make_error_message(self) -> TendermintMessage:
        """Make dummy error message"""
        performative = TendermintMessage.Performative.ERROR
        error_code = TendermintMessage.ErrorCode.INVALID_REQUEST
        error_msg, error_data = "", {}  # type: ignore
        message = TendermintMessage(
            performative,  # type: ignore
            error_code=error_code,
            error_msg=error_msg,
            error_data=error_data,
        )
        message.sender = "Alice"
        return message

    def test_handle_error(self, caplog: LogCaptureFixture) -> None:
        """Test handle error"""
        message = self.make_error_message()
        self.handler.handle(message)
        assert "Received error response." in caplog.text

    def test_handle_performative_not_recognized(
        self, caplog: LogCaptureFixture
    ) -> None:
        """Test performative no recognized"""
        message = self.make_error_message()
        message._slots.performative = "wacky"
        self.handler.handle(message)
        assert f"Performative not recognized: {message}" in caplog.text

    def test_handle_error_no_target_message_retrieved(
        self, caplog: LogCaptureFixture
    ) -> None:
        """Test handle error no target message retrieved"""
        message = self.make_error_message()
        nonce = "0"
        dialogue = TendermintDialogue(mock.Mock(), "Bob", mock.Mock())
        dialogue.dialogue_label.dialogue_reference = nonce, "stub"
        self.handler.dialogues.update = lambda _: dialogue  # type: ignore
        callback = lambda *args, **kwargs: None  # noqa: E731
        self.context.requests.request_id_to_callback = {nonce: callback}
        self.handler.handle(message)
        assert (
            "Received error message but could not retrieve target message"
            in caplog.text
        )
