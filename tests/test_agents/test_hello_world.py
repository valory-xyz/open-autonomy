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

"""End2end tests for the valory/hello_world skill."""
import pytest

from tests.test_agents.base import BaseTestEnd2EndNormalExecution


# round check log messages of the happy path
EXPECTED_ROUND_LOG_COUNT = {
    "registration": 1,
    "print_message": 3,
    "select_keeper": 2,
    "reset_and_pause": 2,
}

# strict check log messages of the happy path
STRICT_CHECK_STRINGS = (
    "Period end",
    " in period 0 says: HELLO WORLD!",
    " in period 1 says: HELLO WORLD!",
    " in period 2 says: HELLO WORLD!",
    " in period 3 says: HELLO WORLD!",
)


@pytest.mark.parametrize("nb_nodes", (4,))
class TestHelloWorldABCIFourAgents(
    BaseTestEnd2EndNormalExecution,
):
    """Test the ABCI hello_world skill with four agents."""

    agent_package = "valory/hello_world:0.1.0"
    skill_package = "valory/hello_world_abci:0.1.0"
    wait_to_finish = 160
    round_check_strings_to_n_periods = EXPECTED_ROUND_LOG_COUNT
    strict_check_strings = STRICT_CHECK_STRINGS
