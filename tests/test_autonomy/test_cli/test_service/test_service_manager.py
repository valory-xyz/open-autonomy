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

from typing import Optional
from unittest import mock

from aea.crypto.registries import make_crypto
from aea_test_autonomy.configurations import ETHEREUM_KEY_PATH_5
from aea_test_autonomy.fixture_helpers import registries_scope_class  # noqa: F401
from click.testing import Result

from autonomy.chain.service import activate_service, register_instance

from tests.test_autonomy.test_chain.base import (
    AGENT_ID,
    BaseChainInteractionTest,
    COST_OF_BOND_FOR_AGENT,
    DUMMY_SERVICE,
    NUMBER_OF_SLOTS_PER_AGENT,
    THRESHOLD,
)


DEFAULT_AGENT_INSTANCE_ADDRESS = (
    "0x976EA74026E726554dB657fA54763abd0C3a0aa9"  # a key from default hardhat keys
)


class BaseServiceManagerTest(BaseChainInteractionTest):
    """Test service manager."""

    cli_options = ("service",)
    key_file = ETHEREUM_KEY_PATH_5

    def mint_service(
        self,
    ) -> int:
        """Mint service component"""
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

        assert isinstance(service_id, int)
        return service_id

    def activate_service(self, service_id: int) -> None:
        """Activate service"""
        activate_service(
            ledger_api=self.ledger_api,
            crypto=self.crypto,
            chain_type=self.chain_type,
            service_id=service_id,
        )

    def register_instances(
        self, service_id: int, agent_instance: Optional[str] = None
    ) -> None:
        """Register agent instance."""

        register_instance(
            ledger_api=self.ledger_api,
            crypto=self.crypto,
            chain_type=self.chain_type,
            service_id=service_id,
            instance=(agent_instance or make_crypto("ethereum").address),
            agent_id=AGENT_ID,
        )


class TestServiceManager(BaseServiceManagerTest):
    """Test service manager."""

    def test_activate_service(self) -> None:
        """Test activate service."""

        def _run_command(service_id: str) -> Result:
            """Run command and return result"""
            return self.run_cli(
                commands=(
                    "activate",
                    service_id,
                    str(self.key_file),
                )
            )

        result = _run_command("100")
        # This should fail since the service is not there yet
        assert result.exit_code == 1, result.output
        assert "Service does not exist" in result.stderr

        service_id = self.mint_service()

        result = _run_command(str(service_id))
        # first attempt should be succesfull
        assert result.exit_code == 0, result.output
        assert "Service activated succesfully" in result.output

        result = _run_command(str(service_id))
        # first attempt should fail since the service already active
        assert result.exit_code == 1, service_id
        assert "Service must be inactive" in result.stderr

    def test_register_instances(
        self,
    ) -> None:
        """Test register instance on a service"""

        agent_instance = make_crypto("ethereum")

        def _run_command(service_id: str) -> Result:
            """Run command and return result"""
            return self.run_cli(
                commands=(
                    "register",
                    service_id,
                    str(self.key_file),
                    "-a",
                    "1",
                    "-i",
                    agent_instance.address,
                )
            )

        result = _run_command("100")
        assert result.exit_code == 1, result.output
        assert "Service does not exist" in result.stderr

        service_id = self.mint_service()
        result = _run_command(str(service_id))
        assert result.exit_code == 1, result.output
        assert "Service needs to be in active state" in result.stderr

        self.activate_service(
            service_id=service_id,
        )

        result = _run_command(str(service_id))
        assert result.exit_code == 0, result.stderr
        assert "Agent instance registered succesfully" in result.output

        result = _run_command(str(service_id))
        # Will fail becaue the agent instance is already registered
        assert result.exit_code == 1, result.stdout
        assert "Instance registration failed" in result.stderr
        assert "AgentInstanceRegistered" in result.stderr

    def test_deploy(
        self,
    ) -> None:
        """Test register instance on a service"""

        def _run_command(service_id: str) -> Result:
            """Run command and return result"""
            return self.run_cli(
                commands=(
                    "deploy",
                    service_id,
                    str(self.key_file),
                )
            )

        service_id = self.mint_service()
        self.activate_service(
            service_id=service_id,
        )

        result = _run_command(str(service_id))
        assert result.exit_code == 1, result.output
        assert "Service needs to be in finished registration state" in result.stderr

        for _ in range(NUMBER_OF_SLOTS_PER_AGENT):
            self.register_instances(
                service_id=service_id,
            )

        result = _run_command(str(service_id))

        assert result.exit_code == 0, result.stderr
        assert "Service deployed succesfully" in result.output

        result = self.run_cli(
            commands=(
                "deploy",
                str(service_id),
                str(self.key_file),
            )
        )

        # Will fail becaue the service is already deployed
        assert result.exit_code == 1, result.stdout
        assert "Service needs to be in finished registration state" in result.stderr
