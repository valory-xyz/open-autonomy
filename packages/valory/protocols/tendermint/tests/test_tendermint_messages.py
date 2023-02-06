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

"""Test messages module for tendermint protocol."""

# pylint: disable=too-many-statements,too-many-locals,no-member,too-few-public-methods,redefined-builtin
from typing import List

from aea.test_tools.test_protocol import BaseProtocolMessagesTestCase

from packages.valory.protocols.tendermint.custom_types import ErrorCode
from packages.valory.protocols.tendermint.message import TendermintMessage


class TestMessageTendermint(BaseProtocolMessagesTestCase):
    """Test for the 'tendermint' protocol message."""

    MESSAGE_CLASS = TendermintMessage

    def build_messages(self) -> List[TendermintMessage]:  # type: ignore[override]
        """Build the messages to be used for testing."""
        return [
            TendermintMessage(
                performative=TendermintMessage.Performative.GET_GENESIS_INFO,
                query="some str",
            ),
            TendermintMessage(
                performative=TendermintMessage.Performative.GET_RECOVERY_PARAMS,
                query="some str",
            ),
            TendermintMessage(
                performative=TendermintMessage.Performative.GENESIS_INFO,
                info="some str",
            ),
            TendermintMessage(
                performative=TendermintMessage.Performative.RECOVERY_PARAMS,
                params="some str",
            ),
            TendermintMessage(
                performative=TendermintMessage.Performative.ERROR,
                error_code=ErrorCode.INVALID_REQUEST,
                error_msg="some str",
                error_data={"some str": "some str"},
            ),
        ]

    def build_inconsistent(self) -> List[TendermintMessage]:  # type: ignore[override]
        """Build inconsistent messages to be used for testing."""
        return [
            TendermintMessage(
                performative=TendermintMessage.Performative.GENESIS_INFO,
                # skip content: info
            ),
            TendermintMessage(
                performative=TendermintMessage.Performative.RECOVERY_PARAMS,
                # skip content: params
            ),
            TendermintMessage(
                performative=TendermintMessage.Performative.ERROR,
                # skip content: error_code
                error_msg="some str",
                error_data={"some str": "some str"},
            ),
        ]
