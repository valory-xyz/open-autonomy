# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2023 Valory AG
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

from packages.valory.skills.offend_abci.payloads import OffencesPayload


def test_offences_payload() -> None:
    """Test `OffencesPayload`."""

    payload = OffencesPayload("sender", "dummy_status")

    assert payload.sender == "sender"
    assert payload.id_
    assert payload.status == "dummy_status"
    assert payload.data == {"status": "dummy_status"}
