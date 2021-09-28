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
from typing import Any, Dict

from packages.valory.skills.abstract_round_abci.models import Requests as BaseRequests
from packages.valory.skills.abstract_round_abci.models import (
    SharedState as BaseSharedState,
)
from packages.valory.skills.price_estimation_abci.rounds import RegistrationRound


Requests = BaseRequests


class SharedState(BaseSharedState):
    """Keep the current shared state of the skill."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the state."""
        super().__init__(*args, initial_round_cls=RegistrationRound, **kwargs)
        self._state_start_times: Dict[str, datetime] = {
            "deploy_safe": datetime.min,
            "finalize": datetime.min,
        }

    def reset_state_time(self, state_id: str) -> None:
        """Set the state start time to the current time."""
        self._state_start_times[state_id] = datetime.now()

    def has_keeper_timed_out(self, state_id: str) -> bool:
        """Check if the keeper has timed out."""
        return (
            self._state_start_times[state_id] != datetime.min
            and (datetime.now() - self._state_start_times[state_id]).seconds
            >= self.context.params.keeper_timeout_seconds
        )
