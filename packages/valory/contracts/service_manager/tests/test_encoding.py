# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2026 Valory AG
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

"""Calldata of the direct registration and unbond calls, for both build ABIs."""

import json
from pathlib import Path
from typing import Any

import pytest
import yaml
from web3 import Web3

from packages.valory.contracts.service_manager.contract import SERVICE_MANAGER_BUILD

PACKAGE_DIR = Path(__file__).parent.parent
BUILD_DIR = PACKAGE_DIR / "build"
CONTRACT_CONFIG = yaml.safe_load(
    (PACKAGE_DIR / "contract.yaml").read_text(encoding="utf-8")
)
SERVICE_MANAGER_TOKEN_BUILD = Path(
    CONTRACT_CONFIG["contract_interface_paths"]["ethereum"]
).name
BUILD_FILES = (SERVICE_MANAGER_BUILD, SERVICE_MANAGER_TOKEN_BUILD)

SERVICE_ID = 7
AGENT_INSTANCES = [
    "0x1111111111111111111111111111111111111111",
    "0x2222222222222222222222222222222222222222",
]
AGENT_IDS = [3, 5]

# Encoded with the ServiceManager ABIs these build files carried before 1.3.0.
REGISTER_AGENTS_CALLDATA = (
    "0xd03ca40a"
    "0000000000000000000000000000000000000000000000000000000000000007"
    "0000000000000000000000000000000000000000000000000000000000000060"
    "00000000000000000000000000000000000000000000000000000000000000c0"
    "0000000000000000000000000000000000000000000000000000000000000002"
    "0000000000000000000000001111111111111111111111111111111111111111"
    "0000000000000000000000002222222222222222222222222222222222222222"
    "0000000000000000000000000000000000000000000000000000000000000002"
    "0000000000000000000000000000000000000000000000000000000000000003"
    "0000000000000000000000000000000000000000000000000000000000000005"
)
UNBOND_CALLDATA = (
    "0x27de9e320000000000000000000000000000000000000000000000000000000000000007"
)


def _service_manager(build_file: str) -> Any:
    """Build an offline contract object from a build file's ABI."""
    abi = json.loads((BUILD_DIR / build_file).read_text(encoding="utf-8"))["abi"]
    return Web3().eth.contract(abi=abi)


@pytest.mark.parametrize("build_file", BUILD_FILES)
def test_register_agents_calldata_is_unchanged(build_file: str) -> None:
    """`registerAgents(uint256,address[],uint32[])` encodes as before 1.3.0."""
    calldata = _service_manager(build_file).encode_abi(
        "registerAgents",
        kwargs={
            "serviceId": SERVICE_ID,
            "agentInstances": AGENT_INSTANCES,
            "agentIds": AGENT_IDS,
        },
    )
    assert calldata == REGISTER_AGENTS_CALLDATA


@pytest.mark.parametrize("build_file", BUILD_FILES)
def test_unbond_calldata_is_unchanged(build_file: str) -> None:
    """`unbond(uint256)` encodes as before 1.3.0."""
    calldata = _service_manager(build_file).encode_abi(
        "unbond", kwargs={"serviceId": SERVICE_ID}
    )
    assert calldata == UNBOND_CALLDATA


@pytest.mark.parametrize("build_file", BUILD_FILES)
def test_build_file_describes_only_its_abi(build_file: str) -> None:
    """No key left over from an older compile contradicts the build file's ABI."""
    build = json.loads((BUILD_DIR / build_file).read_text(encoding="utf-8"))
    contract = Web3().eth.contract(abi=build["abi"])
    abi_selectors = {
        f"{fn.abi['name']}({','.join(i['type'] for i in fn.abi['inputs'])})"
        for fn in contract.all_functions()
    }
    assert set(build.get("methodIdentifiers", {})) <= abi_selectors
    assert "metadata" not in build and "rawMetadata" not in build
    # The 1.3.0 bytecode is not published yet; pre-1.3.0 bytecode must not pose as it.
    assert build["bytecode"] == "0x"
    assert build["deployedBytecode"] == "0x"
