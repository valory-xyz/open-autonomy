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
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pytest
from aea.configurations.base import PublicId
from aea.test_tools.test_cases import AEATestCaseMany, Result

from tests.conftest import ANY_ADDRESS
from tests.fixture_helpers import UseFlaskTendermintNode


_HTTP = "http://"


@dataclass
class RoundChecks:
    """
    Class for the necessary checks of a round during the tests.

    name: is the name of the round for which the checks should be performed.
    event: is the name of the event that is considered as successful.
    n_periods: is the number of periods this event should appear for the check to be considered successful.
    """

    name: str
    success_event: str = "DONE"
    n_periods: int = 1


@pytest.mark.e2e
@pytest.mark.integration
class BaseTestEnd2End(AEATestCaseMany, UseFlaskTendermintNode):
    """
    Base class for end-to-end tests of agents with a skill extending the abstract_abci_round skill.

    The setup test function of this class will configure a set of 'n'
    agents with the configured (agent_package) agent, and a Tendermint network
    of 'n' nodes, one for each agent.

    Test subclasses must set `agent_package`, `wait_to_finish` and `check_strings`.
    """

    # where to fetch agent from
    IS_LOCAL = True
    # whether to capture logs of subprocesses
    capture_log = True
    # generic service configurations
    ROUND_TIMEOUT_SECONDS = 10.0
    KEEPER_TIMEOUT = 30.0
    # generic node healthcheck configuration
    HEALTH_CHECK_MAX_RETRIES = 20
    HEALTH_CHECK_SLEEP_INTERVAL = 3.0
    # log option for agent process
    cli_log_options = ["-v", "DEBUG"]
    # reserved variable for subprocesses collection
    processes: Dict
    # name of agent and skill (the one with composed abci apps) to be tested
    agent_package: str
    skill_package: str
    # time to wait for testable log strings to appear
    wait_to_finish: int
    # the "happy path" is a successful finish of the FSM execution
    happy_path: Tuple[RoundChecks, ...] = ()
    # tuple of strings expected to appear in output as is.
    strict_check_strings: Tuple[str, ...] = ()
    # process to be excluded from checks
    exclude_from_checks: List[int] = []
    # dictionary of extra config overrides to be applied
    extra_configs: List[Dict[str, Any]] = []
    # ledger used for testing
    ledger_id: str = "ethereum"
    key_file_name: str = "ethereum_private_key.txt"

    @classmethod
    def set_config(
        cls,
        dotted_path: str,
        value: Any,
        type_: Optional[str] = None,
        aev: bool = True,
    ) -> Result:
        """Set config value."""
        return super().set_config(dotted_path, value, type_, aev)

    def __set_extra_configs(self) -> None:
        """Set the current agent's extra config overrides that are skill specific."""
        for config in self.extra_configs:
            self.set_config(**config)

    def __set_configs(self, i: int, nb_agents: int) -> None:
        """Set the current agent's config overrides."""
        # each agent has its Tendermint node instance
        self.set_config(
            "agent.logging_config.handlers.logfile.filename",
            str(self.t / f"abci_{i}.txt"),
        )
        self.set_config(
            "vendor.valory.connections.abci.config.host",
            ANY_ADDRESS,
        )
        self.set_config(
            "vendor.valory.connections.abci.config.port",
            self.get_abci_port(i),
        )
        self.set_config(
            "vendor.valory.connections.abci.config.use_tendermint",
            False,
        )
        self.set_config(
            "vendor.valory.connections.abci.config.tendermint_config.rpc_laddr",
            self.get_laddr(i),
        )
        self.set_config(
            "vendor.valory.connections.abci.config.tendermint_config.p2p_laddr",
            self.get_laddr(i, p2p=True),
        )
        self.set_config(
            "vendor.valory.connections.abci.config.tendermint_config.p2p_seeds",
            json.dumps(self.p2p_seeds),
            "list",
        )
        self.set_config(
            f"vendor.valory.skills.{PublicId.from_str(self.skill_package).name}.models.params.args.consensus.max_participants",
            nb_agents,
        )
        self.set_config(
            f"vendor.valory.skills.{PublicId.from_str(self.skill_package).name}.models.params.args.reset_tendermint_after",
            5,
        )
        self.set_config(
            f"vendor.valory.skills.{PublicId.from_str(self.skill_package).name}.models.params.args.round_timeout_seconds",
            self.ROUND_TIMEOUT_SECONDS,
            type_="float",
        )
        self.set_config(
            f"vendor.valory.skills.{PublicId.from_str(self.skill_package).name}.models.params.args.tendermint_url",
            f"{_HTTP}{ANY_ADDRESS}:{self.get_port(i)}",
        )
        self.set_config(
            f"vendor.valory.skills.{PublicId.from_str(self.skill_package).name}.models.params.args.tendermint_com_url",
            f"{_HTTP}{ANY_ADDRESS}:{self.get_com_port(i)}",
        )
        self.set_config(
            f"vendor.valory.skills.{PublicId.from_str(self.skill_package).name}.models.params.args.keeper_timeout",
            self.KEEPER_TIMEOUT,
            type_="float",
        )
        self.set_config(
            f"vendor.valory.skills.{PublicId.from_str(self.skill_package).name}.models.benchmark_tool.args.log_dir",
            str(self.t),
            type_="str",
        )
        self.set_config(
            f"vendor.valory.skills.{PublicId.from_str(self.skill_package).name}.models.params.args.observation_interval",
            3,
            type_="int",
        )
        self.set_config(
            f"vendor.valory.skills.{PublicId.from_str(self.skill_package).name}.models.params.args.service_registry_address",
            "0x0DCd1Bf9A1b36cE34237eEaFef220932846BCD82",  # address on staging chain
            type_="str",
        )
        self.set_config(  # dummy service
            f"vendor.valory.skills.{PublicId.from_str(self.skill_package).name}.models.params.args.on_chain_service_id",
            "1",
            type_="int",
        )

        self.__set_extra_configs()

    @staticmethod
    def _get_agent_name(i: int) -> str:
        """Get the ith agent's name."""
        return f"agent_{i:05d}"

    def __prepare_agent_i(self, i: int, nb_agents: int) -> None:
        """Prepare the i-th agent."""
        agent_name = self._get_agent_name(i)
        logging.info(f"Processing agent {agent_name}...")
        self.fetch_agent(self.agent_package, agent_name, is_local=self.IS_LOCAL)
        self.set_agent_context(agent_name)
        if hasattr(self, "key_pairs"):
            Path(self.current_agent_context, self.key_file_name).write_text(
                self.key_pairs[i][1]  # type: ignore
            )
        else:
            self.generate_private_key(self.ledger_id, self.key_file_name)
        self.add_private_key(self.ledger_id, self.key_file_name)
        self.__set_configs(i, nb_agents)
        # issue certificates for libp2p proof of representation
        self.generate_private_key("cosmos", "cosmos_private_key.txt")
        self.add_private_key("cosmos", "cosmos_private_key.txt")
        self.run_cli_command("issue-certificates", cwd=self._get_cwd())

    def prepare(self, nb_nodes: int) -> None:
        """Set up the agents."""
        for agent_id in range(nb_nodes):
            self.__prepare_agent_i(agent_id, nb_nodes)

        # run 'aea install' in only one AEA project, to save time
        self.set_agent_context(self._get_agent_name(0))
        self.run_install()

    def prepare_and_launch(self, nb_nodes: int) -> None:
        """Prepare and launch the agents."""
        self.processes = dict.fromkeys(range(nb_nodes))
        self.prepare(nb_nodes)
        for agent_id in range(nb_nodes):
            self._launch_agent_i(agent_id)

    def _launch_agent_i(self, i: int) -> None:
        """Launch the i-th agent."""
        agent_name = self._get_agent_name(i)
        logging.info(f"Launching agent {agent_name}...")
        self.set_agent_context(agent_name)
        process = self.run_agent()
        self.processes[i] = process

    def terminate_processes(self) -> None:
        """Terminate processes"""
        for i, process in self.processes.items():
            self.terminate_agents(process)
            outs, errs = process.communicate()
            logging.info(f"subprocess logs {process}: {outs} --- {errs}")
            if not self.is_successfully_terminated(process):
                agent_name = self._get_agent_name(i)
                warnings.warn(
                    UserWarning(
                        f"ABCI {agent_name} with process {process} wasn't successfully terminated."
                    )
                )

    @staticmethod
    def __generate_full_strings_from_rounds(
        happy_path: Tuple[RoundChecks, ...]
    ) -> Dict[str, int]:
        """Generate the full strings from the given round strings"""
        full_strings = {}
        for round_check in happy_path:
            entered_str = f"Entered in the '{round_check.name}' round for period"
            done_str = f"'{round_check.name}' round is done with event: Event.{round_check.success_event}"
            full_strings[entered_str] = round_check.n_periods
            full_strings[done_str] = round_check.n_periods

        return full_strings

    @classmethod
    def missing_from_output(  # type: ignore
        cls,
        happy_path: Tuple[RoundChecks, ...] = (),
        strict_check_strings: Tuple[str, ...] = (),
        period: int = 1,
        is_terminating: bool = True,
        **kwargs: Any,
    ) -> Tuple[List[str], List[str]]:
        """
        Check if strings are present in process output.

        Read process stdout in thread and terminate when all strings are present or timeout expired.

        :param happy_path: the happy path of the testing FSM.
        :param strict_check_strings: tuple of strings expected to appear in output as is.
        :param period: period of checking.
        :param is_terminating: whether the agents are terminated if any of the check strings do not appear in the logs.
        :param kwargs: the kwargs of the overridden method.
        :return: tuple with two lists of missed strings, the strict and the round respectively.
        """
        # Call the original method with the strict checks.
        kwargs["strings"] = strict_check_strings
        kwargs["is_terminating"] = False
        missing_strict_strings = super().missing_from_output(**kwargs)

        # Perform checks for the round strings.
        missing_round_strings = []
        if len(happy_path):
            logging.info("Performing checks for the round strings.")
            check_strings_to_n_periods = cls.__generate_full_strings_from_rounds(
                happy_path
            )
            # Create dictionary to keep track of how many times this string has appeared so far.
            check_strings_to_n_appearances = dict.fromkeys(check_strings_to_n_periods)
            end_time = time.time() + kwargs["timeout"]
            # iterate while the check strings are still present in the dictionary,
            # i.e. have not appeared for the required amount of times.
            while bool(check_strings_to_n_periods) and time.time() < end_time:
                for line in check_strings_to_n_periods.copy().keys():
                    # count the number of times the line has appeared so far.
                    n_times_appeared = cls.stdout[kwargs["process"].pid].count(line)
                    # track the number times the line has appeared so far.
                    check_strings_to_n_appearances[line] = n_times_appeared
                    # if the required number has been reached, delete them from the check dictionaries.
                    if (
                        check_strings_to_n_appearances[line]
                        >= check_strings_to_n_periods[line]
                    ):
                        del check_strings_to_n_periods[line]
                        del check_strings_to_n_appearances[line]

                # sleep for `period` amount of time.
                time.sleep(period)

            # generate the missing strings with the number of times they are missing.
            missing_round_strings = [
                f"'{s}' appeared only {n_appeared} out of {n_expected} times"
                for (s, n_expected), (_, n_appeared) in zip(
                    check_strings_to_n_periods.items(),
                    check_strings_to_n_appearances.items(),
                )
            ]

        return missing_strict_strings, missing_round_strings

    def __check_missing_strings(
        self,
        missing_strict_strings: List[str],
        missing_round_strings: List[str],
        i: int,
    ) -> None:
        """Checks for missing strings in agent's output."""
        agent_name = self._get_agent_name(i)
        missing_agent_logs = ""
        if missing_strict_strings:
            missing_agent_logs += f"Strings {missing_strict_strings} didn't appear in {agent_name} output.\n"
        missing_agent_logs += "\n".join(missing_round_strings)

        assert missing_agent_logs == "", missing_agent_logs

    def check_aea_messages(self) -> None:
        """
        Check that *each* AEA prints these messages.

        First failing check will cause assertion error and test tear down.
        """
        for i, process in self.processes.items():
            if i in self.exclude_from_checks:
                continue
            (missing_strict_strings, missing_round_strings,) = self.missing_from_output(
                process=process,
                happy_path=self.happy_path,
                strict_check_strings=self.strict_check_strings,
                timeout=self.wait_to_finish,
            )

            self.__check_missing_strings(
                missing_strict_strings, missing_round_strings, i
            )


class BaseTestEnd2EndExecution(BaseTestEnd2End):
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

    nb_nodes: int = 0  # number of agents with tendermint nodes

    # configuration specific for agent restart
    stop_string: str  # mandatory argument if n_terminal > 0
    n_terminal: int = 0  # number of agents to be restarted
    wait_to_kill: int = 0  # delay the termination event
    restart_after: int = 60  # how long to wait before restart
    wait_before_stop: int = 15  # how long to check logs for `stop_string`

    def check(self) -> None:
        """Check pre-conditions of the test"""
        if self.n_terminal > self.nb_nodes:
            fail_msg = "Cannot terminate {nb_nodes} out of {n_terminal} agents:"
            pytest.fail(
                fail_msg.format(nb_nodes=self.nb_nodes, n_terminal=self.n_terminal)
            )
        if self.n_terminal and not hasattr(self, "stop_string"):
            pytest.fail("'stop_string' must be provided for agent termination.")

    def test_run(self, nb_nodes: int) -> None:
        """Run the test."""
        self.nb_nodes = nb_nodes
        self.check()

        self.prepare_and_launch(nb_nodes)
        self.health_check(
            max_retries=self.HEALTH_CHECK_MAX_RETRIES,
            sleep_interval=self.HEALTH_CHECK_SLEEP_INTERVAL,
        )
        if self.n_terminal:
            self._restart_agents()
        self.check_aea_messages()
        self.terminate_processes()

    def _restart_agents(self) -> None:
        """Stops and restarts agents after stop string is found."""

        # stop the last agent as soon as the "stop string" is found in the output
        # once found, we start terminating the first agent
        logging.info(f"Waiting for string {self.stop_string} in last agent output")
        missing_strict_strings, _ = self.missing_from_output(
            process=self.processes[max(self.processes)],
            strict_check_strings=(self.stop_string,),
            timeout=self.wait_before_stop,
        )
        if missing_strict_strings:
            msg = f"cannot stop agent, stop string `{self.stop_string}` not found"
            raise RuntimeError(msg)

        if self.wait_to_kill:
            logging.info("Waiting to terminate agents")
            time.sleep(self.wait_to_kill)

        # terminate the agents - sequentially
        # don't pop before termination, seems to lead to failure!
        for i in range(self.n_terminal):
            agent_name = self._get_agent_name(i)
            self.terminate_agents(self.processes[i], timeout=0)
            self.processes.pop(i)
            logging.info(f"Terminated {agent_name}")

        # wait for some time before restarting
        logging.info(
            f"Waiting {self.restart_after} seconds before restarting the agent"
        )
        time.sleep(self.restart_after)

        # restart agents
        for i in range(self.n_terminal):
            agent_name = self._get_agent_name(i)
            self._launch_agent_i(i)
            logging.info(f"Restarted {agent_name}")
