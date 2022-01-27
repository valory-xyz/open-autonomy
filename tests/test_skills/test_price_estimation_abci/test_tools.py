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

"""Test the tools.py module of the skill."""

from packages.valory.skills.abstract_round_abci.common import random_selection
from packages.valory.skills.price_estimation_abci.behaviours import (
    payload_to_hex,
    to_int,
)
from packages.valory.skills.transaction_settlement_abci.payload_tools import (
    skill_input_hex_to_payload,
)


def test_random_selection_function() -> None:
    """Test `random_selection` function."""

    assert random_selection(["hello", "world", "!"], 0.1) == "hello"


def test_to_int_positive() -> None:
    """Test `to_int` function."""
    assert to_int(0.542, 5) == 54200
    assert to_int(0.542, 2) == 54
    assert to_int(542, 2) == 54200


def test_payload_to_hex_and_back() -> None:
    """Test `payload_to_hex` function."""
    hex_str = "b0e6add595e00477cf347d09797b156719dc5233283ac76e4efce2a674fe72d9"
    ether_value = 0
    safe_tx_gas = 40000000
    to_address = "0x77E9b2EF921253A171Fa0CB9ba80558648Ff7215"
    data = b"b0e6add595e00477cf347d09797b156719dc5233283ac76e4efce2a674fe72d9b0e6add595e00477cf347d09797b156719dc5233283ac76e4efce2a674fe72d9"
    intermediate = payload_to_hex(hex_str, ether_value, safe_tx_gas, to_address, data)
    h_, e_, s_, a_, d_ = skill_input_hex_to_payload(intermediate)
    assert h_ == hex_str
    assert e_ == ether_value
    assert s_ == safe_tx_gas
    assert a_ == to_address
    assert d_ == data
