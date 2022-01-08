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
import logging
from pathlib import Path
from typing import Any, cast
from unittest.mock import MagicMock, patch

from aea.configurations.data_types import PublicId
from aea.protocols.base import Address, Message
from aea.protocols.dialogue.base import Dialogue as BaseDialogue
from aea.test_tools.test_skill import BaseSkillTestCase

from packages.valory.protocols.abci import AbciMessage
from packages.valory.protocols.abci.custom_types import (
    CheckTxType,
    CheckTxTypeEnum,
    PublicKey,
    Result,
    ResultType,
    SnapShots,
    Snapshot,
    Timestamp,
    ValidatorUpdate,
    ValidatorUpdates,
)
from packages.valory.protocols.abci.dialogues import AbciDialogues as BaseAbciDialogues
from packages.valory.skills.abstract_abci.dialogues import AbciDialogue, AbciDialogues
from packages.valory.skills.abstract_abci.handlers import ABCIHandler, ERROR_CODE

from tests.conftest import ROOT_DIR


class AbciDialoguesServer(BaseAbciDialogues):
    """The dialogues class keeps track of all ABCI dialogues."""

    def __init__(self, address: str) -> None:
        """Initialize dialogues."""
        self.address = address

        def role_from_first_message(  # pylint: disable=unused-argument
            message: Message, receiver_address: Address
        ) -> BaseDialogue.Role:
            """Infer the role of the agent from an incoming/outgoing first message

            :param message: an incoming/outgoing first message
            :param receiver_address: the address of the receiving agent
            :return: The role of the agent
            """
            return AbciDialogue.Role.SERVER

        BaseAbciDialogues.__init__(
            self,
            self_address=self.address,
            role_from_first_message=role_from_first_message,
            dialogue_class=AbciDialogue,
        )


class TestABCIHandlerOld(BaseSkillTestCase):
    """Test ABCIHandler methods."""

    path_to_skill = Path(ROOT_DIR, "packages", "valory", "skills", "abstract_abci")
    abci_handler: ABCIHandler
    logger: logging.Logger
    abci_dialogues: AbciDialogues

    @classmethod
    def setup(cls, **kwargs: Any) -> None:
        """Setup the test class."""
        super().setup()
        cls.abci_handler = cast(ABCIHandler, cls._skill.skill_context.handlers.abci)
        cls.logger = cls._skill.skill_context.logger

        cls.abci_dialogues = cast(
            AbciDialogues, cls._skill.skill_context.abci_dialogues
        )

    def test_setup(self) -> None:
        """Test the setup method of the echo handler."""
        with patch.object(self.logger, "log") as mock_logger:
            self.abci_handler.setup()

        # after
        self.assert_quantity_in_outbox(0)

        mock_logger.assert_any_call(logging.DEBUG, "ABCI Handler: setup method called.")

    def test_teardown(self) -> None:
        """Test the teardown method of the echo handler."""
        with patch.object(self.logger, "log") as mock_logger:
            self.abci_handler.teardown()

        # after
        self.assert_quantity_in_outbox(0)

        mock_logger.assert_any_call(
            logging.DEBUG, "ABCI Handler: teardown method called."
        )


class TestABCIHandler:
    """Test 'ABCIHandler'."""

    def setup(self) -> None:
        """Set up the tests."""
        self.skill_id = PublicId.from_str("dummy/skill:0.1.0")
        self.context = MagicMock(skill_id=self.skill_id)
        self.context.abci_dialogues = AbciDialogues(name="", skill_context=self.context)
        self.dialogues = AbciDialoguesServer(address="server")
        self.handler = ABCIHandler(name="", skill_context=self.context)

    def test_setup(self) -> None:
        """Test the setup method."""
        self.handler.setup()

    def test_teardown(self) -> None:
        """Test the teardown method."""
        self.handler.teardown()

    def test_handle(self) -> None:
        """Test the message gets handled."""
        message, _ = self.dialogues.create(
            counterparty=str(self.skill_id),
            performative=AbciMessage.Performative.REQUEST_INFO,
            version="",
            block_version=0,
            p2p_version=0,
        )
        self.handler.handle(cast(AbciMessage, message))

    def test_handle_log_exception(self) -> None:
        """Test the message gets handled."""
        message = AbciMessage(
            dialogue_reference=("", ""),
            performative=AbciMessage.Performative.REQUEST_INFO,  # type: ignore
            version="",
            block_version=0,
            p2p_version=0,
            target=0,
            message_id=1,
        )
        message._sender = "server"
        message._to = str(self.skill_id)
        self.handler.handle(message)

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

    def test_echo(self) -> None:
        """Test the 'echo' handler method."""
        expected_message = "message"
        message, dialogue = self.dialogues.create(
            counterparty="",
            performative=AbciMessage.Performative.REQUEST_ECHO,
            message=expected_message,
        )
        response = self.handler.echo(
            cast(AbciMessage, message), cast(AbciDialogue, dialogue)
        )
        assert response.performative == AbciMessage.Performative.RESPONSE_ECHO
        assert response.message == expected_message

    def test_set_option(self) -> None:
        """Test the 'set_option' handler method."""
        message, dialogue = self.dialogues.create(
            counterparty="",
            performative=AbciMessage.Performative.REQUEST_SET_OPTION,
        )
        response = self.handler.set_option(
            cast(AbciMessage, message), cast(AbciDialogue, dialogue)
        )
        assert response.performative == AbciMessage.Performative.RESPONSE_SET_OPTION
        assert response.code == ERROR_CODE

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
        assert response.code == ERROR_CODE

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
        assert response.code == ERROR_CODE

    def test_end_block(self) -> None:
        """Test the 'end_block' handler method."""
        message, dialogue = self.dialogues.create(
            counterparty="",
            performative=AbciMessage.Performative.REQUEST_END_BLOCK,
            height=1,
        )
        response = self.handler.end_block(
            cast(AbciMessage, message), cast(AbciDialogue, dialogue)
        )
        assert response.performative == AbciMessage.Performative.RESPONSE_END_BLOCK

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

    def test_flush(self) -> None:
        """Test the 'flush' handler method."""
        message, dialogue = self.dialogues.create(
            counterparty="",
            performative=AbciMessage.Performative.REQUEST_FLUSH,
        )
        response = self.handler.flush(
            cast(AbciMessage, message), cast(AbciDialogue, dialogue)
        )
        assert response.performative == AbciMessage.Performative.RESPONSE_FLUSH

    def test_init_chain(self) -> None:
        """Test the 'init_chain' handler method."""
        message, dialogue = self.dialogues.create(
            counterparty="",
            performative=AbciMessage.Performative.REQUEST_INIT_CHAIN,
            time=Timestamp(1, 1),
            chain_id="",
            validators=ValidatorUpdates(
                [
                    ValidatorUpdate(
                        PublicKey(data=b"", key_type=PublicKey.PublicKeyType.ed25519), 1
                    )
                ]
            ),
            app_state_bytes=b"",
            initial_height=0,
        )
        response = self.handler.init_chain(
            cast(AbciMessage, message), cast(AbciDialogue, dialogue)
        )
        assert response.performative == AbciMessage.Performative.RESPONSE_INIT_CHAIN

    def test_query(self) -> None:
        """Test the 'init_chain' handler method."""
        message, dialogue = self.dialogues.create(
            counterparty="",
            performative=AbciMessage.Performative.REQUEST_QUERY,
            query_data=b"",
            path="",
            height=0,
            prove=True,
        )
        response = self.handler.query(
            cast(AbciMessage, message), cast(AbciDialogue, dialogue)
        )
        assert response.performative == AbciMessage.Performative.RESPONSE_QUERY
        assert response.code == ERROR_CODE

    def test_list_snapshots(self) -> None:
        """Test the 'list_snapshots' handler method."""
        message, dialogue = self.dialogues.create(
            counterparty="",
            performative=AbciMessage.Performative.REQUEST_LIST_SNAPSHOTS,
        )
        response = self.handler.list_snapshots(
            cast(AbciMessage, message), cast(AbciDialogue, dialogue)
        )
        assert response.performative == AbciMessage.Performative.RESPONSE_LIST_SNAPSHOTS
        assert response.snapshots == SnapShots([])

    def test_offer_snapshot(self) -> None:
        """Test the 'offer_snapshot' handler method."""
        message, dialogue = self.dialogues.create(
            counterparty="",
            performative=AbciMessage.Performative.REQUEST_OFFER_SNAPSHOT,
            snapshot=Snapshot(0, 0, 0, b"", b""),
            app_hash=b"",
        )
        response = self.handler.offer_snapshot(
            cast(AbciMessage, message), cast(AbciDialogue, dialogue)
        )
        assert response.performative == AbciMessage.Performative.RESPONSE_OFFER_SNAPSHOT
        assert response.result == Result(ResultType.REJECT)

    def test_load_snapshot_chunk(self) -> None:
        """Test the 'load_snapshot_chunk' handler method."""
        message, dialogue = self.dialogues.create(
            counterparty="",
            performative=AbciMessage.Performative.REQUEST_LOAD_SNAPSHOT_CHUNK,
            height=0,
            format=0,
            chunk_index=0,
        )
        response = self.handler.load_snapshot_chunk(
            cast(AbciMessage, message), cast(AbciDialogue, dialogue)
        )
        assert (
            response.performative
            == AbciMessage.Performative.RESPONSE_LOAD_SNAPSHOT_CHUNK
        )
        assert response.chunk == b""

    def test_apply_snapshot_chunk(self) -> None:
        """Test the 'apply_snapshot_chunk' handler method."""
        message, dialogue = self.dialogues.create(
            counterparty="",
            performative=AbciMessage.Performative.REQUEST_APPLY_SNAPSHOT_CHUNK,
            index=0,
            chunk=b"",
            chunk_sender="",
        )
        response = self.handler.apply_snapshot_chunk(
            cast(AbciMessage, message), cast(AbciDialogue, dialogue)
        )
        assert (
            response.performative
            == AbciMessage.Performative.RESPONSE_APPLY_SNAPSHOT_CHUNK
        )
        assert response.result == Result(ResultType.REJECT)
        assert response.refetch_chunks == []
        assert response.reject_senders == []
