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
from typing import Dict, Optional

from packages.valory.protocols.http.message import HttpMessage
from packages.valory.skills.abstract_round_abci.models import ApiSpecs, ApiSpecsModel


class RandomnessApiSpecs(ApiSpecs):
    """Randomness API specs."""

    def process_response(self, response: HttpMessage) -> Optional[Dict]:
        """Process response"""
        return self._load_json(response)


class CloudflareApiSpecs(RandomnessApiSpecs):  # pylint: disable=too-few-public-methods
    """Contains specs for CoinMarketCap's APIs."""

    api_id = "cloudflare"
    url = "https://drand.cloudflare.com/public/latest"
    method = "GET"


class ProtocolLabsOneApiSpecs(
    RandomnessApiSpecs
):  # pylint: disable=too-few-public-methods
    """Contains specs for CoinMarketCap's APIs."""

    api_id = "protocollabs1"
    url = "https://api.drand.sh/public/latest"
    method = "GET"


class ProtocolLabsTwoApiSpecs(
    RandomnessApiSpecs
):  # pylint: disable=too-few-public-methods
    """Contains specs for CoinMarketCap's APIs."""

    api_id = "protocollabs2"
    url = "https://api2.drand.sh/public/latest"
    method = "GET"


class ProtocolLabsThreeApiSpecs(
    RandomnessApiSpecs
):  # pylint: disable=too-few-public-methods
    """Contains specs for CoinMarketCap's APIs."""

    api_id = "protocollabs3"
    url = "https://api3.drand.sh/public/latest"
    method = "GET"


class RandomnessApi(ApiSpecsModel):
    """A model that wraps APIs to get cryptocurrency prices."""

    _api_id_to_cls = {
        CloudflareApiSpecs.api_id: CloudflareApiSpecs,
        ProtocolLabsOneApiSpecs.api_id: ProtocolLabsOneApiSpecs,
        ProtocolLabsTwoApiSpecs.api_id: ProtocolLabsTwoApiSpecs,
        ProtocolLabsThreeApiSpecs.api_id: ProtocolLabsThreeApiSpecs,
    }
