# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022-2023 Valory AG
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
from aea_test_autonomy.base_test_classes.agents import BaseTestEnd2EndExecution
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


TARGET_AGENT = "valory/test_ipfs:0.1.0"
TARGET_SKILL = "valory/test_ipfs_abci:0.1.0"
TIME_TO_FINISH = 60  # 1 minute


@pytest.mark.e2e
@pytest.mark.integration
@pytest.mark.parametrize("nb_nodes", (1,))
class TestIpfs(
    BaseTestEnd2EndExecution,
):
    """Test whether uploading and receiving from IPFS works.."""

    package_registry_src_rel = Path(__file__).parents[4]
    agent_package = TARGET_AGENT
    skill_package = TARGET_SKILL
    wait_to_finish = TIME_TO_FINISH
    strict_check_strings = (
        "Single object uploading & downloading works.",
        "Multiple object uploading & downloading works.",
    )
