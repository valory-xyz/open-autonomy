# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2026 Valory AG
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

"""Validate packaged ABIs against explorer-verified deployed contracts.

This is an opt-in integration test. Enable it with:

    RUN_CHAIN_ABI_VERIFICATION=1

Optional explorer configuration:

    ETHERSCAN_API_KEY=<key>
    ETHEREUM_BLOCKSCOUT_API_KEY=<key>

Optional explorer endpoint overrides:

    ETHEREUM_ETHERSCAN_API_URL=https://api.etherscan.io/v2/api
    ETHEREUM_BLOCKSCOUT_API_URL=https://eth.blockscout.com/api/v2/smart-contracts
"""

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

import pytest
import requests
import yaml

from autonomy.chain.config import ChainType
from autonomy.chain.constants import CHAIN_NAME_TO_CHAIN_ID, CHAIN_PROFILES

from packages.valory.contracts.service_manager.contract import (
    SERVICE_MANAGER_BUILD,
    SERVICE_MANAGER_TOKEN_COMPATIBLE_CHAINS,
)
from packages.valory.contracts.service_registry.contract import (
    L1_CHAINS,
    L2_BUILD_FILENAME,
)

from tests.conftest import ROOT_DIR

RUN_CHAIN_ABI_VERIFICATION_ENV = "RUN_CHAIN_ABI_VERIFICATION"
ETHERSCAN_API_KEY_ENV = "ETHERSCAN_API_KEY"
ETHEREUM_BLOCKSCOUT_API_KEY_ENV = "ETHEREUM_BLOCKSCOUT_API_KEY"
ETHEREUM_ETHERSCAN_API_URL_ENV = "ETHEREUM_ETHERSCAN_API_URL"
ETHEREUM_BLOCKSCOUT_API_URL_ENV = "ETHEREUM_BLOCKSCOUT_API_URL"

DEFAULT_ETHERSCAN_V2_API_URL = "https://api.etherscan.io/v2/api"
DEFAULT_ETHEREUM_BLOCKSCOUT_API_URL = (
    "https://eth.blockscout.com/api/v2/smart-contracts"
)

CONTRACTS_DIR = ROOT_DIR / "packages" / "valory" / "contracts"
SUPPORTED_CHAINS = (ChainType.ETHEREUM,)
DEFAULT_STATE_MUTABILITY_BY_TYPE = {
    "constructor": "nonpayable",
    "function": "nonpayable",
    "fallback": "nonpayable",
    "receive": "payable",
}
UNSUPPORTED_CONTRACT_CASES = {  # TODO: check with Jose
    (
        ChainType.ETHEREUM,
        "gnosis_safe_proxy_factory",
    ): "Ethereum deploys a GnosisSafeMultisig wrapper at this address, not the gnosis_safe_proxy_factory package ABI.",
}


@dataclass(frozen=True)
class ExplorerConfig:
    """Explorer request configuration."""

    name: str
    api_style: str
    default_api_url: str
    api_url_env_name: str
    api_key_env_name: Optional[str] = None
    api_key_header_name: Optional[str] = None


# Maps package directory names to their CHAIN_PROFILES keys when they differ.
PACKAGE_NAME_TO_PROFILE_KEY = {
    # The gnosis_safe package wraps GnosisSafeL2; the profile slot is named
    # gnosis_safe_same_address_multisig to reflect its deployment pattern.
    "gnosis_safe": "gnosis_safe_same_address_multisig",
}

# Hardcoded canonical addresses for contracts not tracked in CHAIN_PROFILES for
# the supported chains. Only add entries you are confident about
# chains (also the CHAIN_PROFILES default for custom_chain in autonomy/chain/constants.py).
SUPPLEMENTAL_CONTRACT_ADDRESSES: Dict[Tuple[ChainType, str], str] = {
    (
        ChainType.ETHEREUM,
        "agent_registry",
    ): "0x2F1f7D38e4772884b88f3eCd8B6b9faCdC319112",
    (
        ChainType.ETHEREUM,
        "component_registry",
    ): "0x15bd56669F57192a97dF41A2aa8f4403e9491776",
    (ChainType.ETHEREUM, "erc20"): "0x0001A500A6B18995B03f44bb040A5fFc28E45CB0",
    (ChainType.ETHEREUM, "gnosis_safe"): "0xd9Db270c1B5E3Bd161E8c8503c55cEABeE709552",
    (ChainType.ETHEREUM, "multicall2"): "0x5BA1e12693Dc8F9c48aAD8770482f4739bEeD696",
    (
        ChainType.ETHEREUM,
        "registries_manager",
    ): "0x9eC9156dEF5C613B2a7D4c46C383F9B58DfcD6fE",
    (
        ChainType.ETHEREUM,
        "service_manager",
    ): "0x4443ddD8EC67CbCf7E291ee3198f81dD0326b3A1",
    (
        ChainType.ETHEREUM,
        "service_registry",
    ): "0x48b6af7B12C71f09e2fC8aF4855De4Ff54e775cA",
    (ChainType.ETHEREUM, "multisend"): "0x40A2aCCbd92BCA938b02010E17A5b8929b49130D",
}

EXPLORER_CONFIGS = {
    ChainType.ETHEREUM: (
        ExplorerConfig(
            name="etherscan",
            api_style="etherscan",
            default_api_url=DEFAULT_ETHERSCAN_V2_API_URL,
            api_url_env_name=ETHEREUM_ETHERSCAN_API_URL_ENV,
            api_key_env_name=ETHERSCAN_API_KEY_ENV,
        ),
        ExplorerConfig(
            name="blockscout",
            api_style="blockscout_v2",
            default_api_url=DEFAULT_ETHEREUM_BLOCKSCOUT_API_URL,
            api_url_env_name=ETHEREUM_BLOCKSCOUT_API_URL_ENV,
            api_key_env_name=ETHEREUM_BLOCKSCOUT_API_KEY_ENV,
            api_key_header_name="x-api-key",
        ),
    ),
}


def _iter_supported_contracts() -> Iterable[Tuple[ChainType, str, str]]:
    """Yield chain, contract package name and deployed address test cases."""

    seen = set()

    for chain in SUPPORTED_CHAINS:
        for contract_name, address in CHAIN_PROFILES[chain.value].items():
            contract_dir = CONTRACTS_DIR / contract_name
            if not contract_dir.exists():
                continue
            seen.add((chain, contract_name))
            yield chain, contract_name, address

    # Contracts whose package directory name differs from the CHAIN_PROFILES key.
    for package_name, profile_key in PACKAGE_NAME_TO_PROFILE_KEY.items():
        if not (CONTRACTS_DIR / package_name).exists():
            continue
        for chain in SUPPORTED_CHAINS:
            _address = CHAIN_PROFILES[chain.value].get(profile_key)
            if _address is not None:
                seen.add((chain, package_name))
                yield chain, package_name, _address

    # Contracts with canonical addresses not tracked in CHAIN_PROFILES.
    # Supplementals are fallback-only: skip any contract already provided by
    # CHAIN_PROFILES (directly or through PACKAGE_NAME_TO_PROFILE_KEY).
    for (chain, contract_name), address in SUPPLEMENTAL_CONTRACT_ADDRESSES.items():
        if chain not in SUPPORTED_CHAINS:
            continue
        if (chain, contract_name) in seen:
            continue
        if not (CONTRACTS_DIR / contract_name).exists():
            continue
        yield chain, contract_name, address


def _build_json_path(contract_name: str, chain: ChainType) -> Path:
    """Resolve the local ABI JSON path for a contract on a given chain."""

    contract_dir = CONTRACTS_DIR / contract_name
    contract_config = yaml.safe_load((contract_dir / "contract.yaml").read_text())
    interface_paths = contract_config.get("contract_interface_paths", {})
    chain_id = CHAIN_NAME_TO_CHAIN_ID[chain.value]

    if contract_name == "service_registry" and chain_id not in L1_CHAINS:
        return contract_dir / "build" / L2_BUILD_FILENAME

    if contract_name == "service_manager":
        build_filename = (
            interface_paths["ethereum"].split("/")[-1]
            if chain_id in SERVICE_MANAGER_TOKEN_COMPATIBLE_CHAINS
            else SERVICE_MANAGER_BUILD
        )
        return contract_dir / "build" / build_filename

    build_path = interface_paths.get(chain.value) or interface_paths.get("ethereum")
    if build_path is None:
        raise KeyError(
            f"No contract interface path configured for {contract_name} on {chain.value}."
        )
    return contract_dir / build_path


def _load_local_abi(
    contract_name: str, chain: ChainType
) -> Sequence[Mapping[str, Any]]:
    """Load the local ABI for a contract package."""

    build_json = json.loads(
        _build_json_path(contract_name=contract_name, chain=chain).read_text(
            encoding="utf-8"
        )
    )
    abi = build_json.get("abi")
    if not isinstance(abi, list):
        raise TypeError(f"Unexpected ABI payload for {contract_name}: {type(abi)!r}")
    return abi


def _canonicalize_parameter(parameter: Mapping[str, Any]) -> Dict[str, Any]:
    """Normalize ABI parameter data for semantic comparison."""

    canonical: Dict[str, Any] = {"type": parameter["type"]}
    if "indexed" in parameter:
        canonical["indexed"] = bool(parameter["indexed"])
    if "components" in parameter:
        canonical["components"] = [
            _canonicalize_parameter(component)
            for component in parameter.get("components", [])
        ]
    return canonical


def _canonicalize_abi_entry(entry: Mapping[str, Any]) -> Dict[str, Any]:
    """Normalize an ABI item while keeping semantic details intact."""

    canonical: Dict[str, Any] = {"type": entry["type"]}
    for field_name in ("name", "anonymous"):
        if field_name in entry:
            canonical[field_name] = entry[field_name]
    state_mutability = entry.get("stateMutability")
    if state_mutability is None:
        state_mutability = DEFAULT_STATE_MUTABILITY_BY_TYPE.get(entry["type"])
    if state_mutability is not None:
        canonical["stateMutability"] = state_mutability
    for field_name in ("inputs", "outputs"):
        if field_name in entry:
            canonical[field_name] = [
                _canonicalize_parameter(parameter)
                for parameter in entry.get(field_name, [])
            ]
    return canonical


def _canonicalize_abi(abi: Sequence[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    """Return a deterministically sorted ABI representation."""

    canonical = [_canonicalize_abi_entry(entry) for entry in abi]
    return sorted(canonical, key=lambda item: json.dumps(item, sort_keys=True))


def _abi_from_etherscan_payload(
    payload: Mapping[str, Any], address: str
) -> Sequence[Mapping[str, Any]]:
    """Extract a verified ABI from an Etherscan-compatible response."""

    result = payload.get("result")
    if payload.get("status") != "1" or not isinstance(result, str):
        raise AssertionError(
            f"Explorer did not return a verified ABI for {address}: {payload}"
        )

    abi = json.loads(result)
    if not isinstance(abi, list):
        raise TypeError(f"Unexpected explorer ABI payload for {address}: {type(abi)!r}")
    return abi


def _abi_from_blockscout_payload(
    payload: Mapping[str, Any], address: str
) -> Sequence[Mapping[str, Any]]:
    """Extract a verified ABI from a Blockscout v2 response."""

    if payload.get("is_verified") is False:
        raise AssertionError(f"Contract {address} is not verified on the explorer.")

    abi = payload.get("abi")
    if isinstance(abi, str):
        abi = json.loads(abi)

    if not isinstance(abi, list):
        raise TypeError(f"Unexpected explorer ABI payload for {address}: {type(abi)!r}")
    return abi


def _maybe_resolve_blockscout_proxy(
    payload: Mapping[str, Any],
    api_url: str,
    headers: Mapping[str, str],
    timeout: int = 30,
) -> Mapping[str, Any]:
    """Resolve Blockscout proxy contracts to their first verified implementation."""

    implementations = payload.get("implementations") or []
    proxy_type = payload.get("proxy_type")
    if not proxy_type or not implementations:
        return payload

    implementation_address = implementations[0].get("address_hash")
    if implementation_address is None:
        raise AssertionError(
            f"Proxy contract did not expose an implementation address: {payload}"
        )

    response = requests.get(
        f"{api_url.rstrip('/')}/{implementation_address}",
        headers=headers,
        timeout=timeout,
    )
    response.raise_for_status()
    return response.json()


def _skip_if_unsupported_contract_case(chain: ChainType, contract_name: str) -> None:
    """Skip known chain/profile slots that do not map to a local package ABI."""

    reason = UNSUPPORTED_CONTRACT_CASES.get((chain, contract_name))
    if reason is not None:
        pytest.skip(reason)


def _fetch_abi_from_explorer(
    chain: ChainType, address: str, config: ExplorerConfig
) -> Sequence[Mapping[str, Any]]:
    """Fetch a verified ABI from a specific explorer configuration."""

    api_url = os.environ.get(config.api_url_env_name, config.default_api_url)

    if config.api_style == "etherscan":
        params = {
            "chainid": str(CHAIN_NAME_TO_CHAIN_ID[chain.value]),
            "module": "contract",
            "action": "getabi",
            "address": address,
        }
        if config.api_key_env_name is not None:
            api_key = os.environ.get(config.api_key_env_name)
            if api_key:
                params["apikey"] = api_key

        response = requests.get(
            api_url,
            params=params,
            timeout=30,
        )
        response.raise_for_status()
        return _abi_from_etherscan_payload(response.json(), address)

    if config.api_style == "blockscout_v2":
        headers = {}
        if (
            config.api_key_env_name is not None
            and config.api_key_header_name is not None
        ):
            api_key = os.environ.get(config.api_key_env_name)
            if api_key:
                headers[config.api_key_header_name] = api_key

        response = requests.get(
            f"{api_url.rstrip('/')}/{address}", headers=headers, timeout=30
        )
        response.raise_for_status()
        payload = _maybe_resolve_blockscout_proxy(
            payload=response.json(),
            api_url=api_url,
            headers=headers,
        )
        return _abi_from_blockscout_payload(payload, address)

    raise ValueError(f"Unsupported explorer API style: {config.api_style}")


def _fetch_explorer_abi(chain: ChainType, address: str) -> Sequence[Mapping[str, Any]]:
    """Fetch a verified ABI using Etherscan first and Blockscout as fallback."""

    errors = []
    for config in EXPLORER_CONFIGS[chain]:
        try:
            return _fetch_abi_from_explorer(chain=chain, address=address, config=config)
        except (
            AssertionError,
            json.JSONDecodeError,
            requests.RequestException,
            TypeError,
            ValueError,
        ) as exc:
            errors.append(f"{config.name}: {exc}")

    raise AssertionError(
        f"Unable to fetch a verified ABI for {address} on {chain.value}. "
        f"Attempts failed with: {'; '.join(errors)}"
    )


def _require_opt_in() -> None:
    """Skip unless the verification test suite is explicitly enabled."""

    if os.environ.get(RUN_CHAIN_ABI_VERIFICATION_ENV) != "1":
        pytest.skip(
            f"Set {RUN_CHAIN_ABI_VERIFICATION_ENV}=1 to run explorer ABI verification tests."
        )


def _local_abi_contains_explorer_abi(
    local_abi: List[Dict[str, Any]], explorer_abi: List[Dict[str, Any]]
) -> Tuple[bool, List[Dict[str, Any]]]:
    """Check if local ABI contains all entries from explorer ABI (as superset).

    The local ABI may have extra entries not in the explorer ABI, but all
    explorer entries must be present in the local ABI.

    :param local_abi: The canonicalized ABI loaded from local package artifacts.
    :param explorer_abi: The canonicalized ABI returned by the explorer.
    :return: A tuple ``(is_valid, missing_entries)`` where ``missing_entries``
        lists explorer entries not found in ``local_abi``.
    """
    missing = []
    for explorer_entry in explorer_abi:
        if explorer_entry not in local_abi:
            missing.append(explorer_entry)
    return len(missing) == 0, missing


@pytest.mark.integration
@pytest.mark.parametrize(
    argnames=("chain", "contract_name", "address"),
    argvalues=tuple(_iter_supported_contracts()),
    ids=lambda value: value.value if isinstance(value, ChainType) else str(value),
)
def test_packaged_abi_matches_verified_explorer_abi(
    chain: ChainType, contract_name: str, address: str
) -> None:
    """Assert that the packaged ABI matches the explorer-verified deployed ABI."""

    _require_opt_in()
    _skip_if_unsupported_contract_case(chain=chain, contract_name=contract_name)

    local_abi = _canonicalize_abi(
        _load_local_abi(contract_name=contract_name, chain=chain)
    )
    explorer_abi = _fetch_explorer_abi(chain=chain, address=address)
    canonicalized_explorer_abi = _canonicalize_abi(explorer_abi)

    is_valid, missing = _local_abi_contains_explorer_abi(
        local_abi, canonicalized_explorer_abi
    )
    assert (
        is_valid
    ), f"ABI mismatch for {contract_name} on {chain.value} at {address}. Explorer ABI: {json.dumps(explorer_abi, indent=2)}.\nMissing entries: {json.dumps(missing, indent=2)}"
