# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2022 Valory AG
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

"""End2end tests for the valory/hello_world skill."""

# pylint: skip-file

from pathlib import Path
from typing import Tuple

import pytest
from aea_test_autonomy.base_test_classes.agents import (
    BaseTestEnd2EndExecution,
    RoundChecks,
)
from aea_test_autonomy.fixture_helpers import (  # noqa: F401
    abci_host,
    abci_port,
    flask_tendermint,
    tendermint_port,
)


HAPPY_PATH = (
    RoundChecks("registration"),
    RoundChecks("print_message", n_periods=3),
    RoundChecks("collect_randomness", n_periods=3),
    RoundChecks("select_keeper", n_periods=2),
    RoundChecks("reset_and_pause", n_periods=2),
)

# strict check log messages of the happy path
STRICT_CHECK_STRINGS = (
    "Period end",
    " in period 0 says: HELLO_WORLD!",
    " in period 1 says: HELLO_WORLD!",
    " in period 2 says: HELLO_WORLD!",
    " in period 3 says: HELLO_WORLD!",
)


# normal execution
class BaseHelloWorldABCITest(
    BaseTestEnd2EndExecution,
):
    """Test the hello_world_abci skill with four agents."""

    agent_package = "valory/hello_world:0.1.0"
    skill_package = "valory/hello_world_abci:0.1.0"
    wait_to_finish = 160
    happy_path = HAPPY_PATH
    strict_check_strings: Tuple[str, ...] = STRICT_CHECK_STRINGS
    package_registry_src_rel = Path(__file__).parent.parent.parent.parent.parent


@pytest.mark.usefixtures(
    "flask_tendermint", "tendermint_port", "abci_host", "abci_port"
)
@pytest.mark.parametrize("nb_nodes", (1,))
class TestHelloWorldABCISingleAgent(BaseHelloWorldABCITest):
    """Test the hello_world_abci skill with only one agent."""


@pytest.mark.usefixtures(
    "flask_tendermint", "tendermint_port", "abci_host", "abci_port"
)
@pytest.mark.parametrize("nb_nodes", (2,))
class TestHelloWorldABCITwoAgents(BaseHelloWorldABCITest):
    """Test the hello_world_abci skill with two agents."""


@pytest.mark.usefixtures(
    "flask_tendermint", "tendermint_port", "abci_host", "abci_port"
)
@pytest.mark.parametrize("nb_nodes", (4,))
class TestHelloWorldABCIFourAgents(BaseHelloWorldABCITest):
    """Test the hello_world_abci skill with four agents."""


# catchup test
class BaseHelloWorldABCITestCatchup(BaseHelloWorldABCITest):
    """Test the hello_world_abci skill with catch up behaviour."""

    stop_string = "register"
    restart_after = 10
    n_terminal = 1


# four behaviours and different stages of termination and restart
@pytest.mark.parametrize("nb_nodes", (4,))
class TestHelloWorldABCIFourAgentsCatchupOnRegister(BaseHelloWorldABCITestCatchup):
    """Test hello_world_abci skill with four agents; one restarting on `register`."""

    stop_string = "register"


@pytest.mark.parametrize("nb_nodes", (4,))
class TestHelloWorldABCIFourAgentsCatchupRetrieveRandomness(
    BaseHelloWorldABCITestCatchup
):
    """Test hello_world_abci skill with four agents; one restarting on `collect_randomness`."""

    stop_string = "collect_randomness"


@pytest.mark.parametrize("nb_nodes", (4,))
class TestHelloWorldABCIFourAgentsCatchupSelectKeeper(BaseHelloWorldABCITestCatchup):
    """Test hello_world_abci skill with four agents; one restarting on `select_keeper`."""

    stop_string = "select_keeper"


# multiple agents terminating and restarting
@pytest.mark.parametrize("nb_nodes", (4,))
class TestHelloWorldABCIFourAgentsTwoAgentRestarting(BaseHelloWorldABCITestCatchup):
    """Test the hello_world_abci skill with four agents and two restarting."""

    n_terminal = 2


@pytest.mark.skip(reason="not working atm")
@pytest.mark.parametrize("nb_nodes", (1,))
class TestHelloWorldABCISingleAgentGrpc(
    BaseHelloWorldABCITest,
):
    """Test that the hello_world_abci skill with only one agent."""

    USE_GRPC = True
    strict_check_strings = STRICT_CHECK_STRINGS + ("Starting gRPC server",)


@pytest.mark.skip(reason="not working atm")
@pytest.mark.parametrize("nb_nodes", (2,))
class TestHelloWorldABCITwoAgentsGrpc(
    BaseHelloWorldABCITest,
):
    """Test that the hello_world_abci skill with two agents."""

    USE_GRPC = True
    strict_check_strings = STRICT_CHECK_STRINGS + ("Starting gRPC server",)


@pytest.mark.skip(reason="not working atm")
@pytest.mark.parametrize("nb_nodes", (4,))
class TestHelloWorldABCIFourAgentsGrpc(
    BaseHelloWorldABCITest,
):
    """Test that the hello_world_abci skill with four agents."""

    USE_GRPC = True
    strict_check_strings = STRICT_CHECK_STRINGS + ("Starting gRPC server",)
