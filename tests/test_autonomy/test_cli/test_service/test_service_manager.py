# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2023 Valory AG
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

"""Test service management."""

from unittest import mock

from aea_test_autonomy.fixture_helpers import registries_scope_class  # noqa: F401

from tests.test_autonomy.test_cli.test_mint.base import (
    AGENT_ID,
    BaseChainInteractionTest,
    COST_OF_BOND_FOR_AGENT,
    DUMMY_SERVICE,
    NUMBER_OF_SLOTS_PER_AGENT,
    THRESHOLD,
)


DEFAULT_AGENT_INSTANCE_ADDRESS = (
    "0x1CBd3b2770909D4e10f157cABC84C7264073C9Ec"  # a key from default hardhat keys
)


class TestServiceManager(BaseChainInteractionTest):
    """Test service manager."""

    cli_options = ("service",)

    def test_deploy_service(self) -> None:
        """Test activate service."""

        with mock.patch("autonomy.cli.helpers.chain.verify_service_dependencies"):
            service_id = self.mint_component(
                package_id=DUMMY_SERVICE,
                service_mint_parameters=dict(
                    agent_ids=[AGENT_ID],
                    number_of_slots_per_agent=[NUMBER_OF_SLOTS_PER_AGENT],
                    cost_of_bond_per_agent=[COST_OF_BOND_FOR_AGENT],
                    threshold=THRESHOLD,
                ),
            )

        result = self.run_cli(
            commands=(
                "activate",
                str(service_id),
                str(self.key_path),
                "-b",
                str(COST_OF_BOND_FOR_AGENT),
            )
        )

        assert result.exit_code == 0, result.output
        assert "Service activated succesfully" in result.output
