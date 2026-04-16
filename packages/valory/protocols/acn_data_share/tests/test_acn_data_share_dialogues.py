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

"""Test dialogues module for acn_data_share protocol."""

# pylint: disable=too-many-statements,too-many-locals,no-member,too-few-public-methods,redefined-builtin
from aea.test_tools.test_protocol import BaseProtocolDialoguesTestCase

from packages.valory.protocols.acn_data_share.dialogues import (
    AcnDataShareDialogue,
    AcnDataShareDialogues,
)
from packages.valory.protocols.acn_data_share.message import AcnDataShareMessage


class TestDialoguesAcnDataShare(BaseProtocolDialoguesTestCase):
    """Test for the 'acn_data_share' protocol dialogues."""

    MESSAGE_CLASS = AcnDataShareMessage

    DIALOGUE_CLASS = AcnDataShareDialogue

    DIALOGUES_CLASS = AcnDataShareDialogues

    ROLE_FOR_THE_FIRST_MESSAGE = AcnDataShareDialogue.Role.AGENT  # CHECK

    def make_message_content(self) -> dict:
        """Make a dict with message contruction content for dialogues.create."""
        return dict(
            performative=AcnDataShareMessage.Performative.DATA,
            request_id="some str",
            content="some str",
        )
