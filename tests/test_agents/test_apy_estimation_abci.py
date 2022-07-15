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
from tests.test_agents.base import BaseTestEnd2EndExecution, RoundChecks


ipfs_daemon = pytest.mark.usefixtures("ipfs_daemon")

HAPPY_PATH = (
    RoundChecks("collect_history"),
    RoundChecks("transform"),
    RoundChecks("preprocess"),
    RoundChecks("randomness"),
    RoundChecks("optimize"),
    RoundChecks("train"),
    RoundChecks("train", success_event="FULLY_TRAINED"),
    RoundChecks("test"),
    RoundChecks("estimate", n_periods=2, success_event="ESTIMATION_CYCLE"),
    RoundChecks("cycle_reset", n_periods=2),
    RoundChecks("collect_batch", n_periods=2),
    RoundChecks("prepare_batch", n_periods=2),
    RoundChecks("update_forecaster", n_periods=2),
)


@ipfs_daemon
class BaseTestABCIAPYEstimationSkillNormalExecution(BaseTestEnd2EndExecution):
    """Base class for the APY estimation e2e tests."""

    agent_package = "valory/apy_estimation_chained:0.1.0"
    skill_package = "valory/apy_estimation_chained_abci:0.1.0"
    happy_path = HAPPY_PATH
    ROUND_TIMEOUT_SECONDS = 120
    wait_to_finish = 240
    __args_prefix = f"vendor.valory.skills.{PublicId.from_str(skill_package).name}.models.params.args"
    extra_configs = [
        {
            "dotted_path": f"{__args_prefix}.ipfs_domain_name",
            "value": "/dns/localhost/tcp/5001/http",
        }
    ]


@pytest.mark.parametrize("nb_nodes", (1,))
class TestABCIAPYEstimationSingleAgent(
    BaseTestABCIAPYEstimationSkillNormalExecution,
    UseGnosisSafeHardHatNet,
):
    """Test the ABCI apy_estimation_abci skill with only one agent."""


@pytest.mark.parametrize("nb_nodes", (2,))
class TestABCIAPYEstimationTwoAgents(
    BaseTestABCIAPYEstimationSkillNormalExecution,
    UseGnosisSafeHardHatNet,
):
    """Test the ABCI apy_estimation_abci skill with two agents."""


@pytest.mark.parametrize("nb_nodes", (4,))
class TestABCIAPYEstimationFourAgents(
    BaseTestABCIAPYEstimationSkillNormalExecution,
    UseGnosisSafeHardHatNet,
):
    """Test the ABCI apy_estimation_abci skill with four agents."""

    wait_to_finish = 300
