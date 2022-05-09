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

"""Integration tests for the valory/registration skill."""

from typing import Any
import pytest

from tests.fixture_helpers import UseACNNode

from aea.test_tools.test_cases import AEATestCaseMany
from tests.test_agents.base import BaseTestEnd2EndNormalExecution
from tests.fixture_helpers import UseTendermint, ACNNodeBaseTest, UseGnosisSafeHardHatNet


# IntegrationBaseCase

@pytest.mark.e2e
@pytest.mark.integration
class TestRegistrationStartUpSkill(BaseTestEnd2EndNormalExecution, UseACNNode):
    """
    Test registration start-up skill.

    Requires Tendermint, the ACN and access to the on chain protocol service registry contract.
    See the RegistrationStartupBehaviour.async_act method for details.
    """

    NB_AGENTS = 1
    agent_package = "valory/oracle:0.1.0"  # "valory/registration_start_up:0.1.0"
    skill_package = "valory/oracle_abci:0.1.0"
    wait_to_finish = 180

    #
    # IS_LOCAL = False
    # capture_log = True
    # cli_log_options = ["-v", "DEBUG"]
    #
    # @classmethod
    # def _setup_class(cls, **kwargs) -> None:
    #     """Setup test."""
    #
    # # @classmethod
    # # def setup(cls, **kwargs: Any) -> None:
    # #     """Setup."""
    # #     super().setup()
    #
    # def test_run(self) -> None:
    #     """Run the ABCI skill."""
    #     agent_name = "registration_start_up_aea"
    #     # self.fetch_agent("valory/counter:0.1.0", agent_name, is_local=self.IS_LOCAL)
