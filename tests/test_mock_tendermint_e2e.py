# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2026 Valory AG
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
# flake8: noqa: F811

"""
Mock Tendermint vs real Tendermint comparison test.

Runs the same single-agent register_reset service through both real Tendermint
and the MockServerChannel, asserting identical ABCI lifecycle behaviour.
This exercises all ABCI fundamentals:
  - info / init_chain handshake
  - begin_block / end_block / commit block lifecycle
  - transaction submission via HTTP (broadcast_tx_sync)
  - transaction delivery (deliver_tx)
  - transaction query (/tx?hash=...)
  - sync check (/status)
  - round transitions (registration → reset → registration ...)
"""

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
    UseMockTendermint,
    abci_host,
    abci_port,
    flask_tendermint,
    ipfs_daemon,
    ipfs_domain,
    key_pairs,
    tendermint_port,
)

from packages.valory.skills.registration_abci.rounds import RegistrationStartupRound
from packages.valory.skills.reset_pause_abci.rounds import ResetAndPauseRound

SKILL_PACKAGE = "valory/register_reset_abci:0.1.0"
_ARGS = (
    f"vendor.valory.skills.{PublicId.from_str(SKILL_PACKAGE).name}.models.params.args"
)

# With 1 agent, the app enters RegistrationStartupRound (no multi-agent handshake).
# Registration submits a tx (exercises broadcast_tx_sync → deliver_tx → round done).
# Reset submits a tx after a pause (exercises the full cycle again).
# Multiple periods prove the block lifecycle repeats correctly.
HAPPY_PATH = (
    RoundChecks(RegistrationStartupRound.auto_round_id()),
    RoundChecks(ResetAndPauseRound.auto_round_id(), n_periods=2),
)

# Comprehensive ABCI lifecycle strings that must appear in the agent logs.
# These cover every fundamental ABCI interaction.
ABCI_CHECK_STRINGS = (
    # ABCI handshake
    "Received ABCI request of type info",
    "Received ABCI request of type init_chain",
    # block lifecycle
    "Received ABCI request of type begin_block",
    "Received ABCI request of type end_block",
    "Received ABCI request of type commit",
    # transaction delivery
    "Received ABCI request of type deliver_tx",
    "deliver_tx succeeded",
    # sync check
    "Synchronization complete",
    # round transitions
    "Period end",
)

# single-agent configuration: no ACN needed, no TM config sharing
SINGLE_AGENT_CONFIGS = [
    {
        "dotted_path": f"{_ARGS}.share_tm_config_on_startup",
        "value": False,
    },
    {
        "dotted_path": f"{_ARGS}.reset_pause_duration",
        "value": 10,
    },
    {
        "dotted_path": "vendor.valory.connections.p2p_libp2p_client.is_abstract",
        "value": True,
    },
]


class _BaseRegisterResetSingleAgent(BaseTestEnd2EndExecution):
    """Base test: single-agent register_reset exercising all ABCI fundamentals."""

    agent_package = "valory/register_reset:0.1.0"
    skill_package = SKILL_PACKAGE
    happy_path = HAPPY_PATH
    strict_check_strings = ABCI_CHECK_STRINGS
    key_pairs = KEY_PAIRS
    wait_to_finish = 180
    package_registry_src_rel = Path(__file__).parent.parent / "packages"
    extra_configs = SINGLE_AGENT_CONFIGS


@pytest.mark.e2e
@pytest.mark.integration
@pytest.mark.parametrize("nb_nodes", (1,))
class TestRealTendermint(_BaseRegisterResetSingleAgent):
    """Run single-agent register_reset against real Tendermint (Docker)."""


@pytest.mark.e2e
@pytest.mark.parametrize("nb_nodes", (1,))
class TestMockTendermint(UseMockTendermint, _BaseRegisterResetSingleAgent):
    """Run the identical test against the MockServerChannel — no Docker Tendermint.

    Note: inherits the ``integration`` mark from ``BaseTestEnd2End`` because
    the IPFS daemon fixture still requires Docker.  Only the Tendermint
    dependency is removed.
    """
