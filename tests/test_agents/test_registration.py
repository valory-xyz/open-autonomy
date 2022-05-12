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

from tests.test_agents.base import BaseTestEnd2EndNormalExecution
from tests.fixture_helpers import UseGnosisSafeHardHatNet


# strict check log messages of the happy path
STRICT_CHECK_STRINGS = (
    "Local Tendermint configuration obtained",
    "ServiceRegistryContract.getServiceInfo response",
    "Registered addresses retrieved from service registry contract",
    "Completed collecting Tendermint responses",
    "Local TendermintNode updated",
    "Tendermint node restarted",
)


class ACNClientConnectionEndToEndTestBase(BaseTestEnd2EndNormalExecution):
    """Base class for e2e tests using the ACN client connection"""

    skill_package = "valory/registration_abci:0.1.0"
    agent_package = "valory/registration_start_up:0.1.0"
    wait_to_finish = 120

    prefix = "vendor.valory.skills.registration_abci.models.params.args"

    extra_configs = [
        # {
        #     "dotted_path": f"{prefix}.tendermint_com_url",
        #     "value": "",
        # },
        {
            "dotted_path": f"{prefix}.service_registry_address",
            # "value": "0xa51c1fc2f0d1a1b8494ed1fe312d7c3a78ed91c0",
            # "value": "0xA51c1fc2f0D1a1b8494Ed1FE312d7C3a78Ed91C0",
            "value": "0x0DCd1Bf9A1b36cE34237eEaFef220932846BCD82",
        },
        {
            "dotted_path": f"{prefix}.on_chain_service_id",
            "value": "1",
        },
    ]


# @pytest.mark.e2e
# @pytest.mark.integration
# class TestRegistrationStartUpSingleAgent(ACNClientConnectionEndToEndTestBase, UseGnosisSafeHardHatNet, UseACNNode):
#     """Test registration start-up skill with a single agent."""
#
#     # NOTE: is a single agents, it cannot obtain other information, fails at the moment
#     NB_AGENTS = 1
#     strict_check_strings = STRICT_CHECK_STRINGS
#
#
# @pytest.mark.e2e
# @pytest.mark.integration
# class TestRegistrationStartUpTwoAgents(ACNClientConnectionEndToEndTestBase, UseGnosisSafeHardHatNet, UseACNNode):
#     """Test registration start-up skill with two agents."""
#
#     NB_AGENTS = 2
#     strict_check_strings = STRICT_CHECK_STRINGS


@pytest.mark.e2e
@pytest.mark.integration
class TestRegistrationStartUpFourAgents(ACNClientConnectionEndToEndTestBase, UseGnosisSafeHardHatNet, UseACNNode):
    """Test registration start-up skill with two agents."""

    NB_AGENTS = 4
    strict_check_strings = STRICT_CHECK_STRINGS