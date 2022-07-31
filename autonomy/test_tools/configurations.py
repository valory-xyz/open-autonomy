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

"""Test tools configuration."""
import inspect
import os
from pathlib import Path


def get_key(key_path: Path) -> str:
    """Returns key value from file.""" ""
    return key_path.read_bytes().strip().decode()


CUR_PATH = os.path.dirname(inspect.getfile(inspect.currentframe()))  # type: ignore
TEST_TOOLS_DIR = Path(CUR_PATH).resolve().absolute()
ROOT_DIR = Path(CUR_PATH, "..", "..").resolve().absolute()
THIRD_PARTY = ROOT_DIR / "third_party"

DATA_PATH = TEST_TOOLS_DIR / "data"

DEFAULT_REQUESTS_TIMEOUT = 5.0
MAX_RETRIES = 30
DEFAULT_AMOUNT = 1000000000000000000000
ETHEREUM_KEY_DEPLOYER = DATA_PATH / "ethereum_key_deployer.txt"
ETHEREUM_KEY_PATH_1 = DATA_PATH / "ethereum_key_1.txt"
ETHEREUM_KEY_PATH_2 = DATA_PATH / "ethereum_key_2.txt"
ETHEREUM_KEY_PATH_3 = DATA_PATH / "ethereum_key_3.txt"
ETHEREUM_KEY_PATH_4 = DATA_PATH / "ethereum_key_4.txt"
ETHEREUM_ENCRYPTED_KEYS = DATA_PATH / "encrypted_keys.json"
ETHEREUM_ENCRYPTION_PASSWORD = "much-secure"  # nosec
GANACHE_CONFIGURATION = dict(
    accounts_balances=[
        (get_key(ETHEREUM_KEY_DEPLOYER), DEFAULT_AMOUNT),
        (get_key(ETHEREUM_KEY_PATH_1), DEFAULT_AMOUNT),
        (get_key(ETHEREUM_KEY_PATH_2), DEFAULT_AMOUNT),
        (get_key(ETHEREUM_KEY_PATH_3), DEFAULT_AMOUNT),
        (get_key(ETHEREUM_KEY_PATH_4), DEFAULT_AMOUNT),
    ],
)
