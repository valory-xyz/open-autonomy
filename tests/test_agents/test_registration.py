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
import logging
import time

import pytest

from tests.fixture_helpers import UseACNNode, UseGnosisSafeHardHatNet
from tests.test_agents.base import (
    BaseTestEnd2EndAgentCatchup,
    BaseTestEnd2EndNormalExecution,
)


@pytest.fixture(autouse=True)
def slow_down_tests() -> None:
    """Sleep in between tests"""
    logging.info("SLOWING DOWN TESTS")
    yield
    time.sleep(1)


# strict check log messages of the happy path
STRICT_CHECK_STRINGS = (
    # "Local Tendermint configuration obtained",
    # "ServiceRegistryContract.getServiceInfo response",
    "Registered addresses retrieved from service registry contract",
    "Completed collecting Tendermint responses",
    # "Local TendermintNode updated",
    # "Tendermint node restarted",
    "RegistrationStartupBehaviour executed",
)


class RegistrationStartUpTestConfig(UseGnosisSafeHardHatNet, UseACNNode):
    """Base class for e2e tests using the ACN client connection"""

    skill_package = "valory/registration_abci:0.1.0"
    agent_package = "valory/registration_start_up:0.1.0"
    wait_to_finish = 60

    prefix = "vendor.valory.skills.registration_abci.models.params.args"

    extra_configs = [
        {
            "dotted_path": f"{prefix}.service_registry_address",
            "value": "0x0DCd1Bf9A1b36cE34237eEaFef220932846BCD82",
        },
        {
            "dotted_path": f"{prefix}.on_chain_service_id",
            "value": "1",
        },
    ]


@pytest.mark.e2e
@pytest.mark.integration
class TestRegistrationStartUpFourAgents(
    RegistrationStartUpTestConfig, BaseTestEnd2EndNormalExecution
):
    """Test registration start-up skill with four agents."""

    NB_AGENTS = 4
    strict_check_strings = STRICT_CHECK_STRINGS


@pytest.mark.e2e
@pytest.mark.integration  # NOTE: looks like other agents crash a little while after first one!
class TestRegistrationStartUpFourAgentsCatchUp(
    RegistrationStartUpTestConfig, BaseTestEnd2EndAgentCatchup
):
    """Test registration start-up skill with four agents and catch up."""

    NB_AGENTS = 4
    strict_check_strings = STRICT_CHECK_STRINGS
    stop_string = "My address: "
    restart_after = 10
