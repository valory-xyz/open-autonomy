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

"""Test `autonomy analyse service` command"""

import logging
from copy import deepcopy
from typing import Any, Dict, List, Tuple
from unittest import mock

import pytest
from aea.configurations.base import AgentConfig
from aea.configurations.data_types import ComponentId, ComponentType, PublicId
from aea.helpers.cid import to_v0
from aea_cli_ipfs.ipfs_utils import IPFSTool

from autonomy.analyse.service import ServiceAnalyser
from autonomy.configurations.base import Service

from tests.test_autonomy.test_cli.base import BaseCliTest


DUMMY_AGENT_HASH = "bafybeib56ojddzexxbapowofypmpk6zeznqaumwgj7ftneb5ua6sk5k5vm"
DUMMY_LEDGER_CONNECTION_HASH = (
    "bafybeib56ojddzexxbapowofypmpk6zeznqaumwgj7ftneb5ua6sk5k5vn"
)
DUMMY_ABCI_CONNECTION_HASH = (
    "bafybeib56ojddzexxbapowofypmpk6zeznqaumwgj7ftneb5ua6sk5k5vo"
)
DUMMY_SKILL_HASH = "bafybeib56ojddzexxbapowofypmpk6zeznqaumwgj7ftneb5ua6sk5k5vp"


def get_dummy_service_config() -> Dict:
    """Returns dummy service config."""
    return {
        "name": "dummy_service",
        "author": "valory",
        "version": "0.1.0",
        "description": "A dummy service config file with sigular overrides.",
        "aea_version": ">=1.0.0, <2.0.0",
        "license": "Apache-2.0",
        "fingerprint": {
            "README.md": "bafybeiapubcoersqnsnh3acia5hd7otzt7kjxekr6gkbrlumv6tkajl6jm"
        },
        "fingerprint_ignore_patterns": [],
        "agent": f"valory/dummy_agent:0.1.0:{DUMMY_AGENT_HASH}",
        "number_of_agents": 1,
    }


def get_dummy_overrides_skill() -> Dict:
    """Returns dummy skill overrides."""
    return {
        "public_id": "valory/abci_skill:0.1.0",
        "type": "skill",
        "models": {
            "params": {
                "args": {
                    "message": "Hello, World!",
                    "setup": {
                        "safe_contract_address": [
                            ["0xAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"]
                        ],
                        "all_participants": [["0x"]],
                    },
                    "tendermint_url": "tendermint_url",
                    "tendermint_com_url": "tendermint_com_url",
                    "tendermint_p2p_url": "tendermint_p2p_url",
                    "service_registry_address": "service_registry_address",
                    "share_tm_config_on_startup": "share_tm_config_on_startup",
                    "on_chain_service_id": "on_chain_service_id",
                },
            }
        },
    }


def get_dummy_overrides_ledger_connection() -> Dict:
    """Returns dummy connection overrides"""
    return {
        "public_id": "valory/ledger:0.1.0",
        "type": "connection",
        "config": {
            "ledger_apis": {
                "ethereum": {
                    "address": "address",
                    "chain_id": 1,
                    "poa_chain": False,
                    "default_gas_price_strategy": "eip1559",
                }
            }
        },
    }


def get_dummy_overrides_abci_connection() -> Dict:
    """Returns dummy connection overrides"""
    return {
        "public_id": "valory/abci:0.1.0",
        "type": "connection",
        "config": {
            "host": "host",
            "port": "port",
            "use_tendermint": "use_tendermint",
        },
    }


def get_dummy_agent_config() -> Dict:
    """Returns dummy agent config"""
    return {
        "agent_name": "dummy_agent",
        "author": "valory",
        "version": "0.1.0",
        "license": "Apache-2.0",
        "description": "agent",
        "aea_version": ">=1.0.0, <2.0.0",
        "fingerprint": {},
        "fingerprint_ignore_patterns": [],
        "connections": [
            f"valory/abci:0.1.0:{DUMMY_ABCI_CONNECTION_HASH}",
            f"valory/ledger:0.1.0:{DUMMY_LEDGER_CONNECTION_HASH}",
        ],
        "contracts": [],
        "protocols": [],
        "skills": [
            f"valory/abci_skill:0.1.0:{DUMMY_SKILL_HASH}",
        ],
        "default_ledger": "ethereum",
        "required_ledgers": ["ethereum"],
        "default_routing": {},
        "connection_private_key_paths": {},
        "private_key_paths": {},
        "logging_config": {
            "version": 1,
            "disable_existing_loggers": False,
        },
        "dependencies": {},
        "default_connection": None,
    }


@pytest.mark.skip
class BaseAnalyseServiceTest(BaseCliTest):
    """Base class for service verifier tests"""

    cli_options: Tuple[str, ...] = ("analyse", "service")

    @classmethod
    def setup_class(cls) -> None:
        """Setup class."""
        super().setup_class()

        cls.cli_runner.mix_stderr = False

    @staticmethod
    def patch_check_agent_package_published(**kwargs: Any) -> mock._patch:
        """Patch `ServiceAnalyser.check_agent_package_published` method"""
        return mock.patch.object(
            ServiceAnalyser, "check_agent_package_published", **kwargs
        )

    @staticmethod
    def patch_check_agent_dependencies_published(**kwargs: Any) -> mock._patch:
        """Patch `ServiceAnalyser.check_agent_dependencies_published` method"""
        return mock.patch.object(
            ServiceAnalyser, "check_agent_dependencies_published", **kwargs
        )

    @staticmethod
    def patch_verify_overrides(**kwargs: Any) -> mock._patch:
        """Patch `ServiceAnalyser.verify_overrides` method"""
        return mock.patch.object(ServiceAnalyser, "verify_overrides", **kwargs)

    @staticmethod
    def patch_validate_service_overrides(**kwargs: Any) -> mock._patch:
        """Patch `ServiceAnalyser.validate_service_overrides` method"""
        return mock.patch.object(
            ServiceAnalyser, "validate_service_overrides", **kwargs
        )

    @staticmethod
    def patch_check_skill_override(**kwargs: Any) -> mock._patch:
        """Patch `ServiceAnalyser.check_skill_override` method"""
        return mock.patch.object(ServiceAnalyser, "check_skill_override", **kwargs)

    @staticmethod
    def patch_ipfs_tool(pins: List[str]) -> mock._patch:
        """Patch `ServiceAnalyser.check_skill_override` method"""
        return mock.patch.object(IPFSTool, "all_pins", return_value=pins)

    @staticmethod
    def patch_service_loader(data: List[Dict[str, Any]]) -> mock._patch:
        """Patch service loader method"""

        config, *overrides = data
        service = Service.from_json(config)
        service.overrides = overrides

        return mock.patch(
            "autonomy.analyse.service.load_service_config",
            return_value=service,
        )

    @staticmethod
    def patch_agent_loader(data: List[Dict[str, Any]]) -> mock._patch:
        """Patch agent loader method"""
        config, *_overrides = data
        agent_config = AgentConfig.from_json(config)
        if len(_overrides) > 0:
            overrides = {}
            for o in _overrides:
                overrides[
                    ComponentId(
                        component_type=ComponentType(o.pop("type")),
                        public_id=PublicId.from_str(o.pop("public_id")),
                    )
                ] = o
            agent_config.component_configurations = overrides

        return mock.patch(
            "autonomy.cli.helpers.analyse._load_agent_from_ipfs",
            return_value=agent_config,
        )


class TestCheckRequiredOverrides(BaseAnalyseServiceTest):
    """Test override verification."""

    def test_abci_skill_params_not_defined(self) -> None:
        """Test successful run."""

        skill_config = get_dummy_overrides_skill()
        del skill_config["models"]["params"]

        with self.patch_service_loader(
            data=[get_dummy_service_config(), skill_config]
        ), self.patch_ipfs_tool([]), self.patch_agent_loader(
            data=[get_dummy_agent_config()]
        ):
            result = self.run_cli(commands=(str(self.t),))

        assert result.exit_code == 1, result.stdout
        assert (
            "ABCI skill validation failed; 'params' is a required property"
            in result.stderr
        )

    def test_abci_skill_required_arg_not_defined(self) -> None:
        """Test successful run."""

        skill_config = get_dummy_overrides_skill()
        del skill_config["models"]["params"]["args"]["tendermint_url"]

        with self.patch_service_loader(
            data=[get_dummy_service_config(), skill_config]
        ), self.patch_ipfs_tool([]), self.patch_agent_loader(
            data=[get_dummy_agent_config()]
        ):
            result = self.run_cli(commands=(str(self.t),))

        assert result.exit_code == 1, result.stdout
        assert (
            "Error: ABCI skill validation failed; 'tendermint_url' is a required property"
            in result.stderr
        )

    def test_abci_skill_setup_param_not_defined(self) -> None:
        """Test successful run."""

        skill_config = get_dummy_overrides_skill()

        del skill_config["models"]["params"]["args"]["setup"]["all_participants"]

        with self.patch_service_loader(
            data=[get_dummy_service_config(), skill_config]
        ), self.patch_ipfs_tool([]), self.patch_agent_loader(
            data=[get_dummy_agent_config()]
        ):
            result = self.run_cli(commands=(str(self.t),))

        assert result.exit_code == 1, result.stdout
        assert (
            "Error: ABCI skill validation failed; 'all_participants' is a required property"
            in result.stderr
        )

    def test_ledger_connection_ledger_not_defined(self) -> None:
        """Test successful run."""

        connection_config = get_dummy_overrides_ledger_connection()
        del connection_config["config"]["ledger_apis"]["ethereum"]

        with self.patch_service_loader(
            data=[get_dummy_service_config(), connection_config]
        ), self.patch_ipfs_tool([]), self.patch_agent_loader(
            data=[get_dummy_agent_config()]
        ):
            result = self.run_cli(commands=(str(self.t),))

        assert result.exit_code == 1, result.stdout
        assert (
            "Error: Ledger connection validation failed; {} does not have enough properties"
            in result.stderr
        )

    def test_ledger_connection_unknown_ledger_defined(self, caplog: Any) -> None:
        """Test successful run."""

        connection_config = get_dummy_overrides_ledger_connection()
        connection_config["config"]["ledger_apis"]["solana"] = connection_config[
            "config"
        ]["ledger_apis"]["ethereum"]

        with self.patch_service_loader(
            data=[get_dummy_service_config(), connection_config]
        ), self.patch_ipfs_tool([]), self.patch_agent_loader(
            data=[get_dummy_agent_config()]
        ), caplog.at_level(
            logging.WARN
        ):
            result = self.run_cli(commands=(str(self.t),))

        assert result.exit_code == 1, result.stdout
        assert "Unknown ledger configuration found with name `solana`" in caplog.text

    def test_ledger_connection_param_not_defined(self) -> None:
        """Test successful run."""

        connection_config = get_dummy_overrides_ledger_connection()
        del connection_config["config"]["ledger_apis"]["ethereum"]["address"]

        with self.patch_service_loader(
            data=[get_dummy_service_config(), connection_config]
        ), self.patch_ipfs_tool([]), self.patch_agent_loader(
            data=[get_dummy_agent_config()]
        ):
            result = self.run_cli(commands=(str(self.t),))

        assert result.exit_code == 1, result.stdout
        assert (
            "Error: Ledger connection validation failed; 'address' is a required property"
            in result.stderr
        )

    def test_abci_connection_setup_param_not_defined(self) -> None:
        """Test successful run."""

        connection_config = get_dummy_overrides_abci_connection()
        del connection_config["config"]["host"]

        with self.patch_service_loader(
            data=[get_dummy_service_config(), connection_config]
        ), self.patch_ipfs_tool([]), self.patch_agent_loader(
            data=[get_dummy_agent_config()]
        ):
            result = self.run_cli(commands=(str(self.t),))

        assert result.exit_code == 1, result.stdout
        assert (
            "Error: ABCI connection validation failed; 'host' is a required property"
            in result.stderr
        )


class TestCheckAgentPackagePublished(BaseAnalyseServiceTest):
    """Test `check_agent_package_published` method."""

    def test_agent_not_found(self) -> None:
        """Test failure."""

        with self.patch_service_loader(
            data=[get_dummy_service_config(), get_dummy_overrides_skill()]
        ), self.patch_ipfs_tool([]), self.patch_agent_loader(
            data=[get_dummy_agent_config()]
        ), self.patch_validate_service_overrides():
            result = self.run_cli(commands=(str(self.t),))

        assert result.exit_code == 1, result.stdout
        assert (
            "Agent package for service valory/dummy_service:0.1.0 not published on the IPFS registry"
            in result.stderr
        )


class TestVerifyOverrides(BaseAnalyseServiceTest):
    """Test verify overrides method."""

    def test_missing_override(self) -> None:
        """Test missing override section from agent config."""

        with self.patch_service_loader(
            data=[get_dummy_service_config(), get_dummy_overrides_skill()]
        ), self.patch_ipfs_tool([]), self.patch_agent_loader(
            data=[get_dummy_agent_config()]
        ), self.patch_validate_service_overrides(), self.patch_check_agent_package_published():
            result = self.run_cli(commands=(str(self.t),))

        assert result.exit_code == 1, result.stdout
        assert (
            "Service config has an overrides which are not defined in the agent config; "
            "packages with missing overrides={PackageId(skill, valory/abci_skill:0.1.0)}"
            in result.stderr
        )


class TestCheckAgentDependenciesPublished(BaseAnalyseServiceTest):
    """Test `check_agent_dependencies_published` method."""

    def test_dependency_missing_from_ipfs(self) -> None:
        """Test missing dependency"""

        with self.patch_service_loader(
            data=[get_dummy_service_config(), get_dummy_overrides_skill()]
        ), self.patch_ipfs_tool([]), self.patch_agent_loader(
            data=[get_dummy_agent_config()]
        ), self.patch_validate_service_overrides(), self.patch_check_agent_package_published(), self.patch_verify_overrides():
            result = self.run_cli(commands=(str(self.t),))

        assert result.exit_code == 1, result.stdout
        assert (
            "Package required for service valory/dummy_service:0.1.0 is not published on the IPFS registry"
            in result.stderr
        )


class TestCheckOnChainState(BaseAnalyseServiceTest):
    """Test `check_on_chain_state` method."""

    def test_on_chain_status_check(self) -> None:
        """Test `check_on_chain_state` failure"""

        with self.patch_service_loader(
            data=[get_dummy_service_config(), get_dummy_overrides_skill()]
        ), mock.patch(
            "autonomy.analyse.service.get_service_info", return_value=[None, 0, None]
        ):
            result = self.run_cli(commands=(str(self.t), "--token-id", "1"))

        assert result.exit_code == 1, result.stdout
        assert "Service needs to be in deployed state on-chain" in result.stderr


class TestCheckSuccessful(BaseAnalyseServiceTest):
    """Test a successful check"""

    def test_run(self) -> None:
        """Test run."""

        skill_config = get_dummy_overrides_skill()
        models = skill_config.pop("models")
        for i in range(4):
            skill_config[i] = {"models": deepcopy(models)}

        with self.patch_service_loader(
            data=[
                get_dummy_service_config(),
                skill_config,
                get_dummy_overrides_abci_connection(),
                get_dummy_overrides_ledger_connection(),
            ]
        ), self.patch_ipfs_tool(
            pins=list(
                map(
                    to_v0,
                    [
                        DUMMY_AGENT_HASH,
                        DUMMY_LEDGER_CONNECTION_HASH,
                        DUMMY_ABCI_CONNECTION_HASH,
                        DUMMY_SKILL_HASH,
                    ],
                )
            )
        ), self.patch_agent_loader(
            data=[
                get_dummy_agent_config(),
                get_dummy_overrides_skill(),
                get_dummy_overrides_abci_connection(),
                get_dummy_overrides_ledger_connection(),
            ]
        ):
            result = self.run_cli(commands=(str(self.t),))

        assert result.exit_code == 0, result.stderr
        assert "Service is ready to be deployed" in result.output
