# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2023 Valory AG
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

"""This module contains the shared state for the offend_abci skill."""

from typing import Any

from packages.valory.skills.abstract_round_abci.models import BaseParams
from packages.valory.skills.abstract_round_abci.models import (
    BenchmarkTool as BaseBenchmarkTool,
)
from packages.valory.skills.abstract_round_abci.models import Requests as BaseRequests
from packages.valory.skills.abstract_round_abci.models import (
    SharedState as BaseSharedState,
)
from packages.valory.skills.offend_abci.rounds import Event, OffendAbciApp


Requests = BaseRequests
BenchmarkTool = BaseBenchmarkTool


class SharedState(BaseSharedState):
    """Keep the current shared state of the skill."""

    abci_app_cls = OffendAbciApp

    def setup(self) -> None:
        """Set up."""
        super().setup()
        OffendAbciApp.event_to_timeout[
            Event.ROUND_TIMEOUT
        ] = self.context.params.round_timeout_seconds


class OffendParams(BaseParams):
    """Offend skill's parameters."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the parameters."""
        self.validator_downtime: bool = self._ensure("validator_downtime", kwargs, bool)
        self.invalid_payload: bool = self._ensure("invalid_payload", kwargs, bool)
        self.blacklisted: bool = self._ensure("blacklisted", kwargs, bool)
        self.suspected: bool = self._ensure("suspected", kwargs, bool)
        self.num_unknown: int = self._ensure("num_unknown", kwargs, int)
        self.num_double_signed: int = self._ensure("num_double_signed", kwargs, int)
        self.num_light_client_attack: int = self._ensure(
            "num_light_client_attack", kwargs, int
        )
        super().__init__(*args, **kwargs)
