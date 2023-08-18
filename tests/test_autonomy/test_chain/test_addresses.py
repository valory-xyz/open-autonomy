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

from autonomy.chain import constants
from autonomy.chain.config import ChainType


ADDRESS_FILE_URL = "https://raw.githubusercontent.com/valory-xyz/autonolas-registries/main/docs/configuration.json"
CHAIN_SLUGS = {ChainType.ETHEREUM: "mainnet", ChainType.GOERLI: "goerli"}


def camel_to_snake_case(string: str) -> str:
    """Convert camelCase to snake_case."""
    _string = string[0].lower()
    for char in string[1:]:
        if char.islower():
            _string += char
        else:
            _string += "_"
            _string += char.lower()
    return _string


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
        argnames="chain",
        argvalues=(
            ChainType.ETHEREUM,
            ChainType.GOERLI,
        ),
    )
    def test_addresses_match(self, chain: ChainType) -> None:
        """Test addresses match with the remote file."""
        l1_chain = chain in (
            ChainType.ETHEREUM,
            ChainType.GOERLI,
        )
        contracts = self.contracts[CHAIN_SLUGS[chain]]
        for contract in contracts:
            name = contract["name"]
            address = contract["address"]
            if name == "serviceManagerAddress" and l1_chain:
                continue
            if name == "serviceManagerTokenAddress" and l1_chain:
                constant = (
                    camel_to_snake_case(name.replace("Token", ""))
                    + "_address_"
                    + chain.value
                ).upper()
            else:
                constant = (
                    camel_to_snake_case(name) + "_address_" + chain.value
                ).upper()
            constant_address = getattr(constants, constant, None)
            if constant_address is None:
                continue
            assert (
                address == constant_address
            ), f"Constant value and remote value does not match for `{constant}`"
