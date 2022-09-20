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

"""Test the payloads.py module of the skill."""

# pylint: skip-file

from packages.valory.skills.reset_pause_abci.payloads import (
    ResetPausePayload,
    TransactionType,
)


def test_reset_pause_payload() -> None:
    """Test `ResetPausePayload`."""

    payload = ResetPausePayload(sender="sender", period_count=1)

    assert payload.period_count == 1
    assert payload.data == {"period_count": 1}
    assert payload.transaction_type == TransactionType.RESETPAUSE
    assert ResetPausePayload.from_json(payload.json) == payload
