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

"""Test the payloads of the pending offences."""

import pytest

from packages.valory.skills.abstract_round_abci.background.pending_offences.payloads import (
    PendingOffencesPayload,
)
from packages.valory.skills.abstract_round_abci.base import ROUND_COUNT_DEFAULT


@pytest.mark.parametrize(
    "sender, accused_agent_address, offense_round, offense_type_value, last_transition_timestamp, time_to_live",
    (
        (
            "sender",
            "test_address",
            90,
            3,
            10,
            2,
        ),
    ),
)
def test_pending_offences_payload(
    sender: str,
    accused_agent_address: str,
    offense_round: int,
    offense_type_value: int,
    last_transition_timestamp: int,
    time_to_live: int,
) -> None:
    """Test `PendingOffencesPayload`"""

    payload = PendingOffencesPayload(
        sender,
        accused_agent_address,
        offense_round,
        offense_type_value,
        last_transition_timestamp,
        time_to_live,
    )

    assert payload.id_
    assert payload.round_count == ROUND_COUNT_DEFAULT
    assert payload.sender == sender
    assert payload.accused_agent_address == accused_agent_address
    assert payload.offense_round == offense_round
    assert payload.offense_type_value == offense_type_value
    assert payload.last_transition_timestamp == last_transition_timestamp
    assert payload.time_to_live == time_to_live
    assert payload.data == {
        "accused_agent_address": accused_agent_address,
        "offense_round": offense_round,
        "offense_type_value": offense_type_value,
        "last_transition_timestamp": last_transition_timestamp,
        "time_to_live": time_to_live,
    }
