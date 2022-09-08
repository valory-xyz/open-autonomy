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

"""Test the common.py module of the skill."""

# pylint: skip-file

import re

import pytest

from packages.valory.skills.abstract_round_abci.common import random_selection


def test_random_selection() -> None:
    """Test 'random_selection'"""
    assert random_selection(elements=[0, 1, 2], randomness=0.25) == 0
    assert random_selection(elements=[0, 1, 2], randomness=0.5) == 1
    assert random_selection(elements=[0, 1, 2], randomness=0.75) == 2

    with pytest.raises(
        ValueError, match=re.escape("Randomness should lie in the [0,1) interval")
    ):
        random_selection(elements=[0, 1], randomness=-1)

    with pytest.raises(
        ValueError, match=re.escape("Randomness should lie in the [0,1) interval")
    ):
        random_selection(elements=[0, 1], randomness=1)

    with pytest.raises(
        ValueError, match=re.escape("Randomness should lie in the [0,1) interval")
    ):
        random_selection(elements=[0, 1], randomness=2)

    with pytest.raises(ValueError, match="No elements to randomly select among"):
        random_selection(elements=[], randomness=0.5)
