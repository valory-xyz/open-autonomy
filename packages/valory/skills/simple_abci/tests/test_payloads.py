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

from packages.valory.skills.simple_abci.payloads import (
    RandomnessPayload,
    RegistrationPayload,
    ResetPayload,
    SelectKeeperPayload,
    TransactionType,
)


def test_registration_payload() -> None:
    """Test `RegistrationPayload`."""

    payload = RegistrationPayload(sender="sender")

    assert payload.sender == "sender"
    assert payload.transaction_type == TransactionType.REGISTRATION


def test_select_keeper_payload() -> None:
    """Test `SelectKeeperPayload`."""

    payload = SelectKeeperPayload(sender="sender", keeper="keeper")

    assert payload.keeper == "keeper"
    assert payload.data == {"keeper": "keeper"}
    assert payload.transaction_type == TransactionType.SELECT_KEEPER


def test_randomness_payload() -> None:
    """Test `RandomnessPayload`"""

    payload = RandomnessPayload(sender="sender", round_id=1, randomness="1", id_="id")

    assert payload.round_id == 1
    assert payload.randomness == "1"
    assert payload.id_ == "id"
    assert payload.data == {"round_id": 1, "randomness": "1"}

    assert payload.transaction_type == TransactionType.RANDOMNESS


def test_reset_payload() -> None:
    """Test `ResetPayload`"""

    payload = ResetPayload(sender="sender", period_count=1, id_="id")

    assert payload.period_count == 1
    assert payload.id_ == "id"
    assert payload.data == {"period_count": 1}
    assert hash(payload) == hash(tuple(sorted(payload.data.items())))

    assert str(payload.transaction_type) == str(TransactionType.RESET)
    assert payload.transaction_type == TransactionType.RESET
