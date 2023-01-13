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

"""End2end tests for the valory/hello_world skill."""

# pylint: skip-file

from pathlib import Path
from typing import Tuple

import pytest
from aea_test_autonomy.base_test_classes.agents import (
    BaseTestEnd2EndExecution,
    RoundChecks,
)
from aea_test_autonomy.configurations import KEY_PAIRS
from aea_test_autonomy.fixture_helpers import (  # noqa: F401
    abci_host,
    abci_port,
    flask_tendermint,
    ipfs_daemon,
    ipfs_domain,
    tendermint_port,
)

from packages.valory.skills.hello_world_abci.behaviours import (
    CollectRandomnessBehaviour,
    RegistrationBehaviour,
    SelectKeeperBehaviour,
)
from packages.valory.skills.hello_world_abci.rounds import (
    CollectRandomnessRound,
    PrintMessageRound,
    RegistrationRound,
    ResetAndPauseRound,
    SelectKeeperRound,
)


HAPPY_PATH = (
    RoundChecks(RegistrationRound.auto_round_id()),
    RoundChecks(PrintMessageRound.auto_round_id(), n_periods=3),
    RoundChecks(CollectRandomnessRound.auto_round_id(), n_periods=3),
    RoundChecks(SelectKeeperRound.auto_round_id(), n_periods=2),
    RoundChecks(ResetAndPauseRound.auto_round_id(), n_periods=2),
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
@pytest.mark.e2e
class BaseHelloWorldABCITest(
    BaseTestEnd2EndExecution,
):
    """Test the hello_world_abci skill with four agents."""

    agent_package = "valory/hello_world:0.1.0"
    skill_package = "valory/hello_world_abci:0.1.0"
    wait_to_finish = 160
    happy_path = HAPPY_PATH
    key_pairs = KEY_PAIRS
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

    stop_string = RegistrationBehaviour.auto_behaviour_id()
    restart_after = 10
    n_terminal = 1


# four behaviours and different stages of termination and restart
@pytest.mark.parametrize("nb_nodes", (4,))
class TestHelloWorldABCIFourAgentsCatchupOnRegister(BaseHelloWorldABCITestCatchup):
    """Test hello_world_abci skill with four agents; one restarting on `register`."""

    stop_string = RegistrationBehaviour.auto_behaviour_id()


@pytest.mark.parametrize("nb_nodes", (4,))
class TestHelloWorldABCIFourAgentsCatchupRetrieveRandomness(
    BaseHelloWorldABCITestCatchup
):
    """Test hello_world_abci skill with four agents; one restarting on `collect_randomness`."""

    stop_string = CollectRandomnessBehaviour.auto_behaviour_id()


@pytest.mark.parametrize("nb_nodes", (4,))
class TestHelloWorldABCIFourAgentsCatchupSelectKeeper(BaseHelloWorldABCITestCatchup):
    """Test hello_world_abci skill with four agents; one restarting on `select_keeper`."""

    stop_string = SelectKeeperBehaviour.auto_behaviour_id()


# multiple agents terminating and restarting
@pytest.mark.parametrize("nb_nodes", (4,))
class TestHelloWorldABCIFourAgentsTwoAgentRestarting(BaseHelloWorldABCITestCatchup):
    """Test the hello_world_abci skill with four agents and two restarting."""

    n_terminal = 2


@pytest.mark.skip(reason="https://github.com/valory-xyz/open-autonomy/issues/1709")
@pytest.mark.parametrize("nb_nodes", (1,))
class TestHelloWorldABCISingleAgentGrpc(
    BaseHelloWorldABCITest,
):
    """Test that the hello_world_abci skill with only one agent."""

    USE_GRPC = True
    strict_check_strings = STRICT_CHECK_STRINGS + ("Starting gRPC server",)


@pytest.mark.skip(reason="https://github.com/valory-xyz/open-autonomy/issues/1709")
@pytest.mark.parametrize("nb_nodes", (2,))
class TestHelloWorldABCITwoAgentsGrpc(
    BaseHelloWorldABCITest,
):
    """Test that the hello_world_abci skill with two agents."""

    USE_GRPC = True
    strict_check_strings = STRICT_CHECK_STRINGS + ("Starting gRPC server",)


@pytest.mark.skip(reason="https://github.com/valory-xyz/open-autonomy/issues/1709")
@pytest.mark.parametrize("nb_nodes", (4,))
class TestHelloWorldABCIFourAgentsGrpc(
    BaseHelloWorldABCITest,
):
    """Test that the hello_world_abci skill with four agents."""

    USE_GRPC = True
    strict_check_strings = STRICT_CHECK_STRINGS + ("Starting gRPC server",)
