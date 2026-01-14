# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022-2026 Valory AG
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

import binascii
import os
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, Optional, Tuple, Type, cast

import click
from aea.configurations.data_types import PublicId
from aea.crypto.base import Crypto, LedgerApi
from aea.crypto.registries import crypto_registry, ledger_apis_registry

from autonomy.chain.base import RegistryContracts
from autonomy.chain.constants import (
    CHAIN_ID_TO_CHAIN_NAME,
    CHAIN_ID_TO_DEFAULT_PUBLIC_RPC,
    CHAIN_NAME_TO_CHAIN_ID,
    CHAIN_PROFILES,
    SERVICE_REGISTRY_CONTRACT,
)


try:
    from aea_ledger_ethereum.ethereum import (  # pylint: disable=ungrouped-imports
        EthereumApi,
        EthereumCrypto,
    )

    ETHEREUM_PLUGIN_INSTALLED = True
except ImportError:  # pragma: nocover
    ETHEREUM_PLUGIN_INSTALLED = False


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
        return os.getenv(
            key=self.rpc_env_name,
            default=CHAIN_ID_TO_DEFAULT_PUBLIC_RPC.get(self.id) if self.id else None,
        )

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


POA_CHAINS = frozenset((ChainType.OPTIMISM, ChainType.POLYGON))


@dataclass
class ContractConfig:
    """Contract config class."""

    name: str
    contracts: Dict[ChainType, str]


class OnChainHelper:  # pylint: disable=too-few-public-methods
    """On-chain interaction helper."""

    def __init__(
        self,
        chain_type: ChainType,
        key: Optional[Path] = None,
        password: Optional[str] = None,
        hwi: bool = False,
        timeout: Optional[float] = None,
        retries: Optional[int] = None,
        sleep: Optional[float] = None,
        dry_run: bool = False,
    ) -> None:
        """Initialize object."""
        self.chain_type = chain_type
        self.ledger_api, self.crypto = self.get_ledger_and_crypto_objects(
            chain_type=chain_type,
            key=key,
            password=password,
            hwi=hwi,
        )
        self.timeout = timeout
        self.retries = retries
        self.sleep = sleep
        self.dry_run = dry_run

    @staticmethod
    def load_hwi_plugin() -> Type[LedgerApi]:  # pragma: nocover
        """Load HWI Plugin."""
        try:
            from aea_ledger_ethereum_hwi.hwi import (  # pylint: disable=import-outside-toplevel
                EthereumHWIApi,
            )

            return EthereumHWIApi
        except ImportError as e:
            raise click.ClickException(
                "Hardware wallet plugin not installed, "
                "Run `pip3 install open-aea-ledger-ethereum-hwi` to install the plugin"
            ) from e
        except TypeError as e:
            raise click.ClickException(
                'Protobuf compatibility error; Please export PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION="python" '
                "to use the hardware wallet without any issues"
            ) from e

    @staticmethod
    def load_crypto(
        file: Path,
        password: Optional[str] = None,
    ) -> Crypto:
        """Load crypto object."""
        if file is None:
            raise click.ClickException(
                "Please provide key path using `--key` or use `--hwi` if you want to use a hardware wallet"
            )

        try:
            return EthereumCrypto(
                private_key_path=file,
                password=password,
            )
        except (binascii.Error, ValueError) as e:
            raise click.ClickException(
                "Cannot load private key for following possible reasons\n"
                "- Wrong key format\n"
                "- Wrong key length\n"
                "- Trailing spaces or new line characters"
            ) from e

    @classmethod
    def get_ledger_and_crypto_objects(
        cls,
        chain_type: ChainType,
        key: Optional[Path] = None,
        password: Optional[str] = None,
        hwi: bool = False,
    ) -> Tuple[LedgerApi, Crypto]:
        """Create ledger_api and crypto objects"""
        chain_config = ChainConfigs.get(chain_type=chain_type)
        identifier = EthereumApi.identifier

        if chain_config.rpc is None:
            raise click.ClickException(
                f"RPC URL cannot be `None`, "
                f"Please set the environment variable for {chain_type.value} chain "
                f"using `{ChainConfigs.get_rpc_env_var(chain_type)}` environment variable"
            )

        if hwi:
            EthereumHWIApi = cls.load_hwi_plugin()
            identifier = EthereumHWIApi.identifier

        if not hwi and not ETHEREUM_PLUGIN_INSTALLED:  # pragma: nocover
            raise click.ClickException(
                "Ethereum ledger plugin not installed, "
                "Run `pip3 install open-aea-ledger-ethereum` to install the plugin"
            )

        if key is None:
            crypto = crypto_registry.make(identifier)
        else:
            crypto = cls.load_crypto(
                file=key,
                password=password,
            )

        ledger_api = ledger_apis_registry.make(
            identifier,
            **{
                "address": chain_config.rpc,
                "chain_id": chain_config.chain_id,
                "is_gas_estimation_enabled": True,
                "poa_chain": chain_type in POA_CHAINS,
            },
        )

        if hwi:
            # Setting the `LedgerApi.identifier` to `ethereum` for both ledger and
            # hardware plugin to interact with the contract. If we use `ethereum_hwi`
            # as the ledger identifier the contracts will need ABI configuration for
            # the `ethereum_hwi` identifier which means we will have to define hardware
            # wallet as the dependency for contract but the hardware wallet plugin
            # is meant to be used for CLI tools only so we set the identifier to
            # `ethereum` for both ledger and hardware wallet plugin
            ledger_api.identifier = EthereumApi.identifier

        try:
            ledger_api.api.eth.default_account = crypto.address
        except Exception as e:  # pragma: nocover
            raise click.ClickException(str(e))

        return ledger_api, crypto

    def check_required_environment_variables(
        self, configs: Tuple[ContractConfig, ...]
    ) -> None:
        """Check for required enviroment variables when working with the custom chain."""
        if self.chain_type != ChainType.CUSTOM:
            return
        missing = []
        for config in configs:
            if isinstance(config.contracts, DynamicContract):
                continue

            if config.contracts[self.chain_type] is None:
                missing.append(config)

        if len(missing) == 0:
            return

        error = "Addresses for following contracts are None, please set them using their respective environment variables\n"
        for config in missing:
            error += f"- Set `{config.name}` address using `CUSTOM_{config.name.upper()}_ADDRESS`\n"
        raise click.ClickException(error[:-1])


class DynamicContract(Dict[ChainType, str]):
    """Contract mapping for addresses from on-chain deployments."""

    def __init__(self, source_contract_id: PublicId, getter_method: str) -> None:
        """Initialize the dynamic contract."""
        super().__init__()
        self.source_contract_id = source_contract_id
        self.getter_method = getter_method

    def __getitem__(self, chain: ChainType) -> str:
        """Get address for given chain."""
        if chain not in self:
            contract_config = ContractConfigs.get(self.source_contract_id.name)
            on_chain_helper = OnChainHelper(chain_type=chain)
            on_chain_helper.check_required_environment_variables((contract_config,))

            source_contract = RegistryContracts.get_contract(
                public_id=self.source_contract_id,
            )
            source_instance = source_contract.get_instance(
                ledger_api=on_chain_helper.ledger_api,
                contract_address=contract_config.contracts[chain],
            )
            self[chain] = getattr(
                source_instance.functions, self.getter_method
            )().call()

        return super().__getitem__(chain)


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
        rpc=ChainType.LOCAL.rpc,
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
        contracts=DynamicContract(
            source_contract_id=SERVICE_REGISTRY_CONTRACT,
            getter_method="manager",
        ),
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

    safe_multisig_with_recovery_module = ContractConfig(
        name="safe_multisig_with_recovery_module",
        contracts={
            ChainType(chain_name): cast(
                str, container.get("safe_multisig_with_recovery_module")
            )
            for chain_name, container in CHAIN_PROFILES.items()
        },
    )

    poly_safe_creator_with_recovery_module = ContractConfig(
        name="poly_safe_creator_with_recovery_module",
        contracts={
            ChainType(chain_name): cast(
                str, container.get("poly_safe_creator_with_recovery_module")
            )
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
