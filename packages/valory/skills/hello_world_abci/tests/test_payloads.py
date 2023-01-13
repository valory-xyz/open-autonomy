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

from packages.valory.skills.hello_world_abci.payloads import (
    CollectRandomnessPayload,
    PrintMessagePayload,
    RegistrationPayload,
    ResetPayload,
    SelectKeeperPayload,
)


def test_registration_payload() -> None:
    """Test `RegistrationPayload`."""

    payload = RegistrationPayload(sender="sender")

    assert payload.sender == "sender"


def test_collect_randomness_payload() -> None:
    """Test `CollectRandomnessPayload`"""

    payload = CollectRandomnessPayload(sender="sender", round_id=1, randomness="1")

    assert payload.round_id == 1
    assert payload.randomness == "1"
    assert payload.id_
    assert payload.data == {"round_id": 1, "randomness": "1"}


def test_select_keeper_payload() -> None:
    """Test `SelectKeeperPayload`."""

    payload = SelectKeeperPayload(sender="sender", keeper="keeper")

    assert payload.keeper == "keeper"
    assert payload.data == {"keeper": "keeper"}


def test_print_message_payload() -> None:
    """Test `PrintMessagePayload`."""

    payload = PrintMessagePayload(sender="sender", message="message")

    assert payload.message == "message"
    assert payload.data == {"message": "message"}


def test_reset_payload() -> None:
    """Test `ResetPayload`"""

    payload = ResetPayload(sender="sender", period_count=1)

    assert payload.period_count == 1
    assert payload.id_
    assert payload.data == {"period_count": 1}
    assert hash(payload)
