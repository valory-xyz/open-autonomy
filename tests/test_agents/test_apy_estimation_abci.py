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

import pytest
from aea.configurations.data_types import PublicId

from tests.fixture_helpers import UseGnosisSafeHardHatNet
from tests.test_agents.base import BaseTestEnd2EndNormalExecution


ipfs_daemon = pytest.mark.usefixtures("ipfs_daemon")

# round check log messages of the happy path
EXPECTED_ROUND_LOG_COUNT = {
    "collect_history": 1,
    "transform": 1,
    "preprocess": 1,
    "randomness": 1,
    "optimize": 1,
    # One time for training before testing and one time for training on full data after having the final model.
    "train": 2,
    "test": 1,
    "estimate": 2,
    "cycle_reset": 2,
    "collect_batch": 2,
    "prepare_batch": 2,
    "update_forecaster": 2,
}


@ipfs_daemon
class BaseTestABCIAPYEstimationSkillNormalExecution(BaseTestEnd2EndNormalExecution):
    """Base class for the APY estimation e2e tests."""

    agent_package = "valory/apy_estimation_chained:0.1.0"
    skill_package = "valory/apy_estimation_chained_abci:0.1.0"
    round_check_strings_to_n_periods = EXPECTED_ROUND_LOG_COUNT
    ROUND_TIMEOUT_SECONDS = 120
    wait_to_finish = 240
    __args_prefix = f"vendor.valory.skills.{PublicId.from_str(skill_package).name}.models.params.args"
    extra_configs = [
        {
            "dotted_path": f"{__args_prefix}.ipfs_domain_name",
            "value": "/dns/localhost/tcp/5001/http",
        }
    ]


@pytest.mark.skip
@pytest.mark.parametrize("nb_nodes", (1,))
class TestABCIAPYEstimationSingleAgent(
    BaseTestABCIAPYEstimationSkillNormalExecution,
    UseGnosisSafeHardHatNet,
):
    """Test the ABCI apy_estimation_abci skill with only one agent."""


@pytest.mark.skip
@pytest.mark.parametrize("nb_nodes", (2,))
class TestABCIAPYEstimationTwoAgents(
    BaseTestABCIAPYEstimationSkillNormalExecution,
    UseGnosisSafeHardHatNet,
):
    """Test the ABCI apy_estimation_abci skill with two agents."""


@pytest.mark.skip
@pytest.mark.parametrize("nb_nodes", (4,))
class TestABCIAPYEstimationFourAgents(
    BaseTestABCIAPYEstimationSkillNormalExecution,
    UseGnosisSafeHardHatNet,
):
    """Test the ABCI apy_estimation_abci skill with four agents."""

    wait_to_finish = 300
