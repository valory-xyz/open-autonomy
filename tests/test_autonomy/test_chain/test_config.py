# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2023-2025 Valory AG
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

"""Test the chain configuration."""

from typing import Iterable

import pytest
from aea_test_autonomy.fixture_helpers import registries_scope_class  # noqa: F401

from autonomy.chain import config as chain_config
from autonomy.chain.constants import (
    CHAIN_ID_TO_CHAIN_NAME,
    CHAIN_ID_TO_DEFAULT_PUBLIC_RPC,
    CHAIN_PROFILES,
    SERVICE_MANAGER_CONTRACT,
)

from tests.conftest import skip_docker_tests


DEFAULT_LOCAL_RPC = "http://127.0.0.1:8545"
SERVICE_MANAGER_PROXY = "0x4c5859f0F772848b2D91F1D83E2Fe57935348029"  # nosec


def _all_profile_chain_types() -> Iterable[chain_config.ChainType]:
    """Helper to yield ChainType for every CHAIN_PROFILES key."""
    for name in CHAIN_PROFILES.keys():
        yield chain_config.ChainType(name)


def test_ledger_type_files() -> None:
    """`LedgerType` file naming helpers produce expected filenames."""

    assert chain_config.LedgerType.ETHEREUM.config_file == "ethereum.json"
    assert chain_config.LedgerType.ETHEREUM.key_file == "ethereum.txt"

    assert chain_config.LedgerType.SOLANA.config_file == "solana.json"
    assert chain_config.LedgerType.SOLANA.key_file == "solana.txt"


def test_ledger_type_from_id() -> None:
    """LedgerType.from_id maps EVM chain IDs to ETHEREUM ledger type."""

    assert (
        chain_config.LedgerType.from_id(1) == chain_config.LedgerType.ETHEREUM
    )  # ethereum mainnet
    assert (
        chain_config.LedgerType.from_id(31337) == chain_config.LedgerType.ETHEREUM
    )  # local/hardhat


def test_chain_type_id_known_and_unknown() -> None:
    """ChainType.id returns IDs for known chains and errors for unsupported ones."""

    assert chain_config.ChainType.LOCAL.id == 31337
    assert chain_config.ChainType.ETHEREUM.id == 1
    assert chain_config.ChainType.CELO.id == 42220

    with pytest.raises(ValueError, match="does not support a chain ID"):
        # SOLANA has no numeric EVM chain id in our mapping and should error
        _ = chain_config.ChainType.SOLANA.id


def test_chain_type_rpc_and_env_names(monkeypatch: pytest.MonkeyPatch) -> None:
    """`ChainType` RPC and environment variable names behave as expected."""

    # Local RPC is fixed
    assert chain_config.ChainType.LOCAL.rpc == DEFAULT_LOCAL_RPC
    assert chain_config.ChainType.LOCAL.rpc_env_name == "LOCAL_CHAIN_RPC"

    # Other chains resolve from environment when set
    monkeypatch.setenv("ETHEREUM_CHAIN_RPC", "https://eth.example")
    assert chain_config.ChainType.ETHEREUM.rpc_env_name == "ETHEREUM_CHAIN_RPC"
    assert chain_config.ChainType.ETHEREUM.rpc == "https://eth.example"

    # When not set returns None
    monkeypatch.delenv("ETHEREUM_CHAIN_RPC", raising=False)
    assert chain_config.ChainType.ETHEREUM.rpc == CHAIN_ID_TO_DEFAULT_PUBLIC_RPC[1]

    # Custom uses CUSTOM_CHAIN_RPC
    monkeypatch.setenv("CUSTOM_CHAIN_RPC", "https://custom.example")
    assert chain_config.ChainType.CUSTOM.rpc_env_name == "CUSTOM_CHAIN_RPC"
    assert chain_config.ChainType.CUSTOM.rpc == "https://custom.example"


def test_custom_chain_id(monkeypatch: pytest.MonkeyPatch) -> None:
    """Custom chain id is read from CUSTOM_CHAIN_ID if present."""

    monkeypatch.delenv("CUSTOM_CHAIN_ID", raising=False)
    assert chain_config.ChainType.CUSTOM.id is None

    monkeypatch.setenv("CUSTOM_CHAIN_ID", "12345")
    assert chain_config.ChainType.CUSTOM.id == 12345


def test_chain_type_from_string_and_from_id() -> None:
    """from_string and from_id conversions work and error appropriately."""

    assert (
        chain_config.ChainType.from_string("Ethereum")
        == chain_config.ChainType.ETHEREUM
    )
    assert chain_config.ChainType.from_id(31337) == chain_config.ChainType.LOCAL

    with pytest.raises(ValueError, match="Chain ID not found: 999999"):
        chain_config.ChainType.from_id(999999)

    with pytest.raises(ValueError, match="not-a-chain"):
        # invalid string
        chain_config.ChainType.from_string("not-a-chain")


def test_chain_configs_local_and_get(monkeypatch: pytest.MonkeyPatch) -> None:
    """`ChainConfigs` provide expected defaults and env-driven values."""

    c = chain_config.ChainConfigs.local
    assert c.chain_type == chain_config.ChainType.LOCAL
    assert c.rpc == DEFAULT_LOCAL_RPC
    assert c.chain_id == chain_config.DEFAULT_LOCAL_CHAIN_ID

    # get() picks up environment for non-local chains
    monkeypatch.setenv("BASE_CHAIN_RPC", "https://base.example")
    c2 = chain_config.ChainConfigs.get(chain_config.ChainType.BASE)
    assert c2.chain_type == chain_config.ChainType.BASE
    assert c2.rpc == "https://base.example"
    assert c2.chain_id == 8453

    # get_rpc_env_var returns the env var name
    assert (
        chain_config.ChainConfigs.get_rpc_env_var(chain_config.ChainType.CUSTOM)
        == "CUSTOM_CHAIN_RPC"
    )
    assert (
        chain_config.ChainConfigs.get_rpc_env_var(chain_config.ChainType.ETHEREUM)
        == "ETHEREUM_CHAIN_RPC"
    )


def test_chain_type_ledger_types() -> None:
    """Ledger type resolution for chains works as expected."""

    assert (
        chain_config.ChainType.ETHEREUM.ledger_type == chain_config.LedgerType.ETHEREUM
    )
    assert chain_config.ChainType.SOLANA.ledger_type == chain_config.LedgerType.SOLANA


def test_contract_configs_keys_and_values_present() -> None:
    """`ContractConfigs` contain entries for all chains in CHAIN_PROFILES."""

    # For a representative subset, verify exact addresses for 'local'
    assert (
        chain_config.ContractConfigs.component_registry.contracts[
            chain_config.ChainType.LOCAL
        ]
        == CHAIN_PROFILES["local"]["component_registry"]
    )
    assert (
        chain_config.ContractConfigs.agent_registry.contracts[
            chain_config.ChainType.LOCAL
        ]
        == CHAIN_PROFILES["local"]["agent_registry"]
    )
    assert (
        chain_config.ContractConfigs.service_registry.contracts[
            chain_config.ChainType.LOCAL
        ]
        == CHAIN_PROFILES["local"]["service_registry"]
    )
    assert (
        chain_config.ContractConfigs.registries_manager.contracts[
            chain_config.ChainType.LOCAL
        ]
        == CHAIN_PROFILES["local"]["registries_manager"]
    )

    # Ensure every profile key is present as a ChainType key in each contract config mapping
    for cfg in [
        chain_config.ContractConfigs.component_registry,
        chain_config.ContractConfigs.agent_registry,
        chain_config.ContractConfigs.service_registry,
        chain_config.ContractConfigs.registries_manager,
        chain_config.ContractConfigs.gnosis_safe_proxy_factory,
        chain_config.ContractConfigs.gnosis_safe_same_address_multisig,
        chain_config.ContractConfigs.safe_multisig_with_recovery_module,
        chain_config.ContractConfigs.recovery_module,
        chain_config.ContractConfigs.service_registry_token_utility,
        chain_config.ContractConfigs.multisend,
    ]:
        keys = set(cfg.contracts.keys())
        expected = set(_all_profile_chain_types())
        assert expected.issubset(keys)


def test_chain_id_round_trip_known_networks() -> None:
    """Round-trip mapping between ID and name for known networks works."""

    for cid, name in CHAIN_ID_TO_CHAIN_NAME.items():
        ct = chain_config.ChainType.from_id(cid)
        assert ct.value == name


@skip_docker_tests
@pytest.mark.usefixtures("registries_scope_class")
def test_dynamic_contract_addresses() -> None:
    """Dynamic contract address resolution works as expected."""

    service_manager_config = chain_config.ContractConfigs.get(
        SERVICE_MANAGER_CONTRACT.name
    )
    assert (
        service_manager_config.contracts[chain_config.ChainType.LOCAL]
        == SERVICE_MANAGER_PROXY
    )
