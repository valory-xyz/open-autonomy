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

"""End2end tests for the valory/simple_abci skill."""

from tests.test_agents.base import BaseTestEnd2EndNormalExecution


# round check log messages of the happy path
ROUND_CHECK_STRINGS = {
    "registration": 1,
    "randomness_startup": 3,
    "select_keeper_at_startup": 2,
    "reset_and_pause": 2,
}

# strict check log messages of the happy path
STRICT_CHECK_STRINGS = (
    "Period end",
)


class TestSimpleABCISingleAgent(
    BaseTestEnd2EndNormalExecution,
):
    """Test that the ABCI simple_abci skill with only one agent."""

    NB_AGENTS = 1
    agent_package = "valory/simple_abci:0.1.0"
    skill_package = "valory/simple_abci:0.1.0"
    wait_to_finish = 80
    round_check_strings_to_n_periods = ROUND_CHECK_STRINGS
    strict_check_strings = STRICT_CHECK_STRINGS


class TestSimpleABCITwoAgents(
    BaseTestEnd2EndNormalExecution,
):
    """Test that the ABCI simple_abci skill with two agents."""

    NB_AGENTS = 2
    agent_package = "valory/simple_abci:0.1.0"
    skill_package = "valory/simple_abci:0.1.0"
    wait_to_finish = 120
    round_check_strings_to_n_periods = ROUND_CHECK_STRINGS
    strict_check_strings = STRICT_CHECK_STRINGS


class TestSimpleABCIFourAgents(
    BaseTestEnd2EndNormalExecution,
):
    """Test that the ABCI simple_abci skill with four agents."""

    NB_AGENTS = 4
    agent_package = "valory/simple_abci:0.1.0"
    skill_package = "valory/simple_abci:0.1.0"
    wait_to_finish = 120
    round_check_strings_to_n_periods = ROUND_CHECK_STRINGS
    strict_check_strings = STRICT_CHECK_STRINGS
