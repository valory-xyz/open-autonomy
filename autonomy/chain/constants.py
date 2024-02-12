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

"""Chain constants"""

import os
from dataclasses import dataclass
from typing import cast

from aea.configurations.constants import CONTRACTS, PACKAGES
from aea.configurations.data_types import PublicId

from autonomy import AUTONOMY_DIR
from autonomy.constants import VALORY
from autonomy.data import DATA_DIR


CONTRACTS_DIR_FRAMEWORK = DATA_DIR / CONTRACTS
CONTRACTS_DIR_LOCAL = (
    AUTONOMY_DIR.parent / PACKAGES / VALORY / CONTRACTS
)  # use from an editable/local installation

ERC20_TOKEN_ADDRESS_LOCAL = "0x1291Be112d480055DaFd8a610b7d1e203891C274"  # nosec


@dataclass
class ContractAddresses:  # pylint: disable=too-many-instance-attributes
    """Contract addresses container for a chain."""

    component_registry: str
    agent_registry: str
    registries_manager: str
    service_registry: str
    service_registry_token_utility: str
    service_manager: str
    gnosis_safe_proxy_factory: str
    gnosis_safe_same_address_multisig: str
    multisend: str

    def get(self, name: str) -> str:
        """Returns the contract address."""
        return cast(str, getattr(self, name))


HardhatAddresses = ContractAddresses(  # nosec
    component_registry="0x5FbDB2315678afecb367f032d93F642f64180aa3",
    agent_registry="0xe7f1725E7734CE288F8367e1Bb143E90bb3F0512",
    registries_manager="0x9fE46736679d2D9a65F0992F2272dE9f3c7fa6e0",
    service_registry="0x998abeb3E57409262aE5b751f60747921B33613E",
    service_manager="0x4c5859f0F772848b2D91F1D83E2Fe57935348029",
    gnosis_safe_proxy_factory="0x0E801D84Fa97b50751Dbf25036d067dCf18858bF",
    gnosis_safe_same_address_multisig="0x8f86403A4DE0BB5791fa46B8e795C547942fE4Cf",
    service_registry_token_utility="0x36C02dA8a0983159322a80FFE9F24b1acfF8B570",
    multisend="0x9d4454B023096f34B160D6B654540c56A1F81688",
)

EthereumAddresses = ContractAddresses(  # nosec
    component_registry="0x15bd56669F57192a97dF41A2aa8f4403e9491776",
    agent_registry="0x2F1f7D38e4772884b88f3eCd8B6b9faCdC319112",
    registries_manager="0x9eC9156dEF5C613B2a7D4c46C383F9B58DfcD6fE",
    service_registry="0x48b6af7B12C71f09e2fC8aF4855De4Ff54e775cA",
    service_registry_token_utility="0x3Fb926116D454b95c669B6Bf2E7c3bad8d19affA",
    service_manager="0x2EA682121f815FBcF86EA3F3CaFdd5d67F2dB143",
    gnosis_safe_proxy_factory="0x46C0D07F55d4F9B5Eed2Fc9680B5953e5fd7b461",
    gnosis_safe_same_address_multisig="0xfa517d01DaA100cB1932FA4345F68874f7E7eF46",
    multisend="0x40A2aCCbd92BCA938b02010E17A5b8929b49130D",
)

GoerliAddresses = ContractAddresses(  # nosec
    component_registry="0x7Fd1F4b764fA41d19fe3f63C85d12bf64d2bbf68",
    agent_registry="0xEB5638eefE289691EcE01943f768EDBF96258a80",
    registries_manager="0x10c5525F77F13b28f42c5626240c001c2D57CAd4",
    service_registry="0x1cEe30D08943EB58EFF84DD1AB44a6ee6FEff63a",
    service_registry_token_utility="0x6d9b08701Af43D68D991c074A27E4d90Af7f2276",
    service_manager="0x1d333b46dB6e8FFd271b6C2D2B254868BD9A2dbd",
    gnosis_safe_proxy_factory="0x65dD51b02049ad1B6FF7fa9Ea3322E1D2CAb1176",
    gnosis_safe_same_address_multisig="0x06467Cb835da623384a22aa902647784C1c9f5Ae",
    multisend="0x40A2aCCbd92BCA938b02010E17A5b8929b49130D",
)

CustomAddresses = ContractAddresses(
    component_registry=cast(str, os.environ.get("CUSTOM_COMPONENT_REGISTRY_ADDRESS")),
    agent_registry=cast(str, os.environ.get("CUSTOM_AGENT_REGISTRY_ADDRESS")),
    registries_manager=cast(str, os.environ.get("CUSTOM_REGISTRIES_MANAGER_ADDRESS")),
    service_manager=cast(str, os.environ.get("CUSTOM_SERVICE_MANAGER_ADDRESS")),
    service_registry=cast(str, os.environ.get("CUSTOM_SERVICE_REGISTRY_ADDRESS")),
    gnosis_safe_proxy_factory=cast(
        str, os.environ.get("CUSTOM_GNOSIS_SAFE_PROXY_FACTORY_ADDRESS")
    ),
    gnosis_safe_same_address_multisig=cast(
        str, os.environ.get("CUSTOM_GNOSIS_SAFE_SAME_ADDRESS_MULTISIG_ADDRESS")
    ),
    service_registry_token_utility=cast(
        str, os.environ.get("CUSTOM_SERVICE_REGISTRY_TOKEN_UTILITY_ADDRESS")
    ),
    multisend=cast(
        str,
        os.environ.get(
            "CUSTOM_MULTISEND_ADDRESS", "0x40A2aCCbd92BCA938b02010E17A5b8929b49130D"
        ),
    ),
)


# Contract PublicIds
COMPONENT_REGISTRY_CONTRACT = PublicId.from_str("valory/component_registry")
AGENT_REGISTRY_CONTRACT = PublicId.from_str("valory/agent_registry")
REGISTRIES_MANAGER_CONTRACT = PublicId.from_str("valory/registries_manager")
SERVICE_MANAGER_CONTRACT = PublicId.from_str("valory/service_manager")
SERVICE_REGISTRY_CONTRACT = PublicId.from_str("valory/service_registry")
GNOSIS_SAFE_CONTRACT = PublicId.from_str("valory/gnosis_safe")
GNOSIS_SAFE_PROXY_FACTORY_CONTRACT = PublicId.from_str(
    "valory/gnosis_safe_proxy_factory"
)
GNOSIS_SAFE_SAME_ADDRESS_MULTISIG_CONTRACT = PublicId.from_str(
    "valory/gnosis_safe_same_address_multisig"
)
SERVICE_REGISTRY_TOKEN_UTILITY_CONTRACT = PublicId.from_str(
    "valory/service_registry_token_utility"
)
MULTISEND_CONTRACT = PublicId.from_str("valory/multisend")
ERC20_CONTRACT = PublicId.from_str("valory/erc20")

SERVICE_MANAGER_TOKEN_COMPATIBLE_CHAINS = (
    1,
    5,
    31337,
    100,
    10200,
)
