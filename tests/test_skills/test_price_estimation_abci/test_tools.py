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

import sys

import pytest

from packages.valory.skills.abstract_round_abci.common import random_selection
from packages.valory.skills.price_estimation_abci.behaviours import to_int


try:
    import atheris  # type: ignore
except (ImportError, ModuleNotFoundError):
    pytestmark = pytest.mark.skip


def test_random_selection_function() -> None:
    """Test `random_selection` function."""

    assert random_selection(["hello", "world", "!"], 0.1) == "hello"


@pytest.mark.parametrize("value", (-1, 2))
def test_random_selection_function_raises(value: int) -> None:
    """Test `random_selection` function."""
    with pytest.raises(ValueError):
        random_selection(["hello", "world", "!"], value)


def test_to_int_positive() -> None:
    """Test `to_int` function."""
    assert to_int(0.542, 5) == 54200
    assert to_int(0.542, 2) == 54
    assert to_int(542, 2) == 54200


@pytest.mark.skip
def test_fuzz_to_int() -> None:
    """Test fuzz to_int."""

    @atheris.instrument_func
    def fuzz_to_int(input_bytes: bytes) -> None:
        """Fuzz to_int."""
        fdp = atheris.FuzzedDataProvider(input_bytes)
        estimate = fdp.ConsumeFloat()
        decimals = fdp.ConsumeInt(4)
        to_int(estimate, decimals)

    atheris.instrument_all()
    atheris.Setup(sys.argv, fuzz_to_int)
    atheris.Fuzz()


@pytest.mark.skip
def test_fuzz_random_selection() -> None:
    """Test fuzz random_selection."""

    @atheris.instrument_func
    def fuzz_random_selection(input_bytes: bytes) -> None:
        """Fuzz random_selection."""
        fdp = atheris.FuzzedDataProvider(input_bytes)
        elements = [fdp.ConsumeString(12) for _ in range(4)]
        randomness = fdp.ConsumeFloat()
        if randomness > 1 or randomness < 0:
            return
        random_selection(elements, randomness)

    atheris.instrument_all()
    atheris.Setup(sys.argv, fuzz_random_selection)
    atheris.Fuzz()
