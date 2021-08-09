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

"""This module contains the model to interact with crypto price API."""
import json
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Optional, Union

import requests
from aea.exceptions import AEAEnforceError
from aea.skills.base import Model
from pycoingecko import CoinGeckoAPI
from requests import Session
from requests.exceptions import (  # pylint: disable=redefined-builtin
    ConnectionError,
    Timeout,
    TooManyRedirects,
)


class Currency(Enum):
    """Enumeration of currencies (slug)."""

    BITCOIN = "BTC"
    USD = "USD"
    USDT = "USDT"

    @property
    def slug(self):  # type: ignore
        """To slug."""
        return {
            self.BITCOIN.value: "bitcoin",
            self.USD.value: "usd",
            self.USDT.value: "usdt",
        }[self.value]


CurrencyOrStr = Union[Currency, str]


class ApiWrapper(ABC):  # pylint: disable=too-few-public-methods
    """Wrap an API library to access cryptocurrencies' prices."""

    api_id: str

    def __init__(self, api_key: Optional[str] = None):
        """Initialize the API wrapper."""
        self.api_key = api_key if api_key is not None else ""

    @abstractmethod
    def get_price(
        self, currency_id: CurrencyOrStr, convert_id: CurrencyOrStr = Currency.USD
    ) -> Optional[float]:
        """Get the price of a cryptocurrency."""


class CoinMarketCapApiWrapper(ApiWrapper):  # pylint: disable=too-few-public-methods
    """Wrap the CoinMarketCap's APIs."""

    api_id = "coinmarketcap"
    _URL = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"

    def get_price(
        self, currency_id: CurrencyOrStr, convert_id: CurrencyOrStr = Currency.USD
    ) -> Optional[float]:
        """Get the price of a cryptocurrency."""
        currency_id, convert_id = Currency(currency_id), Currency(convert_id)
        url = self._URL
        parameters = {"symbol": currency_id.value, "convert": convert_id.value}
        headers = {
            "Accepts": "application/json",
            "X-CMC_PRO_API_KEY": self.api_key,
        }

        session = Session()
        session.headers.update(headers)

        try:
            response = session.get(url, params=parameters)
            data = json.loads(response.text)
            return data["data"][currency_id.value]["quote"][convert_id.value]["price"]
        except (ConnectionError, Timeout, TooManyRedirects, AEAEnforceError, KeyError):
            return None


class CoinGeckoApiWrapper(ApiWrapper):  # pylint: disable=too-few-public-methods
    """Wrap the CoinGecko's APIs."""

    api_id = "coingecko"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the object."""
        super().__init__(*args, **kwargs)
        self.api = CoinGeckoAPI()

    def get_price(
        self, currency_id: CurrencyOrStr, convert_id: CurrencyOrStr = Currency.USD
    ) -> Optional[float]:
        """Get the price of a cryptocurrency."""
        currency_id, convert_id = Currency(currency_id), Currency(convert_id)
        response = self.api.get_price(
            ids=currency_id.slug, vs_currencies=convert_id.slug
        )
        return float(response[currency_id.slug][convert_id.slug])


class BinanceApiWrapper(ApiWrapper):  # pylint: disable=too-few-public-methods
    """Wrap the Binance's APIs."""

    api_id = "binance"
    _URL = "https://api.binance.com/api/v3/ticker/price"

    def get_price(
        self, currency_id: CurrencyOrStr, convert_id: CurrencyOrStr = Currency.USD
    ) -> Optional[float]:
        """Get the price of a cryptocurrency."""
        currency_id, convert_id = Currency(currency_id), Currency(convert_id)
        url = self._URL
        parameters = {"symbol": currency_id.value + convert_id.value}
        try:
            response = requests.get(url, params=parameters)
            return float(response.json()["price"])
        except (ConnectionError, Timeout, TooManyRedirects, AEAEnforceError, KeyError):
            return None


class CoinbaseApiWrapper(ApiWrapper):  # pylint: disable=too-few-public-methods
    """Wrap the Coinbase's APIs."""

    api_id = "coinbase"
    _URL = "https://api.coinbase.com/v2/prices/{currency_id}-{convert_id}/buy"

    def get_price(
        self, currency_id: CurrencyOrStr, convert_id: CurrencyOrStr = Currency.USD
    ) -> Optional[float]:
        """Get the price of a cryptocurrency."""
        currency_id, convert_id = Currency(currency_id), Currency(convert_id)
        url = self._URL.format(
            currency_id=currency_id.value, convert_id=convert_id.value
        )
        try:
            response = requests.get(url)
            return float(response.json()["data"]["amount"])
        except (ConnectionError, Timeout, TooManyRedirects, AEAEnforceError):
            return None


class PriceApi(Model):
    """A model that wraps APIs to get cryptocurrency prices."""

    _api_id_to_cls = {
        CoinMarketCapApiWrapper.api_id: CoinMarketCapApiWrapper,
        CoinGeckoApiWrapper.api_id: CoinGeckoApiWrapper,
        BinanceApiWrapper.api_id: BinanceApiWrapper,
        CoinbaseApiWrapper.api_id: CoinbaseApiWrapper,
    }

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the price API model."""
        super().__init__(*args, **kwargs)

        self._source_id = kwargs.pop("source_id", None)
        if self._source_id is None:
            raise ValueError("'source_id' is a mandatory configuration")
        self._api_key = kwargs.pop("api_key", None)

        self._api = self._get_api()

    def _get_api(self) -> ApiWrapper:
        """Get the ApiWrapper object."""
        api_cls = self._api_id_to_cls.get(self._source_id)
        if api_cls is None:
            raise ValueError(f"'{self._source_id}' is not a supported API identifier")
        return api_cls(self._api_key)

    def get_price(
        self, currency_id: CurrencyOrStr, convert_id: CurrencyOrStr = Currency.USD
    ) -> Optional[float]:
        """Get the price of a cryptocurrency."""
        return self._api.get_price(currency_id, convert_id)
