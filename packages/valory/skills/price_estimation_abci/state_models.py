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

from typing import cast

from aea.exceptions import enforce

from packages.valory.skills.abstract_round_abci.models import Requests as BaseRequests
from packages.valory.skills.abstract_round_abci.models import (
    SharedState as BaseSharedState,
)
from packages.valory.skills.price_estimation_abci.models.rounds import PeriodState


class SharedState(BaseSharedState):
    """Shared state."""

    def setup(self) -> None:
        """Set up."""
        super().setup()
        consensus_params = self.context.params.consensus_params
        self.period.setup(consensus_params)

    @property
    def period_state(self) -> PeriodState:
        """Get the period state if available."""
        period_state = self.period.latest_result
        enforce(period_state is not None, "period state not available")
        return cast(PeriodState, period_state)


Requests = BaseRequests
