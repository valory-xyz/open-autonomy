# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2022 Valory AG
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
from typing import List, Tuple


def get_key(key_path: Path) -> str:
    """Returns key value from file.""" ""
    return key_path.read_bytes().strip().decode()


CUR_PATH = os.path.dirname(inspect.getfile(inspect.currentframe()))  # type: ignore
TEST_TOOLS_DIR = Path(CUR_PATH).resolve().absolute()
DATA_PATH = TEST_TOOLS_DIR / "data"

LOCALHOST = "localhost"
HTTP_LOCALHOST = f"http://{LOCALHOST}"

DEFAULT_IMAGE_VERSION = "latest"
MATCHING_FRAMEWORK_VERSION = "0.8.0"
TENDERMINT_IMAGE_VERSION = os.environ.get(
    "TENDERMINT_IMAGE_VERSION", MATCHING_FRAMEWORK_VERSION
)
TENDERMINT_IMAGE_NAME = os.environ.get(
    "TENDERMINT_IMAGE_NAME", "valory/open-autonomy-tendermint"
)
DEFAULT_REQUESTS_TIMEOUT = 5.0
MAX_RETRIES = 30
DEFAULT_AMOUNT = 1000000000000000000000
ETHEREUM_KEY_DEPLOYER = DATA_PATH / "ethereum_key_deployer.txt"
ETHEREUM_KEY_PATH_1 = DATA_PATH / "ethereum_key_1.txt"
ETHEREUM_KEY_PATH_2 = DATA_PATH / "ethereum_key_2.txt"
ETHEREUM_KEY_PATH_3 = DATA_PATH / "ethereum_key_3.txt"
ETHEREUM_KEY_PATH_4 = DATA_PATH / "ethereum_key_4.txt"
ETHEREUM_KEY_PATH_5 = DATA_PATH / "ethereum_key_5.txt"
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

# default hardhat key pairs (public key, private key)
KEY_PAIRS: List[Tuple[str, str]] = [
    (
        "0xf39fd6e51aad88f6f4ce6ab8827279cfffb92266",
        "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80",
    ),
    (
        "0x70997970c51812dc3a010c7d01b50e0d17dc79c8",
        "0x59c6995e998f97a5a0044966f0945389dc9e86dae88c7a8412f4603b6b78690d",
    ),
    (
        "0x3c44cdddb6a900fa2b585dd299e03d12fa4293bc",
        "0x5de4111afa1a4b94908f83103eb1f1706367c2e68ca870fc3fb9a804cdab365a",
    ),
    (
        "0x90f79bf6eb2c4f870365e785982e1f101e93b906",
        "0x7c852118294e51e653712a81e05800f419141751be58f605c371e15141b007a6",
    ),
    (
        "0x15d34aaf54267db7d7c367839aaf71a00a2c6a65",
        "0x47e179ec197488593b187f80a00eb0da91f1b9d0b13f8733639f19c30a34926a",
    ),
    (
        "0x9965507d1a55bcc2695c58ba16fb37d819b0a4dc",
        "0x8b3a350cf5c34c9194ca85829a2df0ec3153be0318b5e2d3348e872092edffba",
    ),
    (
        "0x976ea74026e726554db657fa54763abd0c3a0aa9",
        "0x92db14e403b83dfe3df233f83dfa3a0d7096f21ca9b0d6d6b8d88b2b4ec1564e",
    ),
    (
        "0x14dc79964da2c08b23698b3d3cc7ca32193d9955",
        "0x4bbbf85ce3377467afe5d46f804f221813b2bb87f24d81f60f1fcdbf7cbf4356",
    ),
    (
        "0x23618e81e3f5cdf7f54c3d65f7fbc0abf5b21e8f",
        "0xdbda1821b80551c9d65939329250298aa3472ba22feea921c0cf5d620ea67b97",
    ),
    (
        "0xa0ee7a142d267c1f36714e4a8f75612f20a79720",
        "0x2a871d0798f97d79848a013d4936a73bf4cc922c825d33c1cf7073dff6d409c6",
    ),
    (
        "0xbcd4042de499d14e55001ccbb24a551f3b954096",
        "0xf214f2b2cd398c806f84e317254e0f0b801d0643303237d97a22a48e01628897",
    ),
    (
        "0x71be63f3384f5fb98995898a86b02fb2426c5788",
        "0x701b615bbdfb9de65240bc28bd21bbc0d996645a3dd57e7b12bc2bdf6f192c82",
    ),
    (
        "0xfabb0ac9d68b0b445fb7357272ff202c5651694a",
        "0xa267530f49f8280200edf313ee7af6b827f2a8bce2897751d06a843f644967b1",
    ),
    (
        "0x1cbd3b2770909d4e10f157cabc84c7264073c9ec",
        "0x47c99abed3324a2707c28affff1267e45918ec8c3f20b8aa892e8b065d2942dd",
    ),
    (
        "0xdf3e18d64bc6a983f673ab319ccae4f1a57c7097",
        "0xc526ee95bf44d8fc405a158bb884d9d1238d99f0612e9f33d006bb0789009aaa",
    ),
    (
        "0xcd3b766ccdd6ae721141f452c550ca635964ce71",
        "0x8166f546bab6da521a8369cab06c5d2b9e46670292d85c875ee9ec20e84ffb61",
    ),
    (
        "0x2546bcd3c84621e976d8185a91a922ae77ecec30",
        "0xea6c44ac03bff858b476bba40716402b03e41b8e97e276d1baec7c37d42484a0",
    ),
    (
        "0xbda5747bfd65f08deb54cb465eb87d40e51b197e",
        "0x689af8efa8c651a91ad287602527f3af2fe9f6501a7ac4b061667b5a93e037fd",
    ),
    (
        "0xdd2fd4581271e230360230f9337d5c0430bf44c0",
        "0xde9be858da4a475276426320d5e9262ecfc3ba460bfac56360bfa6c4c28b4ee0",
    ),
    (
        "0x8626f6940e2eb28930efb4cef49b2d1f2c9c1199",
        "0xdf57089febbacf7ba0bc227dafbffa9fc08a93fdc68e1e42411a14efcf23656e",
    ),
]
ANY_ADDRESS = "0.0.0.0"  # nosec
