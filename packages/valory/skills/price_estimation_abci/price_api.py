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
from typing import Any, Dict, Optional, Union

from aea.skills.base import Model

from packages.valory.protocols.http import HttpMessage


NUMBER_OF_RETRIES = 5


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


class ApiSpecs(ABC):  # pylint: disable=too-few-public-methods
    """Wrap an API library to access cryptocurrencies' prices."""

    api_id: str
    currency_id: Currency
    convert_id: Currency

    def __init__(self, api_key: Optional[str] = None):
        """Initialize the API wrapper."""
        self.api_key = api_key if api_key is not None else ""

    @abstractmethod
    def get_spec(
        self, currency_id: CurrencyOrStr, convert_id: CurrencyOrStr = Currency.USD
    ) -> Dict:
        """Return API Specs for `currency_id`"""

    @abstractmethod
    def post_request_process(self, response: HttpMessage) -> Optional[float]:
        """Process the response and return observed price."""


class CoinMarketCapApiSpecs(ApiSpecs):  # pylint: disable=too-few-public-methods
    """Contains specs for CoinMarketCap's APIs."""

    api_id = "coinmarketcap"
    _URL = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
    _METHOD = "GET"

    def get_spec(
        self, currency_id: CurrencyOrStr, convert_id: CurrencyOrStr = Currency.USD
    ) -> Dict:
        """Return API Specs for `coinmarket`"""
        self.currency_id, self.convert_id = Currency(currency_id), Currency(convert_id)
        return {
            "method": self._METHOD,
            "url": self._URL,
            "api_id": self.api_id,
            "headers": {
                "Accepts": "application/json",
                "X-CMC_PRO_API_KEY": self.api_key,
            },
            "parameters": {
                "symbol": self.currency_id.value,
                "convert": self.convert_id.value,
            },
        }

    def post_request_process(self, response: HttpMessage) -> Optional[float]:
        """Process the response and return observed price."""
        try:
            response_ = json.loads(response.body.decode())
            return response_["data"][self.currency_id.value]["quote"][
                self.convert_id.value
            ]["price"]
        except (json.JSONDecodeError, KeyError):
            return None


class CoinGeckoApiSpecs(ApiSpecs):  # pylint: disable=too-few-public-methods
    """Contains specs for CoinGecko's APIs."""

    api_id = "coingecko"
    _URL = "https://api.coingecko.com/api/v3/simple/price"
    _METHOD = "GET"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the object."""
        super().__init__(*args, **kwargs)

    def get_spec(
        self, currency_id: CurrencyOrStr, convert_id: CurrencyOrStr = Currency.USD
    ) -> Dict:
        """Return API Specs for `coingecko`"""
        self.currency_id, self.convert_id = Currency(currency_id), Currency(convert_id)
        return {
            "method": self._METHOD,
            "url": self._URL,
            "api_id": self.api_id,
            "headers": {},
            "parameters": {
                "ids": self.currency_id.slug,
                "vs_currencies": self.convert_id.slug,
            },
        }

    def post_request_process(self, response: HttpMessage) -> Optional[float]:
        """Process the response and return observed price."""
        try:
            response_ = json.loads(response.body.decode())
            return float(response_[self.currency_id.slug][self.convert_id.slug])
        except (json.JSONDecodeError, KeyError):
            return None


class BinanceApiSpecs(ApiSpecs):  # pylint: disable=too-few-public-methods
    """Contains specs for Binance's APIs."""

    api_id = "binance"
    _URL = "https://api.binance.com/api/v3/ticker/price"
    _METHOD = "GET"

    def get_spec(
        self, currency_id: CurrencyOrStr, convert_id: CurrencyOrStr = Currency.USD
    ) -> Dict:
        """Return API Specs for `binance`"""
        self.currency_id, self.convert_id = Currency(currency_id), Currency(convert_id)
        return {
            "method": self._METHOD,
            "url": self._URL,
            "api_id": self.api_id,
            "headers": {},
            "parameters": {"symbol": self.currency_id.value + self.convert_id.value},
        }

    def post_request_process(self, response: HttpMessage) -> Optional[float]:
        """Process the response and return observed price."""
        try:
            response_ = json.loads(response.body.decode())
            return float(response_["price"])
        except (json.JSONDecodeError, KeyError):
            return None


class CoinbaseApiSpecs(ApiSpecs):  # pylint: disable=too-few-public-methods
    """Contains specs for Coinbase's APIs."""

    api_id = "coinbase"
    _URL = "https://api.coinbase.com/v2/prices/{currency_id}-{convert_id}/buy"
    _METHOD = "GET"

    def get_spec(
        self, currency_id: CurrencyOrStr, convert_id: CurrencyOrStr = Currency.USD
    ) -> Dict:
        """Return API Specs for `coinbase`"""
        self.currency_id, self.convert_id = Currency(currency_id), Currency(convert_id)
        return {
            "method": self._METHOD,
            "url": self._URL.format(
                currency_id=self.currency_id.value, convert_id=self.convert_id.value
            ),
            "api_id": self.api_id,
            "headers": {},
            "parameters": {},
        }

    def post_request_process(self, response: HttpMessage) -> Optional[float]:
        """Process the response and return observed price."""
        try:
            response_ = json.loads(response.body.decode())
            return float(response_["data"]["amount"])
        except (json.JSONDecodeError, KeyError):
            return None


class PriceApi(Model):
    """A model that wraps APIs to get cryptocurrency prices."""

    _api_id_to_cls = {
        CoinMarketCapApiSpecs.api_id: CoinMarketCapApiSpecs,
        CoinGeckoApiSpecs.api_id: CoinGeckoApiSpecs,
        BinanceApiSpecs.api_id: BinanceApiSpecs,
        CoinbaseApiSpecs.api_id: CoinbaseApiSpecs,
    }

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the price API model."""
        self._source_id = kwargs.pop("source_id", None)
        if self._source_id is None:
            raise ValueError("'source_id' is a mandatory configuration")
        self._retries = kwargs.pop("retries", NUMBER_OF_RETRIES)
        self._api_key = kwargs.pop("api_key", None)
        self._api = self._get_api()
        super().__init__(*args, **kwargs)
        self._retries_attempted = 0

    @property
    def api_id(self) -> str:
        """Get API id."""
        return self._api.api_id

    def increment_retries(self) -> None:
        """Increment the retries counter."""
        self._retries_attempted += 1

    def is_retries_exceeded(self) -> bool:
        """Check if the retries amount has been exceeded."""
        return self._retries_attempted > self._retries

    def _get_api(self) -> ApiSpecs:
        """Get the ApiSpecs object."""
        api_cls = self._api_id_to_cls.get(self._source_id)
        if api_cls is None:
            raise ValueError(f"'{self._source_id}' is not a supported API identifier")
        return api_cls(self._api_key)

    def get_spec(
        self, currency_id: CurrencyOrStr, convert_id: CurrencyOrStr = Currency.USD
    ) -> Dict:
        """Get the spec of the API"""
        return self._api.get_spec(currency_id, convert_id)

    def post_request_process(self, response: HttpMessage) -> Optional[float]:
        """Process the response and return observed price."""
        return self._api.post_request_process(response)
