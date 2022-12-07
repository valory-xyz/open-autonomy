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

"""On-chain tools configurations."""

import json
from dataclasses import dataclass
from typing import Dict

from autonomy.chain.constants import (
    ABI_DIR,
    COMPONENT_REGISTRY_ADDRESS_LOCAL,
    COMPONENT_REGISTRY_FILENAME,
    REGISTRIES_MANAGER_ADDRESS_LOCAL,
    REGISTRIES_MANAGER_FILENAME,
)


DEFAULT_LOCAL_RPC = "http://127.0.0.1:8545"
DEFAULT_LOCAL_CHAIN_ID = 31337


def get_abi(filename: str) -> Dict:
    """Service contract ABI."""
    with (ABI_DIR / filename).open(mode="r", encoding="utf-8") as fp:
        return json.load(fp=fp)


@dataclass
class ContractConfig:
    """Contract config class."""

    name: str

    rpc: str
    chain_id: int
    contract_address: str

    abi_file: str


REGISTRIES_MANAGER_LOCAL = ContractConfig(
    name="registries_manager_local",
    rpc=DEFAULT_LOCAL_RPC,
    chain_id=DEFAULT_LOCAL_CHAIN_ID,
    contract_address=REGISTRIES_MANAGER_ADDRESS_LOCAL,
    abi_file=REGISTRIES_MANAGER_FILENAME,
)

COMPONENT_REGISTRY_LOCAL = ContractConfig(
    name="component_registry_local",
    rpc=DEFAULT_LOCAL_RPC,
    chain_id=DEFAULT_LOCAL_CHAIN_ID,
    contract_address=COMPONENT_REGISTRY_ADDRESS_LOCAL,
    abi_file=COMPONENT_REGISTRY_FILENAME,
)
