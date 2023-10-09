# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2023 Valory AG
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
from dataclasses import dataclass, field
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
from packages.valory.skills.abstract_round_abci.models import TypeCheckMixin
from packages.valory.skills.transaction_settlement_abci.rounds import (
    TransactionSubmissionAbciApp,
)


_MINIMUM_VALIDATE_TIMEOUT = 300  # 5 minutes
BenchmarkTool = BaseBenchmarkTool


class SharedState(BaseSharedState):
    """Keep the current shared state of the skill."""

    abci_app_cls = TransactionSubmissionAbciApp


@dataclass
class MutableParams(TypeCheckMixin):
    """Collection for the mutable parameters."""

    fallback_gas: int
    tx_hash: str = ""
    nonce: Optional[Nonce] = None
    gas_price: Optional[Dict[str, Wei]] = None
    late_messages: List[ContractApiMessage] = field(default_factory=list)


@dataclass
class GasParams(BaseParams):
    """Gas parameters."""

    gas_price: Optional[int] = None
    max_fee_per_gas: Optional[int] = None
    max_priority_fee_per_gas: Optional[int] = None


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
        self.mutable_params = MutableParams(
            fallback_gas=self._ensure("init_fallback_gas", kwargs, int)
        )
        self.keeper_allowed_retries: int = self._ensure(
            "keeper_allowed_retries", kwargs, int
        )
        self.validate_timeout: int = self._ensure_gte(
            "validate_timeout",
            kwargs,
            int,
            min_value=_MINIMUM_VALIDATE_TIMEOUT,
        )
        self.finalize_timeout: float = self._ensure("finalize_timeout", kwargs, float)
        self.history_check_timeout: int = self._ensure(
            "history_check_timeout", kwargs, int
        )
        self.gas_params = self._get_gas_params(kwargs)
        super().__init__(*args, **kwargs)

    @staticmethod
    def _get_gas_params(kwargs: Dict[str, Any]) -> GasParams:
        """Get the gas parameters."""
        gas_params = kwargs.pop("gas_params", {})
        gas_price = gas_params.get("gas_price", None)
        max_fee_per_gas = gas_params.get("max_fee_per_gas", None)
        max_priority_fee_per_gas = gas_params.get("max_priority_fee_per_gas", None)
        return GasParams(
            gas_price=gas_price,
            max_fee_per_gas=max_fee_per_gas,
            max_priority_fee_per_gas=max_priority_fee_per_gas,
        )


RandomnessApi = ApiSpecs
Requests = BaseRequests
