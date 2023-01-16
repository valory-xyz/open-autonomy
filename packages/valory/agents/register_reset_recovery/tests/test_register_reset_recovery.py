# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2023 Valory AG
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


from pathlib import Path

import pytest
from aea.configurations.data_types import PublicId
from aea_test_autonomy.base_test_classes.agents import RoundChecks
from aea_test_autonomy.fixture_helpers import (  # noqa: F401  # pylint: disable=unused-import
    UseACNNode,
    UseRegistries,
    abci_host,
    abci_port,
    acn_config,
    acn_node,
    flask_tendermint,
    hardhat_port,
    ipfs_daemon,
    ipfs_domain,
    key_pairs,
    nb_nodes,
    registries_scope_class,
    tendermint_port,
)

from packages.valory.agents.register_reset_recovery.tests.base import (
    BaseTestRegisterResetRecoveryEnd2End,
)
from packages.valory.skills.registration_abci.rounds import RegistrationStartupRound


HAPPY_PATH = (RoundChecks(RegistrationStartupRound.auto_round_id()),)

# the string used to trigger the breaking of the 3rd tm node (node3).
TM_BREAK_STRING = "Current round count is 3."

# we make sure that all agents are able to reach round 25.
# the third one will communication wth tendermint at round 3.
STRICT_CHECK_STRINGS = ("Current round count is 25.",)


@pytest.mark.e2e
@pytest.mark.integration
@pytest.mark.parametrize("nb_nodes", (4,))
class TestRegisterResetRecoverStartup(
    UseRegistries, UseACNNode, BaseTestRegisterResetRecoveryEnd2End
):
    """Test the ABCI register-reset skill with 4 agents starting up."""

    agent_package = "valory/register_reset_recovery:0.1.0"
    skill_package = "valory/register_reset_recovery_abci:0.1.0"
    happy_path = HAPPY_PATH
    tm_break_string = TM_BREAK_STRING
    strict_check_strings = STRICT_CHECK_STRINGS
    wait_to_finish = 300
    package_registry_src_rel = Path(__file__).parents[4]
    __args_prefix = f"vendor.valory.skills.{PublicId.from_str(skill_package).name}.models.params.args"
    extra_configs = [
        {
            "dotted_path": f"{__args_prefix}.observation_interval",
            "value": 15,
        },
    ]
