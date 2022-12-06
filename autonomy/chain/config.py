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

from dataclasses import dataclass


DEFAULT_LOCAL_RPC = "http://127.0.0.1:8545"
DEFAULT_LOCAL_CHAIN_ID = 31337


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
    contract_address="0x9fE46736679d2D9a65F0992F2272dE9f3c7fa6e0",
    abi_file="registries_manager.json",
)

COMPONENT_REGISTRY_LOCAL = ContractConfig(
    name="component_registry_local",
    rpc=DEFAULT_LOCAL_RPC,
    chain_id=DEFAULT_LOCAL_CHAIN_ID,
    contract_address="0x5FbDB2315678afecb367f032d93F642f64180aa3",
    abi_file="component_registry.json",
)
