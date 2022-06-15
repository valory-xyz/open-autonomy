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
from aea.configurations.data_types import PublicId

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
    wait_to_finish = 200
    restart_after = 45
    round_check_strings_to_n_periods = EXPECTED_ROUND_LOG_COUNT
    stop_string = "'registration_startup' round is done with event: Event.DONE"


@pytest.mark.skip
class TestTendermintReset(TestABCIPriceEstimationFourAgents):
    """Test the ABCI oracle skill with four agents when resetting Tendermint."""

    skill_package = "valory/oracle_abci:0.1.0"
    wait_to_finish = 360
    # run for 4 periods instead of 2
    round_check_strings_to_n_periods = {
        round: 4
        for round in EXPECTED_ROUND_LOG_COUNT.keys()
        if round
        in (
            "estimate_consensus"
            "tx_hash"
            "randomness_transaction_submission"
            "select_keeper_transaction_submission_a"
            "collect_signature"
            "finalization"
            "validate_transaction"
            "reset_and_pause"
            "collect_observation"
        )
    }
    __args_prefix = f"vendor.valory.skills.{PublicId.from_str(skill_package).name}.models.params.args"
    # reset every two rounds
    extra_configs = [
        {
            "dotted_path": f"{__args_prefix}.reset_tendermint_after",
            "value": 2,
        },
        {
            "dotted_path": f"{__args_prefix}.observation_interval",
            "value": 15,
        },
    ]


@pytest.mark.skip
class TestTendermintResetInterrupt(TestAgentCatchup):
    """Test the ABCI oracle skill with four agents when an agent gets temporarily interrupted on Tendermint reset."""

    skill_package = "valory/oracle_abci:0.1.0"
    cli_log_options = ["-v", "INFO"]
    wait_before_stop = 100
    wait_to_finish = 300
    restart_after = 1
    __n_resets_to_perform = 3
    __reset_tendermint_every = 2

    # stop for restart_after seconds when resetting Tendermint for the first time (using -1 because count starts from 0)
    stop_string = f"Entered in the 'reset_and_pause' round for period {__reset_tendermint_every - 1}"
    # check if we manage to reset with Tendermint `__n_resets_to_perform` times with the rest of the agents
    exclude_from_checks = [3]
    round_check_strings_to_n_periods = {
        "reset_and_pause": __n_resets_to_perform * __reset_tendermint_every
    }
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


@pytest.mark.skip
class TestTendermintResetInterruptNoRejoin(TestTendermintResetInterrupt):
    """
    Test a Tendermint reset case for the ABCI oracle skill.

    Test the ABCI oracle skill with four agents when an agent gets temporarily interrupted
    on Tendermint reset and never rejoins.
    """

    wait_to_finish = 300
    # set the restart to a value so that the agent never rejoins, in order to test the impact to the rest of the agents
    restart_after = wait_to_finish
