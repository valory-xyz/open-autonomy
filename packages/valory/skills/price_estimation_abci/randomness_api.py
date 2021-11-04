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
from abc import ABC
from typing import Any, Dict, Optional

from aea.skills.base import Model

from packages.valory.protocols.http import HttpMessage


NUMBER_OF_RETRIES = 5


class RandomnessApiSpecs(ABC):  # pylint: disable=too-few-public-methods
    """Wrap an API library to access cryptocurrencies' prices."""

    api_id: str
    _URL: str
    _METHOD: str

    def __init__(self) -> None:
        """Initialize the API wrapper."""

    def get_spec(self) -> Dict:
        """Return API Specs for `coinmarket`"""
        return {
            "method": self._METHOD,
            "url": self._URL,
            "api_id": self.api_id,
        }

    def post_request_process(  # pylint: disable=no-self-use
        self, response: HttpMessage
    ) -> Optional[float]:
        """Process the response and return observed price."""
        try:
            result_ = json.loads(response.body.decode())
            return result_
        except (json.JSONDecodeError, KeyError):
            return None


class CloudflareApiSpecs(RandomnessApiSpecs):  # pylint: disable=too-few-public-methods
    """Contains specs for CoinMarketCap's APIs."""

    api_id = "cloudflare"
    _URL = "https://drand.cloudflare.com/public/latest"
    _METHOD = "GET"


class RandomnessApi(Model):
    """A model that wraps APIs to get cryptocurrency prices."""

    _api_id_to_cls = {
        CloudflareApiSpecs.api_id: CloudflareApiSpecs,
    }

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the price API model."""
        self._source_id = kwargs.pop("source_id", None)
        if self._source_id is None:
            raise ValueError("'source_id' is a mandatory configuration")
        self._retries = kwargs.pop("retries", NUMBER_OF_RETRIES)
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

    def _get_api(self) -> RandomnessApiSpecs:
        """Get the ApiSpecs object."""
        api_cls = self._api_id_to_cls.get(self._source_id)
        if api_cls is None:
            raise ValueError(f"'{self._source_id}' is not a supported API identifier")
        return api_cls()

    def get_spec(self) -> Dict:
        """Get the spec of the API"""
        return self._api.get_spec()

    def post_request_process(self, response: HttpMessage) -> Optional[float]:
        """Process the response and return observed price."""
        return self._api.post_request_process(response)
