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

"""Conftest module for io tests."""

# pylint: skip-file

from typing import Dict

import pytest

from packages.valory.skills.abstract_round_abci.io_.store import StoredJSONType


@pytest.fixture
def dummy_obj() -> StoredJSONType:
    """A dummy custom object to test the storing with."""
    return {"test_col": ["test_val_1", "test_val_2"]}


@pytest.fixture
def dummy_multiple_obj(dummy_obj: StoredJSONType) -> Dict[str, StoredJSONType]:
    """Many dummy custom objects to test the storing with."""
    return {f"test_obj_{i}": dummy_obj for i in range(10)}
