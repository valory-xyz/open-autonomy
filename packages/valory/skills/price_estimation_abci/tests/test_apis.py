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

"""Test various price apis."""

# pylint: skip-file

import logging  # noqa: F401
from typing import Dict, List, Tuple, Union

import pytest
import requests
from aea.skills.base import SkillContext

from packages.valory.skills.price_estimation_abci.models import PriceApi, RandomnessApi


price_apis = pytest.mark.parametrize(
    "api_specs",
    [
        [
            ("url", "https://api.coingecko.com/api/v3/simple/price"),
            ("api_id", "coingecko"),
            ("parameters", [["ids", "bitcoin"], ["vs_currencies", "usd"]]),
            ("response_key", "bitcoin:usd"),
        ],
        [
            (
                "url",
                "https://ftx.com/api/markets/BTC/USD",
            ),
            ("api_id", "ftx"),
            ("response_key", "result:last"),
        ],
        [
            ("url", "https://api.coinbase.com/v2/prices/BTC-USD/buy"),
            ("api_id", "coinbase"),
            ("response_key", "data:amount"),
        ],
        [
            ("url", "https://api.binance.com/api/v3/ticker/price"),
            ("api_id", "binance"),
            ("parameters", [["symbol", "BTCUSDT"]]),
            ("response_key", "price"),
        ],
    ],
)

randomness_apis = pytest.mark.parametrize(
    "api_specs",
    [
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
    ],
)


class DummyMessage:
    """Dummy api specs class."""

    body: bytes

    def __init__(self, body: bytes) -> None:
        """Initializes DummyMessage"""
        self.body = body


def make_request(api_specs: Dict) -> requests.Response:
    """Make request using api specs."""

    if api_specs["method"] == "GET":
        if api_specs["parameters"]:
            api_specs["url"] = api_specs["url"] + "?"
            for key, val in api_specs["parameters"]:
                api_specs["url"] += f"{key}={val}&"
            api_specs["url"] = api_specs["url"][:-1]
        return requests.get(url=api_specs["url"], headers=dict(api_specs["headers"]))

    raise ValueError(f"Unknown method {api_specs['method']}")


@price_apis
def test_price_api(api_specs: List[Tuple[str, Union[str, List]]]) -> None:
    """Test various price api specs."""

    api = PriceApi(
        name="price_api",
        skill_context=SkillContext(),
        currency_id="BTC",
        convert_id="USD",
        method="GET",
        response_type="float",
        retries=5,
        **dict(api_specs),
    )

    response = make_request(api.get_spec())
    observation = api.process_response(DummyMessage(response.content))  # type: ignore
    assert isinstance(observation, float)


@randomness_apis
def test_randomness_api(api_specs: List[Tuple[str, Union[str, List]]]) -> None:
    """Test various price api specs."""

    api = RandomnessApi(
        name="randomness_api",
        skill_context=SkillContext(),
        method="GET",
        response_type="dict",
        retries=5,
        **dict(api_specs),
    )

    response = make_request(api.get_spec())
    value = api.process_response(DummyMessage(response.content))  # type: ignore
    assert isinstance(value, dict)
    assert all([key in value for key in ["randomness", "round"]])
