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

"""Tests for the payloads of the FundsForwarderAbciApp."""

from packages.valory.skills.funds_forwarder_abci.payloads import (
    FundsForwarderPayload,
)

SENDER = "sender_address"


def test_payload_with_tx() -> None:
    """Test payload with a valid transaction."""
    payload = FundsForwarderPayload(
        sender=SENDER, tx_submitter="funds_forwarder_round", tx_hash="0xhash"
    )
    assert payload.sender == SENDER
    assert payload.tx_submitter == "funds_forwarder_round"
    assert payload.tx_hash == "0xhash"


def test_payload_defaults() -> None:
    """Test payload with default None values."""
    payload = FundsForwarderPayload(sender=SENDER)
    assert payload.tx_submitter is None
    assert payload.tx_hash is None
    assert payload.data == {"tx_submitter": None, "tx_hash": None}


def test_payload_serialization_roundtrip() -> None:
    """Test JSON serialization roundtrip."""
    payload = FundsForwarderPayload(
        sender=SENDER, tx_submitter="funds_forwarder_round", tx_hash="0xhash"
    )
    assert FundsForwarderPayload.from_json(payload.json) == payload  # type: ignore[attr-defined]
