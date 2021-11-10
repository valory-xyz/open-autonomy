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

from typing import cast

import pytest
from aea.skills.base import SkillContext
from requests import get

from packages.valory.protocols.http import HttpMessage
from packages.valory.skills.price_estimation_abci.price_api import (
    ApiSpecs,
    BinancePriceApiSpecs,
    CoinGeckoPriceApiSpecs,
    CoinMarketCapPriceApiSpecs,
    CoinbasePriceApiSpecs,
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
    ) -> None:
        """Run tests."""
        specs = self.api.get_spec()
        assert all(
            [
                key in specs
                for key in ["method", "url", "api_id", "headers", "parameters"]
            ]
        )
        http_response = get(
            url=specs["url"],
            params=dict(specs["parameters"]),
            headers=dict(specs["headers"]),
        )
        response = DummyMessage(http_response.content)
        observation = self.api.process_response(cast(HttpMessage, response))
        assert isinstance(observation, float)

        fake_response = DummyMessage(b"")
        fake_observation = self.api.process_response(cast(HttpMessage, fake_response))
        assert fake_observation is None


class TestCoinbaseApiSpecs(BaseApiSpecTest):
    """Test CoinbaseApiSpecs class."""

    def setup(
        self,
    ) -> None:
        """Setup test."""
        self.api = CoinbasePriceApiSpecs(currency_id=Currency.BITCOIN)


class TestCoinGeckoApiSpecs(BaseApiSpecTest):
    """Test CoinGeckoApiSpecs class."""

    def setup(
        self,
    ) -> None:
        """Setup test."""
        self.api = CoinGeckoPriceApiSpecs(currency_id=Currency.BITCOIN)


class TestCoinMarketCapApiSpecs(BaseApiSpecTest):
    """Test CoinMarketCapApiSpecs class."""

    def setup(
        self,
    ) -> None:
        """Setup test."""
        self.api = CoinMarketCapPriceApiSpecs(
            currency_id=Currency.BITCOIN, api_key=COINMARKETCAP_API_KEY
        )


class TestBinanceApiSpecs(BaseApiSpecTest):
    """Test BinanceApiSpecs class."""

    def setup(
        self,
    ) -> None:
        """Setup test."""
        self.convert_id = Currency.USDT
        self.api = BinancePriceApiSpecs(
            currency_id=Currency.BITCOIN, convert_id=self.convert_id
        )


def test_price_api() -> None:
    """Test `PriceApi` class."""

    api = CoinMarketCapPriceApiSpecs(
        currency_id=Currency.BITCOIN, api_key=COINMARKETCAP_API_KEY
    )
    currency_id = Currency.BITCOIN
    convert_id = Currency.USD

    price_api = PriceApi(
        name="price_api",
        skill_context=SkillContext(),
        source_id=CoinMarketCapPriceApiSpecs.api_id,
        retries=5,
        api_key=COINMARKETCAP_API_KEY,
        currency_id=currency_id,
        convert_id=convert_id,
    )
    api_specs = price_api.get_spec()

    assert api_specs == api.get_spec()
    assert price_api.api_id == CoinMarketCapPriceApiSpecs.api_id
    assert price_api.currency_id == currency_id

    http_response = get(
        url=api_specs["url"],
        params=dict(api_specs["parameters"]),
        headers=dict(api_specs["headers"]),
    )
    response = DummyMessage(http_response.content)
    observation = price_api.process_response(cast(HttpMessage, response))
    assert isinstance(observation, float)

    price_api.increment_retries()
    assert not price_api.is_retries_exceeded()

    for _ in range(5):
        price_api.increment_retries()
    assert price_api.is_retries_exceeded()


def test_price_api_exceptions() -> None:
    """Test excpetions in PriceApi."""

    with pytest.raises(ValueError, match="'currency_id' is a mandatory configuration"):
        # raises ValueError("'source_id' is a mandatory configuration")
        PriceApi()

    with pytest.raises(ValueError, match="'source_id' is a mandatory configuration"):
        # raises ValueError("'source_id' is a mandatory configuration")
        PriceApi(currency_id="BTC")

    with pytest.raises(ValueError, match="'api' is not a supported API identifier"):
        # raises ValueError("'api' is not a supported API identifier")
        PriceApi(
            name="price_api",
            skill_context=SkillContext(),
            source_id="api",
            currency_id="BTC",
        )
