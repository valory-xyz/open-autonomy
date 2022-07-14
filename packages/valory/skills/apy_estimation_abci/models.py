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

"""Custom objects for the APY estimation ABCI application."""

from typing import Any, Optional

from packages.valory.protocols.http import HttpMessage
from packages.valory.skills.abstract_round_abci.models import ApiSpecs, BaseParams
from packages.valory.skills.abstract_round_abci.models import (
    BenchmarkTool as BaseBenchmarkTool,
)
from packages.valory.skills.abstract_round_abci.models import Requests as BaseRequests
from packages.valory.skills.abstract_round_abci.models import (
    SharedState as BaseSharedState,
)
from packages.valory.skills.apy_estimation_abci.rounds import APYEstimationAbciApp


Requests = BaseRequests
BenchmarkTool = BaseBenchmarkTool


class SharedState(BaseSharedState):
    """Keep the current shared state of the skill."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the state."""
        super().__init__(*args, abci_app_cls=APYEstimationAbciApp, **kwargs)


class RandomnessApi(ApiSpecs):
    """A model that wraps ApiSpecs for randomness api specifications."""


class FantomSubgraph(ApiSpecs):
    """A model that wraps ApiSpecs for Fantom subgraph specifications."""


class SpookySwapSubgraph(ApiSpecs):
    """A model that wraps ApiSpecs for SpookySwap subgraph specifications."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize SpookySwapSubgraph."""
        self.bundle_id: int = self.ensure("bundle_id", kwargs)
        self.non_indexed_error_key = kwargs.pop("non_indexed_error_key", "errors")
        self.non_indexed_error_type = kwargs.pop("non_indexed_error_type", "list")
        super().__init__(*args, **kwargs)

    def process_non_indexed_error(self, response: HttpMessage) -> Any:
        """Process a non-indexed block error response from the subgraph."""
        return self._get_response_data(
            response, self.non_indexed_error_key, self.non_indexed_error_type
        )


class APYParams(BaseParams):  # pylint: disable=too-many-instance-attributes
    """Parameters."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the parameters object."""
        self.start: int = self._ensure("history_start", kwargs)
        self.end: Optional[int] = kwargs.pop("history_end", None)
        self.interval: int = self._ensure("history_interval_in_unix", kwargs)
        self.optimizer_params = self._ensure("optimizer", kwargs)
        self.testing = self._ensure("testing", kwargs)
        self.estimation = self._ensure("estimation", kwargs)
        self.pair_ids = self._ensure("pair_ids", kwargs)
        self.ipfs_domain_name = self._ensure("ipfs_domain_name", kwargs)
        super().__init__(*args, **kwargs)

        self.__validate_params()

    def __validate_params(self) -> None:
        """Validate the given parameters."""
        # Eventually, we should probably validate all the parameters.
        for param_name in ("timeout", "window_size"):
            param_val = self.optimizer_params.get(param_name)
            if param_val is not None and not isinstance(param_val, int):
                raise ValueError(
                    f"Optimizer's parameter `{param_name}` can be either of type `int` or `None`. "
                    f"{type(param_val)} was given."
                )
            # if the value did not exist in the config, then we set it to the default (None) returned from `.get` method
            self.optimizer_params[param_name] = param_val
