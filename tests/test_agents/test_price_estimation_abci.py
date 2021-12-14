# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021 Valory AG
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

"""Integration tests for the valory/price_estimation_abci skill."""


from tests.fixture_helpers import UseGnosisSafeHardHatNet
from tests.test_agents.base import (
    BaseTestEnd2EndDelayedStart,
    BaseTestEnd2EndNormalExecution,
)


# check log messages of the happy path
CHECK_STRINGS = (
    "Entered in the 'tendermint_healthcheck' behaviour state",
    "'tendermint_healthcheck' behaviour state is done",
    "Entered in the 'registration_at_startup' round for period 0",
    "'registration_at_startup' round is done",
    "Entered in the 'randomness_startup' round for period 0",
    "'randomness_startup' round is done",
    "Entered in the 'select_keeper_a_startup' round for period 0",
    "'select_keeper_a_startup' round is done",
    "Entered in the 'deploy_safe' round for period 0",
    "'deploy_safe' round is done",
    "Entered in the 'validate_safe' round for period 0",
    "'validate_safe' round is done",
    "Entered in the 'deploy_oracle' round for period 0",
    "'deploy_oracle' round is done",
    "Entered in the 'validate_oracle' round for period 0",
    "'validate_oracle' round is done",
    "Entered in the 'randomness' round for period 0",
    "'randomness' round is done",
    "Entered in the 'select_keeper_a' round for period 0",
    "'select_keeper_a' round is done",
    "Entered in the 'collect_observation' round for period 0",
    "Got observation of BTC price in USD",
    "'collect_observation' round is done",
    "Entered in the 'estimate_consensus' round for period 0",
    "Got estimate of BTC price in USD:",
    "'estimate_consensus' round is done",
    "Entered in the 'tx_hash' round for period 0",
    "'tx_hash' round is done",
    "Entered in the 'collect_signature' round for period 0",
    "Signature:",
    "'collect_signature' round is done",
    "Entered in the 'finalization' round for period 0",
    "'finalization' round is done",
    "Finalized estimate",
    "Entered in the 'validate_transaction' round for period 0",
    "'validate_transaction' round is done",
    "Period end",
    "Entered in the 'reset_and_pause' round for period 0",
    "'reset_and_pause' round is done",
    "Period end",
    "Entered in the 'randomness' round for period 1",
    "Entered in the 'select_keeper_a' round for period 1",
    "Entered in the 'collect_observation' round for period 1",
    "Entered in the 'estimate_consensus' round for period 1",
    "Entered in the 'tx_hash' round for period 1",
    "Entered in the 'collect_signature' round for period 1",
    "Entered in the 'finalization' round for period 1",
    "Entered in the 'validate_transaction' round for period 1",
    "Entered in the 'reset_and_pause' round for period 1",
)


class TestABCIPriceEstimationSingleAgent(
    BaseTestEnd2EndNormalExecution,
    UseGnosisSafeHardHatNet,
):
    """Test that the ABCI price_estimation skill with only one agent."""

    NB_AGENTS = 1
    agent_package = "valory/price_estimation:0.1.0"
    wait_to_finish = 120
    check_strings = CHECK_STRINGS


class TestABCIPriceEstimationTwoAgents(
    BaseTestEnd2EndNormalExecution,
    UseGnosisSafeHardHatNet,
):
    """Test that the ABCI price_estimation skill with two agents."""

    NB_AGENTS = 2
    agent_package = "valory/price_estimation:0.1.0"
    wait_to_finish = 120
    check_strings = CHECK_STRINGS


class TestABCIPriceEstimationFourAgents(
    BaseTestEnd2EndNormalExecution,
    UseGnosisSafeHardHatNet,
):
    """Test that the ABCI price_estimation skill with four agents."""

    NB_AGENTS = 4
    agent_package = "valory/price_estimation:0.1.0"
    wait_to_finish = 120
    check_strings = CHECK_STRINGS


class TestDelayedStart(BaseTestEnd2EndDelayedStart, UseGnosisSafeHardHatNet):
    """Test that an agent that is launched later can synchronize with the rest of the network"""

    NB_AGENTS = 4
    agent_package = "valory/price_estimation:0.1.0"
    wait_to_finish = 120
    check_strings = CHECK_STRINGS
