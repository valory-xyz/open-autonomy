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
from web3.exceptions import Web3Exception

from autonomy.chain.config import ChainType, ContractConfigs
from autonomy.chain.constants import CHAIN_PROFILES

from tests.utils.live_fetch import fetch_upstream_or_skip

ADDRESS_FILE_URL = "https://raw.githubusercontent.com/valory-xyz/autonolas-registries/refs/tags/v1.3.0/docs/configuration.json"


class TestAddresses:
    """Test addresses."""

    contracts: t.Dict[str, t.List[t.Dict[str, str]]]

    @classmethod
    def setup_class(cls) -> None:
        """Setup test class."""
        chain_configs = fetch_upstream_or_skip(ADDRESS_FILE_URL).json()
        cls.contracts = {
            _camel_case_to_snake_case(config["name"]): config["contracts"]
            for config in chain_configs
        }

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

        if chain == ChainType.ETHEREUM:
            contracts = self.contracts["mainnet"]
        else:
            contracts = self.contracts[chain.value]

        for contract in contracts:
            name = _camel_case_to_snake_case(contract["name"]).replace("_l2", "")
            if name in ("service_manager", "service_manager_token"):
                continue

            address = contract["address"]
            if name == "service_manager_proxy":
                monkeypatch.setenv(f"{chain.value.upper()}_CHAIN_RPC", chain.rpc)
                try:
                    constant_address = ContractConfigs.service_manager.contracts[chain]
                except (
                    requests.ConnectionError,
                    requests.Timeout,
                    requests.HTTPError,
                    Web3Exception,
                    ValueError,
                ) as exc:
                    # An RPC outage is not a test failure. A real drift would
                    # still surface once the RPC returns, because the constant
                    # lookup also happens at agent runtime. Web3Exception covers
                    # provider-level errors; ValueError covers JSON-RPC decode
                    # failures from the web3 transport layer.
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
