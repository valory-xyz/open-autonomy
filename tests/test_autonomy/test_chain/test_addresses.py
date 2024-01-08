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

"""Verify the on-chain addresses against the defined constants."""

import typing as t

import pytest
import requests

from autonomy.chain.config import ChainType
from autonomy.chain.constants import (
    ContractAddresses,
    EthereumAddresses,
    GoerliAddresses,
)


ADDRESS_FILE_URL = "https://raw.githubusercontent.com/valory-xyz/autonolas-registries/main/docs/configuration.json"
CHAIN_SLUGS = {ChainType.ETHEREUM: "mainnet", ChainType.GOERLI: "goerli"}
ADDRESSES_TO_CHECK = {
    "ComponentRegistry": "component_registry",
    "AgentRegistry": "agent_registry",
    "RegistriesManager": "registries_manager",
    "ServiceRegistry": "service_registry",
    "ServiceRegistryTokenUtility": "service_registry_token_utility",
    "ServiceManagerToken": "service_manager",
    "GnosisSafeMultisig": "gnosis_safe_proxy_factory",
    "GnosisSafeSameAddressMultisig": "gnosis_safe_same_address_multisig",  # noqa: E800
}


class TestAddresses:
    """Test addesses."""

    contracts: t.Dict[str, t.List[t.Dict[str, str]]]

    @classmethod
    def setup_class(cls) -> None:
        """Setup test class."""
        chain_configs = requests.get(url=ADDRESS_FILE_URL).json()
        cls.contracts = {
            config["name"]: config["contracts"] for config in chain_configs
        }

    @pytest.mark.parametrize(
        argnames="chain,addresses",
        argvalues=(
            (ChainType.ETHEREUM, EthereumAddresses),
            (ChainType.GOERLI, GoerliAddresses),
        ),
    )
    def test_addresses_match(
        self, chain: ChainType, addresses: ContractAddresses
    ) -> None:
        """Test addresses match with the remote file."""
        contracts = self.contracts[CHAIN_SLUGS[chain]]
        for contract in contracts:
            name = contract["name"]
            if name not in ADDRESSES_TO_CHECK:
                continue
            address = contract["address"]
            constant_address = addresses.get(name=ADDRESSES_TO_CHECK[name])
            assert (
                address == constant_address
            ), f"Constant value and remote value does not match for `{name}`"
