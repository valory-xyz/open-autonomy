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

"""Custom objects for the APY estimation ABCI application."""

from typing import Any

from packages.valory.skills.abstract_round_abci.models import (
    ApiSpecs,
    SharedState as BaseSharedState,
    Requests as BaseRequests,
)
from packages.valory.skills.apy_estimation.rounds import APYEstimationAbciApp
from packages.valory.skills.price_estimation_abci.rounds import Event
from packages.valory.skills.simple_abci.models import Params as BaseParams

Requests = BaseRequests

MARGIN = 5


class SharedState(BaseSharedState):
    """Keep the current shared state of the skill."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the state."""
        super().__init__(*args, abci_app_cls=APYEstimationAbciApp, **kwargs)

    def setup(self) -> None:
        """Set up."""
        super().setup()

        event_to_timeout_overrides = {
            Event.ROUND_TIMEOUT: self.context.params.round_timeout_seconds,
            Event.RESET_TIMEOUT: self.context.params.observation_interval + MARGIN,
        }

        for event, override in event_to_timeout_overrides.items():
            APYEstimationAbciApp.event_to_timeout[event] = override


class FantomSubgraph(ApiSpecs):
    """A model that wraps ApiSpecs for Fantom subgraph specifications."""


class SpookySwapSubgraph(ApiSpecs):
    """A model that wraps ApiSpecs for SpookySwap subgraph specifications."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize SpookySwapSubgraph."""
        self.bundle_id: int = self.ensure("bundle_id", kwargs)
        self.top_n_pools: int = self.ensure("top_n_pools", kwargs)
        super().__init__(*args, **kwargs)


class APYParams(BaseParams):
    """Parameters."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the parameters object."""
        self.history_duration = self._ensure("history_duration", kwargs)
        self.data_folder = self._ensure("data_folder", kwargs)
        self.optimizer_params = self._ensure("optimizer", kwargs)
        self.testing = self._ensure("testing", kwargs)
        super().__init__(*args, **kwargs)
