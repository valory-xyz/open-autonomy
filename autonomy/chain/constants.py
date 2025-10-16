# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022-2025 Valory AG
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
        "service_registry_token_utility": "0x36C02dA8a0983159322a80FFE9F24b1acfF8B570",
        "service_manager": "0x4c5859f0F772848b2D91F1D83E2Fe57935348029",
        "gnosis_safe_proxy_factory": "0x0E801D84Fa97b50751Dbf25036d067dCf18858bF",  # Multisig WITHOUT recovery module
        "gnosis_safe_same_address_multisig": "0x8f86403A4DE0BB5791fa46B8e795C547942fE4Cf",  # Same address multisig WITHOUT recovery module
        "safe_multisig_with_recovery_module": "0xb7278A61aa25c888815aFC32Ad3cC52fF24fE575",  # Multisig WITH recovery module
        "recovery_module": "0x5f3f1dBD7B74C6B46e8c44f98792A1dAf8d69154",  # Same address multisig WITH recovery module
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
        "gnosis_safe_proxy_factory": "0x46C0D07F55d4F9B5Eed2Fc9680B5953e5fd7b461",  # Multisig WITHOUT recovery module
        "gnosis_safe_same_address_multisig": "0xfa517d01DaA100cB1932FA4345F68874f7E7eF46",  # Same address multisig WITHOUT recovery module
        "safe_multisig_with_recovery_module": "0xCb728aefD88FCA806d638EAEeEAcFC03Dd985d70",  # Multisig WITH recovery module
        "recovery_module": "0x69D97b5c4F35fd3A72FA83b6B1eB911c6A8a2e3c",  # Same address multisig WITH recovery module
        "staking_token": "0x0Dc23eEf3bC64CF3cbd8f9329B57AE4C4f28d5d2",
        "staking_verifier": "0x4503b79d468e81Ad2d4bd6Db991810da269bA777",
        "staking_factory": "0xEBdde456EA288b49f7D5975E7659bA1Ccf607efc",
        "complementary_service_metadata": "0x0561cE39A1ab785B02DE0D9903125702559993A1",
    },
    "polygon": {
        "service_registry": "0xE3607b00E75f6405248323A9417ff6b39B244b50",
        "service_manager": "0x3C1fF68f5aa342D296d4DEe4Bb1cACCA912D95fE",
        "service_registry_token_utility": "0xa45E64d13A30a51b91ae0eb182e88a40e9b18eD8",
        "service_manager_token": "0x04b0007b2aFb398015B76e5f22993a1fddF83644",
        "gnosis_safe_proxy_factory": "0x3d77596beb0f130a4415df3D2D8232B3d3D31e44",  # Multisig WITHOUT recovery module
        "gnosis_safe_same_address_multisig": "0xd8BCC126ff31d2582018715d5291A508530587b0",  # Same address multisig WITHOUT recovery module
        "safe_multisig_with_recovery_module": "0x1a0bFCC27051BCcDDc444578f56A4F5920e0E083",  # Multisig WITH recovery module
        "recovery_module": "0x02C26437B292D86c5F4F21bbCcE0771948274f84",  # Same address multisig WITH recovery module
        "operator_whitelist": "0x526E064cB694E8f5B7DB299158e17F33055B3943",
        "staking_token": "0x4aba1Cf7a39a51D75cBa789f5f21cf4882162519",
        "staking_verifier": "0x8Bc0a5c5B1612A16983B01ecd7ae130E728390CB",
        "staking_factory": "0x46C0D07F55d4F9B5Eed2Fc9680B5953e5fd7b461",
    },
    "gnosis": {
        "service_registry": "0x9338b5153AE39BB89f50468E608eD9d764B755fD",
        "service_registry_token_utility": "0xa45E64d13A30a51b91ae0eb182e88a40e9b18eD8",
        "service_manager_token": "0x04b0007b2aFb398015B76e5f22993a1fddF83644",
        "operator_whitelist": "0x526E064cB694E8f5B7DB299158e17F33055B3943",
        "gnosis_safe_proxy_factory": "0x3C1fF68f5aa342D296d4DEe4Bb1cACCA912D95fE",  # Multisig WITHOUT recovery module
        "gnosis_safe_same_address_multisig": "0x6e7f594f680f7aBad18b7a63de50F0FeE47dfD06",  # Same address multisig WITHOUT recovery module
        "safe_multisig_with_recovery_module": "0xB4eB492bbfDcE5ccc11d675797cCF090eB0bCbd6",  # Multisig WITH recovery module
        "recovery_module": "0x0Cb12457ed26d572c5e4A50f30b6f7A904662a72",  # Same address multisig WITH recovery module
        "staking_token": "0xEa00be6690a871827fAfD705440D20dd75e67AB1",
        "staking_verifier": "0x1D59DadE4FAeA7771eC7221420012d413175404C",
        "staking_factory": "0xb0228CA253A88Bc8eb4ca70BCAC8f87b381f4700",
        "complementary_service_metadata": "0x0598081D48FB80B0A7E52FAD2905AE9beCd6fC69",
    },
    "arbitrum_one": {
        "service_registry": "0xE3607b00E75f6405248323A9417ff6b39B244b50",
        "service_registry_token_utility": "0x3d77596beb0f130a4415df3D2D8232B3d3D31e44",
        "service_manager_token": "0x34C895f302D0b5cf52ec0Edd3945321EB0f83dd5",
        "operator_whitelist": "0x3C1fF68f5aa342D296d4DEe4Bb1cACCA912D95fE",
        "gnosis_safe_proxy_factory": "0x63e66d7ad413C01A7b49C7FF4e3Bb765C4E4bd1b",  # Multisig WITHOUT recovery module
        "gnosis_safe_same_address_multisig": "0xBb7e1D6Cb6F243D6bdE81CE92a9f2aFF7Fbe7eac",  # Same address multisig WITHOUT recovery module
        "safe_multisig_with_recovery_module": "0x17B2198872216D8469AdeBC1227D0d4824940821",  # Multisig WITH recovery module
        "recovery_module": "0xD0863340f947bE329c67e196e192705e53A1338f",  # Same address multisig WITH recovery module
        "staking_token": "0x04b0007b2aFb398015B76e5f22993a1fddF83644",
        "staking_verifier": "0x7Fd1F4b764fA41d19fe3f63C85d12bf64d2bbf68",
        "staking_factory": "0xEB5638eefE289691EcE01943f768EDBF96258a80",
    },
    "optimism": {
        "service_registry": "0x3d77596beb0f130a4415df3D2D8232B3d3D31e44",
        "service_registry_token_utility": "0xBb7e1D6Cb6F243D6bdE81CE92a9f2aFF7Fbe7eac",
        "service_manager_token": "0xFbBEc0C8b13B38a9aC0499694A69a10204c5E2aB",
        "operator_whitelist": "0x63e66d7ad413C01A7b49C7FF4e3Bb765C4E4bd1b",
        "gnosis_safe_proxy_factory": "0x5953f21495BD9aF1D78e87bb42AcCAA55C1e896C",  # Multisig WITHOUT recovery module
        "gnosis_safe_same_address_multisig": "0xb09CcF0Dbf0C178806Aaee28956c74bd66d21f73",  # Same address multisig WITHOUT recovery module
        "safe_multisig_with_recovery_module": "0x4be7A91e67be963806FeFA9C1FD6C53DfC358d94",  # Multisig WITH recovery module
        "recovery_module": "0x6e7f594f680f7aBad18b7a63de50F0FeE47dfD06",  # Same address multisig WITH recovery module
        "staking_token": "0x63C2c53c09dE534Dd3bc0b7771bf976070936bAC",
        "staking_verifier": "0x526E064cB694E8f5B7DB299158e17F33055B3943",
        "staking_factory": "0xa45E64d13A30a51b91ae0eb182e88a40e9b18eD8",
    },
    "base": {
        "service_registry": "0x3C1fF68f5aa342D296d4DEe4Bb1cACCA912D95fE",
        "service_registry_token_utility": "0x34C895f302D0b5cf52ec0Edd3945321EB0f83dd5",
        "service_manager_token": "0x63e66d7ad413C01A7b49C7FF4e3Bb765C4E4bd1b",
        "operator_whitelist": "0x3d77596beb0f130a4415df3D2D8232B3d3D31e44",
        "gnosis_safe_proxy_factory": "0x22bE6fDcd3e29851B29b512F714C328A00A96B83",  # Multisig WITHOUT recovery module
        "gnosis_safe_same_address_multisig": "0xFbBEc0C8b13B38a9aC0499694A69a10204c5E2aB",  # Same address multisig WITHOUT recovery module
        "safe_multisig_with_recovery_module": "0x8c534420Db046d6801A1A8bE6fb602cC8F257453",  # Multisig WITH recovery module
        "recovery_module": "0x359d53C326388D24037b3b1590d217fdb5EEE74c",  # Same address multisig WITH recovery module
        "staking_token": "0xEB5638eefE289691EcE01943f768EDBF96258a80",
        "staking_verifier": "0x10c5525F77F13b28f42c5626240c001c2D57CAd4",
        "staking_factory": "0x1cEe30D08943EB58EFF84DD1AB44a6ee6FEff63a",
        "complementary_service_metadata": "0x28C1edC7CEd549F7f80B732fDC19f0370160707d",
    },
    "celo": {
        "service_registry": "0xE3607b00E75f6405248323A9417ff6b39B244b50",
        "service_registry_token_utility": "0x3d77596beb0f130a4415df3D2D8232B3d3D31e44",
        "service_manager_token": "0x34C895f302D0b5cf52ec0Edd3945321EB0f83dd5",
        "operator_whitelist": "0x3C1fF68f5aa342D296d4DEe4Bb1cACCA912D95fE",
        "gnosis_safe_proxy_factory": "0x63e66d7ad413C01A7b49C7FF4e3Bb765C4E4bd1b",  # Multisig WITHOUT recovery module
        "gnosis_safe_same_address_multisig": "0xBb7e1D6Cb6F243D6bdE81CE92a9f2aFF7Fbe7eac",  # Same address multisig WITHOUT recovery module
        "safe_multisig_with_recovery_module": "0x379451B13e4900C7005Bf57467770b2EE4e62a86",  # Multisig WITH recovery module
        "recovery_module": "0x24F792D51b398928459Dfbb4181bDb4D5d2CD472",  # Same address multisig WITH recovery module
        "staking_token": "0xe1E1B286EbE95b39F785d8069f2248ae9C41b7a9",
        "staking_verifier": "0xc40C79C275F3fA1F3f4c723755C81ED2D53A8D81",
        "staking_factory": "0x1c2cD884127b080F940b7546c1e9aaf525b1FA55",
    },
    "mode": {
        "service_registry": "0x3C1fF68f5aa342D296d4DEe4Bb1cACCA912D95fE",
        "service_registry_token_utility": "0x34C895f302D0b5cf52ec0Edd3945321EB0f83dd5",
        "service_manager_token": "0x63e66d7ad413C01A7b49C7FF4e3Bb765C4E4bd1b",
        "operator_whitelist": "0x3d77596beb0f130a4415df3D2D8232B3d3D31e44",
        "gnosis_safe_proxy_factory": "0xBb7e1D6Cb6F243D6bdE81CE92a9f2aFF7Fbe7eac",  # Multisig WITHOUT recovery module
        "gnosis_safe_same_address_multisig": "0xFbBEc0C8b13B38a9aC0499694A69a10204c5E2aB",  # Same address multisig WITHOUT recovery module
        "safe_multisig_with_recovery_module": "0x7Fd1F4b764fA41d19fe3f63C85d12bf64d2bbf68",  # Multisig WITH recovery module
        "recovery_module": "0x1d79e0a600B61FAC1B8F40c27347e48962Ed2f23",  # Same address multisig WITH recovery module
        "staking_token": "0xE49CB081e8d96920C38aA7AB90cb0294ab4Bc8EA",
        "staking_native_token": "0x88DE734655184a09B70700aE4F72364d1ad23728",
        "staking_verifier": "0x87c511c8aE3fAF0063b3F3CF9C6ab96c4AA5C60c",
        "staking_factory": "0x75D529FAe220bC8db714F0202193726b46881B76",
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
        "gnosis_safe_proxy_factory": cast(  # Multisig WITHOUT recovery module
            str, os.environ.get("CUSTOM_GNOSIS_SAFE_PROXY_FACTORY_ADDRESS")
        ),
        "gnosis_safe_same_address_multisig": cast(  # Same address multisig WITHOUT recovery module
            str, os.environ.get("CUSTOM_GNOSIS_SAFE_SAME_ADDRESS_MULTISIG_ADDRESS")
        ),
        "safe_multisig_with_recovery_module": cast(  # Multisig WITH recovery module
            str, os.environ.get("CUSTOM_SAFE_MULTISIG_WITH_RECOVERY_MODULE_ADDRESS")
        ),
        "recovery_module": cast(
            str, os.environ.get("CUSTOM_RECOVERY_MODULE_ADDRESS")
        ),  # Same address multisig WITH recovery module
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
    "polygon": 137,
    "gnosis": 100,
    "arbitrum_one": 42161,
    "optimism": 10,
    "base": 8453,
    "celo": 42220,
    "mode": 34443,
}
CHAIN_ID_TO_CHAIN_NAME = {
    chain_id: chain_name for chain_name, chain_id in CHAIN_NAME_TO_CHAIN_ID.items()
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
)  # Multisig WITHOUT recovery module
GNOSIS_SAFE_SAME_ADDRESS_MULTISIG_CONTRACT = PublicId.from_str(
    "valory/gnosis_safe_same_address_multisig"
)  # Same address multisig WITHOUT recovery module
SAFE_MULTISIG_WITH_RECOVERY_MODULE_CONTRACT = PublicId.from_str(
    "valory/safe_multisig_with_recovery_module"
)  # Multisig WITH recovery module
RECOVERY_MODULE_CONTRACT = PublicId.from_str(
    "valory/recovery_module"
)  # Same address multisig WITH recovery module
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
