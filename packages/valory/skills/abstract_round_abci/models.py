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
import json
from abc import ABC
from typing import Any, Callable, Dict, List, Optional, Tuple, Type, cast

from aea.exceptions import enforce
from aea.skills.base import Model

from packages.valory.protocols.http.message import HttpMessage
from packages.valory.skills.abstract_round_abci.base import (
    AbciApp,
    BasePeriodState,
    ConsensusParams,
    Period,
)


NUMBER_OF_RETRIES: int = 5


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

    def __init__(self, *args: Any, abci_app_cls: Type[AbciApp], **kwargs: Any) -> None:
        """Initialize the state."""
        self.abci_app_cls = self._process_abci_app_cls(abci_app_cls)
        super().__init__(*args, **kwargs)

    def setup(self) -> None:
        """Set up the model."""
        self.period = Period(self.abci_app_cls)
        consensus_params = cast(BaseParams, self.context.params).consensus_params
        self.period.setup(BasePeriodState(), consensus_params, self.context.logger)

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


class ApiSpecs(ABC):
    """External API Specs."""

    api_id: str
    url: str
    method: str

    headers: List[Tuple[str, str]] = []
    parameters: List[Tuple[str, str]] = []

    def get_spec(
        self,
    ) -> Dict:
        """Returns dictionary containing api specifications."""

        return {
            "api_id": self.api_id,
            "method": self.method,
            "url": self.url,
            "headers": self.headers,
            "parameters": self.parameters,
        }

    def _load_json(  # pylint: disable=no-self-use
        self, response: HttpMessage
    ) -> Optional[Dict]:
        """Process response."""
        try:
            result_ = json.loads(response.body.decode())
            return result_
        except (json.JSONDecodeError, KeyError):
            return None

    def process_response(self, response: HttpMessage) -> Any:
        """Process response from api."""
        raise NotImplementedError()


class ApiSpecsModel(Model):
    """A model that wraps APIs to get cryptocurrency prices."""

    _api_id_to_cls: Dict[str, Type[ApiSpecs]]
    _retries_attempted: int
    _retries: int
    _source_id: str
    _api: ApiSpecs

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize ApiSpecsModel."""
        self._retries = kwargs.pop("retries", NUMBER_OF_RETRIES)
        self._retries_attempted = 0
        self._source_id = kwargs.pop("source_id", None)
        if self._source_id is None:
            raise ValueError("'source_id' is a mandatory configuration")
        self._api = self._get_api()
        super().__init__(*args, **kwargs)

    @property
    def api_id(self) -> str:
        """Get API id."""
        return self._api.api_id

    def increment_retries(self) -> None:
        """Increment the retries counter."""
        self._retries_attempted += 1

    def is_retries_exceeded(self) -> bool:
        """Check if the retries amount has been exceeded."""
        return self._retries_attempted > self._retries

    def _get_api(self) -> ApiSpecs:
        """Get the ApiSpecs object."""
        api_cls = self._api_id_to_cls.get(self._source_id)
        if api_cls is None:
            raise ValueError(f"'{self._source_id}' is not a supported API identifier")
        return api_cls()

    def get_spec(self) -> Dict:
        """Get the spec of the API"""
        return self._api.get_spec()

    def process_response(self, response: HttpMessage) -> Optional[Any]:
        """Process the response and return observed price."""
        return self._api.process_response(response)
