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

"""Integration tests for the valory/abstract_abci skill."""

# pylint: skip-file

import time
import warnings
from pathlib import Path

import pytest
from aea.test_tools.test_cases import AEATestCaseMany
from aea_test_autonomy.configurations import ANY_ADDRESS
from aea_test_autonomy.fixture_helpers import (  # noqa: F401
    UseTendermint,
    abci_host,
    abci_port,
    tendermint,
    tendermint_port,
)


@pytest.mark.e2e
@pytest.mark.integration
@pytest.mark.usefixtures("tendermint", "tendermint_port", "abci_host", "abci_port")
class TestABCISkill(AEATestCaseMany, UseTendermint):
    """Test that the ABCI skill works together with Tendermint."""

    IS_LOCAL = True
    capture_log = True
    cli_log_options = ["-v", "DEBUG"]
    package_registry_src_rel = Path(__file__).parent.parent.parent.parent.parent

    def test_run(self) -> None:
        """Run the ABCI skill."""
        agent_name = "abstract_abci_aea"
        self.fetch_agent("valory/abstract_abci:0.1.0", agent_name)
        self.set_agent_context(agent_name)
        self.generate_private_key("ethereum")
        self.add_private_key("ethereum", "ethereum_private_key.txt")
        self.set_config(
            "vendor.valory.connections.abci.config.host",
            ANY_ADDRESS,
        )
        self.set_config(
            "vendor.valory.connections.abci.config.port",
            self.abci_port,
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
