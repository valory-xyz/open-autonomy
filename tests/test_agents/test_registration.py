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
import pytest

from tests.fixture_helpers import UseACNNode

from aea.test_tools.test_cases import AEATestCaseMany
from tests.fixture_helpers import UseTendermint


# IntegrationBaseCase

@pytest.mark.e2e
@pytest.mark.integration
class TestRegistrationStartUpSkill(AEATestCaseMany, UseTendermint):  #, UseACNNode):
    """Test registration start up skill interaction with Tendermint and the ACN."""

    IS_LOCAL = True
    capture_log = True
    cli_log_options = ["-v", "DEBUG"]

    def test_run(self) -> None:
        """Run the ABCI skill."""
        agent_name = "registration_start_up_aea"


