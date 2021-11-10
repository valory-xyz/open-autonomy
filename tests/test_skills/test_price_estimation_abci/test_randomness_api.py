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
from packages.valory.skills.price_estimation_abci.randomness_api import (
    CloudflareApiSpecs,
    ProtocolLabsOneApiSpecs,
    ProtocolLabsThreeApiSpecs,
    ProtocolLabsTwoApiSpecs,
    RandomnessApi,
    RandomnessApiSpecs,
)


class DummyMessage:
    """Dummy HttpMessage"""

    body: bytes

    def __init__(self, response: bytes) -> None:
        """Dummy HttpMessage"""
        self.body = response


class BaseApiSpecTest:
    """Base test class for ApiSpec class."""

    api: RandomnessApiSpecs

    def test_run(
        self,
    ) -> None:
        """Run tests."""
        specs = self.api.get_spec()
        assert all([key in specs for key in ["method", "url"]])
        http_response = get(url=specs["url"])
        response = DummyMessage(http_response.content)
        observation = self.api.process_response(cast(HttpMessage, response))
        assert isinstance(observation, dict)

        fake_response = DummyMessage(b"")
        fake_observation = self.api.process_response(cast(HttpMessage, fake_response))
        assert fake_observation is None


class TestCloudflareApiSpecs(BaseApiSpecTest):
    """Test CoinbaseApiSpecs class."""

    def setup(
        self,
    ) -> None:
        """Setup test."""
        self.api = CloudflareApiSpecs()


class TestProtocolLabsOneApiSpecs(BaseApiSpecTest):
    """Test ProtocolLabsOneApiSpecs class."""

    def setup(
        self,
    ) -> None:
        """Setup test."""
        self.api = ProtocolLabsOneApiSpecs()


class TestProtocolLabsTwoApiSpecs(BaseApiSpecTest):
    """Test ProtocolLabsTwoApiSpecs class."""

    def setup(
        self,
    ) -> None:
        """Setup test."""
        self.api = ProtocolLabsTwoApiSpecs()


class TestProtocolLabsThreeApiSpecs(BaseApiSpecTest):
    """Test ProtocolLabsThreeApiSpecs class."""

    def setup(
        self,
    ) -> None:
        """Setup test."""
        self.api = ProtocolLabsThreeApiSpecs()


def test_price_api() -> None:
    """Test `PriceApi` class."""

    api = CloudflareApiSpecs()

    randomness_api = RandomnessApi(
        name="price_api",
        skill_context=SkillContext(),
        source_id=CloudflareApiSpecs.api_id,
        retries=5,
    )
    api_specs = randomness_api.get_spec()

    assert api_specs == api.get_spec()
    assert randomness_api.api_id == CloudflareApiSpecs.api_id

    http_response = get(
        url=api_specs["url"],
    )
    response = DummyMessage(http_response.content)
    observation = randomness_api.process_response(cast(HttpMessage, response))
    assert isinstance(observation, dict)

    randomness_api.increment_retries()
    assert not randomness_api.is_retries_exceeded()

    for _ in range(5):
        randomness_api.increment_retries()
    assert randomness_api.is_retries_exceeded()


def test_randomness_api_exceptions() -> None:
    """Test excpetions in PriceApi."""

    with pytest.raises(ValueError, match="'source_id' is a mandatory configuration"):
        # raises ValueError("'source_id' is a mandatory configuration")
        RandomnessApi()

    with pytest.raises(ValueError, match="'api' is not a supported API identifier"):
        # raises ValueError("'api' is not a supported API identifier")
        RandomnessApi(name="price_api", skill_context=SkillContext(), source_id="api")
