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
# pylint: disable=broad-except,unspecified-encoding,import-error,redefined-outer-name

"""End2End tests base classes for the register_reset_recovery agent."""
import logging

import requests
from aea_test_autonomy.base_test_classes.agents import BaseTestEnd2End
from aea_test_autonomy.configurations import LOCALHOST


TERMINATION_TIMEOUT = 120


class BaseTestRegisterResetRecoveryEnd2End(
    BaseTestEnd2End
):  # pylint: disable=too-few-public-methods
    """
    Extended base class for conducting E2E tests with `termination_abci` activated.

    Test subclasses must set NB_AGENTS, agent_package, wait_to_finish and check_strings.
    """

    skill_package = "valory/register_reset_recovery_abci:0.1.0"
    tm_break_string = "Current round count is 3."
    wait_before_stop = 100  # wait for 100s for tm_break_string to show

    def _disrupt_tm_node(self) -> None:
        """Disrupts the work of node0. This is done to force the tm node to stop syncing."""
        logging.info(f"Waiting for string {self.tm_break_string} in last agent output")
        missing_strict_strings, _ = self.missing_from_output(
            process=self.processes[max(self.processes)],
            strict_check_strings=(self.tm_break_string,),
            timeout=self.wait_before_stop,
        )
        if missing_strict_strings:
            msg = (
                f"cannot break tm node, break string `{self.tm_break_string}` not found"
            )
            raise RuntimeError(msg)

        tm_server_port = self.get_com_port(3)
        endpoint = f"http://{LOCALHOST}:{tm_server_port}/hard_reset"
        # after sending the following params, the tendermint node will not be
        # able to catch up with the rest of the network.
        # The agent should send a hard reset req to recover it.
        bad_params = {"initial_height": "10"}
        requests.get(endpoint, params=bad_params)

    def test_run(self, nb_nodes: int) -> None:
        """Run the test."""
        self.prepare_and_launch(nb_nodes)
        self.health_check(
            max_retries=self.HEALTH_CHECK_MAX_RETRIES,
            sleep_interval=self.HEALTH_CHECK_SLEEP_INTERVAL,
        )
        self._disrupt_tm_node()
        self.check_aea_messages()
        self.terminate_agents(timeout=TERMINATION_TIMEOUT)
