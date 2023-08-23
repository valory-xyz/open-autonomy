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

"""Test the models.py module of the skill."""

# pylint: skip-file

import builtins
import json
import logging
import re
from collections import OrderedDict
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from tempfile import TemporaryDirectory
from time import sleep
from typing import Any, Dict, List, Optional, Set, Tuple, Type, cast
from unittest import mock
from unittest.mock import MagicMock

import pytest
from aea.exceptions import AEAEnforceError
from typing_extensions import Literal, TypedDict

from packages.valory.skills.abstract_round_abci.base import (
    AbstractRound,
    BaseSynchronizedData,
    OffenceStatus,
    OffenseStatusEncoder,
    ROUND_COUNT_DEFAULT,
)
from packages.valory.skills.abstract_round_abci.models import (
    ApiSpecs,
    BaseParams,
    BenchmarkTool,
    DEFAULT_BACKOFF_FACTOR,
    GenesisBlock,
    GenesisConfig,
    GenesisConsensusParams,
    GenesisEvidence,
    GenesisValidator,
    MIN_RESET_PAUSE_DURATION,
    NUMBER_OF_RETRIES,
    Requests,
)
from packages.valory.skills.abstract_round_abci.models import (
    SharedState as BaseSharedState,
)
from packages.valory.skills.abstract_round_abci.models import (
    TendermintRecoveryParams,
    _MetaSharedState,
    check_type,
)
from packages.valory.skills.abstract_round_abci.test_tools.abci_app import AbciAppTest
from packages.valory.skills.abstract_round_abci.tests.conftest import (
    irrelevant_genesis_config,
)


BASE_DUMMY_SPECS_CONFIG = dict(
    name="dummy",
    skill_context=MagicMock(),
    url="http://dummy",
    api_id="api_id",
    method="GET",
    headers=OrderedDict([("Dummy-Header", "dummy_value")]),
    parameters=OrderedDict([("Dummy-Param", "dummy_param")]),
)

BASE_DUMMY_PARAMS = dict(
    name="",
    skill_context=MagicMock(is_abstract_component=True),
    setup={},
    tendermint_url="",
    max_healthcheck=1,
    round_timeout_seconds=1.0,
    sleep_time=1,
    retry_timeout=1,
    retry_attempts=1,
    reset_pause_duration=MIN_RESET_PAUSE_DURATION,
    drand_public_key="",
    tendermint_com_url="",
    reset_tendermint_after=1,
    service_id="abstract_round_abci",
    service_registry_address="0xa51c1fc2f0d1a1b8494ed1fe312d7c3a78ed91c0",
    keeper_timeout=1.0,
    tendermint_check_sleep_delay=3,
    tendermint_max_retries=5,
    cleanup_history_depth=0,
    genesis_config=irrelevant_genesis_config,
    cleanup_history_depth_current=None,
    request_timeout=0.0,
    request_retry_delay=0.0,
    tx_timeout=0.0,
    max_attempts=0,
    on_chain_service_id=None,
    share_tm_config_on_startup=False,
    tendermint_p2p_url="",
    use_termination=False,
    use_slashing=False,
    slash_cooldown_hours=3,
    slash_threshold_amount=10_000_000_000_000_000,
    light_slash_unit_amount=5_000_000_000_000_000,
    serious_slash_unit_amount=8_000_000_000_000_000,
)


class TestApiSpecsModel:
    """Test ApiSpecsModel."""

    api_specs: ApiSpecs

    def setup(
        self,
    ) -> None:
        """Setup test."""

        self.api_specs = ApiSpecs(
            **BASE_DUMMY_SPECS_CONFIG,
            response_key="value",
            response_index=0,
            response_type="float",
            error_key="error",
            error_index=None,
            error_type="str",
            error_data="error text",
        )

    def test_init(
        self,
    ) -> None:
        """Test initialization."""

        # test ensure method.
        with pytest.raises(
            AEAEnforceError,
            match="'url' of type '<class 'str'>' required, but it is not set in `models.params.args` of `skill.yaml` of",
        ):
            _ = ApiSpecs(
                name="dummy",
                skill_context=MagicMock(),
            )

        assert self.api_specs.retries_info.backoff_factor == DEFAULT_BACKOFF_FACTOR
        assert self.api_specs.retries_info.retries == NUMBER_OF_RETRIES
        assert self.api_specs.retries_info.retries_attempted == 0

        assert self.api_specs.url == "http://dummy"
        assert self.api_specs.api_id == "api_id"
        assert self.api_specs.method == "GET"
        assert self.api_specs.headers == {"Dummy-Header": "dummy_value"}
        assert self.api_specs.parameters == {"Dummy-Param": "dummy_param"}
        assert self.api_specs.response_info.response_key == "value"
        assert self.api_specs.response_info.response_index == 0
        assert self.api_specs.response_info.response_type == "float"
        assert self.api_specs.response_info.error_key == "error"
        assert self.api_specs.response_info.error_index is None
        assert self.api_specs.response_info.error_type == "str"
        assert self.api_specs.response_info.error_data is None

    @pytest.mark.parametrize("retries", range(10))
    def test_suggested_sleep_time(self, retries: int) -> None:
        """Test `suggested_sleep_time`"""
        self.api_specs.retries_info.retries_attempted = retries
        assert (
            self.api_specs.retries_info.suggested_sleep_time
            == DEFAULT_BACKOFF_FACTOR**retries
        )

    def test_retries(
        self,
    ) -> None:
        """Tests for retries."""

        self.api_specs.increment_retries()
        assert self.api_specs.retries_info.retries_attempted == 1
        assert not self.api_specs.is_retries_exceeded()

        for _ in range(NUMBER_OF_RETRIES):
            self.api_specs.increment_retries()
        assert self.api_specs.is_retries_exceeded()
        self.api_specs.reset_retries()
        assert self.api_specs.retries_info.retries_attempted == 0

    def test_get_spec(
        self,
    ) -> None:
        """Test get_spec method."""

        actual_specs = {
            "url": "http://dummy",
            "method": "GET",
            "headers": {"Dummy-Header": "dummy_value"},
            "parameters": {"Dummy-Param": "dummy_param"},
        }

        specs = self.api_specs.get_spec()
        assert all([key in specs for key in actual_specs.keys()])
        assert all([specs[key] == actual_specs[key] for key in actual_specs])

    @pytest.mark.parametrize(
        "api_specs_config, message, expected_res, expected_error",
        (
            (
                dict(
                    **BASE_DUMMY_SPECS_CONFIG,
                    response_key="value",
                    response_index=None,
                    response_type="float",
                    error_key=None,
                    error_index=None,
                    error_data=None,
                ),
                MagicMock(body=b'{"value": "10.232"}'),
                10.232,
                None,
            ),
            (
                dict(
                    **BASE_DUMMY_SPECS_CONFIG,
                    response_key="test:response:key",
                    response_index=2,
                    response_type="dict",
                    error_key="error:key",
                    error_index=3,
                    error_type="str",
                    error_data=None,
                ),
                MagicMock(
                    body=b'{"test": {"response": {"key": ["does_not_matter", "does_not_matter", {"this": "matters"}]}}}'
                ),
                {"this": "matters"},
                None,
            ),
            (
                dict(
                    **BASE_DUMMY_SPECS_CONFIG,
                    response_key="test:response:key",
                    response_index=2,
                    error_key="error:key",
                    error_index=3,
                    error_type="str",
                    error_data=None,
                ),
                MagicMock(body=b'{"cannot be parsed'),
                None,
                None,
            ),
            (
                dict(
                    **BASE_DUMMY_SPECS_CONFIG,
                    response_key="test:response:key",
                    response_index=2,
                    error_key="error:key",
                    error_index=3,
                    error_type="str",
                    error_data=None,
                ),
                MagicMock(
                    # the null will raise `TypeError` and we test that it is handled
                    body=b'{"test": {"response": {"key": ["does_not_matter", "does_not_matter", null]}}}'
                ),
                "None",
                None,
            ),
            (
                dict(
                    **BASE_DUMMY_SPECS_CONFIG,
                    response_key="test:response:key",
                    response_index=2,  # this will raise `IndexError` and we test that it is handled
                    error_key="error:key",
                    error_index=3,
                    error_type="str",
                    error_data=None,
                ),
                MagicMock(
                    body=b'{"test": {"response": {"key": ["does_not_matter", "does_not_matter"]}}}'
                ),
                None,
                None,
            ),
            (
                dict(
                    **BASE_DUMMY_SPECS_CONFIG,
                    response_key="test:response:key",  # this will raise `KeyError` and we test that it is handled
                    response_index=2,
                    error_key="error:key",
                    error_index=3,
                    error_type="str",
                    error_data=None,
                ),
                MagicMock(
                    body=b'{"test": {"response": {"key_does_not_match": ["does_not_matter", "does_not_matter"]}}}'
                ),
                None,
                None,
            ),
            (
                dict(
                    **BASE_DUMMY_SPECS_CONFIG,
                    response_key="test:response:key",
                    response_index=2,
                    error_key="error:key",
                    error_index=3,
                    error_type="str",
                    error_data=None,
                ),
                MagicMock(
                    body=b'{"test": {"response": {"key_does_not_match": ["does_not_matter", "does_not_matter"]}}, '
                    b'"error": {"key": [0, 1, 2, "test that the error is being parsed correctly"]}}'
                ),
                None,
                "test that the error is being parsed correctly",
            ),
        ),
    )
    def test_process_response(
        self,
        api_specs_config: dict,
        message: MagicMock,
        expected_res: Any,
        expected_error: Any,
    ) -> None:
        """Test `process_response` method."""
        api_specs = ApiSpecs(**api_specs_config)
        actual = api_specs.process_response(message)
        assert actual == expected_res
        response_type = api_specs_config.get("response_type", None)
        if response_type is not None:
            assert type(actual) == getattr(builtins, response_type)
        assert api_specs.response_info.error_data == expected_error

    def test_attribute_manipulation(self) -> None:
        """Test manipulating the attributes."""
        with pytest.raises(AttributeError, match="This object is frozen!"):
            del self.api_specs.url

        with pytest.raises(AttributeError, match="This object is frozen!"):
            self.api_specs.url = ""

        self.api_specs.__dict__["_frozen"] = False
        self.api_specs.url = ""
        del self.api_specs.url


class ConcreteRound(AbstractRound):
    """A ConcreteRoundA for testing purposes."""

    synchronized_data_class = MagicMock()
    payload_attribute = MagicMock()
    payload_class = MagicMock()

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Enum]]:
        """Handle the end of the block."""


class SharedState(BaseSharedState):
    """Shared State for testing purposes."""

    abci_app_cls = AbciAppTest


class TestSharedState:
    """Test SharedState(Model) class."""

    def test_initialization(self, *_: Any) -> None:
        """Test the initialization of the shared state."""
        SharedState(name="", skill_context=MagicMock())

    @staticmethod
    def dummy_state_setup(shared_state: SharedState) -> None:
        """Setup a shared state instance with dummy params."""
        shared_state.context.params.setup_params = {
            "test": [],
            "all_participants": list(range(4)),
        }
        shared_state.setup()

    @pytest.mark.parametrize(
        "acn_configured_agents, validator_to_agent, raises",
        (
            (
                {i for i in range(4)},
                {f"validator_address_{i}": i for i in range(4)},
                False,
            ),
            (
                {i for i in range(5)},
                {f"validator_address_{i}": i for i in range(4)},
                True,
            ),
            (
                {i for i in range(4)},
                {f"validator_address_{i}": i for i in range(5)},
                True,
            ),
        ),
    )
    def test_setup_slashing(
        self,
        acn_configured_agents: Set[str],
        validator_to_agent: Dict[str, str],
        raises: bool,
    ) -> None:
        """Test the `validator_to_agent` properties."""
        shared_state = SharedState(name="", skill_context=MagicMock())
        self.dummy_state_setup(shared_state)

        if not raises:
            shared_state.initial_tm_configs = dict.fromkeys(acn_configured_agents)
            shared_state.setup_slashing(validator_to_agent)
            assert shared_state.round_sequence.validator_to_agent == validator_to_agent

            status = shared_state.round_sequence.offence_status
            encoded_status = json.dumps(
                status,
                cls=OffenseStatusEncoder,
            )
            expected_status = {
                agent: OffenceStatus() for agent in acn_configured_agents
            }
            encoded_expected_status = json.dumps(
                expected_status, cls=OffenseStatusEncoder
            )

            assert encoded_status == encoded_expected_status

            random_agent = acn_configured_agents.pop()
            status[random_agent].num_unknown_offenses = 10
            assert status[random_agent].num_unknown_offenses == 10

            for other_agent in acn_configured_agents - {random_agent}:
                assert status[other_agent].num_unknown_offenses == 0

            return

        expected_diff = acn_configured_agents.symmetric_difference(
            validator_to_agent.values()
        )
        with pytest.raises(
            ValueError,
            match=re.escape(
                f"Trying to use the mapping `{validator_to_agent}`, which contains validators for non-configured "
                "agents and/or does not contain validators for some configured agents. The agents which have been "
                f"configured via ACN are `{acn_configured_agents}` and the diff was for {expected_diff}."
            ),
        ):
            shared_state.initial_tm_configs = dict.fromkeys(acn_configured_agents)
            shared_state.setup_slashing(validator_to_agent)

    def test_setup(self, *_: Any) -> None:
        """Test setup method."""
        shared_state = SharedState(
            name="", skill_context=MagicMock(is_abstract_component=False)
        )
        assert shared_state.initial_tm_configs == {}
        self.dummy_state_setup(shared_state)
        assert shared_state.initial_tm_configs == {i: None for i in range(4)}

    @pytest.mark.parametrize(
        "initial_tm_configs, address_input, exception, expected",
        (
            (
                {},
                "0x1",
                "The validator address of non-participating agent `0x1` was requested.",
                None,
            ),
            ({}, "0x0", "SharedState's setup was not performed successfully.", None),
            (
                {"0x0": None},
                "0x0",
                "ACN registration has not been successfully performed for agent `0x0`. "
                "Have you set the `share_tm_config_on_startup` flag to `true` in the configuration?",
                None,
            ),
            (
                {"0x0": {}},
                "0x0",
                "The tendermint configuration for agent `0x0` is invalid: `{}`.",
                None,
            ),
            (
                {"0x0": {"address": None}},
                "0x0",
                "The tendermint configuration for agent `0x0` is invalid: `{'address': None}`.",
                None,
            ),
            (
                {"0x0": {"address": "test_validator_address"}},
                "0x0",
                None,
                "test_validator_address",
            ),
        ),
    )
    def test_get_validator_address(
        self,
        initial_tm_configs: Dict[str, Optional[Dict[str, Any]]],
        address_input: str,
        exception: Optional[str],
        expected: Optional[str],
    ) -> None:
        """Test `get_validator_address` method."""
        shared_state = SharedState(name="", skill_context=MagicMock())
        with mock.patch.object(shared_state.context, "params") as mock_params:
            mock_params.setup_params = {
                "all_participants": ["0x0"],
            }
            shared_state.setup()
            shared_state.initial_tm_configs = initial_tm_configs
            if exception is None:
                assert shared_state.get_validator_address(address_input) == expected
                return
            with pytest.raises(ValueError, match=exception):
                shared_state.get_validator_address(address_input)

    @pytest.mark.parametrize("self_idx", (range(4)))
    def test_acn_container(self, self_idx: int) -> None:
        """Test the `acn_container` method."""

        shared_state = SharedState(
            name="", skill_context=MagicMock(agent_address=self_idx)
        )
        self.dummy_state_setup(shared_state)
        expected = {i: None for i in range(4) if i != self_idx}
        assert shared_state.acn_container() == expected

    def test_synchronized_data_negative_not_available(self, *_: Any) -> None:
        """Test 'synchronized_data' property getter, negative case (not available)."""
        shared_state = SharedState(name="", skill_context=MagicMock())
        with pytest.raises(ValueError, match="round sequence not available"):
            shared_state.synchronized_data

    def test_synchronized_data_positive(self, *_: Any) -> None:
        """Test 'synchronized_data' property getter, negative case (not available)."""
        shared_state = SharedState(name="", skill_context=MagicMock())
        shared_state.context.params.setup_params = {
            "test": [],
            "all_participants": [["0x0"]],
        }
        shared_state.setup()
        shared_state.round_sequence.abci_app._round_results = [MagicMock()]
        shared_state.synchronized_data

    def test_synchronized_data_db(self, *_: Any) -> None:
        """Test 'synchronized_data' AbciAppDB."""
        shared_state = SharedState(name="", skill_context=MagicMock())
        with mock.patch.object(shared_state.context, "params") as mock_params:
            mock_params.setup_params = {
                "safe_contract_address": "0xsafe",
                "oracle_contract_address": "0xoracle",
                "all_participants": "0x0",
            }
            shared_state.setup()
            for key, value in mock_params.setup_params.items():
                assert shared_state.synchronized_data.db.get_strict(key) == value

    @pytest.mark.parametrize(
        "address_to_acn_deliverable, n_participants, expected",
        (
            ({}, 4, None),
            ({i: "test" for i in range(4)}, 4, "test"),
            (
                {i: TendermintRecoveryParams("test") for i in range(4)},
                4,
                TendermintRecoveryParams("test"),
            ),
            ({1: "test", 2: "non-matching", 3: "test", 4: "test"}, 4, "test"),
            ({i: "test" for i in range(4)}, 4, "test"),
            ({1: "no", 2: "result", 3: "matches", 4: ""}, 4, None),
        ),
    )
    def test_get_acn_result(
        self,
        address_to_acn_deliverable: Dict[str, Any],
        n_participants: int,
        expected: Optional[str],
    ) -> None:
        """Test `get_acn_result`."""
        shared_state = SharedState(
            abci_app_cls=AbciAppTest, name="", skill_context=MagicMock()
        )
        shared_state.context.params.setup_params = {
            "test": [],
            "all_participants": ["0x0"],
        }
        shared_state.setup()
        shared_state.synchronized_data.update(participants=tuple(range(n_participants)))
        shared_state.address_to_acn_deliverable = address_to_acn_deliverable
        actual = shared_state.get_acn_result()

        assert actual == expected

    def test_recovery_params_on_init(self) -> None:
        """Test that `tm_recovery_params` get initialized correctly."""
        shared_state = SharedState(name="", skill_context=MagicMock())
        assert shared_state.tm_recovery_params is not None
        assert shared_state.tm_recovery_params.round_count == ROUND_COUNT_DEFAULT
        assert (
            shared_state.tm_recovery_params.reset_from_round
            == AbciAppTest.initial_round_cls.auto_round_id()
        )
        assert shared_state.tm_recovery_params.reset_params is None

    def test_set_last_reset_params(self) -> None:
        """Test that `last_reset_params` get set correctly."""
        shared_state = SharedState(name="", skill_context=MagicMock())
        test_params = [("genesis_time", "some-time"), ("initial_height", "0")]
        shared_state.last_reset_params = test_params
        assert shared_state.last_reset_params == test_params


class TestBenchmarkTool:
    """Test BenchmarkTool"""

    @staticmethod
    def _check_behaviour_data(data: List, agent_name: str) -> None:
        """Check behaviour data."""
        assert len(data) == 1

        (behaviour_data,) = data
        assert behaviour_data["behaviour"] == agent_name
        assert all(
            [key in behaviour_data["data"] for key in ("local", "consensus", "total")]
        )

    def test_end_2_end(self) -> None:
        """Test end 2 end of the tool."""

        agent_name = "agent"
        skill_context = MagicMock(
            agent_address=agent_name, logger=MagicMock(info=logging.info)
        )

        with TemporaryDirectory() as temp_dir:
            benchmark = BenchmarkTool(
                name=agent_name, skill_context=skill_context, log_dir=temp_dir
            )

            with benchmark.measure(agent_name).local():
                sleep(1.0)

            with benchmark.measure(agent_name).consensus():
                sleep(1.0)

            self._check_behaviour_data(benchmark.data, agent_name)

            benchmark.save()

            benchmark_dir = Path(temp_dir, agent_name)
            benchmark_file = benchmark_dir / "0.json"
            assert (benchmark_file).is_file()

            behaviour_data = json.loads(benchmark_file.read_text())
            self._check_behaviour_data(behaviour_data, agent_name)


def test_requests_model_initialization() -> None:
    """Test initialization of the 'Requests(Model)' class."""
    Requests(name="", skill_context=MagicMock())


def test_base_params_model_initialization() -> None:
    """Test initialization of the 'BaseParams(Model)' class."""
    kwargs = BASE_DUMMY_PARAMS.copy()
    bp = BaseParams(**kwargs)

    with pytest.raises(AttributeError, match="This object is frozen!"):
        bp.request_timeout = 0.1

    with pytest.raises(AttributeError, match="This object is frozen!"):
        del bp.request_timeout

    bp.__dict__["_frozen"] = False
    del bp.request_timeout

    assert getattr(bp, "request_timeout", None) is None

    kwargs["skill_context"] = MagicMock(is_abstract_component=False)
    required_setup_params = {
        "safe_contract_address": "0x0",
        "all_participants": ["0x0"],
        "consensus_threshold": 1,
    }
    kwargs["setup"] = required_setup_params
    BaseParams(**kwargs)


@pytest.mark.parametrize(
    "setup, error_text",
    (
        ({}, "`setup` params contain no values!"),
        (
            {"a": "b"},
            "Value for `safe_contract_address` missing from the `setup` params.",
        ),
    ),
)
def test_incorrect_setup(setup: Dict[str, Any], error_text: str) -> None:
    """Test BaseParams model initialization with incorrect setup data."""
    kwargs = BASE_DUMMY_PARAMS.copy()

    with pytest.raises(
        AEAEnforceError,
        match=error_text,
    ):
        kwargs["skill_context"] = MagicMock(is_abstract_component=False)
        kwargs["setup"] = setup
        BaseParams(**kwargs)

    with pytest.raises(
        AEAEnforceError,
        match=f"`reset_pause_duration` must be greater than or equal to {MIN_RESET_PAUSE_DURATION}",
    ):
        kwargs["reset_pause_duration"] = MIN_RESET_PAUSE_DURATION - 1
        BaseParams(**kwargs)


def test_genesis_block() -> None:
    """Test genesis block methods."""
    json = {"max_bytes": "a", "max_gas": "b", "time_iota_ms": "c"}
    gb = GenesisBlock(**json)
    assert gb.to_json() == json

    with pytest.raises(TypeError, match="Error in field 'max_bytes'. Expected type .*"):
        json["max_bytes"] = 0  # type: ignore
        GenesisBlock(**json)


def test_genesis_evidence() -> None:
    """Test genesis evidence methods."""
    json = {"max_age_num_blocks": "a", "max_age_duration": "b", "max_bytes": "c"}
    ge = GenesisEvidence(**json)
    assert ge.to_json() == json


def test_genesis_validator() -> None:
    """Test genesis validator methods."""
    json = {"pub_key_types": ["a", "b"]}
    ge = GenesisValidator(pub_key_types=tuple(json["pub_key_types"]))
    assert ge.to_json() == json

    with pytest.raises(
        TypeError, match="Error in field 'pub_key_types'. Expected type .*"
    ):
        GenesisValidator(**json)  # type: ignore


def test_genesis_consensus_params() -> None:
    """Test genesis consensus params methods."""
    consensus_params = cast(Dict, irrelevant_genesis_config["consensus_params"])
    gcp = GenesisConsensusParams.from_json_dict(consensus_params)
    assert gcp.to_json() == consensus_params


def test_genesis_config() -> None:
    """Test genesis config methods."""
    gcp = GenesisConfig.from_json_dict(irrelevant_genesis_config)
    assert gcp.to_json() == irrelevant_genesis_config


def test_meta_shared_state_when_instance_not_subclass_of_shared_state() -> None:
    """Test instantiation of meta class when instance not a subclass of shared state."""

    class MySharedState(metaclass=_MetaSharedState):
        pass


def test_shared_state_instantiation_without_attributes_raises_error() -> None:
    """Test that definition of concrete subclass of SharedState without attributes raises error."""
    with pytest.raises(AttributeError, match="'abci_app_cls' not set on .*"):

        class MySharedState(BaseSharedState):
            pass

    with pytest.raises(AttributeError, match="The object `None` is not a class"):

        class MySharedStateB(BaseSharedState):
            abci_app_cls = None  # type: ignore

    with pytest.raises(
        AttributeError,
        match="The class <class 'unittest.mock.MagicMock'> is not an instance of packages.valory.skills.abstract_round_abci.base.AbciApp",
    ):

        class MySharedStateC(BaseSharedState):
            abci_app_cls = MagicMock


@dataclass
class A:
    """Class for testing."""

    value: int


@dataclass
class B:
    """Class for testing."""

    value: str


class C(TypedDict):
    """Class for testing."""

    name: str
    year: int


class D(TypedDict, total=False):
    """Class for testing."""

    name: str
    year: int


testdata_positive = [
    ("test_arg", 1, int),
    ("test_arg", "1", str),
    ("test_arg", True, bool),
    ("test_arg", 1, Optional[int]),
    ("test_arg", None, Optional[int]),
    ("test_arg", "1", Optional[str]),
    ("test_arg", None, Optional[str]),
    ("test_arg", None, Optional[bool]),
    ("test_arg", None, Optional[List[int]]),
    ("test_arg", [], Optional[List[int]]),
    ("test_arg", [1], Optional[List[int]]),
    ("test_arg", {"str": 1}, Optional[Dict[str, int]]),
    ("test_arg", {"str": A(1)}, Dict[str, A]),
    ("test_arg", [("1", "2")], List[Tuple[str, str]]),
    ("test_arg", [1], List[Optional[int]]),
    ("test_arg", [1, None], List[Optional[int]]),
    ("test_arg", A, Type[A]),
    ("test_arg", A, Optional[Type[A]]),
    ("test_arg", None, Optional[Type[A]]),
    ("test_arg", MagicMock(), Optional[Type[A]]),  # any type allowed
    ("test_arg", {"name": "str", "year": 1}, C),
    ("test_arg", 42, Literal[42]),
    ("test_arg", {"name": "str"}, D),
]


@pytest.mark.parametrize("name,value,type_hint", testdata_positive)
def test_type_check_positive(name: str, value: Any, type_hint: Any) -> None:
    """Test the type check mixin."""

    check_type(name, value, type_hint)


testdata_negative = [
    ("test_arg", "1", int),
    ("test_arg", 1, str),
    ("test_arg", None, bool),
    ("test_arg", "1", Optional[int]),
    ("test_arg", 1, Optional[str]),
    ("test_arg", 1, Optional[bool]),
    ("test_arg", ["1"], Optional[List[int]]),
    ("test_arg", {"str": "1"}, Optional[Dict[str, int]]),
    ("test_arg", {1: 1}, Optional[Dict[str, int]]),
    ("test_arg", {"str": B("1")}, Dict[str, A]),
    ("test_arg", [()], List[Tuple[str, str]]),
    ("test_arg", [("1",)], List[Tuple[str, str]]),
    ("test_arg", [("1", 1)], List[Tuple[str, str]]),
    ("test_arg", [("1", 1, "1")], List[Tuple[str, ...]]),
    ("test_arg", ["1"], List[Optional[int]]),
    ("test_arg", [1, None, "1"], List[Optional[int]]),
    ("test_arg", B, Type[A]),
    ("test_arg", B, Optional[Type[A]]),
    ("test_arg", {"name": "str", "year": "1"}, C),
    ("test_arg", 41, Literal[42]),
    ("test_arg", C({"name": "str", "year": 1}), A),
    ("test_arg", {"name": "str"}, C),
]


@pytest.mark.parametrize("name,value,type_hint", testdata_negative)
def test_type_check_negative(name: str, value: Any, type_hint: Any) -> None:
    """Test the type check mixin."""

    with pytest.raises(TypeError):
        check_type(name, value, type_hint)
