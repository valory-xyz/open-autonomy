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

ADDRESS_FILE_URL = "https://raw.githubusercontent.com/valory-xyz/autonolas-registries/refs/tags/v1.3.0/docs/configuration.json"

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

    # Class-level cache of the upstream configuration. ``None`` until the
    # first call to ``_get_contracts`` succeeds (lazy fetch). Storing the
    # result here lets each parametrized test call ``pytest.skip``
    # individually if the upstream is unreachable, which keeps every
    # skipped case visible in the pytest report — fetching from
    # ``setup_class`` would make the whole class silently vanish on a
    # GitHub outage.
    _contracts: t.Optional[t.Dict[str, t.List[t.Dict[str, str]]]] = None

    @classmethod
    def _get_contracts(cls) -> t.Dict[str, t.List[t.Dict[str, str]]]:
        """Fetch (or return cached) upstream contracts mapping.

        Calls ``pytest.skip`` inside the current test if the upstream is
        unreachable.

        :return: the contracts dict keyed by chain name.
        """
        if cls._contracts is None:
            chain_configs = fetch_upstream_or_skip(ADDRESS_FILE_URL).json()
            cls._contracts = {
                _camel_case_to_snake_case(config["name"]): config["contracts"]
                for config in chain_configs
            }
        return cls._contracts

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
        if chain == ChainType.ETHEREUM:
            contracts = contracts_by_chain["mainnet"]
        else:
            contracts = contracts_by_chain[chain.value]

        for contract in contracts:
            name = _camel_case_to_snake_case(contract["name"]).replace("_l2", "")
            if name in ("service_manager", "service_manager_token"):
                continue

            address = contract["address"]
            if name == "service_manager_proxy":
                monkeypatch.setenv(f"{chain.value.upper()}_CHAIN_RPC", chain.rpc)
                try:
                    constant_address = ContractConfigs.service_manager.contracts[chain]
                except _TRANSIENT_RPC_ERRORS as exc:
                    # Transport-level RPC failure. A real drift would still
                    # surface once the RPC returns, because this same lookup
                    # happens at agent runtime.
                    pytest.skip(f"chain RPC unreachable for {chain.value}: {exc}")
            elif name == "gnosis_safe_multisig":
                constant_address = CHAIN_PROFILES[chain.value][
                    "gnosis_safe_proxy_factory"
                ]
            else:
                constant_address = CHAIN_PROFILES[chain.value][name]
            assert (
                address == constant_address
            ), f"Constant value and remote value does not match for `{name}`"
