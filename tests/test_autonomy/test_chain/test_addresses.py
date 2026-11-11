# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2023-2026 Valory AG
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

"""Verify the on-chain addresses against the defined constants."""

import typing as t

import pytest
import requests
from aea.protocols.generator.common import _camel_case_to_snake_case
from web3.exceptions import (
    BadFunctionCallOutput,
    BadResponseFormat,
    ProviderConnectionError,
    TooManyRequests,
)

from autonomy.chain.config import ChainType, ContractConfigs
from autonomy.chain.constants import CHAIN_PROFILES

from tests.utils.live_fetch import fetch_upstream_or_skip

ADDRESS_FILE_URL = "https://raw.githubusercontent.com/valory-xyz/autonolas-registries/refs/tags/v1.3.4/docs/configuration.json"

UPSTREAM_CHAIN_NAMES = {
    ChainType.ETHEREUM: "mainnet",
    ChainType.ARBITRUM_ONE: "arbitrum",
}
UPSTREAM_TO_PROFILE_KEY = {
    "gnosis_safe_multisig": "gnosis_safe_proxy_factory",
    "identity_registry_bridger_proxy": "erc8004_identity_registry_bridger",
}
# Contracts Proposal 17 replaced. autonolas-registries#343 publishes the new ones in its deployment
# globals; its ``docs/configuration.json`` still lists the replaced ones.
REGISTRIES_DEPLOYMENT_URL = (
    "https://raw.githubusercontent.com/valory-xyz/autonolas-registries/"
    "5d5b1f1c366d25890126e7d534d9a61b8dc21ae8/scripts/deployment/"
)
REPLACED_CONTRACTS_GLOBALS_KEYS = {
    "gnosis_safe_multisig": "gnosisSafeMultisigImplementationAddress",
    "staking_token": "stakingTokenAddress",
}
DEPLOYMENT_GLOBALS_FILES = {
    ChainType.ETHEREUM: ("globals_mainnet.json", "l2/globals_eth_mainnet.json"),
    ChainType.POLYGON: ("l2/globals_polygon_mainnet.json",),
    ChainType.GNOSIS: ("l2/globals_gnosis_mainnet.json",),
    ChainType.ARBITRUM_ONE: ("l2/globals_arbitrum_mainnet.json",),
    ChainType.OPTIMISM: ("l2/globals_optimism_mainnet.json",),
    ChainType.BASE: ("l2/globals_base_mainnet.json",),
    ChainType.CELO: ("l2/globals_celo_mainnet.json",),
    ChainType.MODE: ("l2/globals_mode_mainnet.json",),
    ChainType.ROBINHOOD: ("l2/globals_robinhood_mainnet.json",),
}
UNTRACKED_CONTRACTS = (
    "service_manager",
    "service_manager_token",
    "identity_registry_bridger",
    "hash_checkpoint",
)

# Transport-level errors from the chain RPC call inside DynamicContract.
# Other web3 exceptions (e.g. InvalidAddress, ContractLogicError) are real
# bugs the test exists to catch — let those propagate.
_TRANSIENT_RPC_ERRORS = (
    requests.ConnectionError,
    requests.Timeout,
    requests.HTTPError,
    BadResponseFormat,
    BadFunctionCallOutput,
    ProviderConnectionError,
    TooManyRequests,
)


class TestAddresses:
    """Test addresses."""

    # Lazy class-level cache of the upstream configuration. Each
    # parametrized test calls ``_get_contracts``; the first call drives
    # the fetch and the rest reuse the result. Letting each test call
    # ``pytest.skip`` individually keeps every skipped case visible in
    # the pytest report — fetching from ``setup_class`` would make the
    # whole class silently vanish on a GitHub outage.
    _contracts: t.Optional[t.Dict[str, t.List[t.Dict[str, str]]]] = None
    # When the first fetch fails (``pytest.skip`` raised), record that
    # so subsequent parametrized calls short-circuit instead of paying
    # the ~31s retry budget again for each remaining chain.
    _fetch_failed: bool = False

    @classmethod
    def _get_contracts(cls) -> t.Dict[str, t.List[t.Dict[str, str]]]:
        """Fetch (or return cached) upstream contracts mapping.

        Calls ``pytest.skip`` inside the current test if the upstream is
        unreachable. The skip outcome is cached at class scope so a
        persistent outage costs one retry budget total, not one per
        parametrized variant.

        :return: the contracts dict keyed by chain name.
        """
        if cls._fetch_failed:
            pytest.skip(
                f"upstream {ADDRESS_FILE_URL} already failed earlier in this run"
            )
        if cls._contracts is None:
            try:
                chain_configs = fetch_upstream_or_skip(ADDRESS_FILE_URL).json()
            except pytest.skip.Exception:
                # The fetch helper raised ``Skipped`` after exhausting
                # retries. Record the outcome so subsequent parametrized
                # iterations skip immediately, then re-raise to skip
                # the current one.
                cls._fetch_failed = True
                raise
            cls._contracts = {
                _camel_case_to_snake_case(config["name"]): config["contracts"]
                for config in chain_configs
            }
        return cls._contracts

    _deployment_globals: t.Dict[ChainType, t.Dict[str, str]] = {}

    @classmethod
    def _get_deployment_globals(cls, chain: ChainType) -> t.Dict[str, str]:
        """Fetch (or return cached) the chain's registries deployment globals.

        Calls ``pytest.skip`` inside the current test if they are unreachable.

        :param chain: the chain whose globals to fetch.
        :return: the merged globals of the chain's files.
        """
        if chain not in cls._deployment_globals:
            merged: t.Dict[str, str] = {}
            for path in DEPLOYMENT_GLOBALS_FILES[chain]:
                merged.update(
                    fetch_upstream_or_skip(REGISTRIES_DEPLOYMENT_URL + path).json()
                )
            cls._deployment_globals[chain] = merged
        return cls._deployment_globals[chain]

    @pytest.mark.parametrize(argnames="chain", argvalues=list(ChainType))
    def test_addresses_match(
        self, chain: ChainType, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test addresses match with the remote file."""
        # TODO: re-enable ChainType.POLYGON once a reliable RPC is available
        if chain in (
            ChainType.LOCAL,
            ChainType.CUSTOM,
            ChainType.SOLANA,
            ChainType.POLYGON,
        ):
            return

        contracts_by_chain = self._get_contracts()
        contracts = contracts_by_chain[UPSTREAM_CHAIN_NAMES.get(chain, chain.value)]

        for contract in contracts:
            name = _camel_case_to_snake_case(contract["name"]).replace("_l2", "")
            if name in UNTRACKED_CONTRACTS:
                continue

            address = contract["address"]
            if name in REPLACED_CONTRACTS_GLOBALS_KEYS:
                address = self._get_deployment_globals(chain)[
                    REPLACED_CONTRACTS_GLOBALS_KEYS[name]
                ]
            if name == "service_manager_proxy":
                monkeypatch.setenv(f"{chain.value.upper()}_CHAIN_RPC", chain.rpc)
                try:
                    constant_address = ContractConfigs.service_manager.contracts[chain]
                except _TRANSIENT_RPC_ERRORS as exc:
                    # Transport-level RPC failure. A real drift would still
                    # surface once the RPC returns, because this same lookup
                    # happens at agent runtime.
                    pytest.skip(f"chain RPC unreachable for {chain.value}: {exc}")
            else:
                constant_address = CHAIN_PROFILES[chain.value][
                    UPSTREAM_TO_PROFILE_KEY.get(name, name)
                ]
            assert (
                address == constant_address
            ), f"Constant value and remote value does not match for `{name}`"
