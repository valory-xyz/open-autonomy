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

"""Agent config."""

from typing import List, Optional, Tuple


KEYS: List[str] = [
    "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80",
    "0x59c6995e998f97a5a0044966f0945389dc9e86dae88c7a8412f4603b6b78690d",
    "0x5de4111afa1a4b94908f83103eb1f1706367c2e68ca870fc3fb9a804cdab365a",
    "0x7c852118294e51e653712a81e05800f419141751be58f605c371e15141b007a6",
    "0x47e179ec197488593b187f80a00eb0da91f1b9d0b13f8733639f19c30a34926a",
    "0x8b3a350cf5c34c9194ca85829a2df0ec3153be0318b5e2d3348e872092edffba",
    "0x92db14e403b83dfe3df233f83dfa3a0d7096f21ca9b0d6d6b8d88b2b4ec1564e",
    "0x4bbbf85ce3377467afe5d46f804f221813b2bb87f24d81f60f1fcdbf7cbf4356",
    "0xdbda1821b80551c9d65939329250298aa3472ba22feea921c0cf5d620ea67b97",
    "0x2a871d0798f97d79848a013d4936a73bf4cc922c825d33c1cf7073dff6d409c6",
    "0xf214f2b2cd398c806f84e317254e0f0b801d0643303237d97a22a48e01628897",
    "0x701b615bbdfb9de65240bc28bd21bbc0d996645a3dd57e7b12bc2bdf6f192c82",
    "0xa267530f49f8280200edf313ee7af6b827f2a8bce2897751d06a843f644967b1",
    "0x47c99abed3324a2707c28affff1267e45918ec8c3f20b8aa892e8b065d2942dd",
    "0xc526ee95bf44d8fc405a158bb884d9d1238d99f0612e9f33d006bb0789009aaa",
    "0x8166f546bab6da521a8369cab06c5d2b9e46670292d85c875ee9ec20e84ffb61",
    "0xea6c44ac03bff858b476bba40716402b03e41b8e97e276d1baec7c37d42484a0",
    "0x689af8efa8c651a91ad287602527f3af2fe9f6501a7ac4b061667b5a93e037fd",
    "0xde9be858da4a475276426320d5e9262ecfc3ba460bfac56360bfa6c4c28b4ee0",
    "0xdf57089febbacf7ba0bc227dafbffa9fc08a93fdc68e1e42411a14efcf23656e",
]

RANDOMNESS_APIS: List[List[Tuple[str, str]]] = [
    [
        ("url", "https://drand.cloudflare.com/public/latest"),
        ("api_id", "cloudflare"),
    ],
    [
        ("url", "https://api.drand.sh/public/latest"),
        ("api_id", "protocollabs1"),
    ],
    [
        ("url", "https://api2.drand.sh/public/latest"),
        ("api_id", "protocollabs2"),
    ],
    [
        ("url", "https://api3.drand.sh/public/latest"),
        ("api_id", "protocollabs3"),
    ],
]

PRICE_APIS: List[List[Tuple[str, str]]] = [
    [
        ("url", "https://api.coingecko.com/api/v3/simple/price"),
        ("api_id", "coingecko"),
        (
            "parameters",
            """'[["ids", "bitcoin"],["vs_currencies", "usd"]]'  --type list""",
        ),
        ("response_key", "'bitcoin:usd'"),
    ],
    [
        ("url", "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"),
        ("api_id", "coinmarketcap"),
        (
            "headers",
            """'[{"Accepts": "application/json"}, {"X-CMC_PRO_API_KEY": "27d2cd0d-80c3-4ec3-9305-4f3d9ad34e41"}]'  --type list  --type list""",
        ),
        ("parameters", """'[["symbol","BTC"], ["convert","USD"]]'  --type list"""),
        ("response_key", "'data:BTC:quote:USD:price'"),
    ],
    [
        ("url", "https://api.coinbase.com/v2/prices/BTC-USD/buy"),
        ("api_id", "coinbase"),
        ("response_key", "'data:amount'"),
    ],
    [
        ("url", "https://api.binance.com/api/v3/ticker/price"),
        ("api_id", "binance"),
        ("parameters", """'[["symbol", "BTCUSDT"]]' --type list"""),
        ("response_key", "price"),
    ],
]

COMON_CONFIG: List[Tuple[str, str, Optional[str]]] = [
    ("agent.skill_exception_policy", "just_log", None),
    ("agent.connection_exception_policy", "just_log", None),
    ("vendor.valory.connections.abci.config.use_tendermint", "False", None),
    (
        "vendor.valory.skills.price_estimation_abci.models.params.args.consensus.max_participants",
        "{max_participants}",
        None,
    ),
    (
        "vendor.valory.skills.price_estimation_abci.models.params.args.round_timeout_seconds",
        "5",
        None,
    ),
    (
        "vendor.valory.skills.price_estimation_abci.models.params.args.tendermint_url",
        "http://node{node_id}:26657",
        None,
    ),
    (
        "vendor.valory.skills.price_estimation_abci.models.params.args.tendermint_com_url",
        "http://node{node_id}:8080",
        None,
    ),
    (
        "vendor.valory.skills.price_estimation_abci.models.params.args.reset_tendermint_after",
        "10",
        "int",
    ),
    (
        "vendor.valory.skills.price_estimation_abci.models.params.args.observation_interval",
        "3",
        "int",
    ),
    (
        "vendor.valory.skills.price_estimation_abci.models.params.args.max_healthcheck",
        "10",
        "int",
    ),
    (
        "vendor.valory.connections.ledger.config.ledger_apis.ethereum.address",
        "http://hardhat:8545",
        None,
    ),
    (
        "vendor.valory.connections.ledger.config.ledger_apis.ethereum.chain_id",
        "31337",
        "int",
    ),
]
