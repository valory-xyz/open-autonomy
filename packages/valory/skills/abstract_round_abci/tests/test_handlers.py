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

"""Test the handlers.py module of the skill."""

# pylint: skip-file

import json
import logging
from dataclasses import asdict
from datetime import datetime
from typing import Any, Dict, cast
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
    ConsensusParams,
    Evidences,
    Header,
    LastCommitInfo,
    Timestamp,
    ValidatorUpdates,
)
from packages.valory.protocols.http import HttpMessage
from packages.valory.protocols.tendermint import TendermintMessage
from packages.valory.skills.abstract_round_abci import handlers
from packages.valory.skills.abstract_round_abci.base import (
    ABCIAppInternalError,
    AddBlockError,
    ERROR_CODE,
    OK_CODE,
    SignatureNotValidError,
    TransactionNotValidError,
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
    Transaction,
    exception_to_info_msg,
)
from packages.valory.skills.abstract_round_abci.models import TendermintRecoveryParams
from packages.valory.skills.abstract_round_abci.test_tools.rounds import DummyRound


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
        self.context.state.round_sequence.height = 0
        self.context.state.round_sequence.root_hash = b"root_hash"
        self.context.state.round_sequence.last_round_transition_timestamp = (
            datetime.now()
        )

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
        time = Timestamp(0, 0)
        consensus_params = ConsensusParams(*(mock.MagicMock() for _ in range(4)))
        validators = ValidatorUpdates(mock.MagicMock())
        message, dialogue = self.dialogues.create(
            counterparty="",
            performative=AbciMessage.Performative.REQUEST_INIT_CHAIN,
            time=time,
            chain_id="test_chain_id",
            consensus_params=consensus_params,
            validators=validators,
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
        header = Header(*(MagicMock() for _ in range(14)))
        last_commit_info = LastCommitInfo(*(MagicMock() for _ in range(2)))
        byzantine_validators = Evidences(MagicMock())
        message, dialogue = self.dialogues.create(
            counterparty="",
            performative=AbciMessage.Performative.REQUEST_BEGIN_BLOCK,
            hash=b"",
            header=header,
            last_commit_info=last_commit_info,
            byzantine_validators=byzantine_validators,
        )
        response = self.handler.begin_block(
            cast(AbciMessage, message), cast(AbciDialogue, dialogue)
        )
        assert response.performative == AbciMessage.Performative.RESPONSE_BEGIN_BLOCK

    @mock.patch.object(handlers, "Transaction")
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

    @mock.patch.object(
        Transaction,
        "decode",
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

    @mock.patch.object(handlers, "Transaction")
    def test_deliver_tx(self, *_: Any) -> None:
        """Test the 'deliver_tx' handler method."""
        message, dialogue = self.dialogues.create(
            counterparty="",
            performative=AbciMessage.Performative.REQUEST_DELIVER_TX,
            tx=b"",
        )
        with mock.patch.object(
            self.context.state.round_sequence, "add_pending_offence"
        ) as mock_add_pending_offence:
            response = self.handler.deliver_tx(
                cast(AbciMessage, message), cast(AbciDialogue, dialogue)
            )
            mock_add_pending_offence.assert_called_once()

        assert response.performative == AbciMessage.Performative.RESPONSE_DELIVER_TX
        assert response.code == OK_CODE

    @mock.patch.object(
        Transaction,
        "decode",
        side_effect=SignatureNotValidError,
    )
    def test_deliver_tx_negative(self, *_: Any) -> None:
        """Test the 'deliver_tx' handler method, negative case."""
        message, dialogue = self.dialogues.create(
            counterparty="",
            performative=AbciMessage.Performative.REQUEST_DELIVER_TX,
            tx=b"",
        )
        with mock.patch.object(
            self.context.state.round_sequence, "add_pending_offence"
        ) as mock_add_pending_offence:
            response = self.handler.deliver_tx(
                cast(AbciMessage, message), cast(AbciDialogue, dialogue)
            )
            mock_add_pending_offence.assert_not_called()

        assert response.performative == AbciMessage.Performative.RESPONSE_DELIVER_TX
        assert response.code == ERROR_CODE

    @mock.patch.object(handlers, "Transaction")
    def test_deliver_bad_tx(self, *_: Any) -> None:
        """Test the 'deliver_tx' handler method, when the transaction is not ok."""
        message, dialogue = self.dialogues.create(
            counterparty="",
            performative=AbciMessage.Performative.REQUEST_DELIVER_TX,
            tx=b"",
        )
        with mock.patch.object(
            self.context.state.round_sequence,
            "check_is_finished",
            side_effect=TransactionNotValidError,
        ), mock.patch.object(
            self.context.state.round_sequence, "add_pending_offence"
        ) as mock_add_pending_offence:
            response = self.handler.deliver_tx(
                cast(AbciMessage, message), cast(AbciDialogue, dialogue)
            )
            mock_add_pending_offence.assert_called_once()

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
        self.agent_name = "Alice"
        self.context = MagicMock(skill_id=PublicId.from_str("dummy/skill:0.1.0"))
        other_agents = ["Alice", "Bob", "Charlie"]
        self.context.state = MagicMock(acn_container=lambda: other_agents)
        self.handler = TendermintHandler(name="dummy", skill_context=self.context)
        self.handler.context.logger = logging.getLogger()
        self.dialogues = TendermintDialogues(name="dummy", skill_context=self.context)

    @property
    def dummy_validator_config(self) -> Dict[str, Dict[str, str]]:
        """Dummy validator config"""
        return {
            self.agent_name: {
                "hostname": "localhost",
                "address": "address",
                "pub_key": "pub_key",
                "peer_id": "peer_id",
            }
        }

    @staticmethod
    def make_error_message() -> TendermintMessage:
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

    # pre-condition checks
    def test_handle_unidentified_tendermint_dialogue(
        self, caplog: LogCaptureFixture
    ) -> None:
        """Test unidentified tendermint dialogue"""
        message = Message()
        with mock.patch.object(self.handler.dialogues, "update", return_value=None):
            self.handler.handle(message)
            log_message = self.handler.LogMessages.unidentified_dialogue.value
            assert log_message in caplog.text

    def test_handle_no_addresses_retrieved_yet(self, caplog: LogCaptureFixture) -> None:
        """Test handle request no registered addresses"""
        performative = TendermintMessage.Performative.GET_GENESIS_INFO
        message = TendermintMessage(performative)  # type: ignore
        message.sender = "Alice"
        self.handler.initial_tm_configs = {}
        self.handler.handle(message)
        log_message = self.handler.LogMessages.no_addresses_retrieved_yet.value
        assert log_message in caplog.text
        log_message = self.handler.LogMessages.sending_error_response.value
        assert log_message in caplog.text

    def test_handle_not_in_registered_addresses(
        self, caplog: LogCaptureFixture
    ) -> None:
        """Test handle response sender not in registered addresses"""
        performative = TendermintMessage.Performative.GENESIS_INFO
        message = TendermintMessage(performative, info="info")  # type: ignore
        message.sender = "NotAlice"
        self.handler.handle(message)
        log_message = self.handler.LogMessages.not_in_registered_addresses.value
        assert log_message in caplog.text

    # request
    def test_handle_get_genesis_info(self, caplog: LogCaptureFixture) -> None:
        """Test handle request for genesis info"""
        performative = TendermintMessage.Performative.GET_GENESIS_INFO
        message = TendermintMessage(performative)  # type: ignore
        self.context.agent_address = message.sender = self.agent_name
        self.handler.initial_tm_configs = self.dummy_validator_config
        self.handler.handle(message)
        log_message = self.handler.LogMessages.sending_request_response.value
        assert log_message in caplog.text

    # response
    def test_handle_response_invalid_addresses(self, caplog: LogCaptureFixture) -> None:
        """Test handle response for genesis info with invalid address."""
        validator_config = self.dummy_validator_config
        validator_config[self.agent_name]["hostname"] = "random"
        performative = TendermintMessage.Performative.GENESIS_INFO
        info = json.dumps(validator_config[self.agent_name])
        message = TendermintMessage(performative, info=info)  # type: ignore
        self.context.agent_address = message.sender = self.agent_name
        self.handler.initial_tm_configs = validator_config
        self.handler.handle(message)
        log_message = self.handler.LogMessages.failed_to_parse_address.value
        assert log_message in caplog.text

    def test_handle_genesis_info(self, caplog: LogCaptureFixture) -> None:
        """Test handle response for genesis info with valid address"""
        performative = TendermintMessage.Performative.GENESIS_INFO
        info = json.dumps(self.dummy_validator_config[self.agent_name])
        message = TendermintMessage(performative, info=info)  # type: ignore
        self.context.agent_address = message.sender = self.agent_name
        self.handler.initial_tm_configs = self.dummy_validator_config
        self.handler.handle(message)
        log_message = self.handler.LogMessages.collected_config_info.value
        assert log_message in caplog.text

    @pytest.mark.parametrize("registered", (True, False))
    @pytest.mark.parametrize(
        "performative",
        (
            TendermintMessage.Performative.RECOVERY_PARAMS,
            TendermintMessage.Performative.GET_RECOVERY_PARAMS,
        ),
    )
    def test_recovery_params(
        self,
        registered: bool,
        performative: TendermintMessage.Performative,
        caplog: LogCaptureFixture,
    ) -> None:
        """Test handle response for recovery parameters."""
        if not registered:
            self.agent_name = "not-registered"

        if performative == TendermintMessage.Performative.GET_RECOVERY_PARAMS:
            self.context.state.tm_recovery_params = TendermintRecoveryParams(
                "DummyRound"
            )
            message = TendermintMessage(performative)  # type: ignore
            log_message = self.handler.LogMessages.sending_request_response.value
        elif performative == TendermintMessage.Performative.RECOVERY_PARAMS:
            params = json.dumps(
                asdict(TendermintRecoveryParams(DummyRound.auto_round_id()))
            )
            message = TendermintMessage(performative, params=params)  # type: ignore
            log_message = self.handler.LogMessages.collected_params.value
        else:
            raise AssertionError(
                f"Invalid performative {performative} for `test_recovery_params`."
            )

        self.context.agent_address = message.sender = self.agent_name
        tm_configs = {self.agent_name: {"dummy": "value"}} if registered else {}

        self.handler.initial_tm_configs = tm_configs
        self.handler.handle(message)

        if not registered:
            log_message = self.handler.LogMessages.not_in_registered_addresses.value

        assert log_message in caplog.text

    @pytest.mark.parametrize(
        "side_effect, expected_exception",
        (
            (
                json.decoder.JSONDecodeError("", "", 0),
                ": line 1 column 1 (char 0)",
            ),
            (
                {"not a dict"},
                "argument after ** must be a mapping, not str",
            ),
        ),
    )
    def test_recovery_params_error(
        self,
        side_effect: Any,
        expected_exception: str,
        caplog: LogCaptureFixture,
    ) -> None:
        """Test handle response for recovery parameters."""
        message = TendermintMessage(
            TendermintMessage.Performative.RECOVERY_PARAMS, params=MagicMock()  # type: ignore
        )

        self.context.agent_address = message.sender = self.agent_name
        tm_configs = {self.agent_name: {"dummy": "value"}}
        self.handler.initial_tm_configs = tm_configs
        with mock.patch.object(json, "loads", side_effect=side_effect):
            self.handler.handle(message)

        log_message = self.handler.LogMessages.failed_to_parse_params.value
        assert log_message in caplog.text
        assert expected_exception in caplog.text

    # error
    def test_handle_error(self, caplog: LogCaptureFixture) -> None:
        """Test handle error"""
        message = self.make_error_message()
        self.handler.initial_tm_configs = self.dummy_validator_config
        self.handler.handle(message)
        log_message = self.handler.LogMessages.received_error_response.value
        assert log_message in caplog.text

    def test_handle_error_no_target_message_retrieved(
        self, caplog: LogCaptureFixture
    ) -> None:
        """Test handle error no target message retrieved"""
        message, nonce = self.make_error_message(), "0"
        dialogue = TendermintDialogue(mock.Mock(), "Bob", mock.Mock())
        dialogue.dialogue_label.dialogue_reference = nonce, "stub"
        self.handler.dialogues.update = lambda _: dialogue  # type: ignore
        callback = lambda *args, **kwargs: None  # noqa: E731
        self.context.requests.request_id_to_callback = {nonce: callback}
        self.handler.initial_tm_configs = self.dummy_validator_config
        self.handler.handle(message)
        log_message = (
            self.handler.LogMessages.received_error_without_target_message.value
        )
        assert log_message in caplog.text

    # performative
    def test_handle_performative_not_recognized(
        self, caplog: LogCaptureFixture
    ) -> None:
        """Test performative no recognized"""
        message = self.make_error_message()
        message._slots.performative = MagicMock(value="wacky")
        self.handler.initial_tm_configs = self.dummy_validator_config
        self.handler.handle(message)
        log_message = self.handler.LogMessages.performative_not_recognized.value
        assert log_message in caplog.text

    def test_sender_not_in_registered_addresses(
        self, caplog: LogCaptureFixture
    ) -> None:
        """Test sender not in registered addresses."""

        performative = TendermintMessage.Performative.GET_GENESIS_INFO
        message = TendermintMessage(performative)  # type: ignore
        self.context.agent_address = message.sender = "dummy"
        self.handler.initial_tm_configs = self.dummy_validator_config
        self.handler.handle(message)
        log_message = self.handler.LogMessages.not_in_registered_addresses.value
        assert log_message in caplog.text
