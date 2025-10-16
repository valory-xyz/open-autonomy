# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022-2025 Valory AG
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

"""On-chain tools configurations."""

import os
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional, cast

from autonomy.chain.constants import (
    CHAIN_ID_TO_CHAIN_NAME,
    CHAIN_NAME_TO_CHAIN_ID,
    CHAIN_PROFILES,
)


DEFAULT_LOCAL_RPC = "http://127.0.0.1:8545"
DEFAULT_LOCAL_CHAIN_ID = 31337
CUSTOM_CHAIN_RPC = "CUSTOM_CHAIN_RPC"
ETHEREUM_CHAIN_RPC = "ETHEREUM_CHAIN_RPC"


def _get_chain_id_for_custom_chain() -> Optional[int]:
    """Get chain if for custom chain from environment"""
    chain_id = os.environ.get("CUSTOM_CHAIN_ID")
    if chain_id is None:
        return None
    return int(chain_id)


class LedgerType(str, Enum):
    """Ledger type enum."""

    ETHEREUM = "ethereum"
    SOLANA = "solana"

    @property
    def config_file(self) -> str:
        """Config filename."""
        return f"{self.name.lower()}.json"

    @property
    def key_file(self) -> str:
        """Key filename."""
        return f"{self.name.lower()}.txt"

    @classmethod
    def from_id(cls, chain_id: int) -> "LedgerType":
        """Load from chain ID."""
        return Chain.from_id(chain_id).ledger_type


class ChainType(Enum):
    """Chain types."""

    LOCAL = "local"
    CUSTOM = "custom_chain"
    ETHEREUM = "ethereum"
    POLYGON = "polygon"
    GNOSIS = "gnosis"
    ARBITRUM_ONE = "arbitrum_one"
    OPTIMISM = "optimism"
    BASE = "base"
    CELO = "celo"
    MODE = "mode"
    SOLANA = "solana"

    @property
    def id(self) -> Optional[int]:
        """Chain ID"""
        if self == ChainType.CUSTOM:
            return _get_chain_id_for_custom_chain()
        try:
            return CHAIN_NAME_TO_CHAIN_ID[self.value]
        except KeyError as e:
            raise ValueError(f"{self.name} does not support a chain ID") from e

    @property
    def rpc(self) -> Optional[str]:
        """RPC String"""
        if self == ChainType.LOCAL:
            return DEFAULT_LOCAL_RPC
        return os.environ.get(self.rpc_env_name)

    @property
    def rpc_env_name(self) -> str:
        """RPC Environment variable name"""
        if self == ChainType.CUSTOM:
            return f"{self.value}_rpc".upper()
        return f"{self.value}_chain_rpc".upper()

    @property
    def ledger_type(self) -> LedgerType:
        """Ledger type."""
        if self in (Chain.SOLANA,):
            return LedgerType.SOLANA
        return LedgerType.ETHEREUM

    @classmethod
    def from_string(cls, chain: str) -> "Chain":
        """Load from string."""
        return Chain(chain.lower())

    @classmethod
    def from_id(cls, chain_id: int) -> "Chain":
        """Load from chain ID."""
        try:
            return Chain(CHAIN_ID_TO_CHAIN_NAME[chain_id])
        except KeyError as e:
            raise ValueError(f"Chain ID not found: {chain_id}") from e


Chain = ChainType


@dataclass
class ContractConfig:
    """Contract config class."""

    name: str
    contracts: Dict[ChainType, str]


@dataclass
class ChainConfig:
    """Chain config"""

    chain_type: ChainType
    rpc: Optional[str]
    chain_id: Optional[int]


class ChainConfigs:  # pylint: disable=too-few-public-methods
    """Name space for chain configs."""

    local = ChainConfig(
        chain_type=ChainType.LOCAL,
        rpc=DEFAULT_LOCAL_RPC,
        chain_id=DEFAULT_LOCAL_CHAIN_ID,
    )

    @classmethod
    def get(cls, chain_type: ChainType) -> ChainConfig:
        """Return chain config for given chain type."""
        return ChainConfig(
            chain_type=chain_type,
            rpc=chain_type.rpc,
            chain_id=chain_type.id,
        )

    @classmethod
    def get_rpc_env_var(cls, chain_type: ChainType) -> Optional[str]:
        """Return chain config for given chain type."""
        return chain_type.rpc_env_name


class ContractConfigs:  # pylint: disable=too-few-public-methods
    """A namespace for contract configs."""

    component_registry = ContractConfig(
        name="component_registry",
        contracts={
            ChainType(chain_name): cast(str, container.get("component_registry"))
            for chain_name, container in CHAIN_PROFILES.items()
        },
    )

    agent_registry = ContractConfig(
        name="agent_registry",
        contracts={
            ChainType(chain_name): cast(str, container.get("agent_registry"))
            for chain_name, container in CHAIN_PROFILES.items()
        },
    )

    service_registry = ContractConfig(
        name="service_registry",
        contracts={
            ChainType(chain_name): cast(str, container.get("service_registry"))
            for chain_name, container in CHAIN_PROFILES.items()
        },
    )

    service_manager = ContractConfig(
        name="service_manager",
        contracts={
            ChainType(chain_name): cast(
                str,
                container.get(
                    "service_manager", container.get("service_manager_token")
                ),
            )
            for chain_name, container in CHAIN_PROFILES.items()
        },
    )

    registries_manager = ContractConfig(
        name="registries_manager",
        contracts={
            ChainType(chain_name): cast(str, container.get("registries_manager"))
            for chain_name, container in CHAIN_PROFILES.items()
        },
    )

    gnosis_safe_proxy_factory = ContractConfig(
        name="gnosis_safe_proxy_factory",
        contracts={
            ChainType(chain_name): cast(str, container.get("gnosis_safe_proxy_factory"))
            for chain_name, container in CHAIN_PROFILES.items()
        },
    )

    gnosis_safe_same_address_multisig = ContractConfig(
        name="gnosis_safe_same_address_multisig",
        contracts={
            ChainType(chain_name): cast(
                str, container.get("gnosis_safe_same_address_multisig")
            )
            for chain_name, container in CHAIN_PROFILES.items()
        },
    )

    safe_multisig_with_recovery_module = ContractConfig(
        name="safe_multisig_with_recovery_module",
        contracts={
            ChainType(chain_name): cast(
                str, container.get("safe_multisig_with_recovery_module")
            )
            for chain_name, container in CHAIN_PROFILES.items()
        },
    )

    recovery_module = ContractConfig(
        name="recovery_module",
        contracts={
            ChainType(chain_name): cast(str, container.get("recovery_module"))
            for chain_name, container in CHAIN_PROFILES.items()
        },
    )

    service_registry_token_utility = ContractConfig(
        name="service_registry_token_utility",
        contracts={
            ChainType(chain_name): cast(
                str, container.get("service_registry_token_utility")
            )
            for chain_name, container in CHAIN_PROFILES.items()
        },
    )

    multisend = ContractConfig(
        name="multisend",
        contracts={
            ChainType(chain_name): cast(str, container.get("multisend"))
            for chain_name, container in CHAIN_PROFILES.items()
        },
    )

    erc20 = ContractConfig(
        name="erc20",
        contracts={},
    )

    @classmethod
    def get(cls, name: str) -> ContractConfig:
        """Return chain config for given chain type."""
        return cast(ContractConfig, getattr(cls, name))
