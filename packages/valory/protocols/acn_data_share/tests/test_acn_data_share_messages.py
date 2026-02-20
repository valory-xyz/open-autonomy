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

"""Test messages module for acn_data_share protocol."""

# pylint: disable=too-many-statements,too-many-locals,no-member,too-few-public-methods,redefined-builtin
from typing import List

from aea.test_tools.test_protocol import BaseProtocolMessagesTestCase

from packages.valory.protocols.acn_data_share.message import AcnDataShareMessage


class TestMessageAcnDataShare(BaseProtocolMessagesTestCase):
    """Test for the 'acn_data_share' protocol message."""

    MESSAGE_CLASS = AcnDataShareMessage

    def build_messages(self) -> List[AcnDataShareMessage]:  # type: ignore[override]
        """Build the messages to be used for testing."""
        return [
            AcnDataShareMessage(
                performative=AcnDataShareMessage.Performative.DATA,
                request_id="some str",
                content="some str",
            ),
        ]

    def build_inconsistent(self) -> List[AcnDataShareMessage]:  # type: ignore[override]
        """Build inconsistent messages to be used for testing."""
        return [
            AcnDataShareMessage(
                performative=AcnDataShareMessage.Performative.DATA,
                # skip content: request_id
                content="some str",
            ),
        ]
