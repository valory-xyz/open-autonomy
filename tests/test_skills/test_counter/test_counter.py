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

"""Tests for valory/counter skill."""
import logging
import struct
from pathlib import Path
from typing import Any, Tuple, cast
from unittest.mock import patch

from aea.test_tools.test_skill import BaseSkillTestCase

from packages.valory.protocols.abci.custom_types import (
    CheckTxType,
    CheckTxTypeEnum,
    Events,
    ProofOps,
    ValidatorUpdates,
)
from packages.valory.protocols.abci.message import AbciMessage
from packages.valory.skills.counter.dialogues import AbciDialogue, AbciDialogues
from packages.valory.skills.counter.handlers import ABCICounterHandler

from tests.conftest import ROOT_DIR


OK_CODE = 0
ERROR_CODE = 1


class TestCounterHandler(BaseSkillTestCase):
    """Test ABCICounterHandler methods."""

    path_to_skill = Path(ROOT_DIR, "packages", "valory", "skills", "counter")
    abci_counter_handler: ABCICounterHandler
    logger: logging.Logger
    abci_dialogues: AbciDialogues

    @classmethod
    def setup(cls, **kwargs: Any) -> None:
        """Setup the test class."""
        super().setup()
        cls.abci_counter_handler = cast(
            ABCICounterHandler, cls._skill.skill_context.handlers.abci
        )
        cls.logger = cls._skill.skill_context.logger

        cls.abci_dialogues = cast(
            AbciDialogues, cls._skill.skill_context.abci_dialogues
        )

    def test_setup(self) -> None:
        """Test the setup method of the echo handler."""
        with patch.object(self.logger, "log") as mock_logger:
            self.abci_counter_handler.setup()
            mock_logger.assert_any_call(
                logging.DEBUG, "ABCI Handler: setup method called."
            )

        # after
        self.assert_quantity_in_outbox(0)

    def test_teardown(self) -> None:
        """Test the teardown method of the echo handler."""
        with patch.object(self.logger, "log") as mock_logger:
            self.abci_counter_handler.teardown()
            mock_logger.assert_any_call(
                logging.DEBUG, "ABCI Handler: teardown method called."
            )

        # after
        self.assert_quantity_in_outbox(0)

    def test_info(
        self,
    ) -> None:
        """Test ABCICounterHandler.info method."""

        abci_message, abci_dialogue = cast(
            Tuple[AbciMessage, AbciDialogue],
            self.abci_dialogues.create(
                performative=AbciMessage.Performative.REQUEST_INFO,
                counterparty="address",
                version="",
                block_version=0,
                p2p_version=0,
            ),
        )

        reply = self.abci_counter_handler.info(abci_message, abci_dialogue)
        has_attr, msg = self.message_has_attributes(
            actual_message=reply,
            message_type=AbciMessage,
            performative=AbciMessage.Performative.RESPONSE_INFO,
            info_data="",
            app_version=0,
            last_block_height=0,
            last_block_app_hash=b"",
        )
        assert has_attr, msg

    def test_init_chain(
        self,
    ) -> None:
        """Test ABCICounterHandler.init_chain method."""

        abci_message, abci_dialogue = cast(
            Tuple[AbciMessage, AbciDialogue],
            self.abci_dialogues.create(
                performative=AbciMessage.Performative.REQUEST_INIT_CHAIN,
                counterparty="address",
                version="",
                block_version=0,
                p2p_version=0,
            ),
        )

        reply = self.abci_counter_handler.init_chain(abci_message, abci_dialogue)
        has_attr, msg = self.message_has_attributes(
            actual_message=reply,
            message_type=AbciMessage,
            performative=AbciMessage.Performative.RESPONSE_INIT_CHAIN,
            validators=ValidatorUpdates([]),
            app_hash=b"",
        )
        assert has_attr, msg

    def test_query(
        self,
    ) -> None:
        """Test ABCICounterHandler.query method."""

        abci_message, abci_dialogue = cast(
            Tuple[AbciMessage, AbciDialogue],
            self.abci_dialogues.create(
                performative=AbciMessage.Performative.REQUEST_QUERY,
                counterparty="address",
                version="",
                query_data=b"",
                path="/",
                height=1,
                prove=True,
            ),
        )

        reply = self.abci_counter_handler.query(abci_message, abci_dialogue)
        has_attr, msg = self.message_has_attributes(
            actual_message=reply,
            performative=AbciMessage.Performative.RESPONSE_QUERY,
            message_type=AbciMessage,
            code=OK_CODE,
            log="value: 0",
            info="",
            index=0,
            key=b"",
            value=b"\x00\x00\x00\x00",
            proof_ops=ProofOps([]),
            height=self.abci_counter_handler.last_block_height,
            codespace="",
        )
        assert has_attr, msg

    def test_check_tx(
        self,
    ) -> None:
        """Test ABCICounterHandler. method."""

        tx = 10

        abci_message, abci_dialogue = cast(
            Tuple[AbciMessage, AbciDialogue],
            self.abci_dialogues.create(
                performative=AbciMessage.Performative.REQUEST_CHECK_TX,
                counterparty="address",
                version="",
                tx=tx.to_bytes(4, "big"),
                type=CheckTxType(CheckTxTypeEnum.NEW),
            ),
        )

        reply = self.abci_counter_handler.check_tx(abci_message, abci_dialogue)
        has_attr, msg = self.message_has_attributes(
            actual_message=reply,
            performative=AbciMessage.Performative.RESPONSE_CHECK_TX,
            message_type=AbciMessage,
            code=ERROR_CODE,
            log="invalid transaction.",
            info="ERROR: the next count must be a unitary increment.",
        )
        assert has_attr, msg

        tx = self.abci_counter_handler.tx_count + 1

        abci_message, abci_dialogue = cast(
            Tuple[AbciMessage, AbciDialogue],
            self.abci_dialogues.create(
                performative=AbciMessage.Performative.REQUEST_CHECK_TX,
                counterparty="address",
                version="",
                tx=tx.to_bytes(4, "big"),
                type=CheckTxType(CheckTxTypeEnum.NEW),
            ),
        )

        reply = self.abci_counter_handler.check_tx(abci_message, abci_dialogue)
        has_attr, msg = self.message_has_attributes(
            actual_message=reply,
            performative=AbciMessage.Performative.RESPONSE_CHECK_TX,
            message_type=AbciMessage,
            code=OK_CODE,
            log="valid transaction.",
            info="OK: the next count is a unitary increment.",
        )
        assert has_attr, msg

    def test_deliver_tx(
        self,
    ) -> None:
        """Test ABCICounterHandler. method."""

        abci_message, abci_dialogue = cast(
            Tuple[AbciMessage, AbciDialogue],
            self.abci_dialogues.create(
                performative=AbciMessage.Performative.REQUEST_DELIVER_TX,
                counterparty="address",
                version="",
                tx=b"",
            ),
        )

        reply = self.abci_counter_handler.deliver_tx(abci_message, abci_dialogue)
        has_attr, msg = self.message_has_attributes(
            actual_message=reply,
            performative=AbciMessage.Performative.RESPONSE_DELIVER_TX,
            message_type=AbciMessage,
            code=OK_CODE,
            data=b"",
            log="",
            info="",
            gas_wanted=0,
            gas_used=0,
            events=Events([]),
            codespace="",
        )
        assert has_attr, msg

    def test_commit(
        self,
    ) -> None:
        """Test ABCICounterHandler. method."""

        abci_message, abci_dialogue = cast(
            Tuple[AbciMessage, AbciDialogue],
            self.abci_dialogues.create(
                performative=AbciMessage.Performative.REQUEST_COMMIT,
                counterparty="address",
                version="",
            ),
        )

        reply = self.abci_counter_handler.commit(abci_message, abci_dialogue)
        has_attr, msg = self.message_has_attributes(
            actual_message=reply,
            performative=AbciMessage.Performative.RESPONSE_COMMIT,
            message_type=AbciMessage,
            data=struct.pack(">Q", self.abci_counter_handler.tx_count),
            retain_height=0,
        )
        assert has_attr, msg
