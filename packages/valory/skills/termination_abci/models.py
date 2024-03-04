# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022-2024 Valory AG
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

"""This module contains the shared state for TerminationAbci."""

from typing import Any

from packages.valory.skills.abstract_round_abci.models import (
    BenchmarkTool as BaseBenchmarkTool,
)
from packages.valory.skills.abstract_round_abci.models import Requests as BaseRequests
from packages.valory.skills.abstract_round_abci.models import (
    SharedState as BaseSharedState,
)
from packages.valory.skills.termination_abci.rounds import TerminationAbciApp
from packages.valory.skills.transaction_settlement_abci.models import (
    RandomnessApi as TransactionSettlementRandomness,
)
from packages.valory.skills.transaction_settlement_abci.models import TransactionParams


class SharedState(BaseSharedState):
    """Keep the current shared state of the skill."""

    abci_app_cls = TerminationAbciApp


class TerminationParams(TransactionParams):
    """Defines the class to hold the termination parameters."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Set up the termination parameters."""
        self.termination_sleep: int = self._ensure("termination_sleep", kwargs, int)
        self.multisend_address: str = self._ensure("multisend_address", kwargs, str)
        self.termination_from_block: int = self._ensure(
            "termination_from_block", kwargs, int
        )
        super().__init__(*args, **kwargs)


Requests = BaseRequests
BenchmarkTool = BaseBenchmarkTool
RandomnessApi = TransactionSettlementRandomness
