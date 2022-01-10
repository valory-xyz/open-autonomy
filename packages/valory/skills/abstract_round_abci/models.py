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

"""This module contains the shared state for the price estimation ABCI application."""
import inspect
import json
from typing import Any, Callable, Dict, List, Tuple, Type, cast

from aea.exceptions import enforce
from aea.skills.base import Model

from packages.valory.protocols.http.message import HttpMessage
from packages.valory.skills.abstract_round_abci.base import (
    AbciApp,
    BasePeriodState,
    ConsensusParams,
    Period,
    StateDB,
)


NUMBER_OF_RETRIES: int = 5


class BaseParams(Model):  # pylint: disable=too-many-instance-attributes
    """Parameters."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the parameters object."""
        self.service_id = self._ensure("service_id", kwargs)
        self.tendermint_url = self._ensure("tendermint_url", kwargs)
        self.max_healthcheck = self._ensure("max_healthcheck", kwargs)
        self.round_timeout_seconds = self._ensure("round_timeout_seconds", kwargs)
        self.sleep_time = self._ensure("sleep_time", kwargs)
        self.retry_timeout = self._ensure("retry_timeout", kwargs)
        self.retry_attempts = self._ensure("retry_attempts", kwargs)
        self.observation_interval = self._ensure("observation_interval", kwargs)
        self.drand_public_key = self._ensure("drand_public_key", kwargs)
        self.tendermint_com_url = self._ensure("tendermint_com_url", kwargs)
        self.reset_tendermint_after = self._ensure("reset_tendermint_after", kwargs)
        self.safe_tx_gas = self._ensure("safe_tx_gas", kwargs)
        self.consensus_params = ConsensusParams.from_json(kwargs.pop("consensus", {}))
        self.period_setup_params = kwargs.pop("period_setup", {})
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

    def __init__(self, *args: Any, abci_app_cls: Type[AbciApp], **kwargs: Any) -> None:
        """Initialize the state."""
        self.abci_app_cls = self._process_abci_app_cls(abci_app_cls)
        super().__init__(*args, **kwargs)

    def setup(self) -> None:
        """Set up the model."""
        self.period = Period(self.abci_app_cls)
        consensus_params = cast(BaseParams, self.context.params).consensus_params
        period_setup_params = cast(BaseParams, self.context.params).period_setup_params
        self.period.setup(
            BasePeriodState(
                StateDB(initial_period=0, initial_data=period_setup_params)
            ),
            consensus_params,
            self.context.logger,
        )

    @property
    def period_state(self) -> BasePeriodState:
        """Get the period state if available."""
        period_state = self.period.latest_result
        if period_state is None:
            raise ValueError("period_state not available")
        return period_state

    @classmethod
    def _process_abci_app_cls(cls, abci_app_cls: Type[AbciApp]) -> Type[AbciApp]:
        """Process the 'initial_round_cls' parameter."""
        if not inspect.isclass(abci_app_cls):
            raise ValueError(f"The object {abci_app_cls} is not a class")
        if not issubclass(abci_app_cls, AbciApp):
            cls_name = AbciApp.__name__
            cls_module = AbciApp.__module__
            raise ValueError(
                f"The class {abci_app_cls} is not an instance of {cls_module}.{cls_name}"
            )
        return abci_app_cls


class Requests(Model):
    """Keep the current pending requests."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the state."""
        super().__init__(*args, **kwargs)

        # mapping from dialogue reference nonce to a callback
        self.request_id_to_callback: Dict[str, Callable] = {}


class ApiSpecs(Model):  # pylint: disable=too-many-instance-attributes
    """A model that wraps APIs to get cryptocurrency prices."""

    url: str
    api_id: str
    method: str
    response_key: str
    response_type: str
    headers: List[Tuple[str, str]]
    parameters: List[Tuple[str, str]]

    _retries_attempted: int
    _retries: int
    _response_types: Dict[str, Any] = {
        "int": int,
        "float": float,
        "dict": dict,
        "list": list,
        "str": str,
    }

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize ApiSpecsModel."""

        self.url = self.ensure("url", kwargs)
        self.api_id = self.ensure("api_id", kwargs)
        self.method = self.ensure("method", kwargs)
        self.headers = kwargs.pop("headers", [])
        self.parameters = kwargs.pop("parameters", [])
        self.response_key = kwargs.pop("response_key", None)
        self.response_type = kwargs.pop("response_type", str)

        self._retries_attempted = 0
        self._retries = kwargs.pop("retries", NUMBER_OF_RETRIES)

        super().__init__(*args, **kwargs)

    def ensure(self, keyword: str, kwargs: Dict) -> Any:
        """Ensure a keyword argument."""
        value = kwargs.pop(keyword, None)
        if value is None:
            raise ValueError(
                f"Value for {keyword} is required by {self.__class__.__name__}."
            )
        return value

    def get_spec(
        self,
    ) -> Dict:
        """Returns dictionary containing api specifications."""

        return {
            "url": self.url,
            "method": self.method,
            "headers": self.headers,
            "parameters": self.parameters,
        }

    def process_response(self, response: HttpMessage) -> Any:
        """Process response from api."""
        try:
            response_data = json.loads(response.body.decode())
            if self.response_key is None:
                return response_data

            first_key, *keys = self.response_key.split(":")
            value = response_data[first_key]
            for key in keys:
                value = value[key]

            return self._response_types.get(self.response_type)(value)  # type: ignore

        except (json.JSONDecodeError, KeyError):
            return None

    def increment_retries(self) -> None:
        """Increment the retries counter."""
        self._retries_attempted += 1

    def reset_retries(self) -> None:
        """Reset the retries counter."""
        self._retries_attempted = 0

    def is_retries_exceeded(self) -> bool:
        """Check if the retries amount has been exceeded."""
        return self._retries_attempted > self._retries
