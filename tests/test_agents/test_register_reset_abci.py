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

"""Integration tests for the valory/register_reset skill."""
import pytest
from aea.configurations.data_types import PublicId

from tests.test_agents.base import (
    BaseTestEnd2EndAgentCatchup,
    BaseTestEnd2EndNormalExecution,
)


# round check log messages of the happy path
EXPECTED_ROUND_LOG_COUNT = {
    "registration_startup": 1,
    "registration": 3,
    "reset_and_pause": 4,
}


@pytest.mark.parametrize("nb_nodes", (4,))
class TestTendermintStartup(BaseTestEnd2EndNormalExecution):
    """Test the ABCI register-reset skill with 4 agents starting up."""

    agent_package = "valory/register_reset:0.1.0"
    skill_package = "valory/register_reset_abci:0.1.0"
    round_check_strings_to_n_periods = {
        "registration_startup": 1,
        "reset_and_pause": 1,
    }
    wait_to_finish = 60
    __args_prefix = f"vendor.valory.skills.{PublicId.from_str(skill_package).name}.models.params.args"
    extra_configs = [
        {
            "dotted_path": f"{__args_prefix}.observation_interval",
            "value": 15,
        },
    ]


@pytest.mark.parametrize("nb_nodes", (4,))
class TestTendermintReset(BaseTestEnd2EndNormalExecution):
    """Test the ABCI register-reset skill with 4 agents when resetting Tendermint."""

    agent_package = "valory/register_reset:0.1.0"
    skill_package = "valory/register_reset_abci:0.1.0"
    round_check_strings_to_n_periods = EXPECTED_ROUND_LOG_COUNT
    wait_to_finish = 200
    __reset_tendermint_every = 1
    __args_prefix = f"vendor.valory.skills.{PublicId.from_str(skill_package).name}.models.params.args"
    # reset every `__reset_tendermint_every` rounds
    extra_configs = [
        {
            "dotted_path": f"{__args_prefix}.reset_tendermint_after",
            "value": __reset_tendermint_every,
        },
        {
            "dotted_path": f"{__args_prefix}.observation_interval",
            "value": 15,
        },
    ]


@pytest.mark.parametrize("nb_nodes", (4,))
class TestTendermintResetInterrupt(BaseTestEnd2EndAgentCatchup):
    """Test the ABCI register-reset skill with 4 agents when an agent gets interrupted on Tendermint reset."""

    agent_package = "valory/register_reset:0.1.0"
    skill_package = "valory/register_reset_abci:0.1.0"
    cli_log_options = ["-v", "INFO"]
    wait_before_stop = 60
    wait_to_finish = 300
    restart_after = 1
    __reset_tendermint_every = 1
    stop_string = f"Entered in the 'reset_and_pause' round for period {__reset_tendermint_every - 1}"
    round_check_strings_to_n_periods = EXPECTED_ROUND_LOG_COUNT

    __args_prefix = f"vendor.valory.skills.{PublicId.from_str(skill_package).name}.models.params.args"
    # reset every `__reset_tendermint_every` rounds
    extra_configs = [
        {
            "dotted_path": f"{__args_prefix}.reset_tendermint_after",
            "value": __reset_tendermint_every,
        },
        {
            "dotted_path": f"{__args_prefix}.observation_interval",
            "value": 15,
        },
    ]


class TestTendermintResetInterruptNoRejoin(TestTendermintResetInterrupt):
    """
    Test a Tendermint reset case for the ABCI register-reset skill.

    Test the ABCI register-reset skill with 4 agents when an agent gets temporarily interrupted
    on Tendermint reset and never rejoins.
    """

    wait_to_finish = 200
    # set the restart to a value so that the agent never rejoins, in order to test the impact to the rest of the agents
    restart_after = wait_to_finish
    # check if we manage to reset with Tendermint with the rest of the agents; 3rd agent will not rejoin in this test
    exclude_from_checks = [3]
