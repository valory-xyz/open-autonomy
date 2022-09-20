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

# pylint: skip-file

import logging
import time
from pathlib import Path
from typing import Generator, Tuple

import pytest
from aea.configurations.data_types import PublicId
from aea_test_autonomy.base_test_classes.agents import (
    BaseTestEnd2End,
    BaseTestEnd2EndExecution,
    RoundChecks,
)
from aea_test_autonomy.fixture_helpers import (  # noqa: F401
    UseACNNode,
    UseRegistries,
    abci_host,
    abci_port,
    acn_config,
    acn_node,
    flask_tendermint,
    hardhat_port,
    key_pairs,
    nb_nodes,
    registries_scope_class,
    tendermint_port,
)

from packages.valory.skills.registration_abci.behaviours import (
    RegistrationStartupBehaviour,
)


log_messages = RegistrationStartupBehaviour.LogMessages


@pytest.fixture(autouse=True)
def slow_down_tests() -> Generator:
    """Sleep in between tests"""
    logging.info("SLOWING DOWN TESTS")
    yield
    time.sleep(1)


# strict check log messages of the happy path
STRICT_CHECK_STRINGS = (
    log_messages.request_personal.value,
    log_messages.response_personal.value,
    log_messages.request_verification.value,
    log_messages.response_verification.value,
    log_messages.request_others.value,
    log_messages.collection_complete.value,
    log_messages.request_update.value,
    log_messages.response_update.value,
    "local height == remote height; continuing execution...",
)


HAPPY_PATH = (RoundChecks("registration_startup"),)


class RegistrationStartUpTestConfig(UseRegistries, UseACNNode, BaseTestEnd2End):
    """Base class for e2e tests using the ACN client connection"""

    skill_package = "valory/registration_abci:0.1.0"
    agent_package = "valory/registration_start_up:0.1.0"
    wait_to_finish = 60
    happy_path = HAPPY_PATH
    strict_check_strings: Tuple[str, ...] = STRICT_CHECK_STRINGS
    __p2p_prefix = "vendor.valory.connections.p2p_libp2p_client"
    __args_prefix = f"vendor.valory.skills.{PublicId.from_str(skill_package).name}.models.params.args"
    extra_configs = [
        {
            "dotted_path": f"{__args_prefix}.share_tm_config_on_startup",
            "value": True,
        },
        {
            "dotted_path": f"vendor.valory.skills.{PublicId.from_str(skill_package).name}.is_abstract",
            "value": False,
        },
        {
            "dotted_path": f"{__args_prefix}.observation_interval",
            "value": 15,
        },
    ]


@pytest.mark.e2e
@pytest.mark.integration
@pytest.mark.parametrize("nb_nodes", (4,))
class TestRegistrationStartUpFourAgents(
    RegistrationStartUpTestConfig, BaseTestEnd2EndExecution
):
    """Test registration start-up skill with four agents."""

    package_registry_src_rel = Path(__file__).parent.parent.parent.parent.parent


@pytest.mark.e2e
@pytest.mark.integration
@pytest.mark.parametrize("nb_nodes", (4,))
class TestRegistrationStartUpFourAgentsCatchUp(
    RegistrationStartUpTestConfig, BaseTestEnd2EndExecution
):
    """Test registration start-up skill with four agents and catch up."""

    stop_string = "My address: "
    restart_after = 10
    n_terminal = 1
    package_registry_src_rel = Path(__file__).parent.parent.parent.parent.parent
