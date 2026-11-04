# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2026 Valory AG
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

"""Tests for the Agent Mech contract module."""

from typing import Any, Dict
from unittest.mock import MagicMock, patch

from packages.valory.contracts.agent_mech.contract import AgentMech

CONTRACT_ADDRESS = "0x1234567890abcdef1234567890abcdef12345678"
TX_HASH = "0xdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeef"


def _process_request_event(
    mock_get_instance: MagicMock, **kwargs: Any
) -> Dict[str, Any]:
    """Process a receipt with one two-request `MarketplaceRequest` event."""
    ledger_api = MagicMock()
    ledger_api.api.to_checksum_address = lambda addr: addr
    log = {
        "args": {
            "priorityMech": "0x1",
            "requester": "0x2",
            "numRequests": 2,
            "requestIds": [b"\x01" * 32, b"\x02" * 32],
            "requestDatas": [b"\xaa\xbb", b"\xcc\xdd"],
        }
    }
    event = mock_get_instance.return_value.events.MarketplaceRequest
    event.return_value.process_receipt.return_value = [log]

    return AgentMech.process_request_event(
        ledger_api=ledger_api,
        contract_address=CONTRACT_ADDRESS,
        tx_hash=TX_HASH,
        **kwargs,
    )


class TestAgentMechProcessRequestEvent:
    """Tests for AgentMech.process_request_event."""

    @patch.object(AgentMech, "get_instance")
    def test_default_result_omits_request_datas(
        self, mock_get_instance: MagicMock
    ) -> None:
        """By default the result has only the request ids and their count."""
        result = _process_request_event(mock_get_instance)

        assert result == {
            "results": [
                {
                    "requestIds": ["0x" + "01" * 32, "0x" + "02" * 32],
                    "numRequests": 2,
                }
            ]
        }

    @patch.object(AgentMech, "get_instance")
    def test_opt_in_returns_request_ids_with_their_request_datas(
        self, mock_get_instance: MagicMock
    ) -> None:
        """When opted in, each request id is returned next to its request data."""
        result = _process_request_event(mock_get_instance, include_request_datas=True)

        assert result == {
            "results": [
                {
                    "requestIds": ["0x" + "01" * 32, "0x" + "02" * 32],
                    "requestDatas": ["0xaabb", "0xccdd"],
                    "numRequests": 2,
                }
            ]
        }
