# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
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

import pytest
from aea_test_autonomy.fixture_helpers import (  # noqa: F401
    abci_host,
    abci_port,
    flask_tendermint,
    tendermint_port,
)

from packages.valory.agents.register_termination.tests.base import (
    BaseTestTerminationEnd2End,
)
from packages.valory.agents.register_termination.tests.fixtures import (
    UseHardHatRegistriesTest,
)


TARGET_AGENT = "valory/register_termination:0.1.0"
TARGET_SKILL = "valory/register_termination_abci:0.1.0"
TIME_TO_FINISH = 60  # 1 minute

REGISTRATION_CHECK_STRINGS = (
    "Entered in the 'registration_startup' round for period 0",
    "'registration_startup' round is done",
)
TRANSACTION_SUBMISSION_STRINGS = (
    "Entered in the 'validate_transaction' round for period 0",
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
    UseHardHatRegistriesTest,
):
    """Test that termination works right."""

    agent_package = TARGET_AGENT
    skill_package = TARGET_SKILL
    wait_to_finish = TIME_TO_FINISH
    strict_check_strings = (
        REGISTRATION_CHECK_STRINGS
        + TERMINATION_STRINGS
        + TRANSACTION_SUBMISSION_STRINGS
    )
