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

"""Test dialogues module for ipfs protocol."""

# pylint: disable=too-many-statements,too-many-locals,no-member,too-few-public-methods,redefined-builtin
from aea.test_tools.test_protocol import BaseProtocolDialoguesTestCase

from packages.valory.protocols.ipfs.dialogues import IpfsDialogue, IpfsDialogues
from packages.valory.protocols.ipfs.message import IpfsMessage


class TestDialoguesIpfs(BaseProtocolDialoguesTestCase):
    """Test for the 'ipfs' protocol dialogues."""

    MESSAGE_CLASS = IpfsMessage

    DIALOGUE_CLASS = IpfsDialogue

    DIALOGUES_CLASS = IpfsDialogues

    ROLE_FOR_THE_FIRST_MESSAGE = IpfsDialogue.Role.CONNECTION  # CHECK

    def make_message_content(self) -> dict:
        """Make a dict with message contruction content for dialogues.create."""
        return dict(
            performative=IpfsMessage.Performative.GET_FILES,
            ipfs_hash="some str",
            timeout=1.0,
        )
