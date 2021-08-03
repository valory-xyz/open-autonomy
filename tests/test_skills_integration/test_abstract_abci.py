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

from aea.test_tools.test_cases import AEATestCaseEmpty

from tests.conftest import UseTendermint


class TestABCISkill(AEATestCaseEmpty, UseTendermint):
    """Test that the ABCI skill works together with Tendermint."""

    IS_LOCAL = False
    capture_log = True

    def test_run(self):
        """Run the ABCI skill."""
        self.generate_private_key()
        self.add_private_key()
        self.add_item("skill", "valory/abstract_abci:0.1.0")
        self.set_config("vendor.valory.skills.abstract_abci.is_abstract", False)
        self.set_config(
            "vendor.valory.connections.abci.config.target_skill_id",
            "valory/abstract_abci:0.1.0",
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

        assert (
            self.is_successfully_terminated()
        ), "ABCI agent wasn't successfully terminated."
