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

"""Chain constants"""

from autonomy.data import DATA_DIR


ABI_DIR = DATA_DIR / "abis"


COMPONENT_REGISTRY_FILENAME = "ComponentRegistry.json"
AGENT_REGISTRY_FILENAME = "AgentRegistry.json"
REGISTRIES_MANAGER_FILENAME = "RegistriesManager.json"
GNOSIS_SAFE_MULTISIG_FILENAME = "GnosisSafeMultisig.json"
SERVICE_MANAGER_FILENAME = "ServiceManager.json"
SERVICE_REGISTRY_FILENAME = "ServiceRegistry.json"

# contract address from `valory/autonolas-registries` image
COMPONENT_REGISTRY_ADDRESS_LOCAL = "0x5FbDB2315678afecb367f032d93F642f64180aa3"
AGENT_REGISTRY_ADDRESS_LOCAL = "0xe7f1725E7734CE288F8367e1Bb143E90bb3F0512"
REGISTRIES_MANAGER_ADDRESS_LOCAL = "0x9fE46736679d2D9a65F0992F2272dE9f3c7fa6e0"
GNOSIS_SAFE_MULTISIG_ADDRESS_LOCAL = "0xA51c1fc2f0D1a1b8494Ed1FE312d7C3a78Ed91C0"
SERVICE_MANAGER_ADDRESS_LOCAL = "0x70e0bA845a1A0F2DA3359C97E0285013525FFC49"
SERVICE_REGISTRY_ADDRESS_LOCAL = "0x998abeb3E57409262aE5b751f60747921B33613E"
