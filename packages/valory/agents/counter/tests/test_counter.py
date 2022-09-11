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

"""Integration tests for the valory/counter skill."""

# pylint: skip-file

import base64
import json
import logging
import random
import struct
import time
import warnings
from pathlib import Path

import pytest
import requests
from aea.test_tools.test_cases import AEATestCaseMany
from aea_test_autonomy.configurations import ANY_ADDRESS, DEFAULT_REQUESTS_TIMEOUT
from aea_test_autonomy.fixture_helpers import (  # noqa: F401
    UseTendermint,
    abci_host,
    abci_port,
    tendermint,
    tendermint_port,
)
from aea_test_autonomy.helpers.tendermint_utils import (
    BaseTendermintTestClass,
    TendermintLocalNetworkBuilder,
)


@pytest.mark.e2e
class BaseTestABCICounterSkill:
    """Base test class."""

    def _send_tx_to_node(
        self, node_address: str, value: int, expected_status_code: int
    ) -> None:
        """
        Send a transaction to a certain node.

        :param node_address: the node address
        :param value: the value to propose in the tx
        :param expected_status_code: the expected status code
        """
        # at least two hex digits
        tx_arg = "0x{:02x}".format(value)
        result = requests.get(
            node_address + "/broadcast_tx_commit",
            params=dict(tx=tx_arg),
            timeout=DEFAULT_REQUESTS_TIMEOUT,
        )
        assert result.status_code == expected_status_code

    def _query_node(self, node_address: str, expected_value: int) -> None:
        """
        Send a query to a node about the state of the replicated counter.

        :param node_address: the node address
        :param expected_value: the expected value of the counter.
        """
        result = requests.get(
            node_address + "/abci_query",
            timeout=DEFAULT_REQUESTS_TIMEOUT,
        )
        assert result.status_code == 200
        counter_value_base64 = result.json()["result"]["response"]["value"].encode(
            "ascii"
        )
        counter_value_bytes = base64.b64decode(counter_value_base64)
        counter_value, *_ = struct.unpack(">I", counter_value_bytes)
        assert counter_value == expected_value


@pytest.mark.e2e
@pytest.mark.integration
@pytest.mark.usefixtures("tendermint", "tendermint_port", "abci_host", "abci_port")
class TestABCICounterSkill(AEATestCaseMany, UseTendermint):
    """Test that the ABCI counter skill works together with Tendermint."""

    IS_LOCAL = True
    capture_log = True
    cli_log_options = ["-v", "DEBUG"]
    package_registry_src_rel = Path(__file__).parent.parent.parent.parent.parent

    def test_run(self) -> None:
        """Run the ABCI skill."""
        agent_name = "counter_aea"
        self.fetch_agent("valory/counter:0.1.0", agent_name, is_local=self.IS_LOCAL)
        self.set_agent_context(agent_name)
        self.generate_private_key("ethereum")
        self.add_private_key("ethereum", "ethereum_private_key.txt")
        self.set_config(
            "vendor.valory.connections.abci.config.use_tendermint", False, aev=True
        )
        self.set_config(
            "vendor.valory.connections.abci.config.host", ANY_ADDRESS, aev=True
        )
        self.set_config(
            "vendor.valory.connections.abci.config.port", self.abci_port, aev=True
        )

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

        if not self.is_successfully_terminated(process):
            warnings.warn(
                UserWarning(
                    f"ABCI agent with process {process} wasn't successfully terminated."
                )
            )


class TestABCICounterSkillMany(
    AEATestCaseMany, BaseTendermintTestClass, BaseTestABCICounterSkill
):
    """Test that the ABCI counter skill works together with Tendermint."""

    IS_LOCAL = True
    capture_log = True
    NB_AGENTS = 4
    NB_TX = 15
    package_registry_src_rel = Path(__file__).parent.parent.parent.parent.parent

    def test_run(self) -> None:
        """Run the ABCI skill."""
        self.agent_names = [f"agent_{i:05d}" for i in range(self.NB_AGENTS)]
        processes = []
        self.tendermint_net_builder = TendermintLocalNetworkBuilder(
            self.NB_AGENTS, Path(self.t)
        )

        for agent_id, agent_name in enumerate(self.agent_names):
            logging.debug(f"Processing agent {agent_name}...")
            node = self.tendermint_net_builder.nodes[agent_id]
            self.fetch_agent("valory/counter:0.1.0", agent_name, is_local=self.IS_LOCAL)
            self.set_agent_context(agent_name)
            self.generate_private_key("ethereum")
            self.add_private_key("ethereum", "ethereum_private_key.txt")
            # each agent has its Tendermint node instance
            self.set_config(
                "vendor.valory.connections.abci.config.port", node.abci_port, aev=True
            )
            self.set_config(
                "vendor.valory.connections.abci.config.tendermint_config.rpc_laddr",
                node.rpc_laddr,
                aev=True,
            )
            self.set_config(
                "vendor.valory.connections.abci.config.tendermint_config.p2p_laddr",
                node.p2p_laddr,
                aev=True,
            )
            self.set_config(
                "vendor.valory.connections.abci.config.tendermint_config.home",
                str(node.home),
                aev=True,
            )
            self.set_config(
                "vendor.valory.connections.abci.config.tendermint_config.p2p_seeds",
                json.dumps(self.tendermint_net_builder.get_p2p_seeds()),
                "list",
                aev=True,
            )
            self.set_config(
                "vendor.valory.connections.abci.config.use_tendermint", True, aev=True
            )
            process = self.run_agent()
            processes.append(process)

        logging.info("Waiting Tendermint nodes to be up")
        self.health_check(self.tendermint_net_builder)

        # start test of the ABCI app
        # check that the initial counter state is 0
        self._query_agents(0)
        # send transactions to each node, randomly
        for tx_number in range(self.NB_TX):
            time.sleep(0.5)
            agent_id = random.randint(0, self.NB_AGENTS - 1)  # nosec
            new_value = tx_number + 1
            self._send_tx(new_value, agent_id, 200)
        # wait synchronization
        time.sleep(2.0)
        # check that the final counter state is N
        self._query_agents(self.NB_TX)
        # end test of the ABCI app

        check_strings = (*[f"The new count is: {x + 1}" for x in range(self.NB_TX)],)

        # check that *each* AEA prints these messages
        for process in processes:
            missing_strings = self.missing_from_output(process, check_strings)
            assert (
                missing_strings == []
            ), "Strings {} didn't appear in agent output.".format(missing_strings)

            if not self.is_successfully_terminated(process):
                warnings.warn(
                    UserWarning(
                        f"ABCI agent with process {process} wasn't successfully terminated."
                    )
                )

    def _query_agents(self, expected_value: int) -> None:
        """
        Send queries to each agent about the state of the replicated counter.

        :param expected_value: the expected value of the counter.
        """
        for agent_id in range(self.NB_AGENTS):
            self._query_agent(expected_value, agent_id)

    def _send_tx(self, value: int, agent_id: int, expected_status_code: int) -> None:
        """
        Send a transaction to a certain agent.

        :param value: the value to propose in the tx
        :param agent_id: the agent id
        :param expected_status_code: the expected status code
        """
        node = self.tendermint_net_builder.nodes[agent_id]
        self._send_tx_to_node(
            node.get_http_addr("localhost"), value, expected_status_code
        )

    def _query_agent(self, expected_value: int, agent_id: int) -> None:
        """
        Send a query to the ith agent about the state of the replicated counter.

        :param expected_value: the expected value of the counter.
        :param agent_id: the agent to be queried
        """
        node = self.tendermint_net_builder.nodes[agent_id]
        result = requests.get(
            node.get_http_addr("localhost") + "/abci_query",
            timeout=DEFAULT_REQUESTS_TIMEOUT,
        )
        assert result.status_code == 200
        counter_value_base64 = result.json()["result"]["response"]["value"].encode(
            "ascii"
        )
        counter_value_bytes = base64.b64decode(counter_value_base64)
        counter_value, *_ = struct.unpack(">I", counter_value_bytes)
        assert counter_value == expected_value


class TestABCICounterCrashFailureRestart(
    AEATestCaseMany, BaseTendermintTestClass, BaseTestABCICounterSkill
):
    """Test that restarting the agent with the same Tendermint node will restore the state."""

    NB_TX = 5
    package_registry_src_rel = Path(__file__).parent.parent.parent.parent.parent

    def test_run(self) -> None:
        """Run the test."""
        agent_name = "counter_aea"
        self.fetch_agent("valory/counter:0.1.0", agent_name)
        self.set_agent_context(agent_name)
        self.generate_private_key("ethereum")
        self.add_private_key("ethereum", "ethereum_private_key.txt")
        self.set_config(
            "vendor.valory.connections.abci.config.tendermint_config.home",
            str(self.t / "tendermint_home"),
            aev=True,
        )
        self.set_config(
            "vendor.valory.connections.abci.config.use_tendermint", True, aev=True
        )

        node_address = "http://localhost:26657"

        process = self.run_agent()
        is_running = self.is_running(process)
        assert is_running, "AEA not running within timeout!"

        time.sleep(5.0)

        for tx_number in range(self.NB_TX):
            time.sleep(2.0)
            new_value = tx_number + 1
            self._send_tx_to_node(node_address, new_value, 200)
        # wait synchronization
        time.sleep(5.0)

        # check that the final counter state is N
        self._query_node(node_address, self.NB_TX)

        check_strings = (*[f"The new count is: {x + 1}" for x in range(self.NB_TX)],)
        missing_strings = self.missing_from_output(process, check_strings)
        assert (
            missing_strings == []
        ), "Strings {} didn't appear in agent output.".format(missing_strings)

        # Run it again
        process = self.run_agent()
        is_running = self.is_running(process)
        assert is_running, "AEA not running within timeout!"

        # give time to synchronize
        time.sleep(5.0)

        self._query_node(node_address, self.NB_TX)

        missing_strings = self.missing_from_output(process, check_strings)
        assert (
            missing_strings == []
        ), "Strings {} didn't appear in agent output.".format(missing_strings)

        if not self.is_successfully_terminated(process):
            warnings.warn(
                UserWarning(
                    f"ABCI agent with process {process} wasn't successfully terminated."
                )
            )
