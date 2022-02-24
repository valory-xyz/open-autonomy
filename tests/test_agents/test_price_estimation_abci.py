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

"""Integration tests for the valory/price_estimation_abci skill."""
from enum import Enum
from operator import itemgetter

from tests.fixture_helpers import UseGnosisSafeHardHatNet
from tests.test_agents.base import (
    BaseTestEnd2EndAgentCatchup,
    BaseTestEnd2EndNormalExecution,
)


class StringType(Enum):
    """
    Type of string to be found in the agent's output.

    BEHAVIOUR: the string is printed by an agent's behaviour
    ROUND: the string is printed by the ABCI app.
    """

    BEHAVIOUR = "behaviour"
    ROUND = "round"


# check log messages of the happy path
# fmt: off
CHECK_STRINGS_LABELLED = [
    ("Entered in the 'registration_startup' round for period 0", StringType.ROUND),
    ("'registration_startup' round is done", StringType.ROUND),
    ("Entered in the 'randomness_safe' round for period 0", StringType.ROUND),
    ("'randomness_safe' round is done", StringType.ROUND),
    ("Entered in the 'select_keeper_safe' round for period 0", StringType.ROUND),
    ("'select_keeper_safe' round is done", StringType.ROUND),
    ("Entered in the 'deploy_safe' round for period 0", StringType.ROUND),
    ("'deploy_safe' round is done", StringType.ROUND),
    ("Entered in the 'validate_safe' round for period 0", StringType.ROUND),
    ("'validate_safe' round is done", StringType.ROUND),
    ("Entered in the 'randomness_oracle' round for period 0", StringType.ROUND),
    ("'randomness_oracle' round is done", StringType.ROUND),
    ("Entered in the 'select_keeper_oracle' round for period 0", StringType.ROUND),
    ("'select_keeper_oracle' round is done", StringType.ROUND),
    ("Entered in the 'deploy_oracle' round for period 0", StringType.ROUND),
    ("'deploy_oracle' round is done", StringType.ROUND),
    ("Entered in the 'validate_oracle' round for period 0", StringType.ROUND),
    ("'validate_oracle' round is done", StringType.ROUND),
    ("Entered in the 'collect_observation' round for period 0", StringType.ROUND),
    ("Got observation of BTC price in USD", StringType.BEHAVIOUR),
    ("'collect_observation' round is done", StringType.ROUND),
    ("Entered in the 'estimate_consensus' round for period 0", StringType.ROUND),
    ("Got estimate of BTC price in USD:", StringType.BEHAVIOUR),
    ("'estimate_consensus' round is done", StringType.ROUND),
    ("Entered in the 'tx_hash' round for period 0", StringType.ROUND),
    ("'tx_hash' round is done", StringType.ROUND),
    ("Entered in the 'randomness_transaction_submission' round for period 0", StringType.ROUND),
    ("'randomness_transaction_submission' round is done", StringType.ROUND),
    ("Entered in the 'select_keeper_transaction_submission_a' round for period 0", StringType.ROUND),
    ("'select_keeper_transaction_submission_a' round is done", StringType.ROUND),
    ("Entered in the 'collect_signature' round for period 0", StringType.ROUND),
    ("Signature:", StringType.BEHAVIOUR),
    ("'collect_signature' round is done", StringType.ROUND),
    ("Entered in the 'finalization' round for period 0", StringType.ROUND),
    ("'finalization' round is done", StringType.ROUND),
    ("Finalized with transaction hash", StringType.BEHAVIOUR),
    ("Entered in the 'validate_transaction' round for period 0", StringType.ROUND),
    ("'validate_transaction' round is done", StringType.ROUND),
    ("Period end", StringType.BEHAVIOUR),
    ("Entered in the 'reset_and_pause' round for period 0", StringType.ROUND),
    ("'reset_and_pause' round is done", StringType.ROUND),
    ("Period end", StringType.BEHAVIOUR),
    ("Entered in the 'collect_observation' round for period 1", StringType.ROUND),
    ("Entered in the 'estimate_consensus' round for period 1", StringType.ROUND),
    ("Entered in the 'tx_hash' round for period 1", StringType.ROUND),
    ("Entered in the 'randomness_transaction_submission' round for period 1", StringType.ROUND),
    ("Entered in the 'select_keeper_transaction_submission_a' round for period 1", StringType.ROUND),
    ("Entered in the 'collect_signature' round for period 1", StringType.ROUND),
    ("Entered in the 'finalization' round for period 1", StringType.ROUND),
    ("Entered in the 'validate_transaction' round for period 1", StringType.ROUND),
    ("Entered in the 'reset_and_pause' round for period 1", StringType.ROUND),
    ("Entered in the 'collect_observation' round for period 2", StringType.ROUND),
]
# fmt: on

# take all strings
CHECK_STRINGS_ALL = tuple(map(itemgetter(0), CHECK_STRINGS_LABELLED))

# take only round strings
CHECK_STRINGS_ONLY_ROUND = tuple(
    map(
        itemgetter(0),
        filter(lambda x: x[1] == StringType.ROUND, CHECK_STRINGS_LABELLED),
    )
)


class TestABCIPriceEstimationSingleAgent(
    BaseTestEnd2EndNormalExecution,
    UseGnosisSafeHardHatNet,
):
    """Test that the ABCI price_estimation skill with only one agent."""

    NB_AGENTS = 1
    agent_package = "valory/price_estimation:0.1.0"
    skill_package = "valory/price_estimation_abci:0.1.0"
    wait_to_finish = 180
    check_strings = CHECK_STRINGS_ALL


class TestABCIPriceEstimationTwoAgents(
    BaseTestEnd2EndNormalExecution,
    UseGnosisSafeHardHatNet,
):
    """Test that the ABCI price_estimation skill with two agents."""

    NB_AGENTS = 2
    agent_package = "valory/price_estimation:0.1.0"
    skill_package = "valory/price_estimation_abci:0.1.0"
    wait_to_finish = 180
    check_strings = CHECK_STRINGS_ALL


class TestABCIPriceEstimationFourAgents(
    BaseTestEnd2EndNormalExecution,
    UseGnosisSafeHardHatNet,
):
    """Test that the ABCI price_estimation skill with four agents."""

    NB_AGENTS = 4
    agent_package = "valory/price_estimation:0.1.0"
    skill_package = "valory/price_estimation_abci:0.1.0"
    wait_to_finish = 180
    check_strings = CHECK_STRINGS_ALL


class TestAgentCatchup(BaseTestEnd2EndAgentCatchup, UseGnosisSafeHardHatNet):
    """Test that an agent that is launched later can synchronize with the rest of the network"""

    NB_AGENTS = 4
    agent_package = "valory/price_estimation:0.1.0"
    skill_package = "valory/price_estimation_abci:0.1.0"
    KEEPER_TIMEOUT = 10
    wait_to_finish = 180
    restart_after = 45
    check_strings = CHECK_STRINGS_ONLY_ROUND
    stop_string = "'registration_startup' round is done with event: Event.DONE"
