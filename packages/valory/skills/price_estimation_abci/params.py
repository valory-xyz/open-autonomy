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

"""This module contains the parameters for the price estimation ABCI application."""
from math import ceil
from typing import Any, Dict

from aea.exceptions import enforce
from aea.skills.base import Model


class ConsensusParams:
    """Represent the consensus parameters."""

    def __init__(self, max_participants: int):
        """Initialize the consensus parameters."""
        self._max_participants = max_participants

    @property
    def max_participants(self) -> int:
        """Get the maximum number of participants."""
        return self._max_participants

    @property
    def two_thirds_threshold(self) -> int:
        """Get the 2/3 threshold."""
        return ceil(self.max_participants * 2 / 3)

    @classmethod
    def from_json(cls, obj: Dict) -> "ConsensusParams":
        """Get from JSON."""
        max_participants = obj["max_participants"]
        enforce(
            isinstance(max_participants, int) and max_participants >= 0,
            "max_participants must be an integer greater than 0.",
        )

        return ConsensusParams(max_participants)


class Params(Model):
    """Parameters."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the parameters object."""
        super().__init__(*args, **kwargs)
        self.tendermint_url = self._ensure("tendermint_url", kwargs)
        self.initial_delay = self._ensure("initial_delay", kwargs)

        self.consensus_params = ConsensusParams.from_json(kwargs.get("consensus", {}))

        self.currency_id = self._ensure("currency_id", kwargs)
        self.convert_id = self._ensure("convert_id", kwargs)

    @classmethod
    def _ensure(cls, key: str, kwargs: Dict) -> Any:
        """Get and ensure the configuration field is not None."""
        value = kwargs.get(key)
        enforce(value is not None, f"'{key}' required, but it is not set")
        return value
