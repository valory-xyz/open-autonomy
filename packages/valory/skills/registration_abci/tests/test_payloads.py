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

"""Test the payloads.py module of the skill."""

# pylint: skip-file

import pytest

from packages.valory.skills.abstract_round_abci.base import Transaction
from packages.valory.skills.registration_abci.payloads import RegistrationPayload


def test_registration_abci_payload() -> None:
    """Test `RegistrationPayload`."""

    payload = RegistrationPayload(sender="sender", initialisation="dummy")

    assert payload.initialisation == "dummy"
    assert payload.data == {"initialisation": "dummy"}
    assert RegistrationPayload.from_json(payload.json) == payload


def test_registration_abci_payload_raises() -> None:
    """Test `RegistrationPayload`."""
    payload = RegistrationPayload(sender="sender", initialisation="0" * 10 ** 7)
    signature = "signature"
    tx = Transaction(payload, signature)
    with pytest.raises(ValueError, match="Transaction must be smaller"):
        tx.encode()
