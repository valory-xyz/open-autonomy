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

"""Test the models.py module of the skill."""

# pylint: skip-file

import builtins
import json
import logging
from enum import Enum
from pathlib import Path
from tempfile import TemporaryDirectory
from time import sleep
from typing import Any, List, Optional, Tuple
from unittest import mock
from unittest.mock import MagicMock

import pytest

from packages.valory.skills.abstract_round_abci.base import (
    AbciApp,
    AbstractRound,
    BaseSynchronizedData,
)
from packages.valory.skills.abstract_round_abci.models import (
    ApiSpecs,
    BaseParams,
    BenchmarkTool,
    DEFAULT_BACKOFF_FACTOR,
    NUMBER_OF_RETRIES,
    Requests,
    SharedState,
)
from packages.valory.skills.abstract_round_abci.test_tools.abci_app import AbciAppTest


BASE_DUMMY_SPECS_CONFIG = dict(
    name="dummy",
    skill_context=MagicMock(),
    url="http://dummy",
    api_id="api_id",
    method="GET",
    headers=[["Dummy-Header", "dummy_value"]],
    parameters=[["Dummy-Param", "dummy_param"]],
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
        with pytest.raises(ValueError, match="Value for url is required by ApiSpecs"):
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
        assert self.api_specs.headers == [["Dummy-Header", "dummy_value"]]
        assert self.api_specs.parameters == [["Dummy-Param", "dummy_param"]]
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
            == DEFAULT_BACKOFF_FACTOR ** retries
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
            "headers": [["Dummy-Header", "dummy_value"]],
            "parameters": [["Dummy-Param", "dummy_param"]],
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
                    error_type=None,
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
                    response_type=None,
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
                    response_type=None,
                    error_key="error:key",
                    error_index=3,
                    error_type="str",
                    error_data=None,
                ),
                MagicMock(
                    # the null will raise `TypeError` and we test that it is handled
                    body=b'{"test": {"response": {"key": ["does_not_matter", "does_not_matter", null]}}}'
                ),
                None,
                None,
            ),
            (
                dict(
                    **BASE_DUMMY_SPECS_CONFIG,
                    response_key="test:response:key",
                    response_index=2,  # this will raise `IndexError` and we test that it is handled
                    response_type=None,
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
                    response_type=None,
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
                    response_type=None,
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
        response_type = api_specs_config["response_type"]
        if response_type is not None:
            assert type(actual) == getattr(builtins, response_type)
        assert api_specs.response_info.error_data == expected_error


class ConcreteRound(AbstractRound):
    """A ConcreteRoundA for testing purposes."""

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Enum]]:
        """Handle the end of the block."""


class TestSharedState:
    """Test SharedState(Model) class."""

    @mock.patch.object(SharedState, "_process_abci_app_cls")
    def test_initialization(self, *_: Any) -> None:
        """Test the initialization of the shared state."""
        SharedState(abci_app_cls=MagicMock(), name="", skill_context=MagicMock())

    @mock.patch.object(SharedState, "_process_abci_app_cls")
    def test_setup(self, *_: Any) -> None:
        """Test setup method."""
        shared_state = SharedState(
            abci_app_cls=MagicMock, name="", skill_context=MagicMock()
        )
        shared_state.context.params.setup_params = {"test": []}
        shared_state.context.params.consensus_params = MagicMock()
        shared_state.setup()

    @mock.patch.object(SharedState, "_process_abci_app_cls")
    def test_synchronized_data_negative_not_available(self, *_: Any) -> None:
        """Test 'synchronized_data' property getter, negative case (not available)."""
        shared_state = SharedState(
            abci_app_cls=AbciAppTest, name="", skill_context=MagicMock()
        )
        with mock.patch.object(shared_state.context, "params"):
            with pytest.raises(ValueError, match="round sequence not available"):
                shared_state.synchronized_data

    @mock.patch.object(SharedState, "_process_abci_app_cls")
    def test_synchronized_data_positive(self, *_: Any) -> None:
        """Test 'synchronized_data' property getter, negative case (not available)."""
        shared_state = SharedState(
            abci_app_cls=AbciAppTest, name="", skill_context=MagicMock()
        )
        shared_state.context.params.setup_params = {"test": []}
        shared_state.context.params.consensus_params = MagicMock()
        shared_state.setup()
        shared_state.round_sequence.abci_app._round_results = [MagicMock()]
        shared_state.synchronized_data

    def test_synchronized_data_db(self, *_: Any) -> None:
        """Test 'synchronized_data' AbciAppDB."""
        shared_state = SharedState(
            abci_app_cls=AbciAppTest, name="", skill_context=MagicMock()
        )
        with mock.patch.object(shared_state.context, "params") as mock_params:
            mock_params.setup_params = {
                "safe_contract_address": ["0xsafe"],
                "oracle_contract_address": ["0xoracle"],
            }
            shared_state.setup()
            assert (
                shared_state.synchronized_data.db.get_strict("safe_contract_address")
                == "0xsafe"
            )
            assert (
                shared_state.synchronized_data.db.get_strict("oracle_contract_address")
                == "0xoracle"
            )

    def test_process_abci_app_cls_negative_not_a_class(self) -> None:
        """Test '_process_abci_app_cls', negative case (not a class)."""
        mock_obj = MagicMock()
        with pytest.raises(ValueError, match=f"The object {mock_obj} is not a class"):
            SharedState._process_abci_app_cls(mock_obj)

    def test_process_abci_app_cls_negative_not_subclass_of_abstract_round(
        self,
    ) -> None:
        """Test '_process_abci_app_cls', negative case (not subclass of AbstractRound)."""
        with pytest.raises(
            ValueError,
            match=f"The class {MagicMock} is not an instance of {AbciApp.__module__}.{AbciApp.__name__}",
        ):
            SharedState._process_abci_app_cls(MagicMock)

    def test_process_abci_app_cls_positive(self) -> None:
        """Test '_process_abci_app_cls', positive case."""

        SharedState._process_abci_app_cls(AbciAppTest)

    def test_last_reset_params_on_init(self) -> None:
        """Test that `last_reset_params` gets initialized correctly."""
        # by default `last_reset_params` should be None
        shared_state = SharedState(
            abci_app_cls=AbciAppTest, name="", skill_context=MagicMock()
        )
        assert shared_state.last_reset_params is None

    def test_set_last_reset_params(self) -> None:
        """Test that `last_reset_params` get set correctly."""
        shared_state = SharedState(
            abci_app_cls=AbciAppTest, name="", skill_context=MagicMock()
        )
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
    BaseParams(
        name="",
        skill_context=MagicMock(),
        setup={},
        consensus=dict(max_participants=1),
        tendermint_url="",
        max_healthcheck=1,
        round_timeout_seconds=1,
        sleep_time=1,
        retry_timeout=1,
        retry_attempts=1,
        observation_interval=1,
        drand_public_key="",
        tendermint_com_url="",
        reset_tendermint_after=1,
        service_id="abstract_round_abci",
        service_registry_address="0xa51c1fc2f0d1a1b8494ed1fe312d7c3a78ed91c0",
        keeper_timeout=1.0,
        tendermint_check_sleep_delay=3,
        tendermint_max_retries=5,
        cleanup_history_depth=0,
        genesis_config={"voting_power": "0"},
    )
