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

"""Test the payloads of the skill."""
from packages.valory.skills.transaction_settlement_abci.payloads import (
    FinalizationTxPayload,
    TransactionType,
    SignaturePayload, ResetPayload,
)


def test_signature_payload() -> None:
    """Test `SignaturePayload`."""

    payload = SignaturePayload(sender="sender", signature="sign")

    assert payload.signature == "sign"
    assert payload.data == {"signature": "sign"}
    assert payload.transaction_type == TransactionType.SIGNATURE


def test_finalization_tx_payload() -> None:
    """Test `FinalizationTxPayload`."""

    payload = FinalizationTxPayload(
        sender="sender",
        tx_data={
            "tx_digest": "hash",
            "nonce": 0,
            "max_fee_per_gas": 0,
            "max_priority_fee_per_gas": 0,
        },
    )

    assert payload.data == {
        "tx_data": {
            "tx_digest": "hash",
            "nonce": 0,
            "max_fee_per_gas": 0,
            "max_priority_fee_per_gas": 0,
        }
    }
    assert payload.transaction_type == TransactionType.FINALIZATION


def test_reset_payload() -> None:
    """Test `ResetPayload`."""

    payload = ResetPayload(sender="sender", period_count=1)

    assert payload.period_count == 1
    assert payload.data == {"period_count": 1}
    assert payload.transaction_type == TransactionType.RESET
