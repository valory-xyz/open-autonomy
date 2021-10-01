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

"""Integration tests for the valory/price_estimation_abci skill."""
import json
import logging
from pathlib import Path

from aea.test_tools.test_cases import AEATestCaseMany

from tests.fixture_helpers import UseGnosisSafeHardHatNet
from tests.helpers.tendermint_utils import (
    BaseTendermintTestClass,
    TendermintLocalNetworkBuilder,
)


class TestABCIPriceEstimationSkillMany(
    AEATestCaseMany, BaseTendermintTestClass, UseGnosisSafeHardHatNet
):
    """Test that the ABCI price_estimation skill works together with Tendermint."""

    IS_LOCAL = False
    capture_log = True
    NB_AGENTS = 4
    NB_OWNERS = NB_AGENTS
    THRESHOLD = NB_AGENTS * 2 // 3 + 1
    NB_KEEPER_TIMEOUT = 5
    SOLIDITY_VERSION = "v0.7.6"
    cli_log_options = ["-v", "DEBUG"]

    def test_run(self):
        """Run the ABCI skill."""
        self.agent_names = [f"agent_{i:05d}" for i in range(self.NB_AGENTS)]
        processes = []
        self.create_agents(*self.agent_names, is_local=self.IS_LOCAL)
        self.tendermint_net_builder = TendermintLocalNetworkBuilder(
            self.NB_AGENTS, Path(self.t)
        )

        for agent_id, agent_name in enumerate(self.agent_names):
            logging.debug(f"Processing agent {agent_name}...")
            node = self.tendermint_net_builder.nodes[agent_id]
            self.set_agent_context(agent_name)
            Path(self.current_agent_context, "ethereum_private_key.txt").write_text(
                self.hardhat_key_pairs[agent_id][1]
            )
            self.add_private_key("ethereum", "ethereum_private_key.txt")
            self.set_config("agent.default_ledger", "ethereum")
            self.set_config("agent.required_ledgers", '["ethereum"]', type_="list")
            self.add_item("skill", "valory/price_estimation_abci:0.1.0", local=False)
            self.set_config(
                "vendor.valory.connections.abci.config.target_skill_id",
                "valory/price_estimation_abci:0.1.0",
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
                json.dumps(self.tendermint_net_builder.get_p2p_seeds()),
                "list",
            )
            self.set_config(
                "vendor.valory.skills.price_estimation_abci.models.params.args.consensus.max_participants",
                self.NB_AGENTS,
            )
            self.set_config(
                "vendor.valory.skills.price_estimation_abci.models.params.args.keeper_timeout_seconds",
                self.NB_KEEPER_TIMEOUT,
            )
            self.set_config(
                "vendor.valory.skills.price_estimation_abci.models.params.args.solidity_version",
                self.SOLIDITY_VERSION,
            )
            self.set_config(
                "vendor.valory.skills.price_estimation_abci.models.params.args.tendermint_url",
                node.get_http_addr("localhost"),
            )

        # run 'aea install' in only one AEA project, to save time
        self.set_agent_context(self.agent_names[0])
        self.run_install()

        for agent_name in self.agent_names:
            logging.debug(f"Launching agent {agent_name}...")
            self.set_agent_context(agent_name)
            process = self.run_agent()
            processes.append(process)

        logging.info("Waiting Tendermint nodes to be up")
        self.health_check(
            self.tendermint_net_builder, max_retries=20, sleep_interval=3.0
        )

        check_strings = (
            "Entered in the 'register' behaviour state",
            "'register' behaviour state is done",
            "Entered in the 'deploy_safe' behaviour state",
            "'deploy_safe' behaviour state is done",
            "Entered in the 'observe' behaviour state",
            "Got observation of BTC price in USD",
            "'observe' behaviour state is done",
            "Entered in the 'estimate' behaviour state",
            "Got estimate of BTC price in USD:",
            "'estimate' behaviour state is done",
            "Entered in the 'tx_hash' behaviour state",
            "'tx_hash' behaviour state is done",
            "Entered in the 'sign' behaviour state",
            "Signature:",
            "'sign' behaviour state is done",
            "Entered in the 'finalize' behaviour state",
            "'finalize' behaviour state is done",
            "Finalized estimate",
            "Period end",
        )
        # check that *each* AEA prints these messages
        for process in processes:
            missing_strings = self.missing_from_output(process, check_strings)
            assert (
                missing_strings == []
            ), "Strings {} didn't appear in agent output.".format(missing_strings)

            assert self.is_successfully_terminated(
                process
            ), "ABCI agent wasn't successfully terminated."
