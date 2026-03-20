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

"""Tests for the payloads of the IdentifyServiceOwnerAbciApp."""

from typing import Optional

import pytest

from packages.valory.skills.identify_service_owner_abci.payloads import (
    IdentifyServiceOwnerPayload,
)

SENDER = "sender_address"


@pytest.mark.parametrize(
    "service_owner",
    [
        "0xOwnerAddress",
        None,
    ],
)
def test_payload_attributes(service_owner: Optional[str]) -> None:
    """Test payload attributes for both valid and None service owner."""
    kwargs = {"sender": SENDER}
    if service_owner is not None:
        kwargs["service_owner"] = service_owner
    payload = IdentifyServiceOwnerPayload(**kwargs)
    assert payload.sender == SENDER
    assert payload.service_owner == service_owner
    assert payload.data == {"service_owner": service_owner}


def test_payload_serialization_roundtrip() -> None:
    """Test JSON serialization roundtrip."""
    payload = IdentifyServiceOwnerPayload(sender=SENDER, service_owner="0xOwnerAddress")
    assert IdentifyServiceOwnerPayload.from_json(payload.json) == payload  # type: ignore[attr-defined]
