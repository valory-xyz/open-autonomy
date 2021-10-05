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
import inspect
from typing import Any, Callable, Dict, Type, cast

from aea.exceptions import enforce
from aea.skills.base import Model

from packages.valory.skills.abstract_round_abci.base import (
    AbstractRound,
    BasePeriodState,
    ConsensusParams,
    Period,
)


class BaseParams(Model):
    """Parameters."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the parameters object."""
        self.tendermint_url = self._ensure("tendermint_url", kwargs)

        self.consensus_params = ConsensusParams.from_json(kwargs.pop("consensus", {}))
        super().__init__(*args, **kwargs)

    @classmethod
    def _ensure(cls, key: str, kwargs: Dict) -> Any:
        """Get and ensure the configuration field is not None."""
        value = kwargs.pop(key, None)
        enforce(value is not None, f"'{key}' required, but it is not set")
        return value


class SharedState(Model):
    """Keep the current shared state of the skill."""

    period: Period

    def __init__(
        self, *args: Any, initial_round_cls: Type[AbstractRound], **kwargs: Any
    ) -> None:
        """Initialize the state."""
        self.initial_round_cls = self._process_initial_round_cls(initial_round_cls)
        super().__init__(*args, **kwargs)

    def setup(self) -> None:
        """Set up the model."""
        self.period = Period(self.initial_round_cls)
        consensus_params = cast(BaseParams, self.context.params).consensus_params
        self.period.setup(BasePeriodState(), consensus_params)

    @property
    def period_state(self) -> BasePeriodState:
        """Get the period state if available."""
        period_state = self.period.latest_result
        if period_state is None:
            raise ValueError("period_state not available")
        return period_state

    @classmethod
    def _process_initial_round_cls(
        cls, initial_round_cls: Type[AbstractRound]
    ) -> Type[AbstractRound]:
        """Process the 'initial_round_cls' parameter."""
        if not inspect.isclass(initial_round_cls):
            raise ValueError(f"The object {initial_round_cls} is not a class")
        if not issubclass(initial_round_cls, AbstractRound):
            cls_name = AbstractRound.__name__
            cls_module = AbstractRound.__module__
            raise ValueError(
                f"The class {initial_round_cls} is not an instance of {cls_module}.{cls_name}"
            )
        return initial_round_cls


class Requests(Model):
    """Keep the current pending requests."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the state."""
        super().__init__(*args, **kwargs)

        # mapping from dialogue reference nonce to a callback
        self.request_id_to_callback: Dict[str, Callable] = {}
