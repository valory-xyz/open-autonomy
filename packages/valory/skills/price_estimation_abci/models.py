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

"""This module contains the shared state for the price estimation ABCI application."""

from typing import Any

from packages.valory.skills.abstract_round_abci.models import ApiSpecs, BaseParams
from packages.valory.skills.abstract_round_abci.models import Requests as BaseRequests
from packages.valory.skills.abstract_round_abci.models import (
    SharedState as BaseSharedState,
)
from packages.valory.skills.price_estimation_abci.rounds import (
    Event,
    PriceEstimationAbciApp,
)


MARGIN = 5
MULTIPLIER = 2


Requests = BaseRequests


class SharedState(BaseSharedState):
    """Keep the current shared state of the skill."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the state."""
        super().__init__(*args, abci_app_cls=PriceEstimationAbciApp, **kwargs)

    def setup(self) -> None:
        """Set up."""
        super().setup()
        PriceEstimationAbciApp.event_to_timeout[
            Event.ROUND_TIMEOUT
        ] = self.context.params.round_timeout_seconds
        PriceEstimationAbciApp.event_to_timeout[Event.RESET_TIMEOUT] = (
            self.context.params.round_timeout_seconds * MULTIPLIER
        )
        PriceEstimationAbciApp.event_to_timeout[Event.VALIDATE_TIMEOUT] = (
            self.context.params.retry_timeout * self.context.params.retry_attempts
            + MARGIN
        )
        PriceEstimationAbciApp.event_to_timeout[Event.DEPLOY_TIMEOUT] = (
            self.context.params.retry_timeout * self.context.params.retry_attempts
            + MARGIN
        )
        PriceEstimationAbciApp.event_to_timeout[Event.RESET_AND_PAUSE_TIMEOUT] = (
            self.context.params.observation_interval + MARGIN
        )


class Params(BaseParams):
    """Parameters."""

    observation_interval: float

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the parameters object."""
        self.max_healthcheck = self._ensure("max_healthcheck", kwargs)
        self.round_timeout_seconds = self._ensure("round_timeout_seconds", kwargs)
        self.sleep_time = self._ensure("sleep_time", kwargs)
        self.retry_timeout = self._ensure("retry_timeout", kwargs)
        self.retry_attempts = self._ensure("retry_attempts", kwargs)
        self.observation_interval = self._ensure("observation_interval", kwargs)
        self.oracle_params = self._ensure("oracle", kwargs)
        self.drand_public_key = self._ensure("drand_public_key", kwargs)
        super().__init__(*args, **kwargs)


class RandomnessApi(ApiSpecs):
    """A model that wraps ApiSpecs for randomness api specifications."""


class PriceApi(ApiSpecs):
    """A model that wraps ApiSpecs for various cryptocurrency price api specifications."""

    convert_id: str
    currency_id: str

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize PriceApi."""
        self.convert_id = self.ensure("convert_id", kwargs)
        self.currency_id = self.ensure("currency_id", kwargs)
        super().__init__(*args, **kwargs)
