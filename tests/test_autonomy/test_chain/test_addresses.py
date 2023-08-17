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


CHAIN_ADDRESSES_URLS = {
    ChainType.ETHEREUM: "https://raw.githubusercontent.com/valory-xyz/autonolas-registries/main/docs/mainnet_addresses/ethereum.json",
    ChainType.GOERLI: "https://raw.githubusercontent.com/valory-xyz/autonolas-registries/main/scripts/deployment/globals_goerli.json",
}


def load_addresses_file(url: str) -> t.Optional[t.Dict[str, str]]:
    """Load addresses file."""
    try:
        return requests.get(url=url).json()
    except Exception:
        return None


def camel_to_snake_case(string: str) -> str:
    """Convert camelCase to snake_case."""
    _string = ""
    for char in string:
        if char.islower():
            _string += char
        else:
            _string += "_"
            _string += char.lower()
    return _string


@pytest.mark.parametrize(
    argnames="chain",
    argvalues=(
        ChainType.ETHEREUM,
        ChainType.GOERLI,
    ),
)
def test_addresses_match(chain: ChainType) -> None:
    """Test addresses match with the remote file."""
    l1_chain = chain in (
        ChainType.ETHEREUM,
        ChainType.GOERLI,
    )
    url = CHAIN_ADDRESSES_URLS[chain]
    addresses = load_addresses_file(url=url)
    assert (
        addresses is not None
    ), f"Failed fetching the addresses file for chain {chain}"
    for name, address in addresses.items():
        if name == "serviceManagerAddress" and l1_chain:
            continue
        if name == "serviceManagerTokenAddress" and l1_chain:
            constant = (
                camel_to_snake_case(name.replace("Token", "")).upper()
                + "_"
                + chain.value.upper()
            )
        else:
            constant = camel_to_snake_case(name).upper() + "_" + chain.value.upper()
        constant_address = getattr(constants, constant, None)
        if constant_address is None:
            continue
        assert (
            address == constant_address
        ), f"Constant value and remote value does not match for `{constant}`"
