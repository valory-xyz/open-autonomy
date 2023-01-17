# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022-2023 Valory AG
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

# pylint: skip-file

from pathlib import Path

import pytest
from aea.configurations.data_types import PublicId
from aea_test_autonomy.base_test_classes.agents import (
    BaseTestEnd2EndExecution,
    RoundChecks,
)
from aea_test_autonomy.configurations import KEY_PAIRS
from aea_test_autonomy.fixture_helpers import (  # noqa: F401
    abci_host,
    abci_port,
    ipfs_daemon,
    ipfs_domain,
    nb_nodes,
    tendermint_port,
)

from packages.valory.agents.register_reset.tests.helpers.conftest import (  # noqa: F401
    flask_tendermint,
)
from packages.valory.skills.registration_abci.rounds import (
    RegistrationRound,
    RegistrationStartupRound,
)
from packages.valory.skills.reset_pause_abci.rounds import ResetAndPauseRound


HAPPY_PATH = (
    RoundChecks(RegistrationStartupRound.auto_round_id()),
    RoundChecks(RegistrationRound.auto_round_id(), n_periods=2),
    RoundChecks(ResetAndPauseRound.auto_round_id(), n_periods=3),
)


@pytest.mark.e2e
@pytest.mark.integration
@pytest.mark.flaky(reruns=1)
@pytest.mark.parametrize("nb_nodes", (4,))
class TestRaceConditionTendermintReset(BaseTestEnd2EndExecution):
    """Test that ABCI register-reset skill with 4 agents when resetting Tendermint, with a slow Tendermint server."""

    agent_package = "valory/register_reset:0.1.0"
    skill_package = "valory/register_reset_abci:0.1.0"
    happy_path = HAPPY_PATH
    key_pairs = KEY_PAIRS
    wait_to_finish = 200
    __reset_tendermint_every = 1
    package_registry_src_rel = Path(__file__).parents[4]
    __args_prefix = f"vendor.valory.skills.{PublicId.from_str(skill_package).name}.models.params.args"
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
