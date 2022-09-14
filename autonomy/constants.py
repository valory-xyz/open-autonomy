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
"""Constants"""
import os


DEFAULT_BUILD_FOLDER = "abci_build"
DEFAULT_KEYS_FILE = "keys.json"
DEFAULT_IMAGE_VERSION = "latest"
DEFAULT_SERVICE_REGISTRY_CONTRACTS_IMAGE = "valory/autonolas-registries:latest"
SERVICE_REGISTRY_CONTRACT_CONTAINER_NAME = "autonolas-registries"

AUTONOMY_IMAGE_VERSION = os.environ.get("AUTONOMY_IMAGE_VERSION", DEFAULT_IMAGE_VERSION)
TENDERMINT_IMAGE_VERSION = os.environ.get(
    "TENDERMINT_IMAGE_VERSION", DEFAULT_IMAGE_VERSION
)
HARDHAT_IMAGE_VERSION = os.environ.get("HARDHAT_IMAGE_VERSION", DEFAULT_IMAGE_VERSION)

AUTONOMY_IMAGE_NAME = os.environ.get("AUTONOMY_IMAGE_NAME", "valory/open-autonomy")
TENDERMINT_IMAGE_NAME = os.environ.get(
    "TENDERMINT_IMAGE_NAME", "valory/open-autonomy-tendermint"
)
HARDHAT_IMAGE_NAME = os.environ.get(
    "HARDHAT_IMAGE_NAME", "valory/open-autonomy-hardhat"
)

OAR_IMAGE = "valory/oar-{agent}:{version}"
ABSTRACT_ROUND_ABCI_SKILL_WITH_HASH = "valory/abstract_round_abci:0.1.0:bafybeigpz64qx22a4zzlcczmc5frhlecytrh5q3x77lwe3a5kee2qrcchm"
