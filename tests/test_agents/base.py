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

"""End2end tests base class."""
import json
import logging
import time
import warnings
from pathlib import Path
from typing import List, Tuple

import pytest
from aea.configurations.base import PublicId
from aea.test_tools.test_cases import AEATestCaseMany

from tests.helpers.tendermint_utils import (
    BaseTendermintTestClass,
    TendermintLocalNetworkBuilder,
)


@pytest.mark.e2e
class BaseTestEnd2End(AEATestCaseMany, BaseTendermintTestClass):
    """
    Base class for end-to-end tests of agents with a skill extending the abstract_abci_round skill.

    The setup test function of this class will configure a set of 'n'
    agents with the configured (agent_package) agent, and a Tendermint network
    of 'n' nodes, one for each agent.

    Test subclasses must set NB_AGENTS, agent_package, wait_to_finish and check_strings.
    """

    NB_AGENTS: int
    IS_LOCAL = True
    capture_log = True
    KEEPER_TIMEOUT = 10
    HEALTH_CHECK_MAX_RETRIES = 20
    HEALTH_CHECK_SLEEP_INTERVAL = 3.0
    cli_log_options = ["-v", "DEBUG"]
    processes: List
    agent_package: str
    skill_package: str
    wait_to_finish: int
    check_strings: Tuple[str, ...]

    def setup(self) -> None:
        """Set up the test."""
        self.agent_names = [f"agent_{i:05d}" for i in range(self.NB_AGENTS)]
        self.processes = []
        self.tendermint_net_builder = TendermintLocalNetworkBuilder(
            self.NB_AGENTS, Path(self.t)
        )

        for agent_id, agent_name in enumerate(self.agent_names):
            logging.debug(f"Processing agent {agent_name}...")
            node = self.tendermint_net_builder.nodes[agent_id]
            self.fetch_agent(self.agent_package, agent_name, is_local=self.IS_LOCAL)
            self.set_agent_context(agent_name)
            if hasattr(self, "key_pairs"):
                Path(self.current_agent_context, "ethereum_private_key.txt").write_text(
                    self.key_pairs[agent_id][1]  # type: ignore
                )
            else:
                self.generate_private_key("ethereum", "ethereum_private_key.txt")
            self.add_private_key("ethereum", "ethereum_private_key.txt")
            # each agent has its Tendermint node instance
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
                f"vendor.valory.skills.{PublicId.from_str(self.skill_package).name}.models.params.args.consensus.max_participants",
                self.NB_AGENTS,
            )
            self.set_config(
                f"vendor.valory.skills.{PublicId.from_str(self.skill_package).name}.models.params.args.reset_tendermint_after",
                5,
            )
            self.set_config(
                f"vendor.valory.skills.{PublicId.from_str(self.skill_package).name}.models.params.args.round_timeout_seconds",
                self.KEEPER_TIMEOUT,
            )
            self.set_config(
                f"vendor.valory.skills.{PublicId.from_str(self.skill_package).name}.models.params.args.tendermint_url",
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


class BaseTestEnd2EndNormalExecution(BaseTestEnd2End):
    """Test that the ABCI simple skill works together with Tendermint under normal circumstances."""

    def test_run(self) -> None:
        """Run the ABCI skill."""
        for agent_id in range(self.NB_AGENTS):
            self._launch_agent_i(agent_id)

        logging.info("Waiting Tendermint nodes to be up")
        self.health_check(
            self.tendermint_net_builder,
            max_retries=self.HEALTH_CHECK_MAX_RETRIES,
            sleep_interval=self.HEALTH_CHECK_SLEEP_INTERVAL,
        )

        # check that *each* AEA prints these messages
        for process in self.processes:
            missing_strings = self.missing_from_output(
                process, self.check_strings, self.wait_to_finish
            )
            assert (
                missing_strings == []
            ), "Strings {} didn't appear in agent output.".format(missing_strings)

            if not self.is_successfully_terminated(process):
                warnings.warn(
                    UserWarning(
                        f"ABCI agent with process {process} wasn't successfully terminated."
                    )
                )


class BaseTestEnd2EndAgentCatchup(BaseTestEnd2End):
    """
    Test that an agent that is launched later can synchronize with the rest of the network

    - each agent starts, and sets up the ABCI connection, which in turn spawns both an ABCI
      server and a local Tendermint node (using the configuration folders we set up previously).
      The Tendermint node is unique for each agent
    - when we will stop one agent, also the ABCI server created by the ABCI connection will
      stop, and in turn the Tendermint node will stop. In particular, it does not keep polling
      the endpoint until it is up again, it just stops.
    - when we will restart the previously stopped agent, the ABCI connection will set up again
      both the server and the Tendermint node. The node will automatically connect to the rest
      of the Tendermint network, loads the entire blockchain bulit so far by the others, and
      starts sending ABCI requests to the agent (begin_block; deliver_tx*; end_block), plus
      other auxiliary requests like info , flush etc. The agent which is already processing
      incoming messages, forwards the ABCI requests to the ABCIHandler, which produces ABCI
      responses that are forwarded again via the ABCI connection such that the Tendermint
      node can receive the responses
    """

    restart_after: int = 60

    def test_run(self) -> None:
        """Run the test."""

        for agent_id in range(self.NB_AGENTS):
            self._launch_agent_i(agent_id)

        logging.info("Waiting Tendermint nodes to be up")
        self.health_check(
            self.tendermint_net_builder,
            max_retries=self.HEALTH_CHECK_MAX_RETRIES,
            sleep_interval=self.HEALTH_CHECK_SLEEP_INTERVAL,
        )

        # wait for some time before restarting
        time.sleep(self.restart_after)

        # restart agent
        self.terminate_agents(self.processes[-1])
        self.processes.pop(-1)
        self._launch_agent_i(-1)

        # check that *each* AEA prints these messages
        for i, process in enumerate(self.processes):
            missing_strings = self.missing_from_output(
                process, self.check_strings, self.wait_to_finish
            )
            assert (
                missing_strings == []
            ), "Strings {} didn't appear in agent_{} output.".format(missing_strings, i)

            if not self.is_successfully_terminated(process):
                warnings.warn(
                    UserWarning(
                        f"ABCI agent with process {process} wasn't successfully terminated."
                    )
                )
