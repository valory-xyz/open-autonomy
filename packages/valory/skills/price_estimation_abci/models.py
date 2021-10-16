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

from datetime import datetime
from typing import Any, Dict, Optional

from packages.valory.skills.abstract_round_abci.models import BaseParams
from packages.valory.skills.abstract_round_abci.models import Requests as BaseRequests
from packages.valory.skills.abstract_round_abci.models import (
    SharedState as BaseSharedState,
)
from packages.valory.skills.price_estimation_abci.rounds import (
    PriceEstimationAbciApp,
    RegistrationRound,
)


Requests = BaseRequests


class SharedState(BaseSharedState):
    """Keep the current shared state of the skill."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the state."""
        super().__init__(*args, abci_app_cls=PriceEstimationAbciApp, **kwargs)
        self._state_start_times: Dict[str, Optional[datetime]] = {
            "deploy_safe": None,
            "finalize": None,
        }

    def reset_state_time(self, state_id: str) -> None:
        """Reset the state start time to the current time."""
        self._state_start_times[state_id] = None

    def set_state_time(self, state_id: str) -> None:
        """Set the state start time to the current time."""
        if self._state_start_times[state_id] is None:
            self._state_start_times[state_id] = datetime.now()

    def has_keeper_timed_out(self, state_id: str) -> bool:
        """Check if the keeper has timed out."""
        time = self._state_start_times[state_id]
        return time is not None and (
            (datetime.now() - time).seconds
            >= self.context.params.keeper_timeout_seconds
        )


class Params(BaseParams):
    """Parameters."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the parameters object."""
        self.currency_id = self._ensure("currency_id", kwargs)
        self.convert_id = self._ensure("convert_id", kwargs)
        self._max_healthcheck = self._ensure("max_healthcheck", kwargs)
        self.keeper_timeout_seconds = self._ensure("keeper_timeout_seconds", kwargs)
        super().__init__(*args, **kwargs)
        self._count_healthcheck = 0

    def is_health_check_timed_out(self) -> bool:
        """Check if the healthcheck has timed out."""
        self._count_healthcheck += 1
        return self._count_healthcheck > self._max_healthcheck

    def increment_retries(self) -> None:
        """Increment the retries counter."""
        self._count_healthcheck += 1
