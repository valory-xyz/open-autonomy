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

"""Custom objects for the transaction settlement ABCI application."""

from typing import Any, Dict, List, Optional

from web3.types import Nonce, Wei

from packages.valory.protocols.contract_api import ContractApiMessage
from packages.valory.skills.abstract_round_abci.models import ApiSpecs, BaseParams
from packages.valory.skills.abstract_round_abci.models import (
    BenchmarkTool as BaseBenchmarkTool,
)
from packages.valory.skills.abstract_round_abci.models import Requests as BaseRequests
from packages.valory.skills.abstract_round_abci.models import (
    SharedState as BaseSharedState,
)
from packages.valory.skills.transaction_settlement_abci.rounds import (
    TransactionSubmissionAbciApp,
)


BenchmarkTool = BaseBenchmarkTool


class SharedState(BaseSharedState):
    """Keep the current shared state of the skill."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the state."""
        super().__init__(*args, abci_app_cls=TransactionSubmissionAbciApp, **kwargs)


class TransactionParams(BaseParams):  # pylint: disable=too-many-instance-attributes
    """Transaction settlement agent-specific parameters."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Initialize the parameters object.

        We keep track of the nonce and tip across rounds and periods.
        We reuse it each time a new raw transaction is generated. If
        at the time of the new raw transaction being generated the nonce
        on the ledger does not match the nonce on the skill, then we ignore
        the skill nonce and tip (effectively we price fresh). Otherwise, we
        are in a re-submission scenario where we need to take account of the
        old tip.

        :param args: positional arguments
        :param kwargs: keyword arguments
        """
        self.tx_hash: str = ""
        self.nonce: Optional[Nonce] = None
        self.gas_price: Optional[Dict[str, Wei]] = None
        self.fallback_gas: int = 0
        self.late_messages: List[ContractApiMessage] = []
        self.keeper_allowed_retries: int = self._ensure(
            "keeper_allowed_retries", kwargs
        )
        self.validate_timeout = self._ensure("validate_timeout", kwargs)
        self.finalize_timeout = self._ensure("finalize_timeout", kwargs)
        self.history_check_timeout = self._ensure("history_check_timeout", kwargs)
        super().__init__(*args, **kwargs)


class RandomnessApi(ApiSpecs):
    """A model that wraps ApiSpecs for randomness api specifications."""


Requests = BaseRequests
