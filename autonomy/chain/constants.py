# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022-2024 Valory AG
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
DEFAULT_MULTISEND = "0x40A2aCCbd92BCA938b02010E17A5b8929b49130D"
CHAIN_PROFILES = {
    "local": {
        "component_registry": "0x5FbDB2315678afecb367f032d93F642f64180aa3",
        "agent_registry": "0xe7f1725E7734CE288F8367e1Bb143E90bb3F0512",
        "registries_manager": "0x9fE46736679d2D9a65F0992F2272dE9f3c7fa6e0",
        "service_registry": "0x998abeb3E57409262aE5b751f60747921B33613E",
        "service_manager": "0x4c5859f0F772848b2D91F1D83E2Fe57935348029",
        "gnosis_safe_proxy_factory": "0x0E801D84Fa97b50751Dbf25036d067dCf18858bF",
        "gnosis_safe_same_address_multisig": "0x8f86403A4DE0BB5791fa46B8e795C547942fE4Cf",
        "service_registry_token_utility": "0x36C02dA8a0983159322a80FFE9F24b1acfF8B570",
        "multisend": "0x9d4454B023096f34B160D6B654540c56A1F81688",
    },
    "ethereum": {
        "component_registry": "0x15bd56669F57192a97dF41A2aa8f4403e9491776",
        "agent_registry": "0x2F1f7D38e4772884b88f3eCd8B6b9faCdC319112",
        "registries_manager": "0x9eC9156dEF5C613B2a7D4c46C383F9B58DfcD6fE",
        "service_registry": "0x48b6af7B12C71f09e2fC8aF4855De4Ff54e775cA",
        "service_registry_token_utility": "0x3Fb926116D454b95c669B6Bf2E7c3bad8d19affA",
        "service_manager_token": "0x2EA682121f815FBcF86EA3F3CaFdd5d67F2dB143",
        "operator_whitelist": "0x42042799B0DE38AdD2a70dc996f69f98E1a85260",
        "gnosis_safe_proxy_factory": "0x46C0D07F55d4F9B5Eed2Fc9680B5953e5fd7b461",
        "gnosis_safe_same_address_multisig": "0xfa517d01DaA100cB1932FA4345F68874f7E7eF46",
        "staking_token": "0x0Dc23eEf3bC64CF3cbd8f9329B57AE4C4f28d5d2",
        "staking_verifier": "0x4503b79d468e81Ad2d4bd6Db991810da269bA777",
        "staking_factory": "0xEBdde456EA288b49f7D5975E7659bA1Ccf607efc",
    },
    "goerli": {
        "component_registry": "0x7Fd1F4b764fA41d19fe3f63C85d12bf64d2bbf68",
        "agent_registry": "0xEB5638eefE289691EcE01943f768EDBF96258a80",
        "registries_manager": "0x10c5525F77F13b28f42c5626240c001c2D57CAd4",
        "service_registry": "0x1cEe30D08943EB58EFF84DD1AB44a6ee6FEff63a",
        "service_registry_token_utility": "0x6d9b08701Af43D68D991c074A27E4d90Af7f2276",
        "service_manager_token": "0x1d333b46dB6e8FFd271b6C2D2B254868BD9A2dbd",
        "gnosis_safe_proxy_factory": "0x65dD51b02049ad1B6FF7fa9Ea3322E1D2CAb1176",
        "gnosis_safe_same_address_multisig": "0x06467Cb835da623384a22aa902647784C1c9f5Ae",
        "operator_whitelist": "0x0338893fB1A1D9Df03F72CC53D8f786487d3D03E",
    },
    "polygon": {
        "service_registry": "0xE3607b00E75f6405248323A9417ff6b39B244b50",
        "service_manager": "0x3C1fF68f5aa342D296d4DEe4Bb1cACCA912D95fE",
        "service_registry_token_utility": "0xa45E64d13A30a51b91ae0eb182e88a40e9b18eD8",
        "service_manager_token": "0x04b0007b2aFb398015B76e5f22993a1fddF83644",
        "gnosis_safe_proxy_factory": "0x3d77596beb0f130a4415df3D2D8232B3d3D31e44",
        "gnosis_safe_same_address_multisig": "0xd8BCC126ff31d2582018715d5291A508530587b0",
        "operator_whitelist": "0x526E064cB694E8f5B7DB299158e17F33055B3943",
        "staking_token": "0x4aba1Cf7a39a51D75cBa789f5f21cf4882162519",
        "staking_verifier": "0x8Bc0a5c5B1612A16983B01ecd7ae130E728390CB",
        "staking_factory": "0x46C0D07F55d4F9B5Eed2Fc9680B5953e5fd7b461",
    },
    "polygon_mumbai": {
        "service_registry": "0xf805DfF246CC208CD2F08ffaD242b7C32bc93623",
        "service_manager": "0x43d28764bB39936185c84906983fB57A8A905a4F",
        "service_registry_token_utility": "0x131b5551c81e9B3E89E9ACE30A5B3D45144E3e42",
        "service_manager_token": "0xE16adc7777B7C2a0d35033bd3504C028AB28EE8b",
        "gnosis_safe_proxy_factory": "0x9dEc6B62c197268242A768dc3b153AE7a2701396",
        "gnosis_safe_same_address_multisig": "0xd6AA4Ec948d84f6Db8EEf25104CeE0Ecd280C74e",
        "operator_whitelist": "0x118173028162C1b7c6Bf8488bd5dA2abd7c30F9D",
    },
    "gnosis": {
        "service_registry": "0x9338b5153AE39BB89f50468E608eD9d764B755fD",
        "service_registry_token_utility": "0xa45E64d13A30a51b91ae0eb182e88a40e9b18eD8",
        "service_manager_token": "0x04b0007b2aFb398015B76e5f22993a1fddF83644",
        "operator_whitelist": "0x526E064cB694E8f5B7DB299158e17F33055B3943",
        "gnosis_safe_proxy_factory": "0x3C1fF68f5aa342D296d4DEe4Bb1cACCA912D95fE",
        "gnosis_safe_same_address_multisig": "0x6e7f594f680f7aBad18b7a63de50F0FeE47dfD06",
        "staking_token": "0xEa00be6690a871827fAfD705440D20dd75e67AB1",
        "staking_verifier": "0x1D59DadE4FAeA7771eC7221420012d413175404C",
        "staking_factory": "0xb0228CA253A88Bc8eb4ca70BCAC8f87b381f4700",
    },
    "chiado": {
        "service_registry": "0x31D3202d8744B16A120117A053459DDFAE93c855",
        "service_registry_token_utility": "0xc2c7E40674f1C7Bb99eFe5680Efd79842502bED4",
        "service_manager_token": "0xc965a32185590Eb5a5fffDba29E96126b7650eDe",
        "operator_whitelist": "0x6f7661F52fE1919996d0A4F68D09B344093a349d",
        "gnosis_safe_proxy_factory": "0xeB49bE5DF00F74bd240DE4535DDe6Bc89CEfb994",
        "gnosis_safe_same_address_multisig": "0xE16adc7777B7C2a0d35033bd3504C028AB28EE8b",
    },
    "arbitrum_one": {
        "service_registry": "0xE3607b00E75f6405248323A9417ff6b39B244b50",
        "service_registry_token_utility": "0x3d77596beb0f130a4415df3D2D8232B3d3D31e44",
        "service_manager_token": "0x34C895f302D0b5cf52ec0Edd3945321EB0f83dd5",
        "operator_whitelist": "0x3C1fF68f5aa342D296d4DEe4Bb1cACCA912D95fE",
        "gnosis_safe_proxy_factory": "0x63e66d7ad413C01A7b49C7FF4e3Bb765C4E4bd1b",
        "gnosis_safe_same_address_multisig": "0xBb7e1D6Cb6F243D6bdE81CE92a9f2aFF7Fbe7eac",
        "staking_token": "0x04b0007b2aFb398015B76e5f22993a1fddF83644",
        "staking_verifier": "0x7Fd1F4b764fA41d19fe3f63C85d12bf64d2bbf68",
        "staking_factory": "0xEB5638eefE289691EcE01943f768EDBF96258a80",
    },
    "arbitrum_sepolia": {
        "service_registry": "0x31D3202d8744B16A120117A053459DDFAE93c855",
        "service_registry_token_utility": "0xeB49bE5DF00F74bd240DE4535DDe6Bc89CEfb994",
        "service_manager_token": "0x5BA58970c2Ae16Cf6218783018100aF2dCcFc915",
        "operator_whitelist": "0x29086141ecdc310058fc23273F8ef7881d20C2f7",
        "gnosis_safe_proxy_factory": "0x19936159B528C66750992C3cBcEd2e71cF4E4824",
        "gnosis_safe_same_address_multisig": "0x10100e74b7F706222F8A7C0be9FC7Ae1717Ad8B2",
    },
    "optimistic": {
        "service_registry": "0x3d77596beb0f130a4415df3D2D8232B3d3D31e44",
        "service_registry_token_utility": "0xBb7e1D6Cb6F243D6bdE81CE92a9f2aFF7Fbe7eac",
        "service_manager_token": "0xFbBEc0C8b13B38a9aC0499694A69a10204c5E2aB",
        "operator_whitelist": "0x63e66d7ad413C01A7b49C7FF4e3Bb765C4E4bd1b",
        "gnosis_safe_proxy_factory": "0xE43d4F4103b623B61E095E8bEA34e1bc8979e168",
        "gnosis_safe_same_address_multisig": "0xb09CcF0Dbf0C178806Aaee28956c74bd66d21f73",
        "staking_token": "0x63C2c53c09dE534Dd3bc0b7771bf976070936bAC",
        "staking_verifier": "0x526E064cB694E8f5B7DB299158e17F33055B3943",
        "staking_factory": "0xa45E64d13A30a51b91ae0eb182e88a40e9b18eD8",
    },
    "optimistic_sepolia": {
        "service_registry": "0x31D3202d8744B16A120117A053459DDFAE93c855",
        "service_registry_token_utility": "0xeB49bE5DF00F74bd240DE4535DDe6Bc89CEfb994",
        "service_manager_token": "0x5BA58970c2Ae16Cf6218783018100aF2dCcFc915",
        "operator_whitelist": "0x29086141ecdc310058fc23273F8ef7881d20C2f7",
        "gnosis_safe_proxy_factory": "0x19936159B528C66750992C3cBcEd2e71cF4E4824",
        "gnosis_safe_same_address_multisig": "0x10100e74b7F706222F8A7C0be9FC7Ae1717Ad8B2",
    },
    "base": {
        "service_registry": "0x3C1fF68f5aa342D296d4DEe4Bb1cACCA912D95fE",
        "service_registry_token_utility": "0x34C895f302D0b5cf52ec0Edd3945321EB0f83dd5",
        "service_manager_token": "0x63e66d7ad413C01A7b49C7FF4e3Bb765C4E4bd1b",
        "operator_whitelist": "0x3d77596beb0f130a4415df3D2D8232B3d3D31e44",
        "gnosis_safe_proxy_factory": "0xBb7e1D6Cb6F243D6bdE81CE92a9f2aFF7Fbe7eac",
        "gnosis_safe_same_address_multisig": "0xFbBEc0C8b13B38a9aC0499694A69a10204c5E2aB",
        "staking_token": "0xEB5638eefE289691EcE01943f768EDBF96258a80",
        "staking_verifier": "0x10c5525F77F13b28f42c5626240c001c2D57CAd4",
        "staking_factory": "0x1cEe30D08943EB58EFF84DD1AB44a6ee6FEff63a",
    },
    "base_sepolia": {
        "service_registry": "0x31D3202d8744B16A120117A053459DDFAE93c855",
        "service_registry_token_utility": "0xeB49bE5DF00F74bd240DE4535DDe6Bc89CEfb994",
        "service_manager_token": "0x5BA58970c2Ae16Cf6218783018100aF2dCcFc915",
        "operator_whitelist": "0x29086141ecdc310058fc23273F8ef7881d20C2f7",
        "gnosis_safe_proxy_factory": "0x19936159B528C66750992C3cBcEd2e71cF4E4824",
        "gnosis_safe_same_address_multisig": "0x10100e74b7F706222F8A7C0be9FC7Ae1717Ad8B2",
    },
    "celo": {
        "service_registry": "0xE3607b00E75f6405248323A9417ff6b39B244b50",
        "service_registry_token_utility": "0x3d77596beb0f130a4415df3D2D8232B3d3D31e44",
        "service_manager_token": "0x34C895f302D0b5cf52ec0Edd3945321EB0f83dd5",
        "operator_whitelist": "0x3C1fF68f5aa342D296d4DEe4Bb1cACCA912D95fE",
        "gnosis_safe_proxy_factory": "0x63e66d7ad413C01A7b49C7FF4e3Bb765C4E4bd1b",
        "gnosis_safe_same_address_multisig": "0xBb7e1D6Cb6F243D6bdE81CE92a9f2aFF7Fbe7eac",
        "staking_token": "0xe1E1B286EbE95b39F785d8069f2248ae9C41b7a9",
        "staking_verifier": "0xc40C79C275F3fA1F3f4c723755C81ED2D53A8D81",
        "staking_factory": "0x1c2cD884127b080F940b7546c1e9aaf525b1FA55",
    },
    "celo_alfajores": {
        "service_registry": "0x31D3202d8744B16A120117A053459DDFAE93c855",
        "service_registry_token_utility": "0xeB49bE5DF00F74bd240DE4535DDe6Bc89CEfb994",
        "service_manager_token": "0x5BA58970c2Ae16Cf6218783018100aF2dCcFc915",
        "operator_whitelist": "0x29086141ecdc310058fc23273F8ef7881d20C2f7",
        "gnosis_safe_proxy_factory": "0x19936159B528C66750992C3cBcEd2e71cF4E4824",
        "gnosis_safe_same_address_multisig": "0x10100e74b7F706222F8A7C0be9FC7Ae1717Ad8B2",
    },
    "custom_chain": {
        "component_registry": cast(
            str, os.environ.get("CUSTOM_COMPONENT_REGISTRY_ADDRESS")
        ),
        "agent_registry": cast(str, os.environ.get("CUSTOM_AGENT_REGISTRY_ADDRESS")),
        "registries_manager": cast(
            str, os.environ.get("CUSTOM_REGISTRIES_MANAGER_ADDRESS")
        ),
        "service_manager": cast(str, os.environ.get("CUSTOM_SERVICE_MANAGER_ADDRESS")),
        "service_registry": cast(
            str, os.environ.get("CUSTOM_SERVICE_REGISTRY_ADDRESS")
        ),
        "gnosis_safe_proxy_factory": cast(
            str, os.environ.get("CUSTOM_GNOSIS_SAFE_PROXY_FACTORY_ADDRESS")
        ),
        "gnosis_safe_same_address_multisig": cast(
            str, os.environ.get("CUSTOM_GNOSIS_SAFE_SAME_ADDRESS_MULTISIG_ADDRESS")
        ),
        "service_registry_token_utility": cast(
            str, os.environ.get("CUSTOM_SERVICE_REGISTRY_TOKEN_UTILITY_ADDRESS")
        ),
        "multisend": cast(
            str,
            os.environ.get(
                "CUSTOM_MULTISEND_ADDRESS", "0x40A2aCCbd92BCA938b02010E17A5b8929b49130D"
            ),
        ),
    },
}


CHAIN_NAME_TO_CHAIN_ID = {
    "local": 31337,
    "ethereum": 1,
    "goerli": 5,
    "polygon": 137,
    "polygon_mumbai": 80001,
    "gnosis": 100,
    "chiado": 10200,
    "arbitrum_one": 42161,
    "arbitrum_sepolia": 421614,
    "optimistic": 10,
    "optimistic_sepolia": 11155420,
    "base": 8453,
    "base_sepolia": 84532,
    "celo": 42220,
    "celo_alfajores": 42220,
}

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
    42161,
    421614,
    10,
    11155420,
    8453,
    84532,
    42220,
    42220,
)
