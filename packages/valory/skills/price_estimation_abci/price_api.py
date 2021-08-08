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

from aea.exceptions import AEAEnforceError
from aea.skills.base import Model
from pycoingecko import CoinGeckoAPI
from requests import Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects


class Currency(Enum):
    """Enumeration of currencies (slug)."""

    BITCOIN = "BTC"
    USD = "USD"

    @property
    def slug(self):
        """To slug."""
        return {"BTC": "bitcoin", "USD": "usd"}[self.value]


CurrencyOrStr = Union[Currency, str]


class ApiWrapper(ABC):
    """Wrap an API library to access cryptocurrencies' prices."""

    api_id: str

    def __init__(self, api_key: Optional[str] = None):
        """Initialize the API wrapper."""
        self.api_key = api_key

    @abstractmethod
    def get_price(
        self, currency_id: CurrencyOrStr, convert_id: CurrencyOrStr = Currency.USD
    ) -> Optional[float]:
        """Get the price of a cryptocurrency."""


class CoinMarketCapApiWrapper(ApiWrapper):
    """Wrap the CoinMarketCap's APIs."""

    api_id = "coinmarketcap"

    def get_price(
        self, currency_id: Currency, convert_id: CurrencyOrStr = Currency.USD
    ) -> Optional[float]:
        """Get the price of a cryptocurrency."""
        currency_id, convert_id = Currency(currency_id), Currency(convert_id)
        url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
        parameters = {"slug": currency_id.value, "convert": convert_id.value}
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
        except (ConnectionError, Timeout, TooManyRedirects, AEAEnforceError) as e:
            return None


class CoinGeckoApiWrapper(ApiWrapper):
    """Wrap the CoinGecko's APIs."""

    api_id = "coingecko"

    def __init__(self, **kwargs):
        """Initialize the object."""
        super().__init__(**kwargs)
        self.cg = CoinGeckoAPI()

    def get_price(
        self, currency_id: CurrencyOrStr, convert_id: CurrencyOrStr = Currency.USD
    ) -> Optional[float]:
        """Get the price of a cryptocurrency."""
        currency_id, convert_id = Currency(currency_id), Currency(convert_id)
        response = self.cg.get_price(
            ids=currency_id.slug, vs_currencies=convert_id.slug
        )
        return float(response[currency_id.slug][convert_id.slug])


class PriceApi(Model):
    """A model that wraps APIs to get cryptocurrency prices."""

    _api_id_to_cls = {
        CoinMarketCapApiWrapper.api_id: CoinMarketCapApiWrapper,
        CoinGeckoApiWrapper.api_id: CoinGeckoApiWrapper,
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
        if self._source_id == CoinMarketCapApiWrapper.api_id:
            return CoinMarketCapApiWrapper(self._api_key)
        if self._source_id == CoinGeckoApiWrapper.api_id:
            return CoinMarketCapApiWrapper(self._api_key)
        raise ValueError(f"'{self._source_id}' is not a supported API identifier")

    def get_price(
        self, currency_id: CurrencyOrStr, convert_id: CurrencyOrStr = Currency.USD
    ) -> Optional[float]:
        """Get the price of a cryptocurrency."""
        return self._api.get_price(currency_id, convert_id)
