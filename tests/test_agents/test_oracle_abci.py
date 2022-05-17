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

"""Integration tests for the valory/oracle_abci skill."""
import pytest

from tests.fixture_helpers import UseGnosisSafeHardHatNet
from tests.test_agents.base import (
    BaseTestEnd2EndAgentCatchup,
    BaseTestEnd2EndNormalExecution,
)


# round check log messages of the happy path
EXPECTED_ROUND_LOG_COUNT = {
    "registration_startup": 1,
    "randomness_safe": 1,
    "select_keeper_safe": 1,
    "deploy_safe": 1,
    "validate_safe": 1,
    "randomness_oracle": 1,
    "select_keeper_oracle": 1,
    "deploy_oracle": 1,
    "validate_oracle": 1,
    "estimate_consensus": 2,
    "tx_hash": 2,
    "randomness_transaction_submission": 2,
    "select_keeper_transaction_submission_a": 2,
    "collect_signature": 2,
    "finalization": 2,
    "validate_transaction": 2,
    "reset_and_pause": 2,
    "collect_observation": 3,
}

# strict check log messages of the happy path
STRICT_CHECK_STRINGS = (
    "Finalized with transaction hash",
    "Signature:",
    "Got estimate of BTC price in USD:",
    "Got observation of BTC price in USD",
    "Period end",
)


@pytest.mark.parametrize("nb_nodes", (1,))
class TestABCIPriceEstimationSingleAgent(
    BaseTestEnd2EndNormalExecution,
    UseGnosisSafeHardHatNet,
):
    """Test the ABCI oracle skill with only one agent."""

    agent_package = "valory/oracle:0.1.0"
    skill_package = "valory/oracle_abci:0.1.0"
    wait_to_finish = 180
    strict_check_strings = STRICT_CHECK_STRINGS
    round_check_strings_to_n_periods = EXPECTED_ROUND_LOG_COUNT


@pytest.mark.parametrize("nb_nodes", (2,))
class TestABCIPriceEstimationTwoAgents(
    BaseTestEnd2EndNormalExecution,
    UseGnosisSafeHardHatNet,
):
    """Test the ABCI oracle skill with two agents."""

    agent_package = "valory/oracle:0.1.0"
    skill_package = "valory/oracle_abci:0.1.0"
    wait_to_finish = 180
    strict_check_strings = STRICT_CHECK_STRINGS
    round_check_strings_to_n_periods = EXPECTED_ROUND_LOG_COUNT


@pytest.mark.parametrize("nb_nodes", (4,))
class TestABCIPriceEstimationFourAgents(
    BaseTestEnd2EndNormalExecution,
    UseGnosisSafeHardHatNet,
):
    """Test the ABCI oracle skill with four agents."""

    agent_package = "valory/oracle:0.1.0"
    skill_package = "valory/oracle_abci:0.1.0"
    wait_to_finish = 180
    strict_check_strings = STRICT_CHECK_STRINGS
    round_check_strings_to_n_periods = EXPECTED_ROUND_LOG_COUNT


@pytest.mark.parametrize("nb_nodes", (4,))
class TestAgentCatchup(BaseTestEnd2EndAgentCatchup, UseGnosisSafeHardHatNet):
    """Test that an agent that is launched later can synchronize with the rest of the network"""

    agent_package = "valory/oracle:0.1.0"
    skill_package = "valory/oracle_abci:0.1.0"
    KEEPER_TIMEOUT = 30
    wait_to_finish = 200
    restart_after = 45
    round_check_strings_to_n_periods = EXPECTED_ROUND_LOG_COUNT
    stop_string = "'registration_startup' round is done with event: Event.DONE"
