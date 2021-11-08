# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021 Valory AG
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

from packages.valory.skills.price_estimation_abci.tools import (
    aggregate,
    random_selection,
    to_int,
)


def test_aggregate_function() -> None:
    """Test `aggregate` function."""

    assert aggregate(1, 2, 3, 4, 5) == 3.0


def test_random_selection_function() -> None:
    """Test `random_selection` function."""

    assert random_selection(["hello", "world", "!"], 0.1) == "hello"


def test_to_int_positive() -> None:
    """Test `to_int` function."""
    assert to_int(0.542, 5) == 54200
    assert to_int(0.542, 2) == 54
    assert to_int(542, 2) == 54200
