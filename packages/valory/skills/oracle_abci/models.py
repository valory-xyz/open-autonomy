# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2022 Valory AG
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

from packages.valory.skills.abstract_round_abci.models import (
    BenchmarkTool as BaseBenchmarkTool,
)
from packages.valory.skills.abstract_round_abci.models import Requests as BaseRequests
from packages.valory.skills.abstract_round_abci.models import (
    SharedState as BaseSharedState,
)
from packages.valory.skills.oracle_abci.composition import OracleAbciApp
from packages.valory.skills.oracle_deployment_abci.rounds import Event as OracleEvent
from packages.valory.skills.price_estimation_abci.models import (
    Params as PriceEstimationParams,
)
from packages.valory.skills.price_estimation_abci.models import (
    PriceApi as PriceEstimationPriceApi,
)
from packages.valory.skills.price_estimation_abci.models import (
    RandomnessApi as PriceEstimationRandomnessApi,
)
from packages.valory.skills.price_estimation_abci.models import (
    ServerApi as PriceEstimationServerApi,
)
from packages.valory.skills.price_estimation_abci.rounds import Event
from packages.valory.skills.reset_pause_abci.rounds import Event as ResetPauseEvent
from packages.valory.skills.safe_deployment_abci.rounds import Event as SafeEvent
from packages.valory.skills.transaction_settlement_abci.rounds import Event as TSEvent


MARGIN = 5
MULTIPLIER = 2

Requests = BaseRequests
BenchmarkTool = BaseBenchmarkTool
Params = PriceEstimationParams
RandomnessApi = PriceEstimationRandomnessApi
PriceApi = PriceEstimationPriceApi
ServerApi = PriceEstimationServerApi


class SharedState(BaseSharedState):
    """Keep the current shared state of the skill."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the state."""
        super().__init__(*args, abci_app_cls=OracleAbciApp, **kwargs)

    def setup(self) -> None:
        """Set up."""
        super().setup()
        OracleAbciApp.event_to_timeout[
            Event.ROUND_TIMEOUT
        ] = self.context.params.round_timeout_seconds
        OracleAbciApp.event_to_timeout[
            SafeEvent.ROUND_TIMEOUT
        ] = self.context.params.round_timeout_seconds
        OracleAbciApp.event_to_timeout[
            OracleEvent.ROUND_TIMEOUT
        ] = self.context.params.round_timeout_seconds
        OracleAbciApp.event_to_timeout[
            TSEvent.ROUND_TIMEOUT
        ] = self.context.params.round_timeout_seconds
        OracleAbciApp.event_to_timeout[
            ResetPauseEvent.ROUND_TIMEOUT
        ] = self.context.params.round_timeout_seconds
        OracleAbciApp.event_to_timeout[TSEvent.RESET_TIMEOUT] = (
            self.context.params.round_timeout_seconds * MULTIPLIER
        )
        OracleAbciApp.event_to_timeout[
            SafeEvent.VALIDATE_TIMEOUT
        ] = self.context.params.validate_timeout
        OracleAbciApp.event_to_timeout[
            OracleEvent.VALIDATE_TIMEOUT
        ] = self.context.params.validate_timeout
        OracleAbciApp.event_to_timeout[
            TSEvent.VALIDATE_TIMEOUT
        ] = self.context.params.validate_timeout
        OracleAbciApp.event_to_timeout[
            TSEvent.FINALIZE_TIMEOUT
        ] = self.context.params.finalize_timeout
        OracleAbciApp.event_to_timeout[
            TSEvent.CHECK_TIMEOUT
        ] = self.context.params.history_check_timeout
        OracleAbciApp.event_to_timeout[OracleEvent.DEPLOY_TIMEOUT] = (
            self.context.params.keeper_timeout + MARGIN
        )
        OracleAbciApp.event_to_timeout[SafeEvent.DEPLOY_TIMEOUT] = (
            self.context.params.keeper_timeout + MARGIN
        )
        OracleAbciApp.event_to_timeout[ResetPauseEvent.RESET_AND_PAUSE_TIMEOUT] = (
            self.context.params.observation_interval + MARGIN
        )
