#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022-2023 Valory AG
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

"""Script to generate a markdown package table."""

from pathlib import Path

import requests


DOC_FILE = "docs/advanced_reference/on_chain_addresses.md"
ADDRESS_FILE_URL = "https://raw.githubusercontent.com/valory-xyz/autonolas-registries/main/docs/configuration.json"
CONTRACT_TO_SLUG = {
    "ComponentRegistry": "COMPONENT_REGISTRY",
    "AgentRegistry": "AGENT_REGISTRY",
    "RegistriesManager": "REGISTRIES_MANAGER",
    "ServiceRegistry": "SERVICE_REGISTRY",
    "ServiceRegistryL2": "SERVICE_REGISTRY",
    "ServiceRegistryTokenUtility": "SERVICE_REGISTRY_TOKEN_UTILITY",
    "ServiceManagerToken": "SERVICE_MANAGER",
    "ServiceManager": "SERVICE_MANAGER",
    "GnosisSafeMultisig": "GNOSIS_SAFE_PROXY_FACTORY",
    "GnosisSafeSameAddressMultisig": "GNOSIS_SAFE_SAME_ADDRESS_MULTISIG",
}
BLOCKSCAN_URLS = {
    "polygon": "https://polygonscan.com/address/",
    "polygonMumbai": "https://mumbai.polygonscan.com/address/",
    "gnosis": "https://gnosisscan.io/address/",
    "chiado": "https://gnosis-chiado.blockscout.com/address/",
}


def to_title(string: str) -> str:
    """Convert camelCase to snake_case."""
    _string = string[0].upper()
    for char in string[1:]:
        if char.islower():
            _string += char
        else:
            _string += " "
            _string += char
    return _string


def main() -> None:
    """Generate contract addresses list."""
    data = "# List of contract addresses\n"
    chains = requests.get(ADDRESS_FILE_URL).json()
    for chain in chains:
        chain_name = chain["name"]
        chain_id = chain["chainId"]
        if chain_id in ("1", "5"):
            continue
        blockscan_url = BLOCKSCAN_URLS[chain_name]
        contracts = chain["contracts"]
        table = "| Name | Environment Variable | Address |\n"
        table += "| ---- | -------------------- | ------- |\n"
        for contract in contracts:
            name = contract["name"]
            if name not in CONTRACT_TO_SLUG:
                continue
            spaced_title = to_title(name)
            env_var = CONTRACT_TO_SLUG[name]
            address = contract["address"]
            table += f"| `{spaced_title}` | `CUSTOM_{env_var}_ADDRESS` | [`{address}`]({blockscan_url}{address}) |\n"

        # Multisend address is similar for all chains
        table += f"| `Multisend` | `CUSTOM_MULTISEND_ADDRESS` | [`0x40A2aCCbd92BCA938b02010E17A5b8929b49130D`]({blockscan_url}0x40A2aCCbd92BCA938b02010E17A5b8929b49130D) |\n"
        section = f"\n## {to_title(chain_name)} ({chain_id})\n"
        section += table
        data += section
    Path(DOC_FILE).write_text(data, encoding="utf-8")


# [`0xeB49bE5DF00F74bd240DE4535DDe6Bc89CEfb994`](https://gnosis-chiado.blockscout.com/address/0xeB49bE5DF00F74bd240DE4535DDe6Bc89CEfb994)

if __name__ == "__main__":
    main()
