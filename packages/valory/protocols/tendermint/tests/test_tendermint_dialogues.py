# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2023 valory
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

"""Test dialogues module for tendermint protocol."""

# pylint: disable=too-many-statements,too-many-locals,no-member,too-few-public-methods,redefined-builtin
from aea.test_tools.test_protocol import BaseProtocolDialoguesTestCase

from packages.valory.protocols.tendermint.dialogues import (
    TendermintDialogue,
    TendermintDialogues,
)
from packages.valory.protocols.tendermint.message import TendermintMessage


class TestDialoguesTendermint(BaseProtocolDialoguesTestCase):
    """Test for the 'tendermint' protocol dialogues."""

    MESSAGE_CLASS = TendermintMessage

    DIALOGUE_CLASS = TendermintDialogue

    DIALOGUES_CLASS = TendermintDialogues

    ROLE_FOR_THE_FIRST_MESSAGE = TendermintDialogue.Role.AGENT  # CHECK

    def make_message_content(self) -> dict:
        """Make a dict with message contruction content for dialogues.create."""
        return dict(
            performative=TendermintMessage.Performative.GET_GENESIS_INFO,
            query="some str",
        )
