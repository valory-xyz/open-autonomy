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

"""Integration tests for the valory/apy_estimation skill."""

import json
import logging
from pathlib import Path
from typing import List

from aea.test_tools.test_cases import AEATestCaseMany

from tests.fixture_helpers import UseGnosisSafeHardHatNet
from tests.helpers.tendermint_utils import (
    BaseTendermintTestClass,
    TendermintLocalNetworkBuilder,
)


# check log messages of the happy path
CHECK_STRINGS = [
    "Entered in the 'tendermint_healthcheck' behaviour state",
    "'tendermint_healthcheck' behaviour state is done",
]

states_checks_config = {
    "registration": {
        "state_name": "registration",
        "extra_logs": (),
        "only_at_first_period": False,
    },
    "collect_history": {
        "state_name": "collect_history",
        "extra_logs": (
            "Retrieved top ",
            "Retrieved block: ",
            "Retrieved ETH price for block ",
            "Retrieved top ",
        ),
        "only_at_first_period": False,
    },
    "transform": {
        "state_name": "transform",
        "extra_logs": ("Data have been transformed. Showing the first row:\n",),
        "only_at_first_period": False,
    },
    "preprocess": {
        "state_name": "preprocess",
        "extra_logs": ("Data have been preprocessed.",),
        "only_at_first_period": False,
    },
    "optimize": {
        "state_name": "optimize",
        "extra_logs": ("Optimization has finished. Showing the results:\n",),
        "only_at_first_period": False,
    },
    "train": {
        "state_name": "train",
        "extra_logs": ("Training has finished.",),
        "only_at_first_period": False,
    },
    "test": {
        "state_name": "test",
        "extra_logs": ("Testing has finished. Report follows:\n",),
        "only_at_first_period": False,
    },
    "full_train": {
        "state_name": "train",
        "extra_logs": ("Training has finished.",),
        "only_at_first_period": False,
    },
    "estimate": {
        "state_name": "estimate",
        "extra_logs": ("Got estimate of APY for ",),
        "only_at_first_period": False,
    },
    "cycle_reset": {
        "state_name": "cycle_reset",
        "extra_logs": ("Finalized estimate: ", "Period end."),
        "only_at_first_period": False,
    },
}


def build_check_strings() -> None:
    """Build check strings based on the `states_checks_config`."""
    for period in (0, 1):
        for _, config in states_checks_config.items():
            if period == 0:
                CHECK_STRINGS.append(
                    f"Entered in the '{config['state_name']}' round for period {period}"
                )

                for log in config["extra_logs"]:
                    CHECK_STRINGS.append(log)

                CHECK_STRINGS.append(f"'{config['state_name']}' round is done")

            elif not config["only_at_first_period"]:
                CHECK_STRINGS.append(
                    f"Entered in the '{config['state_name']}' round for period {period}"
                )


build_check_strings()


class BaseTestABCIAPYEstimationSkill(
    AEATestCaseMany, BaseTendermintTestClass, UseGnosisSafeHardHatNet
):
    """
    Base class for APY estimation skill tests.

    The setup test function of this class will configure a set of 'n'
    agents with the APY estimation skill, and a Tendermint network
    of 'n' nodes, one for each agent.

    Test subclasses must set NB_AGENTS.
    """

    NB_AGENTS: int
    IS_LOCAL = True
    capture_log = True
    KEEPER_TIMEOUT = 10
    cli_log_options = ["-v", "DEBUG"]
    processes: List

    def setup(self) -> None:
        """Set up the test."""
        self.agent_names = [f"agent_{i:05d}" for i in range(self.NB_AGENTS)]
        self.processes = []
        self.create_agents(*self.agent_names, is_local=self.IS_LOCAL)
        self.tendermint_net_builder = TendermintLocalNetworkBuilder(
            self.NB_AGENTS, Path(self.t)
        )

        for agent_id, agent_name in enumerate(self.agent_names):
            logging.debug(f"Processing agent {agent_name}...")
            node = self.tendermint_net_builder.nodes[agent_id]
            self.set_agent_context(agent_name)
            Path(self.current_agent_context, "ethereum_private_key.txt").write_text(
                self.key_pairs[agent_id][1]
            )
            self.add_private_key("ethereum", "ethereum_private_key.txt")
            self.set_config("agent.default_ledger", "ethereum")
            self.set_config("agent.required_ledgers", '["ethereum"]', type_="list")
            self.add_item("skill", "valory/apy_estimation:0.1.0", local=False)
            self.set_config(
                "vendor.valory.connections.abci.config.target_skill_id",
                "valory/apy_estimation:0.1.0",
            )
            # each agent has its Tendermint node instance
            self.set_config(
                "vendor.valory.connections.abci.config.use_tendermint", True
            )
            self.set_config(
                "vendor.valory.connections.abci.config.tendermint_config.consensus_create_empty_blocks",
                True,
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
                "vendor.valory.skills.apy_estimation.models.params.args.consensus.max_participants",
                self.NB_AGENTS,
            )
            self.set_config(
                "vendor.valory.skills.apy_estimation.models.params.args.round_timeout_seconds",
                self.KEEPER_TIMEOUT,
            )
            self.set_config(
                "vendor.valory.skills.apy_estimation.models.params.args.tendermint_url",
                node.get_http_addr("localhost"),
            )

        # run 'aea install' in only one AEA project, to save time
        self.set_agent_context(self.agent_names[0])
        self.run_install()

    def _launch_agent_i(self, i: int) -> None:
        """Launch the i-th agent."""
        agent_name = self.agent_names[i]
        logging.debug(f"Launching agent {agent_name}...")
        self.set_agent_context(agent_name)
        process = self.run_agent()
        self.processes.append(process)


class BaseTestABCIAPYEstimationSkillNormalExecution(BaseTestABCIAPYEstimationSkill):
    """Test that the ABCI apy_estimation skill works together with Tendermint under normal circumstances."""

    def test_run(self) -> None:
        """Run the ABCI skill."""
        for agent_id in range(self.NB_AGENTS):
            self._launch_agent_i(agent_id)

        logging.info("Waiting Tendermint nodes to be up")
        self.health_check(
            self.tendermint_net_builder, max_retries=20, sleep_interval=3.0
        )

        # check that *each* AEA prints these messages
        for process in self.processes:
            missing_strings = self.missing_from_output(process, CHECK_STRINGS, 120)
            assert (
                missing_strings == []
            ), "Strings {} didn't appear in agent output.".format(missing_strings)

            assert self.is_successfully_terminated(
                process
            ), "ABCI agent wasn't successfully terminated."


class TestABCIAPYEstimationSingleAgent(
    BaseTestABCIAPYEstimationSkillNormalExecution,
    BaseTendermintTestClass,
    UseGnosisSafeHardHatNet,
):
    """Test that the ABCI apy_estimation skill with only one agent."""

    NB_AGENTS = 1


class TestABCIAPYEstimationTwoAgents(
    BaseTestABCIAPYEstimationSkillNormalExecution,
    BaseTendermintTestClass,
    UseGnosisSafeHardHatNet,
):
    """Test that the ABCI apy_estimation skill with two agents."""

    NB_AGENTS = 2


class TestABCIAPYEstimationFourAgents(
    BaseTestABCIAPYEstimationSkillNormalExecution,
    BaseTendermintTestClass,
    UseGnosisSafeHardHatNet,
):
    """Test that the ABCI apy_estimation skill with four agents."""

    NB_AGENTS = 4
