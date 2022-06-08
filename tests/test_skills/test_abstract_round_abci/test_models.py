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
from aea.skills.base import SkillContext

from packages.valory.skills.abstract_round_abci.base import (
    AbciApp,
    AbstractRound,
    BaseSynchronizedData,
)
from packages.valory.skills.abstract_round_abci.models import (
    ApiSpecs,
    BaseParams,
    BenchmarkTool,
    NUMBER_OF_RETRIES,
    Requests,
    SharedState,
)

from tests.test_skills.test_abstract_round_abci.test_base import AbciAppTest


class DummyMessage:
    """Dummy api specs class."""

    body: bytes

    def __init__(self, body: bytes) -> None:
        """Initializes DummyMessage"""
        self.body = body


class TestApiSpecsModel:
    """Test ApiSpecsModel."""

    api_specs: ApiSpecs

    def setup(
        self,
    ) -> None:
        """Setup test."""

        self.api_specs = ApiSpecs(
            name="price_api",
            skill_context=SkillContext(),
            url="http://localhost",
            api_id="api_id",
            method="GET",
            headers=[["Dummy-Header", "dummy_value"]],
            parameters=[["Dummy-Param", "dummy_param"]],
            response_key="value",
            response_type="float",
            retries=NUMBER_OF_RETRIES,
        )

    def test_init(
        self,
    ) -> None:
        """Test initialization."""

        # test ensure method.
        with pytest.raises(ValueError, match="Value for url is required by ApiSpecs"):
            _ = ApiSpecs(
                name="price_api",
                skill_context=SkillContext(),
            )

        assert self.api_specs._retries == NUMBER_OF_RETRIES
        assert self.api_specs._retries_attempted == 0

        assert self.api_specs.url == "http://localhost"
        assert self.api_specs.api_id == "api_id"
        assert self.api_specs.method == "GET"
        assert self.api_specs.headers == [["Dummy-Header", "dummy_value"]]
        assert self.api_specs.parameters == [["Dummy-Param", "dummy_param"]]
        assert self.api_specs.response_key == "value"
        assert self.api_specs.response_type == "float"

    def test_retries(
        self,
    ) -> None:
        """Tests for retries."""

        self.api_specs.increment_retries()
        assert self.api_specs._retries_attempted == 1
        assert not self.api_specs.is_retries_exceeded()

        for _ in range(NUMBER_OF_RETRIES):
            self.api_specs.increment_retries()
        assert self.api_specs.is_retries_exceeded()
        self.api_specs.reset_retries()
        assert self.api_specs._retries_attempted == 0

    def test_get_spec(
        self,
    ) -> None:
        """Test get_spec method."""

        actual_specs = {
            "url": "http://localhost",
            "method": "GET",
            "headers": [["Dummy-Header", "dummy_value"]],
            "parameters": [["Dummy-Param", "dummy_param"]],
        }

        specs = self.api_specs.get_spec()
        assert all([key in specs for key in actual_specs.keys()])
        assert all([specs[key] == actual_specs[key] for key in actual_specs])

    def test_process_response_with_depth_0(
        self,
    ) -> None:
        """Test process_response method."""

        value = self.api_specs.process_response(DummyMessage(b""))  # type: ignore
        assert value is None

        value = self.api_specs.process_response(
            DummyMessage(b'{"value": "10.232"}')  # type: ignore
        )
        assert isinstance(value, float)

    def test_process_response_with_depth_1(
        self,
    ) -> None:
        """Test process_response method."""

        api_specs = ApiSpecs(
            name="price_api",
            skill_context=SkillContext(),
            url="http://localhost",
            api_id="api_id",
            method="GET",
            headers="Dummy-Header:dummy_value",
            parameters="Dummy-Param:dummy_param",
            response_key="value_0:value_1",
            response_type="float",
            retries=NUMBER_OF_RETRIES,
        )

        value = api_specs.process_response(
            DummyMessage(b'{"value_0": {"value_1": "10.232"}}')  # type: ignore
        )
        assert isinstance(value, float)

    def test_process_response_with_key_none(
        self,
    ) -> None:
        """Test process_response method."""

        api_specs = ApiSpecs(
            name="price_api",
            skill_context=SkillContext(),
            url="http://localhost",
            api_id="api_id",
            method="GET",
            headers="Dummy-Header:dummy_value",
            parameters="Dummy-Param:dummy_param",
            response_key=None,
            response_type=None,
            retries=NUMBER_OF_RETRIES,
        )

        value = api_specs.process_response(
            DummyMessage(b'{"value": "10.232"}')  # type: ignore
        )
        assert isinstance(value, dict)


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
    )
