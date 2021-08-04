# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021 Valory AG
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

"""Integration tests for the valory/counter skill."""
import json
import logging
import time
from pathlib import Path

import pytest
from aea.test_tools.test_cases import AEATestCaseEmpty, AEATestCaseMany

from tests.conftest import UseTendermint
from tests.helpers.tendermint_utils import TendermintLocalNetworkBuilder


@pytest.mark.integration
class TestABCICounterSkill(AEATestCaseEmpty, UseTendermint):
    """Test that the ABCI counter skill works together with Tendermint."""

    IS_LOCAL = False
    capture_log = True

    def test_run(self):
        """Run the ABCI skill."""
        self.generate_private_key()
        self.add_private_key()
        self.add_item("skill", "valory/counter:0.1.0")
        self.set_config(
            "vendor.valory.connections.abci.config.target_skill_id",
            "valory/counter:0.1.0",
        )
        self.set_config("vendor.valory.connections.abci.config.use_tendermint", False)

        process = self.run_agent()
        is_running = self.is_running(process)
        assert is_running, "AEA not running within timeout!"

        time.sleep(2.0)

        check_strings = (
            "ABCI Handler: setup method called.",
            "Received ABCI request of type info",
            "Received ABCI request of type flush",
            "Received ABCI request of type begin_block",
            "Received ABCI request of type commit",
            "Received ABCI request of type end_block",
        )
        missing_strings = self.missing_from_output(process, check_strings)
        assert (
            missing_strings == []
        ), "Strings {} didn't appear in agent output.".format(missing_strings)

        assert (
            self.is_successfully_terminated()
        ), "ABCI agent wasn't successfully terminated."


class TestABCICounterSkillMany(AEATestCaseMany):
    """Test that the ABCI counter skill works together with Tendermint."""

    IS_LOCAL = False
    capture_log = True
    NB_AGENTS = 4

    def test_run(self):
        """Run the ABCI skill."""
        agent_names = [f"agent_{i:05d}" for i in range(self.NB_AGENTS)]
        processes = []
        self.create_agents(*agent_names, is_local=self.IS_LOCAL)
        tendermint_net_builder = TendermintLocalNetworkBuilder(
            self.NB_AGENTS, Path(self.t)
        )

        for agent_id, agent_name in enumerate(agent_names):
            logging.debug(f"Processing agent {agent_name}...")
            node = tendermint_net_builder.nodes[agent_id]
            self.set_agent_context(agent_name)
            self.generate_private_key()
            self.add_private_key()
            self.add_item("skill", "valory/counter:0.1.0")
            self.set_config(
                "vendor.valory.connections.abci.config.target_skill_id",
                "valory/counter:0.1.0",
            )
            # each agent has its Tendermint node instance
            self.set_config(
                "vendor.valory.connections.abci.config.use_tendermint", True
            )
            self.set_config(
                "vendor.valory.connections.abci.config.tendermint_config.consensus_create_empty_blocks",
                False,
            )

            self.set_config(
                "vendor.valory.connections.abci.config.port",
                node.abci_port,
            )
            self.set_config(
                "vendor.valory.connections.abci.config.tendermint_config.rpc_laddr",
                node.rpc_laddr,
            )
            self.set_config(
                "vendor.valory.connections.abci.config.tendermint_config.p2p_laddr",
                node.p2p_laddr,
            )
            self.set_config(
                "vendor.valory.connections.abci.config.tendermint_config.home",
                str(node.home),
            )
            self.set_config(
                "vendor.valory.connections.abci.config.tendermint_config.p2p_seeds",
                json.dumps(tendermint_net_builder.get_p2p_seeds()),
                "list",
            )
            process = self.run_agent()
            processes.append(process)

        time.sleep(5.0)

        check_strings = (
            "ABCI Handler: setup method called.",
            "Received ABCI request of type info",
            "Received ABCI request of type flush",
            "Received ABCI request of type begin_block",
            "Received ABCI request of type commit",
            "Received ABCI request of type end_block",
        )

        for process in processes:
            missing_strings = self.missing_from_output(process, check_strings)
            assert (
                missing_strings == []
            ), "Strings {} didn't appear in agent output.".format(missing_strings)

            assert self.is_successfully_terminated(
                process
            ), "ABCI agent wasn't successfully terminated."
