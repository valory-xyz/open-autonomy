# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022-2024 Valory AG
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
# pylint: disable=unused-import

"""Integration tests for the valory/register_termination skill."""
from pathlib import Path

import pytest
from aea_test_autonomy.fixture_helpers import (  # noqa: F401
    UseRegistries,
    abci_host,
    abci_port,
    flask_tendermint,
    hardhat_addr,
    hardhat_port,
    ipfs_daemon,
    ipfs_domain,
    key_pairs,
    registries_scope_class,
    tendermint_port,
)

from packages.valory.agents.register_termination.tests.base import (
    BaseTestTerminationEnd2End,
)
from packages.valory.skills.registration_abci.rounds import RegistrationStartupRound
from packages.valory.skills.transaction_settlement_abci.rounds import (
    ValidateTransactionRound,
)


TARGET_AGENT = "valory/register_termination:0.1.0"
TARGET_SKILL = "valory/register_termination_abci:0.1.0"
TIME_TO_FINISH = 60  # 1 minute

REGISTRATION_CHECK_STRINGS = (
    f"Entered in the '{RegistrationStartupRound.auto_round_id()}' round for period",
    f"'{RegistrationStartupRound.auto_round_id()}' round is done",
)
TRANSACTION_SUBMISSION_STRINGS = (
    f"Entered in the '{ValidateTransactionRound.auto_round_id()}' round for period",
    "Verified result: True",
)
TERMINATION_STRINGS = (
    "Termination signal was picked up, preparing termination transaction.",
    "Successfully prepared termination multisend tx.",
)


@pytest.mark.e2e
@pytest.mark.integration
@pytest.mark.parametrize("nb_nodes", (4,))
class TestTermination(
    BaseTestTerminationEnd2End,
    UseRegistries,
):
    """Test that termination works right."""

    package_registry_src_rel = Path(__file__).parents[4]
    agent_package = TARGET_AGENT
    skill_package = TARGET_SKILL
    wait_to_finish = TIME_TO_FINISH
    strict_check_strings = (
        REGISTRATION_CHECK_STRINGS
        + TERMINATION_STRINGS
        + TRANSACTION_SUBMISSION_STRINGS
    )
