# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2023 Valory AG
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

"""Test the payloads of the slashing."""

import pytest

from packages.valory.skills.abstract_round_abci.base import ROUND_COUNT_DEFAULT
from packages.valory.skills.slashing_abci.payloads import (
    SlashingTxPayload,
    StatusResetPayload,
)


@pytest.mark.parametrize(
    "sender, tx_hex",
    (
        (
            "sender",
            "tx_hex",
        ),
    ),
)
def test_slashing_tx_payload(
    sender: str,
    tx_hex: str,
) -> None:
    """Test `SlashingTxPayload`."""

    payload = SlashingTxPayload(sender, tx_hex)

    assert payload.id_
    assert payload.round_count == ROUND_COUNT_DEFAULT
    assert payload.sender == sender
    assert payload.tx_hex == tx_hex
    assert payload.data == {
        "tx_hex": tx_hex,
        "in_progress": True,
        "sent": True,
    }


@pytest.mark.parametrize(
    "sender, operators_mapping, slash_timestamps",
    (
        (
            "sender",
            "mapping",
            "timestamps",
        ),
    ),
)
def test_status_reset_payload(
    sender: str,
    operators_mapping: str,
    slash_timestamps: str,
) -> None:
    """Test `StatusResetPayload`"""

    payload = StatusResetPayload(
        sender,
        operators_mapping,
        slash_timestamps,
    )

    assert payload.id_
    assert payload.round_count == ROUND_COUNT_DEFAULT
    assert payload.sender == sender
    assert payload.operators_mapping == operators_mapping
    assert payload.slash_timestamps == slash_timestamps
    assert payload.data == {
        "operators_mapping": operators_mapping,
        "slash_timestamps": slash_timestamps,
        "slashing_in_flight": False,
        "slash_tx_sent": False,
    }
