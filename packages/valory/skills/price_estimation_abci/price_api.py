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
from enum import Enum
from typing import Any, Dict, Optional, Union

from packages.valory.protocols.http import HttpMessage
from packages.valory.skills.abstract_round_abci.models import ApiSpecs, ApiSpecsModel


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


class PriceApiSpecs(ApiSpecs):  # pylint: disable=too-few-public-methods
    """Wrap an API library to access cryptocurrencies' prices."""

    currency_id: Currency
    convert_id: Currency

    def __init__(
        self,
        currency_id: CurrencyOrStr,
        convert_id: CurrencyOrStr = Currency.USD,
        api_key: Optional[str] = None,
    ):
        """Initialize the API wrapper."""
        self.api_key = api_key if api_key is not None else ""
        self.currency_id = Currency(currency_id)
        self.convert_id = Currency(convert_id)


class CoinMarketCapPriceApiSpecs(
    PriceApiSpecs
):  # pylint: disable=too-few-public-methods
    """Contains specs for CoinMarketCap's APIs."""

    api_id = "coinmarketcap"
    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
    method = "GET"

    def get_spec(
        self,
    ) -> Dict:
        """Return API Specs for `coinmarket`"""
        self.headers = [
            ("Accepts", "application/json"),
            ("X-CMC_PRO_API_KEY", self.api_key),
        ]
        self.parameters = [
            ("symbol", self.currency_id.value),
            ("convert", self.convert_id.value),
        ]
        return super().get_spec()

    def process_response(self, response: HttpMessage) -> Optional[float]:
        """Process the response and return observed price."""
        response_ = self._load_json(response)
        if response_ is not None:
            return response_["data"][self.currency_id.value]["quote"][
                self.convert_id.value
            ]["price"]
        return None


class CoinGeckoPriceApiSpecs(PriceApiSpecs):  # pylint: disable=too-few-public-methods
    """Contains specs for CoinGecko's APIs."""

    api_id = "coingecko"
    url = "https://api.coingecko.com/api/v3/simple/price"
    method = "GET"

    def get_spec(
        self,
    ) -> Dict:
        """Return API Specs for `coingecko`"""
        self.parameters = [
            ("ids", self.currency_id.slug),
            ("vs_currencies", self.convert_id.slug),
        ]
        return super().get_spec()

    def process_response(self, response: HttpMessage) -> Optional[float]:
        """Process the response and return observed price."""
        response_ = self._load_json(response)
        if response_ is not None:
            return float(response_[self.currency_id.slug][self.convert_id.slug])
        return None


class BinancePriceApiSpecs(PriceApiSpecs):  # pylint: disable=too-few-public-methods
    """Contains specs for Binance's APIs."""

    api_id = "binance"
    url = "https://api.binance.com/api/v3/ticker/price"
    method = "GET"

    def get_spec(
        self,
    ) -> Dict:
        """Return API Specs for `binance`"""
        self.parameters = [
            ("symbol", self.currency_id.value + self.convert_id.value),
        ]
        return super().get_spec()

    def process_response(self, response: HttpMessage) -> Optional[float]:
        """Process the response and return observed price."""
        response_ = self._load_json(response)
        if response_ is not None:
            return float(response_["price"])
        return None


class CoinbasePriceApiSpecs(PriceApiSpecs):  # pylint: disable=too-few-public-methods
    """Contains specs for Coinbase's APIs."""

    api_id = "coinbase"
    url = "https://api.coinbase.com/v2/prices/{currency_id}-{convert_id}/buy"
    method = "GET"

    def get_spec(
        self,
    ) -> Dict:
        """Return API Specs for `coinbase`"""
        self.url = self.url.format(
            currency_id=self.currency_id.value, convert_id=self.convert_id.value
        )
        return super().get_spec()

    def process_response(self, response: HttpMessage) -> Optional[float]:
        """Process the response and return observed price."""
        response_ = self._load_json(response)
        if response_ is not None:
            return float(response_["data"]["amount"])

        return None


class PriceApi(ApiSpecsModel):
    """A model that wraps APIs to get cryptocurrency prices."""

    _api_id_to_cls = {
        CoinMarketCapPriceApiSpecs.api_id: CoinMarketCapPriceApiSpecs,
        CoinGeckoPriceApiSpecs.api_id: CoinGeckoPriceApiSpecs,
        BinancePriceApiSpecs.api_id: BinancePriceApiSpecs,
        CoinbasePriceApiSpecs.api_id: CoinbasePriceApiSpecs,
    }

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the price API model."""
        _currency_id: Optional[CurrencyOrStr] = kwargs.pop("currency_id", None)
        if _currency_id is None:
            raise ValueError("'currency_id' is a mandatory configuration")
        self._currency_id = _currency_id
        self.convert_id: CurrencyOrStr = kwargs.pop("convert_id", Currency.USD)
        self._source_id = kwargs.pop("source_id", None)
        if self._source_id is None:
            raise ValueError("'source_id' is a mandatory configuration")
        self._api_key = kwargs.pop("api_key", None)
        self._api = self._get_api()
        super().__init__(*args, **kwargs)

    @property
    def currency_id(self) -> CurrencyOrStr:
        """Get currency id."""
        return self._currency_id

    def _get_api(self) -> PriceApiSpecs:
        """Get the ApiSpecs object."""
        api_cls = self._api_id_to_cls.get(self._source_id)
        if api_cls is None:
            raise ValueError(f"'{self._source_id}' is not a supported API identifier")
        return api_cls(
            currency_id=self._currency_id,
            convert_id=self.convert_id,
            api_key=self._api_key,
        )
