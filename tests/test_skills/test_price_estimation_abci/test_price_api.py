# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021 Valory AG
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

"""Test the price_api.py module of the skill."""

import pytest
from aea.skills.base import SkillContext
from requests import get

from packages.valory.skills.price_estimation_abci.price_api import (
    ApiSpecs,
    BinanceApiSpecs,
    CoinGeckoApiSpecs,
    CoinMarketCapApiSpecs,
    CoinbaseApiSpecs,
    Currency,
    PriceApi,
)


COINMARKETCAP_API_KEY = "2142662b-985c-4862-82d7-e91457850c2a"


class DummyMessage:
    """Dummy HttpMessage"""

    body: bytes

    def __init__(self, response: bytes) -> None:
        """Dummy HttpMessage"""
        self.body = response


class BaseApiSpecTest:
    """Base test class for ApiSpec class."""

    api: ApiSpecs

    currency_id: Currency = Currency.BITCOIN
    convert_id: Currency = Currency.USD

    def test_run(
        self,
    ):
        """Run tests."""
        specs = self.api.get_spec(self.currency_id, self.convert_id)
        assert all([key in specs for key in ["url", "api_id", "headers", "parameters"]])
        http_response = get(
            url=specs["url"], params=specs["parameters"], headers=specs["headers"]
        )
        response = DummyMessage(http_response.content)
        observation = self.api.post_request_process(response)
        assert isinstance(observation, float)

        fake_response = DummyMessage(b"")
        fake_observation = self.api.post_request_process(fake_response)
        assert fake_observation is None


class TestCoinbaseApiSpecs(BaseApiSpecTest):
    """Test CoinbaseApiSpecs class."""

    def setup(
        self,
    ):
        """Setup test."""
        self.api = CoinbaseApiSpecs()


class TestCoinGeckoApiSpecs(BaseApiSpecTest):
    """Test CoinGeckoApiSpecs class."""

    def setup(
        self,
    ):
        """Setup test."""
        self.api = CoinGeckoApiSpecs()


class TestCoinMarketCapApiSpecs(BaseApiSpecTest):
    """Test CoinMarketCapApiSpecs class."""

    def setup(
        self,
    ):
        """Setup test."""
        self.api = CoinMarketCapApiSpecs(api_key=COINMARKETCAP_API_KEY)


class TestBinanceApiSpecs(BaseApiSpecTest):
    """Test BinanceApiSpecs class."""

    def setup(
        self,
    ):
        """Setup test."""
        self.api = BinanceApiSpecs()
        self.convert_id = Currency.USDT


def test_price_api():
    """Test `PriceApi` class."""

    api = CoinMarketCapApiSpecs(api_key=COINMARKETCAP_API_KEY)
    currency_id = Currency.BITCOIN
    convert_id = Currency.USD

    price_api = PriceApi(
        name="price_api",
        skill_context=SkillContext(),
        source_id=CoinMarketCapApiSpecs.api_id,
        retries=5,
        api_key=COINMARKETCAP_API_KEY,
    )
    api_specs = price_api.get_spec(currency_id, convert_id)

    assert api_specs == api.get_spec(currency_id, convert_id)
    assert price_api.api_id == CoinMarketCapApiSpecs.api_id

    http_response = get(
        url=api_specs["url"],
        params=api_specs["parameters"],
        headers=api_specs["headers"],
    )
    response = DummyMessage(http_response.content)
    observation = price_api.post_request_process(response)
    assert isinstance(observation, float)

    price_api.increment_retries()
    assert not price_api.is_retries_exceeded()


def test_price_api_exceptions():
    """Test excpetions in PriceApi."""

    with pytest.raises(ValueError):
        # raises ValueError("'source_id' is a mandatory configuration")
        PriceApi()

    with pytest.raises(ValueError):
        PriceApi(name="price_api", skill_context=SkillContext(), source_id="api")
