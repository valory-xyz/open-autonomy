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


"""Tools for analysing the service for deployment readiness"""

import logging
from pathlib import Path
from typing import Dict, Set

from aea.configurations.base import AgentConfig
from aea.configurations.data_types import ComponentType, PackageId, PublicId
from aea.crypto.base import LedgerApi
from aea.helpers.cid import to_v0

from autonomy.chain.base import ServiceState
from autonomy.chain.config import ChainType
from autonomy.chain.service import get_service_info
from autonomy.configurations.base import Service
from autonomy.configurations.loader import load_service_config


REQUIRED_SETUP_PARAMETERES = (
    "safe_contract_address",
    "all_participants",
)

REQUIRED_PARAM_VALUES = (
    "share_tm_config_on_startup",
    "on_chain_service_id",
)


class ServiceValidationFailed(Exception):
    """Raise when service validation fails."""


class ServiceAnalyser:
    """Tools to analyse a service"""

    def __init__(self, service_path: Path) -> None:
        """Initialise object."""

        self.service_config = load_service_config(service_path=service_path)

    @staticmethod
    def check_on_chain_state(
        ledger_api: LedgerApi,
        chain_type: ChainType,
        token_id: int,
    ) -> None:
        """Check on-chain state of a service."""

        (*_, service_state, _) = get_service_info(
            ledger_api=ledger_api, chain_type=chain_type, token_id=token_id
        )

        if ServiceState(service_state) != ServiceState.DEPLOYED:
            raise ServiceValidationFailed(
                "Service needs to be in deployed state on-chain"
            )

    def check_agent_package_published(self, ipfs_pins: Set[str]) -> None:
        """Check if the agent package is published or not"""

        if to_v0(self.service_config.agent.hash) not in ipfs_pins:
            raise ServiceValidationFailed(
                f"Agent package for service {self.service_config.public_id} not published on the IPFS registry"
            )

    def check_agent_dependencies_published(
        self, agent_config: AgentConfig, ipfs_pins: Set[str]
    ) -> None:
        """Check if the agent package is published or not"""

        for dependency in agent_config.package_dependencies:
            if to_v0(dependency.package_hash) not in ipfs_pins:
                raise ServiceValidationFailed(
                    f"Package required for service {self.service_config.public_id} is not published on the IPFS registry"
                    f"\n\tagent: {self.service_config.agent.without_hash()}"
                    f"\n\tpackage: {dependency}"
                )
            logging.info(
                f"\t{dependency.public_id.without_hash()} of type {dependency.package_type} is present"
            )

    def verify_overrides(self, agent_config: AgentConfig) -> None:
        """Cross verify overrides between service config and agent config"""

        agent_overrides = set(agent_config.component_configurations)
        service_overrides = {
            PackageId(
                package_type=component_override["type"],
                public_id=PublicId.from_str(component_override["public_id"]),
            )
            for component_override in self.service_config.overrides
        }

        missing_from_agent = service_overrides - agent_overrides
        if len(missing_from_agent) > 0:
            raise ServiceValidationFailed(
                "Service config has an overrides which are not defined in the agent config; "
                f"packages with missing overrides={missing_from_agent}"
            )

    @staticmethod
    def check_skill_override(override: Dict) -> None:
        """Check skill override."""

        if "params" not in override["models"]:
            raise ServiceValidationFailed(
                "Aborting check, overrides not provided for `models:params` parameter"
            )

        for param in REQUIRED_PARAM_VALUES:
            if param not in override["models"]["params"]["args"]:
                raise ServiceValidationFailed(
                    f"`{param}` needs to be defined in the `models:params:args` parameter"
                )

        if "setup" not in override["models"]["params"]["args"]:
            raise ServiceValidationFailed(
                "Aborting check, overrides not provided for `models:params:args:setup` parameter"
            )

        for setup_param in REQUIRED_SETUP_PARAMETERES:
            if setup_param not in override["models"]["params"]["args"]["setup"]:
                raise ServiceValidationFailed(
                    f"`{setup_param}` needs to be defined in the `models:params:args:setup` parameter"
                )

    def check_required_overrides(self) -> None:
        """Check required overrides."""
        for _component_config in self.service_config.overrides:
            (
                component_config,
                component_id,
                has_multiple_overrides,
            ) = Service.process_metadata(configuration=_component_config.copy())
            if component_id.component_type == ComponentType.SKILL:
                logging.info(f"Verifying overrides for {component_id}")
                if has_multiple_overrides:
                    _ = list(map(self.check_skill_override, component_config.values()))
                else:
                    self.check_skill_override(override=component_config)
