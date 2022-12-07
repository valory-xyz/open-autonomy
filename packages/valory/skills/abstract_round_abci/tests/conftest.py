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
import logging
import os
import shutil
from contextlib import suppress
from pathlib import Path
from typing import Dict, Generator

import pytest
from hypothesis import settings

from packages.valory.skills.abstract_round_abci.io_.store import StoredJSONType


# pylint: skip-file


CI = "CI"
PACKAGE_DIR = Path(__file__).parent.parent
settings.register_profile(CI, deadline=5000)


@pytest.fixture(scope="module", autouse=True)
def load_hypothesis_profile() -> Generator:
    """Fixture to load hypothesis CI settings."""
    if os.getenv(CI):
        settings.load_profile(CI)
    profile = settings.get_profile(settings._current_profile)
    logging.info(f"Using hypothesis profile from {__file__}:\n{profile}")
    yield


@pytest.fixture
def dummy_obj() -> StoredJSONType:
    """A dummy custom object to test the storing with."""
    return {"test_col": ["test_val_1", "test_val_2"]}


@pytest.fixture
def dummy_multiple_obj(dummy_obj: StoredJSONType) -> Dict[str, StoredJSONType]:
    """Many dummy custom objects to test the storing with."""
    return {f"test_obj_{i}": dummy_obj for i in range(10)}


@pytest.fixture(scope="session", autouse=True)
def hypothesis_cleanup() -> Generator:
    """Fixture to remove hypothesis directory after tests."""
    yield
    hypothesis_dir = PACKAGE_DIR / ".hypothesis"
    if hypothesis_dir.exists():
        with suppress(OSError, PermissionError):
            shutil.rmtree(hypothesis_dir)
