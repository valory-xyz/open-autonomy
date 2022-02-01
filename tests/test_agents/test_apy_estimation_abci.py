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

"""Integration tests for the valory/apy_estimation_abci skill."""

from typing import Tuple, cast

import pytest

from tests.fixture_helpers import UseGnosisSafeHardHatNet
from tests.test_agents.base import BaseTestEnd2EndNormalExecution


ipfs_daemon = pytest.mark.usefixtures("ipfs_daemon")

# check log messages of the happy path
CHECK_STRINGS_LIST = [
    "Entered in the 'tendermint_healthcheck' behaviour state",
    "'tendermint_healthcheck' behaviour state is done",
]

states_checks_config = {
    "collect_history": {
        "round_name": "collect_history",
        "extra_logs": (),
        "only_at_first_period": True,
        "only_during_cycle": False,
    },
    "transform": {
        "round_name": "transform",
        "extra_logs": (),
        "only_at_first_period": True,
        "only_during_cycle": False,
    },
    "preprocess": {
        "round_name": "preprocess",
        "extra_logs": (),
        "only_at_first_period": True,
        "only_during_cycle": False,
    },
    "randomness": {
        "round_name": "randomness",
        "extra_logs": (),
        "only_at_first_period": True,
        "only_during_cycle": False,
    },
    "optimize": {
        "round_name": "optimize",
        "extra_logs": (),
        "only_at_first_period": True,
        "only_during_cycle": False,
    },
    "train": {
        "round_name": "train",
        "extra_logs": (),
        "only_at_first_period": True,
        "only_during_cycle": False,
    },
    "test": {
        "round_name": "test",
        "extra_logs": (),
        "only_at_first_period": True,
        "only_during_cycle": False,
    },
    "full_train": {
        "round_name": "train",
        "extra_logs": (),
        "only_at_first_period": True,
        "only_during_cycle": False,
    },
    "estimate": {
        "round_name": "estimate",
        "extra_logs": (),
        "only_at_first_period": False,
        "only_during_cycle": False,
    },
    "cycle_reset": {
        "round_name": "cycle_reset",
        "extra_logs": (),
        "only_at_first_period": False,
        "only_during_cycle": False,
    },
    "collect_batch": {
        "round_name": "collect_batch",
        "extra_logs": (),
        "only_at_first_period": False,
        "only_during_cycle": True,
    },
    "prepare_batch": {
        "round_name": "prepare_batch",
        "extra_logs": (),
        "only_at_first_period": False,
        "only_during_cycle": True,
    },
    "update_forecaster": {
        "round_name": "update_forecaster",
        "extra_logs": (),
        "only_at_first_period": False,
        "only_during_cycle": True,
    },
}


def build_check_strings() -> None:
    """Build check strings based on the `states_checks_config`."""
    for period in (0, 1):
        for _, config in states_checks_config.items():
            if period == 0 and not config["only_during_cycle"]:
                CHECK_STRINGS_LIST.append(
                    f"Entered in the '{config['round_name']}' round for period {period}"
                )

                for log in cast(Tuple[str], config["extra_logs"]):
                    CHECK_STRINGS_LIST.append(log)

                CHECK_STRINGS_LIST.append(f"'{config['round_name']}' round is done")

            elif period > 0 and not config["only_at_first_period"]:
                CHECK_STRINGS_LIST.append(
                    f"Entered in the '{config['round_name']}' round for period {period}"
                )


build_check_strings()
CHECK_STRINGS = tuple(CHECK_STRINGS_LIST)


@ipfs_daemon
class BaseTestABCIAPYEstimationSkillNormalExecution(BaseTestEnd2EndNormalExecution):
    """Base class for the APY estimation e2e tests."""

    agent_package = "valory/apy_estimation:0.1.0"
    skill_package = "valory/apy_estimation_abci:0.1.0"
    check_strings = CHECK_STRINGS
    ROUND_TIMEOUT_SECONDS = 120
    wait_to_finish = 240


class TestABCIAPYEstimationSingleAgent(
    BaseTestABCIAPYEstimationSkillNormalExecution,
    UseGnosisSafeHardHatNet,
):
    """Test the ABCI apy_estimation_abci skill with only one agent."""

    NB_AGENTS = 1


@pytest.mark.skip
class TestABCIAPYEstimationTwoAgents(
    BaseTestABCIAPYEstimationSkillNormalExecution,
    UseGnosisSafeHardHatNet,
):
    """Test that the ABCI apy_estimation_abci skill with two agents."""

    NB_AGENTS = 2


class TestABCIAPYEstimationFourAgents(
    BaseTestABCIAPYEstimationSkillNormalExecution,
    UseGnosisSafeHardHatNet,
):
    """Test that the ABCI apy_estimation_abci skill with four agents."""

    NB_AGENTS = 4
