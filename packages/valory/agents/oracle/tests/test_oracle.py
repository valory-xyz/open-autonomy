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

# pylint: skip-file

from copy import deepcopy
from pathlib import Path
from typing import Tuple

import pytest
from aea.configurations.data_types import PublicId
from aea_test_autonomy.base_test_classes.agents import (
    BaseTestEnd2EndExecution,
    RoundChecks,
)
from aea_test_autonomy.fixture_helpers import abci_host  # noqa: F401
from aea_test_autonomy.fixture_helpers import abci_port  # noqa: F401
from aea_test_autonomy.fixture_helpers import flask_tendermint  # noqa: F401
from aea_test_autonomy.fixture_helpers import ganache_addr  # noqa: F401
from aea_test_autonomy.fixture_helpers import ganache_configuration  # noqa: F401
from aea_test_autonomy.fixture_helpers import ganache_port  # noqa: F401
from aea_test_autonomy.fixture_helpers import ganache_scope_class  # noqa: F401
from aea_test_autonomy.fixture_helpers import ganache_scope_function  # noqa: F401
from aea_test_autonomy.fixture_helpers import hardhat_addr  # noqa: F401
from aea_test_autonomy.fixture_helpers import hardhat_port  # noqa: F401
from aea_test_autonomy.fixture_helpers import key_pairs  # noqa: F401
from aea_test_autonomy.fixture_helpers import tendermint  # noqa: F401
from aea_test_autonomy.fixture_helpers import tendermint_port  # noqa: F401
from aea_test_autonomy.fixture_helpers import (  # noqa: F401
    UseGnosisSafeHardHatNet,
    gnosis_safe_hardhat_scope_class,
    gnosis_safe_hardhat_scope_function,
)


HAPPY_PATH: Tuple[RoundChecks, ...] = (
    RoundChecks("registration_startup"),
    RoundChecks("randomness_safe"),
    RoundChecks("select_keeper_safe"),
    RoundChecks("deploy_safe"),
    RoundChecks("validate_safe"),
    RoundChecks("randomness_oracle"),
    RoundChecks("select_keeper_oracle"),
    RoundChecks("deploy_oracle"),
    RoundChecks("validate_oracle"),
    RoundChecks("estimate_consensus", n_periods=2),
    RoundChecks("tx_hash", n_periods=2),
    RoundChecks("randomness_transaction_submission", n_periods=2),
    RoundChecks("select_keeper_transaction_submission_a", n_periods=2),
    RoundChecks("collect_signature", n_periods=2),
    RoundChecks("finalization", n_periods=2),
    RoundChecks("validate_transaction", n_periods=2),
    RoundChecks("reset_and_pause", n_periods=2),
    RoundChecks("collect_observation", n_periods=3),
)


def _generate_reset_happy_path(
    n_resets_to_perform: int, reset_tendermint_every: int
) -> Tuple[RoundChecks, ...]:
    """Generate the happy path for checking the oracle combined with the Tendermint reset functionality."""
    happy_path = deepcopy(HAPPY_PATH)
    for round_checks in happy_path:
        if round_checks.name in (
            "estimate_consensus"
            "tx_hash"
            "randomness_transaction_submission"
            "select_keeper_transaction_submission_a"
            "collect_signature"
            "finalization"
            "validate_transaction"
            "reset_and_pause"
            "collect_observation"
        ):
            round_checks.n_periods = n_resets_to_perform * reset_tendermint_every

    return happy_path


# strict check log messages of the happy path
STRICT_CHECK_STRINGS = (
    "Finalized with transaction hash",
    "Signature:",
    "Got estimate of BTC price in USD:",
    "Got observation of BTC price in USD",
    "Period end",
)
PACKAGES_DIR = Path(__file__).parent.parent.parent.parent.parent


@pytest.mark.parametrize("nb_nodes", (1,))
class TestABCIPriceEstimationSingleAgent(
    BaseTestEnd2EndExecution,
    UseGnosisSafeHardHatNet,
):
    """Test the ABCI oracle skill with only one agent."""

    agent_package = "valory/oracle:0.1.0"
    skill_package = "valory/oracle_abci:0.1.0"
    wait_to_finish = 180
    strict_check_strings = STRICT_CHECK_STRINGS
    happy_path = HAPPY_PATH
    package_registry_src_rel = PACKAGES_DIR


@pytest.mark.parametrize("nb_nodes", (2,))
class TestABCIPriceEstimationTwoAgents(
    BaseTestEnd2EndExecution,
    UseGnosisSafeHardHatNet,
):
    """Test the ABCI oracle skill with two agents."""

    agent_package = "valory/oracle:0.1.0"
    skill_package = "valory/oracle_abci:0.1.0"
    wait_to_finish = 180
    strict_check_strings = STRICT_CHECK_STRINGS
    happy_path = HAPPY_PATH
    package_registry_src_rel = PACKAGES_DIR


@pytest.mark.parametrize("nb_nodes", (4,))
class TestABCIPriceEstimationFourAgents(
    BaseTestEnd2EndExecution,
    UseGnosisSafeHardHatNet,
):
    """Test the ABCI oracle skill with four agents."""

    agent_package = "valory/oracle:0.1.0"
    skill_package = "valory/oracle_abci:0.1.0"
    wait_to_finish = 180
    strict_check_strings = STRICT_CHECK_STRINGS
    happy_path = HAPPY_PATH
    package_registry_src_rel = PACKAGES_DIR


@pytest.mark.parametrize("nb_nodes", (4,))
class TestAgentCatchup(BaseTestEnd2EndExecution, UseGnosisSafeHardHatNet):
    """Test that an agent that is launched later can synchronize with the rest of the network"""

    agent_package = "valory/oracle:0.1.0"
    skill_package = "valory/oracle_abci:0.1.0"
    wait_to_finish = 200
    restart_after = 45
    happy_path = HAPPY_PATH
    stop_string = "'registration_startup' round is done with event: Event.DONE"
    package_registry_src_rel = PACKAGES_DIR

    n_terminal = 1


@pytest.mark.skip
class TestTendermintReset(TestABCIPriceEstimationFourAgents):
    """Test the ABCI oracle skill with four agents when resetting Tendermint."""

    skill_package = "valory/oracle_abci:0.1.0"
    wait_to_finish = 360
    # run for 4 periods instead of 2
    __n_resets_to_perform = 2
    __reset_tendermint_every = 2
    happy_path = _generate_reset_happy_path(
        __n_resets_to_perform, __reset_tendermint_every
    )
    __args_prefix = f"vendor.valory.skills.{PublicId.from_str(skill_package).name}.models.params.args"
    # reset every two rounds
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
    happy_path = _generate_reset_happy_path(
        __n_resets_to_perform, __reset_tendermint_every
    )
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
    # check if we manage to reset with Tendermint `__n_resets_to_perform` times with the rest of the agents
    exclude_from_checks = [3]
