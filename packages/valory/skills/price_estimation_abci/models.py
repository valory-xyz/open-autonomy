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

"""This module contains the shared state for the price estimation app ABCI application."""

from typing import Any

from packages.valory.skills.abstract_round_abci.models import ApiSpecs
from packages.valory.skills.abstract_round_abci.models import Requests as BaseRequests
from packages.valory.skills.abstract_round_abci.models import (
    SharedState as BaseSharedState,
)
from packages.valory.skills.oracle_deployment_abci.models import Params as BaseParams
from packages.valory.skills.oracle_deployment_abci.rounds import Event as OracleEvent
from packages.valory.skills.price_estimation_abci.composition import (
    PriceEstimationAbciApp,
)
from packages.valory.skills.price_estimation_abci.rounds import Event
from packages.valory.skills.safe_deployment_abci.rounds import Event as SafeEvent
from packages.valory.skills.transaction_settlement_abci.rounds import Event as TSEvent


MARGIN = 5
MULTIPLIER = 2

Requests = BaseRequests


class Params(BaseParams):
    """Parameters."""

    observation_aggregator_function: str

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the parameters object."""
        self.observation_aggregator_function = self._ensure(
            "observation_aggregator_function", kwargs
        )
        super().__init__(*args, **kwargs)


class SharedState(BaseSharedState):
    """Keep the current shared state of the skill."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the state."""
        super().__init__(*args, abci_app_cls=PriceEstimationAbciApp, **kwargs)

    def setup(self) -> None:
        """Set up shared state and timeouts for events"""
        super().setup()

        event_to_timeout = PriceEstimationAbciApp.event_to_timeout

        round_timeout_seconds = self.context.params.round_timeout_seconds
        for timeout in (
            Event.ROUND_TIMEOUT,
            SafeEvent.ROUND_TIMEOUT,
            OracleEvent.ROUND_TIMEOUT,
            TSEvent.ROUND_TIMEOUT,
        ):
            event_to_timeout[timeout] = round_timeout_seconds

        retry_attempts = self.context.params.retry_attempts
        retry_timeout = self.context.params.retry_timeout
        retry_time_allowed = retry_timeout * retry_attempts + MARGIN
        for timeout_with_retry in (
            SafeEvent.VALIDATE_TIMEOUT,
            OracleEvent.VALIDATE_TIMEOUT,
            TSEvent.VALIDATE_TIMEOUT,
            OracleEvent.DEPLOY_TIMEOUT,
            SafeEvent.DEPLOY_TIMEOUT,
        ):
            event_to_timeout[timeout_with_retry] = retry_time_allowed

        reset_timeout = round_timeout_seconds * MULTIPLIER
        event_to_timeout[TSEvent.RESET_TIMEOUT] = reset_timeout

        event_to_timeout[TSEvent.RESET_AND_PAUSE_TIMEOUT] = (
            self.context.params.observation_interval + MARGIN
        )


class RandomnessApi(ApiSpecs):
    """A model that wraps ApiSpecs for randomness api specifications."""


class PriceApi(ApiSpecs):
    """A model that wraps ApiSpecs for various cryptocurrency price api specifications.

    currency_id: currency id to be converted
    convert_id: target currency id
    """

    currency_id: str
    convert_id: str

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize PriceApi."""
        self.convert_id = self.ensure("convert_id", kwargs)
        self.currency_id = self.ensure("currency_id", kwargs)
        super().__init__(*args, **kwargs)
