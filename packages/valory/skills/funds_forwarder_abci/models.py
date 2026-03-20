# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2026 Valory AG
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

"""This module contains the shared state for the FundsForwarderAbciApp."""

from typing import Any, Dict, Type

from packages.valory.skills.abstract_round_abci.base import AbciApp
from packages.valory.skills.abstract_round_abci.models import (
    BaseParams,
)
from packages.valory.skills.abstract_round_abci.models import (
    BenchmarkTool as BaseBenchmarkTool,
)
from packages.valory.skills.abstract_round_abci.models import Requests as BaseRequests
from packages.valory.skills.abstract_round_abci.models import (
    SharedState as BaseSharedState,
)
from packages.valory.skills.funds_forwarder_abci.rounds import FundsForwarderAbciApp

ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"


class SharedState(BaseSharedState):
    """Keep the current shared state of the skill."""

    abci_app_cls: Type[AbciApp] = FundsForwarderAbciApp


class FundsForwarderParams(BaseParams):
    """Parameters for the funds_forwarder_abci skill."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the parameters object.

        Note: on_chain_service_id and service_registry_address are inherited
        from BaseParams as Optional fields.
        """
        self.expected_service_owner_address: str = self._ensure(
            "expected_service_owner_address", kwargs, type_=str
        )
        self.funds_forwarder_token_config: Dict[str, Dict[str, int]] = self._ensure(
            "funds_forwarder_token_config", kwargs, type_=Dict[str, Dict[str, int]]
        )
        self._validate_token_limits()
        super().__init__(*args, **kwargs)

    def _validate_token_limits(self) -> None:
        """Validate token limit configuration.

        :raises ValueError: if min_transfer > max_transfer for any token.
        """
        for token, limits in self.funds_forwarder_token_config.items():
            min_transfer = limits.get("min_transfer", 0)
            max_transfer = limits["max_transfer"]
            if min_transfer > max_transfer:
                raise ValueError(
                    f"Token {token}: min_transfer ({min_transfer}) "
                    f"> max_transfer ({max_transfer})"
                )


Requests = BaseRequests
BenchmarkTool = BaseBenchmarkTool
