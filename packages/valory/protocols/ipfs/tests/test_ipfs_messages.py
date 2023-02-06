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

"""Test messages module for ipfs protocol."""

# pylint: disable=too-many-statements,too-many-locals,no-member,too-few-public-methods,redefined-builtin
from typing import List

from aea.test_tools.test_protocol import BaseProtocolMessagesTestCase

from packages.valory.protocols.ipfs.message import IpfsMessage


class TestMessageIpfs(BaseProtocolMessagesTestCase):
    """Test for the 'ipfs' protocol message."""

    MESSAGE_CLASS = IpfsMessage

    def build_messages(self) -> List[IpfsMessage]:  # type: ignore[override]
        """Build the messages to be used for testing."""
        return [
            IpfsMessage(
                performative=IpfsMessage.Performative.STORE_FILES,
                files={"some str": "some str"},
                timeout=1.0,
            ),
            IpfsMessage(
                performative=IpfsMessage.Performative.IPFS_HASH,
                ipfs_hash="some str",
            ),
            IpfsMessage(
                performative=IpfsMessage.Performative.GET_FILES,
                ipfs_hash="some str",
                timeout=1.0,
            ),
            IpfsMessage(
                performative=IpfsMessage.Performative.FILES,
                files={"some str": "some str"},
            ),
            IpfsMessage(
                performative=IpfsMessage.Performative.ERROR,
                reason="some str",
            ),
        ]

    def build_inconsistent(self) -> List[IpfsMessage]:  # type: ignore[override]
        """Build inconsistent messages to be used for testing."""
        return [
            IpfsMessage(
                performative=IpfsMessage.Performative.STORE_FILES,
                # skip content: files
                timeout=1.0,
            ),
            IpfsMessage(
                performative=IpfsMessage.Performative.IPFS_HASH,
                # skip content: ipfs_hash
            ),
            IpfsMessage(
                performative=IpfsMessage.Performative.GET_FILES,
                # skip content: ipfs_hash
                timeout=1.0,
            ),
            IpfsMessage(
                performative=IpfsMessage.Performative.FILES,
                # skip content: files
            ),
            IpfsMessage(
                performative=IpfsMessage.Performative.ERROR,
                # skip content: reason
            ),
        ]
