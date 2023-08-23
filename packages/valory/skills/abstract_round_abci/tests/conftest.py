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

"""Conftest module for io tests."""

import os
import shutil
from contextlib import suppress
from pathlib import Path
from typing import Dict, Generator

import pytest
from hypothesis import settings

from packages.valory.skills.abstract_round_abci.io_.store import StoredJSONType
from packages.valory.skills.abstract_round_abci.models import MIN_RESET_PAUSE_DURATION


# pylint: skip-file


CI = "CI"
PACKAGE_DIR = Path(__file__).parent.parent
settings.register_profile(CI, deadline=5000)
profile_name = ("default", "CI")[bool(os.getenv("CI"))]


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
        with suppress(OSError, PermissionError):  # pragma: nocover
            shutil.rmtree(hypothesis_dir)


# We do not care about these keys but need to set them in the behaviours' tests,
# because `packages.valory.skills.abstract_round_abci.models._ensure` is used.
irrelevant_genesis_config = {
    "consensus_params": {
        "block": {"max_bytes": "str", "max_gas": "str", "time_iota_ms": "str"},
        "evidence": {
            "max_age_num_blocks": "str",
            "max_age_duration": "str",
            "max_bytes": "str",
        },
        "validator": {"pub_key_types": ["str"]},
        "version": {},
    },
    "genesis_time": "str",
    "chain_id": "str",
    "voting_power": "str",
}
irrelevant_config = {
    "tendermint_url": "str",
    "max_healthcheck": 0,
    "round_timeout_seconds": 0.0,
    "sleep_time": 0,
    "retry_timeout": 0,
    "retry_attempts": 0,
    "keeper_timeout": 0.0,
    "reset_pause_duration": MIN_RESET_PAUSE_DURATION,
    "drand_public_key": "str",
    "tendermint_com_url": "str",
    "tendermint_max_retries": 0,
    "reset_tendermint_after": 0,
    "cleanup_history_depth": 0,
    "voting_power": 0,
    "tendermint_check_sleep_delay": 0,
    "cleanup_history_depth_current": None,
    "request_timeout": 0.0,
    "request_retry_delay": 0.0,
    "tx_timeout": 0.0,
    "max_attempts": 0,
    "service_registry_address": None,
    "on_chain_service_id": None,
    "share_tm_config_on_startup": False,
    "tendermint_p2p_url": "str",
    "setup": {},
    "genesis_config": irrelevant_genesis_config,
    "use_termination": False,
    "use_slashing": False,
    "slash_cooldown_hours": 3,
    "slash_threshold_amount": 10_000_000_000_000_000,
    "light_slash_unit_amount": 5_000_000_000_000_000,
    "serious_slash_unit_amount": 8_000_000_000_000_000,
}
