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

"""Test `mint` command group."""

from typing import Any, Tuple
from unittest import mock

import pytest
from aea.configurations.data_types import PackageId, PackageType
from aea_test_autonomy.configurations import ETHEREUM_KEY_DEPLOYER
from aea_test_autonomy.fixture_helpers import registries_scope_class  # noqa: F401
from requests.exceptions import ConnectionError as RequestsConnectionError

from autonomy.chain.mint import registry_contracts

from tests.test_autonomy.test_chain.base import (
    BaseChainInteractionTest,
    DEFAULT_SERVICE_MINT_PARAMETERS,
    DUMMY_AGENT,
    DUMMY_CONNECTION,
    DUMMY_CONTRACT,
    DUMMY_PACKAGE_MANAGER,
    DUMMY_PROTOCOL,
    DUMMY_SERVICE,
    DUMMY_SKILL,
)


class DummyContract:
    """Dummy contract"""

    def filter_token_id_from_emitted_events(self, *args: Any, **kwargs: Any) -> None:
        """Dummy method implementation"""

        raise RequestsConnectionError()

    def get_create_transaction(self, *args: Any, **kwargs: Any) -> None:
        """Dummy method implementation"""


class TestMintComponents(BaseChainInteractionTest):
    """Test `autonomy develop mint` command."""

    cli_options = ("mint",)

    @pytest.mark.parametrize(
        argnames=("package_id"),
        argvalues=(
            DUMMY_PROTOCOL,
            DUMMY_CONTRACT,
            DUMMY_CONNECTION,
            DUMMY_SKILL,
            DUMMY_AGENT,
        ),
    )
    def test_mint_components(self, package_id: PackageId) -> None:
        """Test mint components."""

        commands = [
            package_id.package_type.value,
            str(
                DUMMY_PACKAGE_MANAGER.package_path_from_package_id(
                    package_id=package_id
                )
            ),
            str(ETHEREUM_KEY_DEPLOYER),
        ]

        if package_id.package_type == PackageType.CONNECTION:
            # Dummy protocol is a dependency for the dummy connection
            commands += ["-d", str(self.mint_component(package_id=DUMMY_PROTOCOL))]

        if package_id.package_type == PackageType.SKILL:
            # Dummy protocol, dummy contract and dummy connection are dependencies for the dummy skill
            commands += [
                "-d",
                str(self.mint_component(package_id=DUMMY_PROTOCOL)),
                "-d",
                str(self.mint_component(package_id=DUMMY_CONTRACT)),
                "-d",
                str(self.mint_component(package_id=DUMMY_CONNECTION)),
            ]

        if package_id.package_type == PackageType.AGENT:
            # Dummy protocol, dummy contract, dummy connection and dummy skill are dependencies for the dummy skill
            commands += [
                "-d",
                str(self.mint_component(package_id=DUMMY_PROTOCOL)),
                "-d",
                str(self.mint_component(package_id=DUMMY_CONTRACT)),
                "-d",
                str(self.mint_component(package_id=DUMMY_CONNECTION)),
                "-d",
                str(self.mint_component(package_id=DUMMY_SKILL)),
            ]

        result = self.run_cli(commands=tuple(commands))

        assert result.exit_code == 0, result.output
        assert "Component minted with:" in result.output
        assert "Metadata Hash:" in result.output
        assert "Token ID:" in result.output

        token_id = self.extract_token_id_from_output(output=result.output)
        self.verify_minted_token_id(
            token_id=token_id,
            package_id=package_id,
        )

    def test_mint_service(
        self,
    ) -> None:
        """Test mint components."""
        with mock.patch("autonomy.cli.helpers.chain.verify_component_dependencies"):
            agent_id = self.mint_component(package_id=DUMMY_AGENT, dependencies=[1])

        commands = (
            DUMMY_SERVICE.package_type.value,
            str(
                DUMMY_PACKAGE_MANAGER.package_path_from_package_id(
                    package_id=DUMMY_SERVICE
                )
            ),
            str(ETHEREUM_KEY_DEPLOYER),
            "-a",
            str(agent_id),
            *DEFAULT_SERVICE_MINT_PARAMETERS[2:],
        )

        result = self.run_cli(commands=commands)

        assert result.exit_code == 0, result
        assert "Service minted with:" in result.output
        assert "Metadata Hash:" in result.output
        assert "Token ID:" in result.output

        self.verify_minted_token_id(
            token_id=self.extract_token_id_from_output(output=result.output),
            package_id=DUMMY_SERVICE,
        )

    @pytest.mark.parametrize(
        argnames=("package_id", "parameters"),
        argvalues=(
            (DUMMY_CONNECTION, ("-d", "2")),
            (DUMMY_AGENT, ("-d", "1")),
            (DUMMY_SERVICE, ("-a", "1", "-n", "4", "-c", "1000", "--threshold", "3")),
        ),
    )
    def test_metadata_retrive_failure(
        self, package_id: PackageId, parameters: Tuple[str, ...]
    ) -> None:
        """Test connection error."""

        _ = registry_contracts.component_registry
        _ = registry_contracts.agent_registry
        _ = registry_contracts.service_registry

        with mock.patch.object(
            registry_contracts._component_registry,
            "get_token_uri",
            side_effect=RequestsConnectionError,
        ), mock.patch.object(
            registry_contracts._agent_registry,
            "get_token_uri",
            side_effect=RequestsConnectionError,
        ), mock.patch.object(
            registry_contracts._service_registry,
            "get_token_uri",
            side_effect=RequestsConnectionError,
        ):
            result = self.run_cli(
                commands=(
                    package_id.package_type.value,
                    str(
                        DUMMY_PACKAGE_MANAGER.package_path_from_package_id(
                            package_id=package_id
                        )
                    ),
                    str(ETHEREUM_KEY_DEPLOYER),
                    *parameters,
                ),
            )
            self.cli_runner.mix_stderr = True
            assert result.exit_code == 1, result.output
            assert (
                "Dependency verification failed; Error connecting to the RPC"
                in result.stderr
            )

        with mock.patch.object(
            registry_contracts._component_registry, "get_token_uri"
        ), mock.patch.object(
            registry_contracts._agent_registry, "get_token_uri"
        ), mock.patch.object(
            registry_contracts._service_registry, "get_token_uri"
        ), mock.patch(
            "autonomy.chain.utils.r_get", side_effect=RequestsConnectionError
        ):
            result = self.run_cli(
                commands=(
                    package_id.package_type.value,
                    str(
                        DUMMY_PACKAGE_MANAGER.package_path_from_package_id(
                            package_id=package_id
                        )
                    ),
                    str(ETHEREUM_KEY_DEPLOYER),
                    *parameters,
                ),
            )
            self.cli_runner.mix_stderr = True
            assert result.exit_code == 1, result.output
            assert (
                "Dependency verification failed; Error connecting to the IPFS gateway"
                in result.stdout
            )

    def test_connection_error(
        self,
    ) -> None:
        """Test connection error."""

        with mock.patch(
            "autonomy.chain.mint.transact", side_effect=RequestsConnectionError
        ):
            result = self.run_cli(
                commands=(
                    "protocol",
                    str(
                        DUMMY_PACKAGE_MANAGER.package_path_from_package_id(
                            package_id=DUMMY_PROTOCOL
                        )
                    ),
                    str(ETHEREUM_KEY_DEPLOYER),
                ),
            )
            self.cli_runner.mix_stderr = True
            assert result.exit_code == 1, result.output
            assert (
                "Component mint failed with following error; Cannot connect to the given RPC"
                in result.stderr
            )

    def test_connection_error_service(
        self,
    ) -> None:
        """Test connection error."""

        with mock.patch(
            "autonomy.chain.mint.transact", side_effect=RequestsConnectionError
        ), mock.patch("autonomy.cli.helpers.chain.verify_service_dependencies"):
            result = self.run_cli(
                commands=(
                    "service",
                    str(
                        DUMMY_PACKAGE_MANAGER.package_path_from_package_id(
                            package_id=DUMMY_SERVICE
                        )
                    ),
                    str(ETHEREUM_KEY_DEPLOYER),
                    *DEFAULT_SERVICE_MINT_PARAMETERS,
                ),
            )
            self.cli_runner.mix_stderr = True
            assert result.exit_code == 1, result.output
            assert (
                "Service mint failed with following error; Cannot connect to the given RPC"
                in result.stderr
            )

    def test_fail_token_id_retrieve(
        self,
    ) -> None:
        """Test token id retrieval failure."""

        with mock.patch.object(
            registry_contracts, "_component_registry", DummyContract()
        ), mock.patch("autonomy.chain.mint.transact"):

            result = self.run_cli(
                commands=(
                    DUMMY_PROTOCOL.package_type.value,
                    str(
                        DUMMY_PACKAGE_MANAGER.package_path_from_package_id(
                            package_id=DUMMY_PROTOCOL
                        )
                    ),
                    str(ETHEREUM_KEY_DEPLOYER),
                ),
            )

            assert result.exit_code == 1, result.output
            assert (
                "Component mint was successful but token ID retrieving failed with following error; "
                "Connection interrupted while waiting for the unitId emit event"
                in result.stderr
            )

    def test_fail_token_id_retrieve_service(
        self,
    ) -> None:
        """Test token id retrieval failure."""

        with mock.patch.object(
            registry_contracts, "_service_registry", DummyContract()
        ), mock.patch("autonomy.chain.mint.transact"), mock.patch(
            "autonomy.cli.helpers.chain.verify_service_dependencies"
        ):

            result = self.run_cli(
                commands=(
                    DUMMY_SERVICE.package_type.value,
                    str(
                        DUMMY_PACKAGE_MANAGER.package_path_from_package_id(
                            DUMMY_SERVICE
                        )
                    ),
                    str(ETHEREUM_KEY_DEPLOYER),
                    *DEFAULT_SERVICE_MINT_PARAMETERS,
                ),
            )

            assert result.exit_code == 1, result.output
            assert (
                "Service mint was successful but token ID retrieving failed with following error; "
                "Connection interrupted while waiting for the unitId emit event"
                in result.stderr
            )

    def test_fail_dependency_does_not_match_service(
        self,
    ) -> None:
        """Test token id retrieval failure."""

        result = self.run_cli(
            commands=(
                DUMMY_SERVICE.package_type.value,
                str(DUMMY_PACKAGE_MANAGER.package_path_from_package_id(DUMMY_SERVICE)),
                str(ETHEREUM_KEY_DEPLOYER),
                *DEFAULT_SERVICE_MINT_PARAMETERS,
            ),
        )

        assert result.exit_code == 1, result.output
        assert (
            "On chain ID of the agent does not match with the one in the service configuration"
            in result.stderr
        )

    def test_fail_dependency_does_not_match_component(
        self,
    ) -> None:
        """Test token id retrieval failure."""

        result = self.run_cli(
            commands=(
                DUMMY_CONNECTION.package_type.value,
                str(
                    DUMMY_PACKAGE_MANAGER.package_path_from_package_id(DUMMY_CONNECTION)
                ),
                str(ETHEREUM_KEY_DEPLOYER),
                "-d",
                "1",
            ),
        )

        assert result.exit_code == 1, result.output
        assert (
            "On chain dependency with id 1 not found in the local package configuration"
            in result.stderr
        )
