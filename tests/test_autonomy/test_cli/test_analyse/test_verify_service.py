# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2023-2024 Valory AG
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

from aea.configurations.base import AgentConfig, SkillConfig
from aea.configurations.data_types import (
    ComponentId,
    ComponentType,
    PackageId,
    PackageType,
    PublicId,
)
from aea.helpers.cid import to_v0
from aea_cli_ipfs.ipfs_utils import IPFSDaemon, IPFSTool
from requests.exceptions import ConnectionError as RequestConnectionError

from autonomy.analyse.service import ServiceAnalyser
from autonomy.configurations.base import Service

from tests.test_autonomy.test_cli.base import BaseCliTest


DUMMY_SERVICE_HASH = "bafybeib56ojddzexxbapowofypmpk6zeznqaumwgj7ftneb5ua6sk5k5vj"
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


def get_dummy_overrides_skill(env_vars_with_name: bool = False) -> Dict:
    """Returns dummy skill overrides."""
    if env_vars_with_name:
        return {
            "public_id": "valory/abci_skill:0.1.0",
            "type": "skill",
            "models": {
                "params": {
                    "args": {
                        "message": "${MESSAGE:str:Hello, World!}",
                        "reset_pause_duration": "${RESET_PAUSE_DURATION:int:10}",
                        "setup": {
                            "safe_contract_address": "${SAFE_CONTRACT_ADDRESS:str:0xaddress}",
                            "all_participants": '${ALL_PARTICIPANTS:list:["0x"]}',
                            "consensus_threshold": "${CONSENSUS_THRESHOLD:int:null}",
                        },
                        "tendermint_url": "${TENDERMINT_URL:str:http://localhost}",
                        "tendermint_com_url": "${TENDERMINT_COM_URL:str:http://localhost}",
                        "tendermint_p2p_url": "${TENDERMINT_P2P_URL:str:http://localhost}",
                        "service_registry_address": "${SERVICE_REGISTRY_ADDRESS:str:0xaddress}",
                        "share_tm_config_on_startup": "${SHARE_TM_CONFIG_ON_STARTUP:bool:false}",
                        "on_chain_service_id": "${ON_CHAIN_SERVICE_ID:int:null}",
                    },
                }
            },
        }
    return {
        "public_id": "valory/abci_skill:0.1.0",
        "type": "skill",
        "models": {
            "params": {
                "args": {
                    "message": "${str:Hello, World!}",
                    "reset_pause_duration": "${int:10}",
                    "setup": {
                        "safe_contract_address": "${str:0xaddress}",
                        "all_participants": '${list:["0x"]}',
                        "consensus_threshold": "${int:null}",
                    },
                    "tendermint_url": "${str:http://localhost}",
                    "tendermint_com_url": "${str:http://localhost}",
                    "tendermint_p2p_url": "${str:http://localhost}",
                    "service_registry_address": "${str:0xaddress}",
                    "share_tm_config_on_startup": "${bool:false}",
                    "on_chain_service_id": "${int:null}",
                },
            }
        },
    }


def get_dummy_overrides_ledger_connection(env_vars_with_name: bool = False) -> Dict:
    """Returns dummy connection overrides"""
    if env_vars_with_name:
        return {
            "public_id": "valory/ledger:0.1.0",
            "type": "connection",
            "config": {
                "ledger_apis": {
                    "ethereum": {
                        "address": "${ADDRESS:str:address}",
                        "chain_id": "${CHAIN_ID:int:1}",
                        "poa_chain": "${POA_CHAIN:bool:false}",
                        "default_gas_price_strategy": "${DEFAULT_GAS_PRICE_STRATEGY:str:eip1559}",
                    }
                }
            },
        }
    return {
        "public_id": "valory/ledger:0.1.0",
        "type": "connection",
        "config": {
            "ledger_apis": {
                "ethereum": {
                    "address": "${str:address}",
                    "chain_id": "${int:1}",
                    "poa_chain": "${bool:false}",
                    "default_gas_price_strategy": "${str:eip1559}",
                }
            }
        },
    }


def get_dummy_overrides_abci_connection(env_vars_with_name: bool = False) -> Dict:
    """Returns dummy connection overrides"""
    if env_vars_with_name:
        return {
            "public_id": "valory/abci:0.1.0",
            "type": "connection",
            "config": {
                "host": "${ABCI_HOST:str:host}",
                "port": "${ABCI_PORT:str:port}",
                "use_tendermint": "${ABCI_USE_TENDERMINT:bool:false}",
            },
        }

    return {
        "public_id": "valory/abci:0.1.0",
        "type": "connection",
        "config": {
            "host": "${str:host}",
            "port": "${str:port}",
            "use_tendermint": "${bool:false}",
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


def get_dummy_skill_config() -> Dict:
    """Returns dummy skill config"""
    return {
        "name": "abci_skill",
        "author": "valory",
        "version": "0.1.0",
        "type": "skill",
        "description": "Hello World ABCI application.",
        "license": "Apache-2.0",
        "aea_version": ">=1.0.0, <2.0.0",
        "fingerprint": {},
        "fingerprint_ignore_patterns": [],
        "connections": [],
        "contracts": [],
        "protocols": [],
        "skills": [
            "valory/abstract_round_abci:0.1.0:bafybeiami2y2uwvtmjf76hl3jvfahujdir5docjby6erdyjl66ekoblesi"
        ],
        "behaviours": {"main": {"args": {}, "class_name": "DummyBehaviour"}},
        "handlers": {},
        "models": {
            "params": {
                "args": {
                    "cleanup_history_depth": 1,
                    "cleanup_history_depth_current": None,
                    "drand_public_key": "drand_public_key",
                    "genesis_config": {},
                    "keeper_timeout": 30,
                    "max_attempts": 10,
                    "max_healthcheck": 120,
                    "observation_interval": 10,
                    "on_chain_service_id": None,
                    "request_retry_delay": 1,
                    "request_timeout": 10,
                    "reset_pause_duration": 10,
                    "reset_tendermint_after": 2,
                    "retry_attempts": 400,
                    "retry_timeout": 3,
                    "round_timeout_seconds": 30,
                    "service_id": "hello_world_abci",
                    "service_registry_address": None,
                    "setup": {
                        "all_participants": "- '0x0000000000000000000000000000000000000000'",
                        "safe_contract_address": "0x0000000000000000000000000000000000000000",
                        "consensus_threshold": None,
                    },
                    "share_tm_config_on_startup": False,
                    "sleep_time": 1,
                    "tendermint_check_sleep_delay": 3,
                    "tendermint_com_url": "http://localhost:8080",
                    "tendermint_max_retries": 5,
                    "tendermint_p2p_url": "localhost:26656",
                    "tendermint_url": "http://localhost:26657",
                    "tx_timeout": 10,
                    "use_termination": False,
                    "use_slashing": False,
                    "slash_cooldown_hours": 3,
                    "slash_threshold_amount": 10_000_000_000_000_000,
                    "light_slash_unit_amount": 5_000_000_000_000_000,
                    "serious_slash_unit_amount": 8_000_000_000_000_000,
                },
                "class_name": "Params",
            },
        },
        "dependencies": {},
        "is_abstract": False,
    }


class BaseAnalyseServiceTest(BaseCliTest):
    """Base class for service verifier tests"""

    cli_options: Tuple[str, ...] = ("analyse", "service")
    public_id_option = ("--public-id", "valory/service")
    token_id_option = ("--token-id", "1")

    @classmethod
    def setup_class(cls) -> None:
        """Setup class."""
        super().setup_class()

        cls.cli_runner.mix_stderr = False

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
    def patch_check_on_chain_state(**kwargs: Any) -> mock._patch:
        """Patch `ServiceAnalyser.check_on_chain_state` method"""
        return mock.patch.object(ServiceAnalyser, "check_on_chain_state", **kwargs)

    @staticmethod
    def patch_ipfs_daemon_is_started(**kwargs: Any) -> mock._patch:
        """Patch IPFSDaemon.is_started method"""
        return mock.patch.object(
            IPFSDaemon,
            "is_started",
            **kwargs,
        )

    @staticmethod
    def patch_loader(
        service_data: List[Dict[str, Any]],
        agent_data: List[Dict[str, Any]],
        skill_data: Dict[str, Any],
        is_remote: bool = False,
    ) -> mock._patch:
        """Patch service loader method"""

        def _loader_patch(package_id: PackageId, **kargs: Any) -> Any:
            if package_id.package_type == PackageType.SERVICE:
                config, *overrides = service_data
                service = Service.from_json(config)
                service.overrides = overrides
                return service

            if package_id.package_type == PackageType.AGENT:
                config, *_overrides = agent_data
                agent_config = AgentConfig.from_json(config)
                if len(_overrides) > 0:
                    processed_overrides = {}
                    for o in _overrides:
                        processed_overrides[
                            ComponentId(
                                component_type=ComponentType(o.pop("type")),
                                public_id=PublicId.from_str(o.pop("public_id")),
                            )
                        ] = o
                    agent_config.component_configurations = processed_overrides
                return agent_config

            if package_id.package_type == PackageType.SKILL:
                return SkillConfig.from_json(skill_data)

        if is_remote:
            return mock.patch(
                "autonomy.cli.helpers.analyse._load_from_ipfs",
                new=_loader_patch,
            )

        return mock.patch(
            "autonomy.cli.helpers.analyse._load_from_local",
            new=_loader_patch,
        )

    @staticmethod
    def patch_get_on_chain_service_id() -> mock._patch:
        """Patch _get_on_chain_service_id"""

        return mock.patch(
            "autonomy.cli.helpers.analyse._get_on_chain_service_id",
            return_value=PackageId(
                package_type=PackageType.SERVICE,
                public_id=PublicId.from_str(f"valory/service:{DUMMY_SERVICE_HASH}"),
            ),
        )


class TestVerifySkillConfig(BaseAnalyseServiceTest):
    """Test verify overrides method."""

    def test_abci_skill_not_found(self) -> None:
        """Test run."""

        skill_config = get_dummy_skill_config()
        skill_config["skills"] = []
        with self.patch_loader(
            service_data=[
                get_dummy_service_config(),
                get_dummy_overrides_skill(env_vars_with_name=True),
            ],
            agent_data=[get_dummy_agent_config(), get_dummy_overrides_skill()],
            skill_data=skill_config,
        ), self.patch_ipfs_tool([]):
            result = self.run_cli(commands=self.public_id_option)

        assert result.exit_code == 1, result.stdout
        assert "Chained ABCI skill package not found" in result.stderr

    def test_params_model_not_found(self) -> None:
        """Test run."""

        skill_config = get_dummy_skill_config()
        del skill_config["models"]["params"]

        with self.patch_loader(
            service_data=[
                get_dummy_service_config(),
                get_dummy_overrides_skill(env_vars_with_name=True),
            ],
            agent_data=[get_dummy_agent_config(), get_dummy_overrides_skill()],
            skill_data=skill_config,
        ), self.patch_ipfs_tool([]):
            result = self.run_cli(commands=self.public_id_option)

        assert result.exit_code == 1, result.stdout
        assert (
            "The chained ABCI skill `valory/abci_skill:0.1.0` does not contain `params` model"
            in result.stderr
        )


class TestCheckRequiredAgentOverrides(BaseAnalyseServiceTest):
    """Test agent override verification."""

    def test_missing_override(self) -> None:
        """Test missing override run."""

        skill_config_service = get_dummy_overrides_skill(env_vars_with_name=True)
        skill_config_agent = get_dummy_overrides_skill()

        del skill_config_agent["models"]["params"]["args"]["setup"]

        with self.patch_loader(
            service_data=[get_dummy_service_config(), skill_config_service],
            agent_data=[get_dummy_agent_config(), skill_config_agent],
            skill_data=get_dummy_skill_config(),
        ), self.patch_ipfs_tool([]):
            result = self.run_cli(commands=self.public_id_option)

        assert result.exit_code == 1, result.stdout
        assert (
            "Error: Agent overrides validation failed with following errors"
            "\n\t- ABCI Skill `valory/abci_skill:0.1.0` override validation failed; Following properties are require but missing 'setup'\n"
            in result.stderr
        ), result.stdout


class TestCheckRequiredServiceOverrides(BaseAnalyseServiceTest):
    """Test service override verification."""

    def test_abci_skill_params_not_defined(self) -> None:
        """Test successful run."""

        skill_config = get_dummy_overrides_skill(env_vars_with_name=True)
        del skill_config["models"]["params"]

        with self.patch_loader(
            service_data=[get_dummy_service_config(), skill_config],
            agent_data=[get_dummy_agent_config(), get_dummy_overrides_skill()],
            skill_data=get_dummy_skill_config(),
        ), self.patch_ipfs_tool([]):
            result = self.run_cli(commands=self.public_id_option)

        assert result.exit_code == 1, result.stdout
        assert (
            "Service overrides validation failed with following errors"
            "\n\t- ABCI Skill `valory/abci_skill:0.1.0` override validation failed; Following properties are require but missing 'params'\n"
            in result.stderr
        ), result.stdout

    def test_abci_skill_required_arg_not_defined(self, caplog: Any) -> None:
        """Test successful run."""

        skill_config = get_dummy_overrides_skill(env_vars_with_name=True)
        del skill_config["models"]["params"]["args"]["tendermint_url"]

        with self.patch_loader(
            service_data=[get_dummy_service_config(), skill_config],
            agent_data=[get_dummy_agent_config(), get_dummy_overrides_skill()],
            skill_data=get_dummy_skill_config(),
        ), self.patch_ipfs_tool([]), caplog.at_level(logging.WARNING):
            result = self.run_cli(commands=self.public_id_option)

        assert result.exit_code == 0, result.stderr
        assert (
            "(agent, valory/dummy_agent:0.1.0) contains configuration which is missing from (service, valory/dummy_service:0.1.0)\n\tPath: models.params.args\n\tMissing parameters: {'tendermint_url'}"
            in caplog.text
        )
        assert "Path: models.params.args" in caplog.text
        assert "Missing parameters: {'tendermint_url'}" in caplog.text

    def test_abci_skill_setup_param_not_defined(self) -> None:
        """Test successful run."""

        skill_config = get_dummy_overrides_skill()

        del skill_config["models"]["params"]["args"]["setup"]["all_participants"]

        with self.patch_loader(
            service_data=[get_dummy_service_config(), skill_config],
            agent_data=[get_dummy_agent_config(), get_dummy_overrides_skill()],
            skill_data=get_dummy_skill_config(),
        ), self.patch_ipfs_tool([]):
            result = self.run_cli(commands=self.public_id_option)

        assert result.exit_code == 1, result.stdout
        assert (
            "Service overrides validation failed with following errors\n\t- ABCI Skill `valory/abci_skill:0.1.0` override validation failed; Following properties are require but missing 'all_participants'\n"
            in result.stderr
        )

    def test_ledger_connection_ledger_not_defined(self) -> None:
        """Test successful run."""

        connection_config = get_dummy_overrides_ledger_connection(
            env_vars_with_name=True
        )
        del connection_config["config"]["ledger_apis"]["ethereum"]

        with self.patch_loader(
            service_data=[
                get_dummy_service_config(),
                get_dummy_overrides_skill(env_vars_with_name=True),
                connection_config,
            ],
            agent_data=[get_dummy_agent_config(), get_dummy_overrides_skill()],
            skill_data=get_dummy_skill_config(),
        ), self.patch_ipfs_tool([]):
            result = self.run_cli(commands=self.public_id_option)

        assert result.exit_code == 1, result.stdout
        assert (
            "Service overrides validation failed with following errors"
            "\n\t- (connection, valory/ledger:0.1.0) override needs at least one ledger API definition"
            in result.stderr
        )

    def test_ledger_connection_unknown_ledger_defined(self, caplog: Any) -> None:
        """Test successful run."""

        connection_config = get_dummy_overrides_ledger_connection(
            env_vars_with_name=True
        )
        connection_config["config"]["ledger_apis"]["solana"] = connection_config[
            "config"
        ]["ledger_apis"]["ethereum"]

        with self.patch_loader(
            service_data=[
                get_dummy_service_config(),
                get_dummy_overrides_skill(env_vars_with_name=True),
                connection_config,
            ],
            agent_data=[get_dummy_agent_config(), get_dummy_overrides_skill()],
            skill_data=get_dummy_skill_config(),
        ), self.patch_ipfs_tool([]), caplog.at_level(logging.WARNING):
            result = self.run_cli(commands=self.public_id_option)

        assert result.exit_code == 1, result.stdout
        assert (
            "Following unknown ledgers found in the (connection, valory/ledger:0.1.0) override\n\t- solana\n"
            in caplog.text
        )

    def test_ledger_connection_param_not_defined(self) -> None:
        """Test successful run."""

        connection_config = get_dummy_overrides_ledger_connection()
        del connection_config["config"]["ledger_apis"]["ethereum"]["address"]

        with self.patch_loader(
            service_data=[
                get_dummy_service_config(),
                get_dummy_overrides_skill(),
                connection_config,
            ],
            agent_data=[get_dummy_agent_config(), get_dummy_overrides_skill()],
            skill_data=get_dummy_skill_config(),
        ), self.patch_ipfs_tool([]):
            result = self.run_cli(commands=self.public_id_option)

        assert result.exit_code == 1, result.stdout
        assert (
            "Service overrides validation failed with following errors"
            "\n\t- Ledger connection validation failed; Following properties are require but missing 'address'\n"
            in result.stderr
        )

    def test_abci_connection_setup_param_not_defined(self) -> None:
        """Test successful run."""

        connection_config = get_dummy_overrides_abci_connection()
        del connection_config["config"]["host"]

        with self.patch_loader(
            service_data=[
                get_dummy_service_config(),
                get_dummy_overrides_skill(),
                connection_config,
            ],
            agent_data=[get_dummy_agent_config(), get_dummy_overrides_skill()],
            skill_data=get_dummy_skill_config(),
        ), self.patch_ipfs_tool([]):
            result = self.run_cli(commands=self.public_id_option)

        assert result.exit_code == 1, result.stdout
        assert (
            "Service overrides validation failed with following errors"
            "\n\t- ABCI connection validation failed; Following properties are require but missing 'host'\n"
            in result.stderr
        )


class TestEnvVarValidation(BaseAnalyseServiceTest):
    """Test service override verification."""

    def test_list_var_validation(self) -> None:
        """Test agent var validation."""

        skill_config = get_dummy_overrides_skill()
        skill_config["models"]["params"]["args"]["messages"] = [
            {"text": "${str:hello}"}
        ]

        with self.patch_loader(
            service_data=[
                get_dummy_service_config(),
                get_dummy_overrides_skill(env_vars_with_name=True),
            ],
            agent_data=[get_dummy_agent_config(), skill_config],
            skill_data=get_dummy_skill_config(),
        ), self.patch_ipfs_tool([]):
            result = self.run_cli(commands=self.public_id_option)

        assert result.exit_code == 0, result.stdout

    def test_agent_var_validation(self) -> None:
        """Test agent var validation."""

        skill_config = get_dummy_overrides_skill()
        skill_config["models"]["params"]["args"]["message"] = "Hello, World!"

        with self.patch_loader(
            service_data=[
                get_dummy_service_config(),
                get_dummy_overrides_skill(env_vars_with_name=True),
            ],
            agent_data=[get_dummy_agent_config(), skill_config],
            skill_data=get_dummy_skill_config(),
        ), self.patch_ipfs_tool([]):
            result = self.run_cli(commands=self.public_id_option)

        assert result.exit_code == 1, result.stdout
        assert (
            "(skill, valory/abci_skill:0.1.0) environment variable validation failed with following error\n\t- "
            "`models.params.args.message` needs environment variable defined in following format ${ENV_VAR_NAME:DATA_TYPE:DEFAULT_VALUE}\n"
            in result.stderr
        ), result.stdout

    def test_var_type_validation(self) -> None:
        """Test var type validation."""

        skill_config = get_dummy_overrides_skill()
        skill_config["models"]["params"]["args"]["tendermint_url"] = None

        with self.patch_loader(
            service_data=[
                get_dummy_service_config(),
                get_dummy_overrides_skill(env_vars_with_name=True),
            ],
            agent_data=[get_dummy_agent_config(), skill_config],
            skill_data=get_dummy_skill_config(),
        ), self.patch_ipfs_tool([]):
            result = self.run_cli(commands=self.public_id_option)

        assert result.exit_code == 1, result.stdout
        assert (
            "(skill, valory/abci_skill:0.1.0) environment variable validation failed with following error"
            "\n\t- `models.params.args.tendermint_url` needs to be defined as a environment variable"
            in result.stderr
        ), result.stdout

    def test_loading(self) -> None:
        """Test var type validation."""

        skill_config = get_dummy_overrides_skill()
        skill_config["models"]["params"]["args"]["tendermint_url"] = "${int:hello}"

        with self.patch_loader(
            service_data=[
                get_dummy_service_config(),
                get_dummy_overrides_skill(env_vars_with_name=True),
            ],
            agent_data=[get_dummy_agent_config(), skill_config],
            skill_data=get_dummy_skill_config(),
        ), self.patch_ipfs_tool([]):
            result = self.run_cli(commands=self.public_id_option)

        assert result.exit_code == 1, result.stdout
        assert (
            "(skill, valory/abci_skill:0.1.0) environment variable validation failed with following error"
            "\n\t- `models.params.args.tendermint_url` validation failed with following error; Cannot convert string `hello` to type `int`"
            in result.stderr
        ), result.stdout


class TestCheckAgentDependenciesPublished(BaseAnalyseServiceTest):
    """Test `check_agent_package_published` method."""

    def test_dependency_not_found(self) -> None:
        """Test failure."""

        with self.patch_loader(
            service_data=[
                get_dummy_service_config(),
                get_dummy_overrides_skill(env_vars_with_name=True),
            ],
            agent_data=[get_dummy_agent_config(), get_dummy_overrides_skill()],
            skill_data=get_dummy_skill_config(),
            is_remote=True,
        ), self.patch_ipfs_tool(
            []
        ), self.patch_validate_service_overrides(), self.patch_ipfs_daemon_is_started(
            return_value=True,
        ), self.patch_get_on_chain_service_id(), self.patch_check_on_chain_state():
            result = self.run_cli(commands=self.token_id_option)

        assert result.exit_code == 1, result.stdout
        assert (
            "Error: Package required for service valory/dummy_service:0.1.0 is not published on the IPFS registry"
            in result.stderr
        )
        assert "agent: valory/dummy_agent:0.1.0" in result.stderr


class TestVerifyCrossOverrides(BaseAnalyseServiceTest):
    """Test verify overrides method."""

    def test_overrides_missing_from_agent(self) -> None:
        """Test missing override section from agent config."""

        with self.patch_loader(
            service_data=[
                get_dummy_service_config(),
                get_dummy_overrides_skill(env_vars_with_name=True),
                get_dummy_overrides_ledger_connection(env_vars_with_name=True),
            ],
            agent_data=[get_dummy_agent_config(), get_dummy_overrides_skill()],
            skill_data=get_dummy_skill_config(),
        ), self.patch_ipfs_tool([]), self.patch_validate_service_overrides():
            result = self.run_cli(commands=self.public_id_option)

        assert result.exit_code == 1, result.stdout
        assert (
            "Overrides with following component IDs are defined in the service configuration but not in the agent configuration"
            "\n\t- (connection, valory/ledger:0.1.0)\n" in result.stderr
        )

    def test_overrides_missing_from_service(self, caplog: Any) -> None:
        """Test missing override section from service config."""

        with self.patch_loader(
            service_data=[get_dummy_service_config()],
            agent_data=[get_dummy_agent_config(), get_dummy_overrides_skill()],
            skill_data=get_dummy_skill_config(),
        ), self.patch_ipfs_tool(
            []
        ), self.patch_validate_service_overrides(), caplog.at_level(
            logging.WARNING
        ):
            result = self.run_cli(commands=self.public_id_option)

        assert result.exit_code == 0, result.stdout
        assert (
            "Overrides with following component IDs are defined in the agent configuration but not in the service configuration"
            "\n\t- (skill, valory/abci_skill:0.1.0)" in caplog.text
        )


class TestCheckOnChainState(BaseAnalyseServiceTest):
    """Test `check_on_chain_state` method."""

    def test_on_chain_status_check(self, caplog: Any) -> None:
        """Test `check_on_chain_state` failure"""

        with self.patch_loader(
            service_data=[get_dummy_service_config(), get_dummy_overrides_skill()],
            agent_data=[get_dummy_agent_config(), get_dummy_overrides_skill()],
            skill_data=get_dummy_skill_config(),
            is_remote=True,
        ), mock.patch(
            "autonomy.analyse.service.get_service_info", return_value=[None, 0, None]
        ), self.patch_ipfs_tool(
            []
        ), self.patch_ipfs_daemon_is_started(
            return_value=True,
        ), self.patch_get_on_chain_service_id(), caplog.at_level(
            logging.WARNING
        ):
            result = self.run_cli(commands=self.token_id_option)

        assert result.exit_code == 1, result.stdout
        assert (
            "Service needs to be in deployed state on-chain; Current state=ServiceState.NON_EXISTENT"
            in caplog.text
        )

    def test_on_chain_status_check_rpc_failure(self) -> None:
        """Test `check_on_chain_state` RPC connection failure"""

        with self.patch_loader(
            service_data=[get_dummy_service_config(), get_dummy_overrides_skill()],
            agent_data=[get_dummy_agent_config(), get_dummy_overrides_skill()],
            skill_data=get_dummy_skill_config(),
            is_remote=True,
        ), mock.patch(
            "autonomy.analyse.service.get_service_info",
            side_effect=RequestConnectionError,
        ), self.patch_ipfs_tool(
            []
        ), self.patch_ipfs_daemon_is_started(
            return_value=True,
        ), self.patch_get_on_chain_service_id():
            result = self.run_cli(commands=self.token_id_option)

        assert result.exit_code == 1, result.stdout
        assert (
            "On chain service validation failed, could not connect to the RPC"
            in result.stderr
        )


class TestCheckSuccessful(BaseAnalyseServiceTest):
    """Test a successful check"""

    def test_run(self, caplog: Any) -> None:
        """Test run."""

        skill_config = get_dummy_overrides_skill(env_vars_with_name=True)
        models = skill_config.pop("models")
        skill_config_original = get_dummy_skill_config()
        skill_config_original["models"]["benchmark_tool"] = {
            "args": {"log_dir": "/logs"}
        }

        for i in range(4):
            skill_config[i] = {"models": deepcopy(models)}

        with self.patch_loader(
            service_data=[
                get_dummy_service_config(),
                skill_config,
                get_dummy_overrides_abci_connection(env_vars_with_name=True),
                get_dummy_overrides_ledger_connection(env_vars_with_name=True),
            ],
            agent_data=[
                get_dummy_agent_config(),
                get_dummy_overrides_skill(),
                get_dummy_overrides_abci_connection(),
                get_dummy_overrides_ledger_connection(),
            ],
            skill_data=skill_config_original,
            is_remote=True,
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
        ), self.patch_ipfs_daemon_is_started(
            return_value=True,
        ), self.patch_get_on_chain_service_id(), mock.patch(
            "autonomy.analyse.service.get_service_info",
            return_value=(None, 4, None),
        ), caplog.at_level(
            logging.WARNING
        ):
            result = self.run_cli(commands=self.token_id_option)

        assert result.exit_code == 0, result.stderr
        assert "Service is ready to be deployed" in result.output
        assert (
            "valory/termination_abci:any is not defined as a dependency" in caplog.text
        )
        assert "valory/slashing_abci:any is not defined as a dependency" in caplog.text
