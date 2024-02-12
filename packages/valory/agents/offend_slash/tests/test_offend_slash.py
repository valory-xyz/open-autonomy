# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2023 Valory AG
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

"""e2e tests for the `valory/offend_slash` skill."""

from pathlib import Path

import pytest
from aea.configurations.data_types import PublicId
from aea_test_autonomy.base_test_classes.agents import (
    BaseTestEnd2End,
    BaseTestEnd2EndExecution,
    RoundChecks,
)
from aea_test_autonomy.fixture_helpers import (  # noqa: F401  pylint: disable=unused-import
    UseACNNode,
    UseRegistries,
    abci_host,
    abci_port,
    acn_config,
    acn_node,
    flask_tendermint,
    hardhat_addr,
    hardhat_port,
    ipfs_daemon,
    ipfs_domain,
    key_pairs,
    registries_scope_class,
    tendermint_port,
)

from packages.valory.skills.offend_abci.rounds import OffendRound
from packages.valory.skills.registration_abci.rounds import RegistrationStartupRound
from packages.valory.skills.reset_pause_abci.rounds import ResetAndPauseRound
from packages.valory.skills.slashing_abci.rounds import StatusResetRound
from packages.valory.skills.transaction_settlement_abci.rounds import (
    RandomnessTransactionSubmissionRound,
    ValidateTransactionRound,
)


NO_SLASHING_HAPPY_PATH = (
    RoundChecks(RegistrationStartupRound.auto_round_id()),
    RoundChecks(OffendRound.auto_round_id(), n_periods=2),
    RoundChecks(ResetAndPauseRound.auto_round_id(), n_periods=2),
)

SLASHING_HAPPY_PATH = NO_SLASHING_HAPPY_PATH + (
    RoundChecks(ValidateTransactionRound.auto_round_id()),
)

SLASHING_STRICT_CHECKS = (
    "The Event.SLASH_START event was produced, "
    f"transitioning to `{RandomnessTransactionSubmissionRound.auto_round_id()}`",
    f"Entered in the '{StatusResetRound.auto_round_id()}' round for period 0",
    "The Event.SLASH_END event was produced. Switching back to the normal FSM.",
)


@pytest.mark.parametrize("nb_nodes", (4,))
class SlashingE2E(UseRegistries, UseACNNode, BaseTestEnd2End):
    """Test that slashing works right."""

    package_registry_src_rel = Path(__file__).parents[4]
    agent_package = "valory/offend_slash:0.1.0"
    skill_package = "valory/offend_slash_abci:0.1.0"
    wait_to_finish = 120
    _args_prefix = f"vendor.valory.skills.{PublicId.from_str(skill_package).name}.models.params.args"

    def __set_configs(  # pylint: disable=unused-private-member
        self, i: int, nb_agents: int
    ) -> None:
        """Set the current agent's config overrides."""
        super().__set_configs(i=i, nb_agents=nb_agents)

        self.set_config(
            dotted_path=f"{self._args_prefix}.tendermint_p2p_url",
            value=f"localhost:{self._tendermint_image.get_p2p_port(i=i)}",
            type_="str",
        )


@pytest.mark.e2e
class TestSlashingThresholdUnmet(SlashingE2E, BaseTestEnd2EndExecution):
    """Test that slashing works right."""

    happy_path = NO_SLASHING_HAPPY_PATH
    extra_configs = [
        {
            "dotted_path": f"{SlashingE2E._args_prefix}.validator_downtime",
            "value": True,
        }
    ]


@pytest.mark.e2e
class TestSlashing(SlashingE2E, BaseTestEnd2EndExecution):
    """Test that slashing works right."""

    happy_path = SLASHING_HAPPY_PATH
    strict_check_strings = SLASHING_STRICT_CHECKS
    extra_configs = [
        {
            "dotted_path": f"{SlashingE2E._args_prefix}.validator_downtime",
            "value": True,
        },
        {
            "dotted_path": f"{SlashingE2E._args_prefix}.num_double_signed",
            "value": 1,
        },
    ]
