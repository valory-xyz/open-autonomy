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

"""Test the ABIs are consistent."""
import json
from pathlib import Path

from autonomy.deploy.chain import SERVICE_REGISTRY_ABI, get_abi

from tests.conftest import ROOT_DIR


def test_service_abi_matches_contract() -> None:
    """Test that the ServiceRegistry ABI on autonomy matches the ABI on the ServiceRegistry contract package."""

    contract_directory = Path(
        ROOT_DIR,
        "packages",
        "valory",
        "contracts",
        "service_registry",
    )
    expected_abi_path = contract_directory / "build" / "ServiceRegistry.json"
    with open(expected_abi_path, encoding="utf-8") as expected_abi_file:
        expected_abi = json.load(expected_abi_file)["abi"]

    actual_abi = get_abi(SERVICE_REGISTRY_ABI)

    # the abi on autonomy is at autonomy/data/abis/service_registry/service_registry.json
    assert expected_abi == actual_abi, (
        "The ServiceRegistry ABI in autonomy needs to match the ServiceRegistry contract package ABI",
    )
