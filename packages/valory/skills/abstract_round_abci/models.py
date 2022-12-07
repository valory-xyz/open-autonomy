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
from dataclasses import dataclass
from pathlib import Path
from time import time
from typing import Any, Callable, Dict, List, Optional, Tuple, Type, cast

from aea.exceptions import enforce
from aea.skills.base import Model, SkillContext

from packages.valory.protocols.http.message import HttpMessage
from packages.valory.skills.abstract_round_abci.base import (
    AbciApp,
    AbciAppDB,
    BaseSynchronizedData,
    ConsensusParams,
    RoundSequence,
)
from packages.valory.skills.abstract_round_abci.utils import (
    get_data_from_nested_dict,
    get_value_with_type,
)


NUMBER_OF_RETRIES: int = 5
DEFAULT_BACKOFF_FACTOR: int = 2
DEFAULT_TYPE_NAME: str = "str"
_DEFAULT_REQUEST_TIMEOUT = 10.0
_DEFAULT_REQUEST_RETRY_DELAY = 1.0
_DEFAULT_TX_TIMEOUT = 10.0
_DEFAULT_TX_MAX_ATTEMPTS = 10
_DEFAULT_CLEANUP_HISTORY_DEPTH_CURRENT = None


HeadersType = List[Tuple[str, str]]
ParametersType = HeadersType


class BaseParams(Model):  # pylint: disable=too-many-instance-attributes
    """Parameters."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Initialize the parameters object.

        The genesis configuration should be a dictionary with the following format:
            genesis_time: str
            chain_id: str
            consensus_params:
              block:
                max_bytes: str
                max_gas: str
                time_iota_ms: str
              evidence:
                max_age_num_blocks: str
                max_age_duration: str
                max_bytes: str
              validator:
                pub_key_types: List[str]
              version: dict
            voting_power: str

        :param args: positional arguments
        :param kwargs: keyword arguments
        """
        self.genesis_config = self._ensure("genesis_config", kwargs)
        self.voting_power = self._ensure("voting_power", self.genesis_config)
        self.service_id = self._ensure("service_id", kwargs)
        self.tendermint_url = self._ensure("tendermint_url", kwargs)
        self.max_healthcheck = self._ensure("max_healthcheck", kwargs)
        self.round_timeout_seconds = self._ensure("round_timeout_seconds", kwargs)
        self.sleep_time = self._ensure("sleep_time", kwargs)
        self.retry_timeout = self._ensure("retry_timeout", kwargs)
        self.retry_attempts = self._ensure("retry_attempts", kwargs)
        self.keeper_timeout = self._ensure("keeper_timeout", kwargs)
        self.observation_interval = self._ensure("observation_interval", kwargs)
        self.drand_public_key = self._ensure("drand_public_key", kwargs)
        self.tendermint_com_url = self._ensure("tendermint_com_url", kwargs)
        self.tendermint_max_retries = self._ensure("tendermint_max_retries", kwargs)
        self.tendermint_check_sleep_delay = self._ensure(
            "tendermint_check_sleep_delay", kwargs
        )
        self.reset_tendermint_after = self._ensure("reset_tendermint_after", kwargs)
        self.consensus_params = ConsensusParams.from_json(kwargs.pop("consensus", {}))
        self.cleanup_history_depth = self._ensure("cleanup_history_depth", kwargs)
        self.cleanup_history_depth_current = kwargs.pop(
            "cleanup_history_depth_current", _DEFAULT_CLEANUP_HISTORY_DEPTH_CURRENT
        )
        self.request_timeout = kwargs.pop("request_timeout", _DEFAULT_REQUEST_TIMEOUT)
        self.request_retry_delay = kwargs.pop(
            "request_retry_delay", _DEFAULT_REQUEST_RETRY_DELAY
        )
        self.tx_timeout = kwargs.pop("tx_timeout", _DEFAULT_TX_TIMEOUT)
        self.max_attempts = kwargs.pop("max_attempts", _DEFAULT_TX_MAX_ATTEMPTS)
        self.service_registry_address = kwargs.pop("service_registry_address", None)
        self.on_chain_service_id = kwargs.pop("on_chain_service_id", None)
        self.share_tm_config_on_startup = kwargs.pop(
            "share_tm_config_on_startup", False
        )
        setup_params = kwargs.pop("setup", {})
        # we sanitize for null values as these are just kept for schema definitions
        setup_params = {
            key: val for key, val in setup_params.items() if val is not None
        }
        self.setup_params = setup_params
        super().__init__(*args, **kwargs)

    @classmethod
    def _ensure(cls, key: str, kwargs: Dict) -> Any:
        """Get and ensure the configuration field is not None."""
        value = kwargs.pop(key, None)
        enforce(value is not None, f"'{key}' required, but it is not set")
        return value


class SharedState(Model):
    """Keep the current shared state of the skill."""

    def __init__(
        self,
        *args: Any,
        abci_app_cls: Type[AbciApp],
        skill_context: SkillContext,
        **kwargs: Any,
    ) -> None:
        """Initialize the state."""
        self.abci_app_cls = self._process_abci_app_cls(abci_app_cls)
        self.abci_app_cls._is_abstract = skill_context.is_abstract_component
        self._round_sequence: Optional[RoundSequence] = None
        self.last_reset_params: Optional[List[Tuple[str, str]]] = None
        kwargs["skill_context"] = skill_context
        super().__init__(*args, **kwargs)

    def setup(self) -> None:
        """Set up the model."""
        self._round_sequence = RoundSequence(self.abci_app_cls)
        consensus_params = cast(BaseParams, self.context.params).consensus_params
        setup_params = cast(BaseParams, self.context.params).setup_params
        self.round_sequence.setup(
            BaseSynchronizedData(
                AbciAppDB(
                    setup_data=setup_params,
                    cross_period_persisted_keys=self.abci_app_cls.cross_period_persisted_keys,
                )
            ),
            consensus_params,
            self.context.logger,
        )

    @property
    def round_sequence(self) -> RoundSequence:
        """Get the round_sequence."""
        if self._round_sequence is None:
            raise ValueError("round sequence not available")
        return self._round_sequence

    @property
    def synchronized_data(self) -> BaseSynchronizedData:
        """Get the latest synchronized_data if available."""
        return self.round_sequence.latest_synchronized_data

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


class UnexpectedResponseError(Exception):
    """Exception class for unexpected responses from Apis."""


@dataclass
class ResponseInfo:
    """A dataclass to hold all the information related to the response."""

    def __init__(self, kwargs: Dict) -> None:
        """Initialize a response info object"""
        self.response_key: Optional[str] = kwargs.pop("response_key", None)
        self.response_index: Optional[int] = kwargs.pop("response_index", None)
        self.response_type: str = kwargs.pop("response_type", DEFAULT_TYPE_NAME)
        self.error_key: Optional[str] = kwargs.pop("error_key", None)
        self.error_index: Optional[int] = kwargs.pop("error_index", None)
        self.error_type: str = kwargs.pop("error_type", DEFAULT_TYPE_NAME)
        self.error_data: Any = None


@dataclass
class RetriesInfo:
    """A dataclass to hold all the information related to the retries."""

    def __init__(self, kwargs: Dict) -> None:
        """Initialize a retries info object"""
        self.retries_attempted: int = 0
        self.retries: int = kwargs.pop("retries", NUMBER_OF_RETRIES)
        self.backoff_factor: float = kwargs.pop(
            "backoff_factor", DEFAULT_BACKOFF_FACTOR
        )

    @property
    def suggested_sleep_time(self) -> float:
        """The suggested amount of time to sleep."""
        return self.backoff_factor ** self.retries_attempted


class ApiSpecs(Model):
    """A model that wraps APIs to get cryptocurrency prices."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize ApiSpecsModel."""
        self.url: str = self.ensure("url", kwargs)
        self.api_id: str = self.ensure("api_id", kwargs)
        self.method: str = self.ensure("method", kwargs)
        self.headers: HeadersType = kwargs.pop("headers", [])
        self.parameters: ParametersType = kwargs.pop("parameters", [])
        self.response_info = ResponseInfo(kwargs)
        self.retries_info = RetriesInfo(kwargs)

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

    def _log_response(self, decoded_response: str) -> None:
        """Log the decoded response message using error level."""
        pretty_json_str = json.dumps(decoded_response, indent=4)
        self.context.logger.error(f"Response: {pretty_json_str}")

    @staticmethod
    def _parse_response(
        response_data: Any,
        response_keys: Optional[str],
        response_index: Optional[int],
        response_type: str,
    ) -> Any:
        """Parse a response from an API."""
        if response_keys is not None:
            response_data = get_data_from_nested_dict(response_data, response_keys)

        if response_index is not None:
            response_data = response_data[response_index]

        return get_value_with_type(response_data, response_type)

    def _get_error_from_response(self, response_data: Any) -> Any:
        """Try to get an error from the response."""
        try:
            return self._parse_response(
                response_data,
                self.response_info.error_key,
                self.response_info.error_index,
                self.response_info.error_type,
            )
        except (KeyError, IndexError, TypeError):
            self.context.logger.error(
                f"Could not parse error using the given key(s) ({self.response_info.error_key}) "
                f"and index ({self.response_info.error_index})!"
            )
            return None

    def _parse_response_data(self, response_data: Any) -> Any:
        """Get the response data."""
        try:
            return self._parse_response(
                response_data,
                self.response_info.response_key,
                self.response_info.response_index,
                self.response_info.response_type,
            )
        except (KeyError, IndexError, TypeError) as e:
            raise UnexpectedResponseError from e

    def process_response(self, response: HttpMessage) -> Any:
        """Process response from api."""
        decoded_response = response.body.decode()
        self.response_info.error_data = None

        try:
            response_data = json.loads(decoded_response)
        except json.JSONDecodeError:
            self.context.logger.error("Could not parse the response body!")
            self._log_response(decoded_response)
            return None

        try:
            return self._parse_response_data(response_data)
        except UnexpectedResponseError:
            self.context.logger.error(
                f"Could not access response using the given key(s) ({self.response_info.response_key}) "
                f"and index ({self.response_info.response_index})!"
            )
            self._log_response(decoded_response)
            self.response_info.error_data = self._get_error_from_response(response_data)
            return None

    def increment_retries(self) -> None:
        """Increment the retries counter."""
        self.retries_info.retries_attempted += 1

    def reset_retries(self) -> None:
        """Reset the retries counter."""
        self.retries_info.retries_attempted = 0

    def is_retries_exceeded(self) -> bool:
        """Check if the retries amount has been exceeded."""
        return self.retries_info.retries_attempted > self.retries_info.retries


class BenchmarkBlockTypes:  # pylint: disable=too-few-public-methods
    """Benchmark block types."""

    LOCAL = "local"
    CONSENSUS = "consensus"
    TOTAL = "total"


class BenchmarkBlock:
    """
    Benchmark

    This class represents logic to measure the code block using a
    context manager.
    """

    start: float
    total_time: float
    block_type: str

    def __init__(self, block_type: str) -> None:
        """Benchmark for single round."""
        self.block_type = block_type
        self.start = 0
        self.total_time = 0

    def __enter__(
        self,
    ) -> None:
        """Enter context."""
        self.start = time()

    def __exit__(self, *args: List, **kwargs: Dict) -> None:
        """Exit context"""
        self.total_time = time() - self.start


class BenchmarkBehaviour:
    """
    BenchmarkBehaviour

    This class represents logic to benchmark a single behaviour.
    """

    local_data: Dict[str, BenchmarkBlock]

    def __init__(
        self,
    ) -> None:
        """Initialize Benchmark behaviour object."""
        self.local_data = {}

    def _measure(self, block_type: str) -> BenchmarkBlock:
        """
        Returns a BenchmarkBlock object.

        :param block_type: type of block (e.g. local, consensus, request)
        :return: BenchmarkBlock
        """

        if block_type not in self.local_data:
            self.local_data[block_type] = BenchmarkBlock(block_type)

        return self.local_data[block_type]

    def local(
        self,
    ) -> BenchmarkBlock:
        """Measure local block."""
        return self._measure(BenchmarkBlockTypes.LOCAL)

    def consensus(
        self,
    ) -> BenchmarkBlock:
        """Measure consensus block."""
        return self._measure(BenchmarkBlockTypes.CONSENSUS)


class BenchmarkTool(Model):
    """
    BenchmarkTool

    Tool to benchmark ABCI apps.
    """

    benchmark_data: Dict[str, BenchmarkBehaviour]
    log_dir: Path

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Benchmark tool for rounds behaviours."""
        super().__init__(*args, **kwargs)
        self.benchmark_data = {}
        self.log_dir = Path(kwargs.pop("log_dir", "/logs"))

    def measure(self, behaviour: str) -> BenchmarkBehaviour:
        """Measure time to complete round."""
        if behaviour not in self.benchmark_data:
            self.benchmark_data[behaviour] = BenchmarkBehaviour()
        return self.benchmark_data[behaviour]

    @property
    def data(
        self,
    ) -> List:
        """Returns formatted data."""

        behavioural_data = []
        for behaviour, tool in self.benchmark_data.items():
            data = {k: v.total_time for k, v in tool.local_data.items()}
            data[BenchmarkBlockTypes.TOTAL] = sum(data.values())
            behavioural_data.append({"behaviour": behaviour, "data": data})

        return behavioural_data

    def save(self, period: int = 0, reset: bool = True) -> None:
        """Save logs to a file."""

        try:
            self.log_dir.mkdir(exist_ok=True)
            agent_dir = self.log_dir / self.context.agent_address
            agent_dir.mkdir(exist_ok=True)
            filepath = agent_dir / f"{period}.json"

            with open(str(filepath), "w+", encoding="utf-8") as outfile:
                json.dump(self.data, outfile)
            self.context.logger.info(f"Saving benchmarking data for period: {period}")

        except PermissionError as e:  # pragma: nocover
            self.context.logger.info(f"Error saving benchmark data:\n{e}")

        if reset:
            self.reset()

    def reset(
        self,
    ) -> None:
        """Reset benchmark data"""
        self.benchmark_data = {}
