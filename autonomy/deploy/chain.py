# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
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

"""Utils to support on-chain contract interactions."""


from typing import Dict, cast

import requests
import web3


SERVICE_REGISTRY_ABI = "https://abi-server.staging.autonolas.tech/autonolas-registries/ServiceRegistry.json"
CHAIN_CONFIG = {
    "staging": {
        "rpc": "https://chain.staging.autonolas.tech",
        "address": "0x0DCd1Bf9A1b36cE34237eEaFef220932846BCD82",
    },
    "mainnet": {
        "rpc": "https://eth-rpc.gateway.pokt.network",
        "address": "0x48b6af7B12C71f09e2fC8aF4855De4Ff54e775cA",
    },
    "testnet": {
        "rpc": "https://goerli.infura.io/v3/1622a5f5b56a4e1f9bd9292db7da93b8",
        "address": "0x1cEe30D08943EB58EFF84DD1AB44a6ee6FEff63a",
    },
}


def get_abi(url: str) -> Dict:
    """Get ABI from provided URL"""

    r = requests.get(url=url)
    return r.json().get("abi")


def resolve_token_id(token_id: int, chain_type: str = "staging") -> Dict:
    """Resolve token id using on-chain contracts."""

    w3 = web3.Web3(
        provider=web3.HTTPProvider(
            endpoint_uri=cast(str, CHAIN_CONFIG.get(chain_type).get("rpc"))
        ),
    )
    address = cast(str, CHAIN_CONFIG.get(chain_type).get("address"))
    service_contract = w3.eth.contract(
        address=address, abi=get_abi(SERVICE_REGISTRY_ABI)
    )
    url = service_contract.functions.tokenURI(token_id).call()
    return requests.get(url).json()
