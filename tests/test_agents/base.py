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
import os
import time
import warnings
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pytest
from aea.configurations.base import PublicId
from aea.test_tools.test_cases import AEATestCaseMany

from tests.conftest import ANY_ADDRESS
from tests.fixture_helpers import UseFlaskTendermintNode


_HTTP = "http://"


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

    IS_LOCAL = True
    capture_log = True
    ROUND_TIMEOUT_SECONDS = 10.0
    KEEPER_TIMEOUT = 30.0
    HEALTH_CHECK_MAX_RETRIES = 20
    HEALTH_CHECK_SLEEP_INTERVAL = 3.0
    cli_log_options = ["-v", "DEBUG"]
    processes: List
    agent_package: str
    skill_package: str
    wait_to_finish: int
    # dictionary with the round names expected to appear in output as keys
    # and the number of periods they are expected to appear for as values.
    round_check_strings_to_n_periods: Optional[Dict[str, int]] = None
    # tuple of strings expected to appear in output as is.
    strict_check_strings: Tuple[str, ...] = ()
    extra_configs: List[Dict[str, Any]] = []

    def __set_extra_configs(self) -> None:
        """Set the current agent's extra config overrides that are skill specific."""
        for config in self.extra_configs:
            self.set_config(**config)

    def __set_configs(self, i: int) -> None:
        """Set the current agent's config overrides."""
        # each agent has its Tendermint node instance
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
            self.nb_agents,
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

        self.__set_extra_configs()

    def __get_agent_name(self, i: int) -> str:
        """Get the ith agent's name."""
        if i < 0:
            i = self.nb_agents + i
        if i < 0:
            raise ValueError(
                f"Incorrect negative indexing. {i} was given, but {self.nb_agents} agents are available!"
            )
        agent_name = f"agent_{i:05d}_{self.nb_agents}agents_run"
        return agent_name

    @classmethod
    def setup_class(
        cls,
    ) -> None:
        """Setup class."""
        super().setup_class()

        for dir_path in [
            "logs",
            "nodes",
            "tm_state",
            "benchmarks",
        ]:
            path = Path(cls.t, dir_path)
            path.mkdir()
            os.chmod(path, 755)  # nosec

    def prepare(self, nb_nodes: int) -> None:
        """Set up the test."""
        self.processes = []
        self.nb_agents = nb_nodes

        for agent_id in range(self.nb_agents):
            agent_name = self.__get_agent_name(agent_id)
            logging.debug(f"Processing agent {agent_name}...")
            self.fetch_agent(self.agent_package, agent_name, is_local=self.IS_LOCAL)
            self.set_agent_context(agent_name)
            if hasattr(self, "key_pairs"):
                Path(self.current_agent_context, "ethereum_private_key.txt").write_text(
                    self.key_pairs[agent_id][1]  # type: ignore
                )
            else:
                self.generate_private_key("ethereum", "ethereum_private_key.txt")
            self.add_private_key("ethereum", "ethereum_private_key.txt")
            self.__set_configs(agent_id)

        # run 'aea install' in only one AEA project, to save time
        self.set_agent_context(self.__get_agent_name(0))
        self.run_install()

    def _launch_agent_i(self, i: int) -> None:
        """Launch the i-th agent."""
        agent_name = self.__get_agent_name(i)
        logging.debug(f"Launching agent {agent_name}...")
        self.set_agent_context(agent_name)
        process = self.run_agent()
        self.processes.append(process)

    @staticmethod
    def __generate_full_strings_from_rounds(
        round_check_strings_to_n_periods: Dict[str, int]
    ) -> Dict[str, int]:
        """Generate the full strings from the given round strings"""
        full_strings = {}
        for round_str, n_periods in round_check_strings_to_n_periods.items():
            entered_str = f"Entered in the '{round_str}' round for period"
            done_str = f"'{round_str}' round is done with event: Event.DONE"
            full_strings[entered_str] = n_periods
            full_strings[done_str] = n_periods

        return full_strings

    @classmethod
    def missing_from_output(  # type: ignore
        cls,
        round_check_strings_to_n_periods: Optional[Dict[str, int]] = None,
        strict_check_strings: Tuple[str, ...] = (),
        period: int = 1,
        is_terminating: bool = True,
        **kwargs: Any,
    ) -> Tuple[List[str], List[str]]:
        """
        Check if strings are present in process output.

        Read process stdout in thread and terminate when all strings are present or timeout expired.

        :param round_check_strings_to_n_periods: dictionary with the round names expected to appear in output as keys
            and the number of periods they are expected to appear for as values.
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
        if round_check_strings_to_n_periods is not None:
            check_strings_to_n_periods = cls.__generate_full_strings_from_rounds(
                round_check_strings_to_n_periods
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

        if is_terminating:
            cls.terminate_agents(kwargs["process"])

        return missing_strict_strings, missing_round_strings

    @staticmethod
    def __check_missing_strings(
        missing_strict_strings: List[str], missing_round_strings: List[str], i: int
    ) -> None:
        """Checks for missing strings in agent's output."""
        missing_agent_logs = ""
        if missing_strict_strings:
            missing_agent_logs += (
                f"Strings {missing_strict_strings} didn't appear in agent_{i} output.\n"
            )
        missing_agent_logs += "\n".join(missing_round_strings)

        assert missing_agent_logs == "", missing_agent_logs

    def _check_aea_messages(self) -> None:
        """Check that *each* AEA prints these messages."""
        for i, process in enumerate(self.processes):
            missing_strict_strings, missing_round_strings = self.missing_from_output(
                process=process,
                round_check_strings_to_n_periods=self.round_check_strings_to_n_periods,
                strict_check_strings=self.strict_check_strings,
                timeout=self.wait_to_finish,
            )

            self.__check_missing_strings(
                missing_strict_strings, missing_round_strings, i
            )

            if not self.is_successfully_terminated(process):
                warnings.warn(
                    UserWarning(
                        f"ABCI agent with process {process} wasn't successfully terminated."
                    )
                )


class BaseTestEnd2EndNormalExecution(BaseTestEnd2End):
    """Test that the ABCI simple skill works together with Tendermint under normal circumstances."""

    def test_run(self, nb_nodes: int) -> None:
        """Run the ABCI skill."""
        self.prepare(nb_nodes)
        for agent_id in range(self.nb_agents):
            self._launch_agent_i(agent_id)

        logging.info("Waiting Tendermint nodes to be up")
        self.health_check(
            max_retries=self.HEALTH_CHECK_MAX_RETRIES,
            sleep_interval=self.HEALTH_CHECK_SLEEP_INTERVAL,
        )
        self._check_aea_messages()


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

    # mandatory argument
    stop_string: str

    restart_after: int = 60
    wait_before_stop: int = 15

    def setup(self) -> None:
        """Set up the test."""
        if not hasattr(self, "stop_string"):
            pytest.fail("'stop_string' is a mandatory argument.")

    def test_run(self, nb_nodes: int) -> None:
        """Run the test."""
        self.prepare(nb_nodes)
        for agent_id in range(self.nb_agents):
            self._launch_agent_i(agent_id)

        logging.info("Waiting Tendermint nodes to be up")
        self.health_check(
            max_retries=self.HEALTH_CHECK_MAX_RETRIES,
            sleep_interval=self.HEALTH_CHECK_SLEEP_INTERVAL,
        )

        # stop the last agent as soon as the "stop string" is found in the output
        process_to_stop = self.processes[-1]
        logging.debug(f"Waiting for string {self.stop_string} in last agent output")
        missing_strict_strings, _ = self.missing_from_output(
            process=process_to_stop,
            strict_check_strings=(self.stop_string,),
            timeout=self.wait_before_stop,
        )
        if missing_strict_strings:
            raise RuntimeError("cannot stop agent correctly")
        logging.debug("Last agent stopped")
        self.processes.pop(-1)

        # wait for some time before restarting
        logging.debug(
            f"Waiting {self.restart_after} seconds before restarting the agent"
        )
        time.sleep(self.restart_after)

        # restart agent
        logging.debug("Restart the agent")
        self._launch_agent_i(-1)
        self._check_aea_messages()
