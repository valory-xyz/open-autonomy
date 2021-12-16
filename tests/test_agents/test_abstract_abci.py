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

"""Integration tests for the valory/abstract_abci skill."""
import time

import pytest
from aea.test_tools.test_cases import AEATestCaseMany

from tests.fixture_helpers import UseTendermint


@pytest.mark.integration
class TestABCISkill(AEATestCaseMany, UseTendermint):
    """Test that the ABCI skill works together with Tendermint."""

    IS_LOCAL = True
    capture_log = True
    cli_log_options = ["-v", "DEBUG"]

    def test_run(self) -> None:
        """Run the ABCI skill."""
        agent_name = "abstract_abci_aea"
        self.fetch_agent("valory/abstract_abci:0.1.0", agent_name)
        self.set_agent_context(agent_name)
        self.generate_private_key("ethereum")
        self.add_private_key("ethereum", "ethereum_private_key.txt")
        # self.set_config("agent.default_ledger", "ethereum")  # noqa: E800
        # self.set_config("agent.required_ledgers", '["ethereum"]', type_="list")  # noqa: E800
        # self.add_item("skill", "valory/abstract_abci:0.1.0")  # noqa: E800
        # # don't use 'abstract_abci' as abstract class; for the
        # # purposes of this test the default request handlers work well.
        # self.set_config("vendor.valory.skills.abstract_abci.is_abstract", False)  # noqa: E800
        # # make 'abstract_abci' the target skill for 'valory/abci' connection  # noqa: E800
        # self.set_config(  # noqa: E800
        #     "vendor.valory.connections.abci.config.target_skill_id",  # noqa: E800
        #     "valory/abstract_abci:0.1.0",  # noqa: E800
        # )  # noqa: E800
        # # we use Tendermint node from Docker, not the local one
        # self.set_config(  # noqa: E800
        #     "vendor.valory.connections.abci.config.use_tendermint",  # noqa: E800
        #     False,  # noqa: E800
        # )  # noqa: E800

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
