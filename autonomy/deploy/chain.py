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


from typing import Dict

import requests
import web3


RPC_URL = "https://chain.staging.autonolas.tech"

SERVICE_REGISTRY_ABI = "https://abi-server.staging.autonolas.tech/autonolas-registries/ServiceRegistry.json"
SERVICE_ADDRESS = "0x0DCd1Bf9A1b36cE34237eEaFef220932846BCD82"


def get_abi(url: str) -> Dict:
    """Get ABI from provided URL"""

    r = requests.get(url=url)
    return r.json().get("abi")


class ServiceRegistry:  # pylint: disable=too-few-public-methods
    """Class to represent on-chain service registry."""

    abi_url = SERVICE_REGISTRY_ABI
    address = SERVICE_ADDRESS

    @classmethod
    def resolve(cls, w3: web3.Web3, token_id: int) -> Dict:
        """Resolve token ID."""

        service_contract = w3.eth.contract(
            address=cls.address, abi=get_abi(cls.abi_url)
        )
        url = service_contract.functions.tokenURI(token_id).call()
        return requests.get(url).json()


def resolve_token_id(token_id: int) -> Dict:
    """Resolve token id using on-chain contracts."""
    w3 = web3.Web3(
        provider=web3.HTTPProvider(endpoint_uri=RPC_URL),
    )
    return ServiceRegistry.resolve(w3, token_id)
