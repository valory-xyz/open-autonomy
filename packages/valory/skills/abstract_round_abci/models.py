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

"""This module contains the shared state for the price estimation ABCI application."""

import inspect
import json
from abc import ABC, ABCMeta
from collections import Counter
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from time import time
from typing import (
    Any,
    Callable,
    Dict,
    Iterable,
    List,
    Optional,
    Tuple,
    Type,
    cast,
    get_type_hints,
)

from aea.exceptions import enforce
from aea.skills.base import Model, SkillContext

from packages.valory.protocols.http.message import HttpMessage
from packages.valory.skills.abstract_round_abci.base import (
    AbciApp,
    AbciAppDB,
    BaseSynchronizedData,
    ConsensusParams,
    RESET_INDEX_DEFAULT,
    ROUND_COUNT_DEFAULT,
    RoundSequence,
    consensus_threshold,
    get_name,
)
from packages.valory.skills.abstract_round_abci.utils import (
    check_type,
    get_data_from_nested_dict,
    get_value_with_type,
)


NUMBER_OF_RETRIES: int = 5
DEFAULT_BACKOFF_FACTOR: float = 2.0
DEFAULT_TYPE_NAME: str = "str"


class FrozenMixin:  # pylint: disable=too-few-public-methods
    """Mixin for classes to enforce read-only attributes."""

    _frozen: bool = False

    def __delattr__(self, *args: Any) -> None:
        """Override __delattr__ to make object immutable."""
        if self._frozen:
            raise AttributeError(
                "This object is frozen! To unfreeze switch `self._frozen` via `__dict__`."
            )
        super().__delattr__(*args)

    def __setattr__(self, *args: Any) -> None:
        """Override __setattr__ to make object immutable."""
        if self._frozen:
            raise AttributeError(
                "This object is frozen! To unfreeze switch `self._frozen` via `__dict__`."
            )
        super().__setattr__(*args)


class TypeCheckMixin:  # pylint: disable=too-few-public-methods
    """Mixin for data classes & models to enforce attribute types on construction."""

    def __post_init__(self) -> None:
        """Check that the type of the provided attributes is correct."""
        for attr, type_ in get_type_hints(self).items():
            value = getattr(self, attr)
            check_type(attr, value, type_)

    @classmethod
    def _ensure(cls, key: str, kwargs: Dict, type_: Any) -> Any:
        """Get and ensure the configuration field is not None (if no default is provided) and of correct type."""
        enforce("skill_context" in kwargs, "Only use on models!")
        skill_id = kwargs["skill_context"].skill_id
        enforce(
            key in kwargs,
            f"'{key}' of type '{type_}' required, but it is not set in `models.params.args` of `skill.yaml` of `{skill_id}`",
        )
        value = kwargs.pop(key)
        try:
            check_type(key, value, type_)
        except TypeError:  # pragma: nocover
            enforce(
                False,
                f"'{key}' must be a {type_}, but type {type(value)} was found in `models.params.args` of `skill.yaml` of `{skill_id}`",
            )
        return value


@dataclass(frozen=True)
class GenesisBlock(TypeCheckMixin):
    """A dataclass to store the genesis block."""

    max_bytes: str
    max_gas: str
    time_iota_ms: str

    def to_json(self) -> Dict[str, str]:
        """Get a GenesisBlock instance as a json dictionary."""
        return {
            "max_bytes": self.max_bytes,
            "max_gas": self.max_gas,
            "time_iota_ms": self.time_iota_ms,
        }


@dataclass(frozen=True)
class GenesisEvidence(TypeCheckMixin):
    """A dataclass to store the genesis evidence."""

    max_age_num_blocks: str
    max_age_duration: str
    max_bytes: str

    def to_json(self) -> Dict[str, str]:
        """Get a GenesisEvidence instance as a json dictionary."""
        return {
            "max_age_num_blocks": self.max_age_num_blocks,
            "max_age_duration": self.max_age_duration,
            "max_bytes": self.max_bytes,
        }


@dataclass(frozen=True)
class GenesisValidator(TypeCheckMixin):
    """A dataclass to store the genesis validator."""

    pub_key_types: Tuple[str, ...]

    def to_json(self) -> Dict[str, List[str]]:
        """Get a GenesisValidator instance as a json dictionary."""
        return {"pub_key_types": list(self.pub_key_types)}


@dataclass(frozen=True)
class GenesisConsensusParams(TypeCheckMixin):
    """A dataclass to store the genesis consensus parameters."""

    block: GenesisBlock
    evidence: GenesisEvidence
    validator: GenesisValidator
    version: dict

    @classmethod
    def from_json_dict(cls, json_dict: dict) -> "GenesisConsensusParams":
        """Get a GenesisConsensusParams instance from a json dictionary."""
        block = GenesisBlock(**json_dict["block"])
        evidence = GenesisEvidence(**json_dict["evidence"])
        validator = GenesisValidator(tuple(json_dict["validator"]["pub_key_types"]))
        return cls(block, evidence, validator, json_dict["version"])

    def to_json(self) -> Dict[str, Any]:
        """Get a GenesisConsensusParams instance as a json dictionary."""
        return {
            "block": self.block.to_json(),
            "evidence": self.evidence.to_json(),
            "validator": self.validator.to_json(),
            "version": self.version,
        }


@dataclass(frozen=True)
class GenesisConfig(TypeCheckMixin):
    """A dataclass to store the genesis configuration."""

    genesis_time: str
    chain_id: str
    consensus_params: GenesisConsensusParams
    voting_power: str

    @classmethod
    def from_json_dict(cls, json_dict: dict) -> "GenesisConfig":
        """Get a GenesisConfig instance from a json dictionary."""
        consensus_params = GenesisConsensusParams.from_json_dict(
            json_dict["consensus_params"]
        )
        return cls(
            json_dict["genesis_time"],
            json_dict["chain_id"],
            consensus_params,
            json_dict["voting_power"],
        )

    def to_json(self) -> Dict[str, Any]:
        """Get a GenesisConfig instance as a json dictionary."""
        return {
            "genesis_time": self.genesis_time,
            "chain_id": self.chain_id,
            "consensus_params": self.consensus_params.to_json(),
            "voting_power": self.voting_power,
        }


class BaseParams(
    Model, FrozenMixin, TypeCheckMixin
):  # pylint: disable=too-many-instance-attributes
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
        self.genesis_config: GenesisConfig = GenesisConfig.from_json_dict(
            self._ensure("genesis_config", kwargs, dict)
        )
        self.service_id: str = self._ensure("service_id", kwargs, str)
        self.tendermint_url: str = self._ensure("tendermint_url", kwargs, str)
        self.max_healthcheck: int = self._ensure("max_healthcheck", kwargs, int)
        self.round_timeout_seconds: float = self._ensure(
            "round_timeout_seconds", kwargs, float
        )
        self.sleep_time: int = self._ensure("sleep_time", kwargs, int)
        self.retry_timeout: int = self._ensure("retry_timeout", kwargs, int)
        self.retry_attempts: int = self._ensure("retry_attempts", kwargs, int)
        self.keeper_timeout: float = self._ensure("keeper_timeout", kwargs, float)
        self.observation_interval: int = self._ensure(
            "observation_interval", kwargs, int
        )
        self.drand_public_key: str = self._ensure("drand_public_key", kwargs, str)
        self.tendermint_com_url: str = self._ensure("tendermint_com_url", kwargs, str)
        self.tendermint_max_retries: int = self._ensure(
            "tendermint_max_retries", kwargs, int
        )
        self.tendermint_check_sleep_delay: int = self._ensure(
            "tendermint_check_sleep_delay", kwargs, int
        )
        self.reset_tendermint_after: int = self._ensure(
            "reset_tendermint_after", kwargs, int
        )
        self.consensus_params: ConsensusParams = ConsensusParams.from_json(
            self._ensure("consensus", kwargs, dict)
        )
        self.cleanup_history_depth: int = self._ensure(
            "cleanup_history_depth", kwargs, int
        )
        self.cleanup_history_depth_current: Optional[int] = self._ensure(
            "cleanup_history_depth_current", kwargs, Optional[int]
        )
        self.request_timeout: float = self._ensure("request_timeout", kwargs, float)
        self.request_retry_delay: float = self._ensure(
            "request_retry_delay", kwargs, float
        )
        self.tx_timeout: float = self._ensure("tx_timeout", kwargs, float)
        self.max_attempts: int = self._ensure("max_attempts", kwargs, int)
        self.service_registry_address: Optional[str] = self._ensure(
            "service_registry_address", kwargs, Optional[str]
        )
        self.on_chain_service_id: Optional[int] = self._ensure(
            "on_chain_service_id", kwargs, Optional[int]
        )
        self.share_tm_config_on_startup: bool = self._ensure(
            "share_tm_config_on_startup", kwargs, bool
        )
        self.tendermint_p2p_url: str = self._ensure("tendermint_p2p_url", kwargs, str)
        setup_params_: Dict[str, Any] = self._ensure("setup", kwargs, dict)

        def check_val(val: Any, skill_id: str) -> List[Any]:
            """Check that a value a list"""
            if not isinstance(val, list):
                raise TypeError(
                    f"Value `{val}` in `setup` set in `models.params.args` of `skill.yaml` of `{skill_id}` is not a list"
                )
            return val

        # we sanitize for null values as these are just kept for schema definitions
        skill_id = kwargs["skill_context"].skill_id
        setup_params: Dict[str, List[Any]] = {
            key: check_val(val, skill_id)
            for key, val in setup_params_.items()
            if val is not None
        }
        self.setup_params = setup_params
        super().__init__(*args, **kwargs)

        if not self.context.is_abstract_component:
            # setup data are mandatory for non-abstract skills,
            # and they should always contain at least `all_participants` and `safe_contract_address`
            self._ensure_setup(
                {
                    get_name(BaseSynchronizedData.safe_contract_address),
                    get_name(BaseSynchronizedData.all_participants),
                }
            )
        self._frozen = True

    def _ensure_setup(self, necessary_keys: Iterable[str]) -> Any:
        """Ensure that the `setup` params contain all the `necessary_keys`."""
        enforce(bool(self.setup_params), "`setup` params contain no values!")
        not_found_keys = set(necessary_keys) - set(self.setup_params)
        found = not not_found_keys
        fail_msg = f"Values for `{not_found_keys}` missing from the `setup` params."
        enforce(found, fail_msg)


class _MetaSharedState(ABCMeta):
    """A metaclass that validates SharedState's attributes."""

    def __new__(mcs, name: str, bases: Tuple, namespace: Dict, **kwargs: Any) -> Type:  # type: ignore
        """Initialize the class."""
        new_cls = super().__new__(mcs, name, bases, namespace, **kwargs)

        if ABC in bases:
            # abstract class, return
            return new_cls
        if not issubclass(new_cls, SharedState):
            # the check only applies to SharedState subclasses
            return new_cls

        mcs._check_consistency(cast(Type[SharedState], new_cls))
        return new_cls

    @classmethod
    def _check_consistency(mcs, shared_state_cls: Type["SharedState"]) -> None:
        """Check consistency of class attributes."""
        mcs._check_required_class_attributes(shared_state_cls)

    @classmethod
    def _check_required_class_attributes(
        mcs, shared_state_cls: Type["SharedState"]
    ) -> None:
        """Check that required class attributes are set."""
        if not hasattr(shared_state_cls, "abci_app_cls"):
            raise AttributeError(f"'abci_app_cls' not set on {shared_state_cls}")
        abci_app_cls = shared_state_cls.abci_app_cls
        if not inspect.isclass(abci_app_cls):
            raise AttributeError(f"The object `{abci_app_cls}` is not a class")
        if not issubclass(abci_app_cls, AbciApp):
            cls_name = AbciApp.__name__
            cls_module = AbciApp.__module__
            raise AttributeError(
                f"The class {abci_app_cls} is not an instance of {cls_module}.{cls_name}"
            )


class SharedState(Model, ABC, metaclass=_MetaSharedState):  # type: ignore
    """Keep the current shared state of the skill."""

    abci_app_cls: Type[AbciApp]

    def __init__(
        self,
        *args: Any,
        skill_context: SkillContext,
        **kwargs: Any,
    ) -> None:
        """Initialize the state."""
        self.abci_app_cls._is_abstract = skill_context.is_abstract_component
        self._round_sequence: Optional[RoundSequence] = None
        self.address_to_acn_deliverable: Dict[str, Any] = {}
        self.tm_recovery_params: TendermintRecoveryParams = TendermintRecoveryParams(
            self.abci_app_cls.initial_round_cls.auto_round_id()
        )
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

    def get_acn_result(self) -> Any:
        """Get the majority of the ACN deliverables."""
        if len(self.address_to_acn_deliverable) == 0:
            return None

        # the current agent does not participate, so we need `nb_participants - 1`
        threshold = consensus_threshold(self.synchronized_data.nb_participants - 1)
        counter = Counter(self.address_to_acn_deliverable.values())
        most_common_value, n_appearances = counter.most_common(1)[0]

        if n_appearances < threshold:
            return None

        self.context.logger.debug(
            f"ACN result is '{most_common_value}' from '{self.address_to_acn_deliverable}'."
        )
        return most_common_value


class Requests(Model, FrozenMixin):
    """Keep the current pending requests."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the state."""
        # mapping from dialogue reference nonce to a callback
        self.request_id_to_callback: Dict[str, Callable] = {}
        super().__init__(*args, **kwargs)
        self._frozen = True


class UnexpectedResponseError(Exception):
    """Exception class for unexpected responses from Apis."""


@dataclass
class ResponseInfo(TypeCheckMixin):
    """A dataclass to hold all the information related to the response."""

    response_key: Optional[str]
    response_index: Optional[int]
    response_type: str
    error_key: Optional[str]
    error_index: Optional[int]
    error_type: str
    error_data: Any = None

    @classmethod
    def from_json_dict(cls, kwargs: Dict) -> "ResponseInfo":
        """Initialize a response info object from kwargs."""
        response_key: Optional[str] = kwargs.pop("response_key", None)
        response_index: Optional[int] = kwargs.pop("response_index", None)
        response_type: str = kwargs.pop("response_type", DEFAULT_TYPE_NAME)
        error_key: Optional[str] = kwargs.pop("error_key", None)
        error_index: Optional[int] = kwargs.pop("error_index", None)
        error_type: str = kwargs.pop("error_type", DEFAULT_TYPE_NAME)
        return cls(
            response_key,
            response_index,
            response_type,
            error_key,
            error_index,
            error_type,
        )


@dataclass
class RetriesInfo(TypeCheckMixin):
    """A dataclass to hold all the information related to the retries."""

    retries: int
    backoff_factor: float
    retries_attempted: int = 0

    @classmethod
    def from_json_dict(cls, kwargs: Dict) -> "RetriesInfo":
        """Initialize a retries info object from kwargs."""
        retries: int = kwargs.pop("retries", NUMBER_OF_RETRIES)
        backoff_factor: float = kwargs.pop("backoff_factor", DEFAULT_BACKOFF_FACTOR)
        return cls(retries, backoff_factor)

    @property
    def suggested_sleep_time(self) -> float:
        """The suggested amount of time to sleep."""
        return self.backoff_factor ** self.retries_attempted


@dataclass(frozen=True)
class TendermintRecoveryParams(TypeCheckMixin):
    """A dataclass to hold all parameters related to agent <-> tendermint recovery procedures.

    This must be frozen so that we make sure it does not get edited.
    """

    reset_from_round: str
    round_count: int = ROUND_COUNT_DEFAULT
    reset_index: int = RESET_INDEX_DEFAULT
    reset_params: Optional[List[Tuple[str, str]]] = None


class ApiSpecs(Model, FrozenMixin, TypeCheckMixin):
    """A model that wraps APIs to get cryptocurrency prices."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize ApiSpecsModel."""
        self.url: str = self._ensure("url", kwargs, str)
        self.api_id: str = self._ensure("api_id", kwargs, str)
        self.method: str = self._ensure("method", kwargs, str)
        self.headers: List[Tuple[str, str]] = self._ensure(
            "headers", kwargs, List[Tuple[str, str]]
        )
        self.parameters: List[Tuple[str, str]] = self._ensure(
            "parameters", kwargs, List[Tuple[str, str]]
        )
        self.response_info = ResponseInfo.from_json_dict(kwargs)
        self.retries_info = RetriesInfo.from_json_dict(kwargs)
        super().__init__(*args, **kwargs)
        self._frozen = True

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


class BenchmarkBlockTypes(Enum):
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
        return self._measure(BenchmarkBlockTypes.LOCAL.value)

    def consensus(
        self,
    ) -> BenchmarkBlock:
        """Measure consensus block."""
        return self._measure(BenchmarkBlockTypes.CONSENSUS.value)


class BenchmarkTool(Model, TypeCheckMixin, FrozenMixin):
    """
    BenchmarkTool

    Tool to benchmark ABCI apps.
    """

    benchmark_data: Dict[str, BenchmarkBehaviour]
    log_dir: Path

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Benchmark tool for rounds behaviours."""
        self.benchmark_data = {}
        log_dir_ = self._ensure("log_dir", kwargs, str)
        self.log_dir = Path(log_dir_)
        super().__init__(*args, **kwargs)
        self._frozen = True

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
            data[BenchmarkBlockTypes.TOTAL.value] = sum(data.values())
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
        self.benchmark_data.clear()
