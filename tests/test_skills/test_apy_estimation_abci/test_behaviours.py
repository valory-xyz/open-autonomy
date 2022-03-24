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

"""Tests for valory/apy_estimation_abci skill's behaviours."""
import binascii
import json
import logging
import os
import time
from datetime import datetime
from enum import Enum
from itertools import product
from multiprocessing.pool import AsyncResult
from pathlib import Path, PosixPath
from typing import Any, Callable, Dict, Tuple, Type, Union, cast
from unittest import mock
from uuid import uuid4

import numpy as np
import optuna
import pandas as pd
import pytest
from _pytest.logging import LogCaptureFixture
from _pytest.monkeypatch import MonkeyPatch
from aea.skills.tasks import TaskManager
from pmdarima.pipeline import Pipeline

from packages.valory.protocols.abci import AbciMessage  # noqa: F401
from packages.valory.skills.abstract_round_abci.base import AbciApp, StateDB
from packages.valory.skills.abstract_round_abci.behaviour_utils import BaseState
from packages.valory.skills.abstract_round_abci.io.store import SupportedFiletype
from packages.valory.skills.abstract_round_abci.models import ApiSpecs, BenchmarkTool
from packages.valory.skills.apy_estimation_abci.behaviours import (
    APYEstimationBaseState,
    CycleResetBehaviour,
    EstimateBehaviour,
    EstimatorRoundBehaviour,
    FetchBatchBehaviour,
    FetchBehaviour,
    FreshModelResetBehaviour,
    OptimizeBehaviour,
    PrepareBatchBehaviour,
    PreprocessBehaviour,
    RandomnessBehaviour,
)
from packages.valory.skills.apy_estimation_abci.behaviours import (
    TestBehaviour as _TestBehaviour,
)
from packages.valory.skills.apy_estimation_abci.behaviours import (
    TrainBehaviour,
    TransformBehaviour,
    UpdateForecasterBehaviour,
)
from packages.valory.skills.apy_estimation_abci.rounds import Event, PeriodState
from packages.valory.skills.apy_estimation_abci.tools.etl import ResponseItemType

from tests.conftest import ROOT_DIR
from tests.test_skills.base import FSMBehaviourBaseCase
from tests.test_skills.test_apy_estimation_abci.conftest import DummyPipeline


SLEEP_TIME_TWEAK = 0.01

ipfs_daemon = pytest.mark.usefixtures("ipfs_daemon")


class DummyAsyncResult(object):
    """Dummy class for AsyncResult."""

    def __init__(
        self,
        task_result: Any,
        ready: bool = True,
    ) -> None:
        """Initialize class."""

        self.id = uuid4()
        self._ready = ready
        self._task_result = task_result

    def ready(
        self,
    ) -> bool:
        """Returns bool"""
        return self._ready

    def get(
        self,
    ) -> Any:
        """Returns task result."""
        return self._task_result


@ipfs_daemon
class APYEstimationFSMBehaviourBaseCase(FSMBehaviourBaseCase):
    """Base case for testing APYEstimation FSMBehaviour."""

    path_to_skill = Path(
        ROOT_DIR, "packages", "valory", "skills", "apy_estimation_abci"
    )

    behaviour: EstimatorRoundBehaviour
    behaviour_class: Type[APYEstimationBaseState]
    next_behaviour_class: Type[APYEstimationBaseState]
    period_state: PeriodState

    @classmethod
    def setup(cls, **kwargs: Any) -> None:
        """Set up the test class."""
        super().setup(
            param_overrides={"ipfs_domain_name": "/dns/localhost/tcp/5001/http"}
        )
        cls.period_state = PeriodState(
            StateDB(
                initial_period=0,
                initial_data={"full_training": False, "pair_name": "test"},
            )
        )

    def end_round(self, done_event: Enum = Event.DONE) -> None:
        """Ends round early to cover `wait_for_end` generator."""
        super().end_round(done_event)


class TestFetchAndBatchBehaviours(APYEstimationFSMBehaviourBaseCase):
    """Test FetchBehaviour and FetchBatchBehaviour."""

    behaviour_class = FetchBehaviour
    next_behaviour_class = TransformBehaviour

    @pytest.mark.parametrize("batch_flag", (True, False))
    def test_setup(self, monkeypatch: MonkeyPatch, batch_flag: bool) -> None:
        """Test behaviour setup."""
        self.skill.skill_context.state.period.abci_app._last_timestamp = datetime.now()

        self.fast_forward_to_state(
            self.behaviour,
            self.behaviour_class.state_id,
            self.period_state,
        )
        cast(FetchBehaviour, self.behaviour.current_state).batch = batch_flag

        monkeypatch.setattr(os.path, "join", lambda *_: "")
        cast(APYEstimationBaseState, self.behaviour.current_state).setup()

    def test_handle_response(self, caplog: LogCaptureFixture) -> None:
        """Test `handle_response`."""
        self.fast_forward_to_state(
            self.behaviour,
            self.behaviour_class.state_id,
            self.period_state,
        )
        cast(
            FetchBehaviour, self.behaviour.current_state
        ).params.sleep_time = SLEEP_TIME_TWEAK

        # test with empty response.
        specs = ApiSpecs(
            url="test",
            api_id="test",
            method="GET",
            name="test",
            skill_context=self.behaviour.context,
        )

        handling_generator = cast(
            FetchBehaviour, self.behaviour.current_state
        )._handle_response(None, "test_context", ("", 0), specs)
        next(handling_generator)
        time.sleep(SLEEP_TIME_TWEAK + 0.01)
        try:
            next(handling_generator)
        except StopIteration as res:
            assert res.value is None
        with caplog.at_level(
            logging.ERROR,
            logger="aea.test_agent_name.packages.valory.skills.apy_estimation_abci",
        ):
            assert (
                "[test_agent_name] Could not get test_context from test" in caplog.text
            )
            assert specs._retries_attempted == 1

        caplog.clear()
        with caplog.at_level(
            logging.INFO,
            logger="aea.test_agent_name.packages.valory.skills.apy_estimation_abci",
        ):
            handling_generator = cast(
                FetchBehaviour, self.behaviour.current_state
            )._handle_response({"test": [4, 5]}, "test", ("test", 0), specs)
            try:
                next(handling_generator)
            except StopIteration as res:
                assert res.value == 4
            assert "[test_agent_name] Retrieved test: 4." in caplog.text
            assert specs._retries_attempted == 0

    def test_fetch_behaviour(
        self,
        block_from_timestamp_q: str,
        eth_price_usd_q: str,
        pairs_q: str,
        pool_fields: Tuple[str, ...],
    ) -> None:
        """Run tests."""
        history_duration = cast(
            FetchBehaviour, self.behaviour.current_state
        ).params.history_duration
        self.skill.skill_context.state.period.abci_app._last_timestamp = (
            datetime.utcfromtimestamp(1618735147 + history_duration * 30 * 24 * 60 * 60)
        )

        self.fast_forward_to_state(
            self.behaviour, FetchBehaviour.state_id, self.period_state
        )
        cast(FetchBehaviour, self.behaviour.current_state).params.pair_ids = [
            "0xec454eda10accdd66209c57af8c12924556f3abd"
        ]

        request_kwargs: Dict[str, Union[str, bytes]] = dict(
            method="POST",
            url="https://api.thegraph.com/subgraphs/name/eerieeight/spookyswap",
            headers="Content-Type: application/json\r\n",
            version="",
        )
        response_kwargs = dict(
            version="",
            status_code=200,
            status_text="",
            headers="",
        )

        # block request.
        request_kwargs[
            "url"
        ] = "https://api.thegraph.com/subgraphs/name/matthewlilley/fantom-blocks"
        request_kwargs["body"] = json.dumps({"query": block_from_timestamp_q}).encode(
            "utf-8"
        )
        res = {"data": {"blocks": [{"timestamp": "1", "number": "3830367"}]}}
        response_kwargs["body"] = json.dumps(res).encode("utf-8")
        self.behaviour.act_wrapper()
        self.mock_http_request(request_kwargs, response_kwargs)

        # ETH price request.
        request_kwargs[
            "url"
        ] = "https://api.thegraph.com/subgraphs/name/eerieeight/spookyswap"
        request_kwargs["body"] = json.dumps({"query": eth_price_usd_q}).encode("utf-8")
        res = {"data": {"bundles": [{"ethPrice": "0.8973548"}]}}
        response_kwargs["body"] = json.dumps(res).encode("utf-8")
        self.behaviour.act_wrapper()
        self.mock_http_request(request_kwargs, response_kwargs)

        # top pairs data.
        request_kwargs["body"] = json.dumps({"query": pairs_q}).encode("utf-8")
        res = {
            "data": {
                "pairs": [
                    {field: dummy_value for field in pool_fields}
                    for dummy_value in ("dum1", "dum2")
                ]
            }
        }
        response_kwargs["body"] = json.dumps(res).encode("utf-8")
        self.behaviour.act_wrapper()
        self.mock_http_request(request_kwargs, response_kwargs)

        self.end_round()
        state = cast(BaseState, self.behaviour.current_state)
        assert state.state_id == TransformBehaviour.state_id

    def test_fetch_behaviour_retries_exceeded(
        self, monkeypatch: MonkeyPatch, caplog: LogCaptureFixture
    ) -> None:
        """Run tests for exceeded retries."""
        self.skill.skill_context.state.period.abci_app._last_timestamp = datetime.now()

        self.fast_forward_to_state(
            self.behaviour, FetchBehaviour.state_id, self.period_state
        )

        subgraphs_sorted_by_utilization_moment: Tuple[Any, ...] = (
            self.behaviour.context.spooky_subgraph,
            self.behaviour.context.fantom_subgraph,
            self.behaviour.context.spooky_subgraph,
            self.behaviour.context.spooky_subgraph,
        )

        for subgraph in subgraphs_sorted_by_utilization_moment:
            monkeypatch.setattr(subgraph, "is_retries_exceeded", lambda *_: True)
            with caplog.at_level(
                logging.ERROR,
                logger="aea.test_agent_name.packages.valory.skills.apy_estimation_abci",
            ):
                self.behaviour.act_wrapper()
                self.behaviour.act_wrapper()
            assert (
                "Retries were exceeded while downloading the historical data!"
                in caplog.text
            )

    def test_fetch_value_none(
        self,
        caplog: LogCaptureFixture,
        block_from_timestamp_q: str,
        eth_price_usd_q: str,
        pairs_q: str,
        pool_fields: Tuple[str, ...],
    ) -> None:
        """Test when fetched value is none."""
        history_duration = cast(
            FetchBehaviour, self.behaviour.current_state
        ).params.history_duration
        self.skill.skill_context.state.period.abci_app._last_timestamp = (
            datetime.utcfromtimestamp(1618735147 + history_duration * 30 * 24 * 60 * 60)
        )
        self.fast_forward_to_state(
            self.behaviour, FetchBehaviour.state_id, self.period_state
        )
        cast(FetchBehaviour, self.behaviour.current_state).params.pair_ids = [
            "0xec454eda10accdd66209c57af8c12924556f3abd"
        ]
        cast(
            FetchBehaviour, self.behaviour.current_state
        ).params.sleep_time = SLEEP_TIME_TWEAK

        request_kwargs: Dict[str, Union[str, bytes]] = dict(
            method="POST",
            url="https://api.thegraph.com/subgraphs/name/eerieeight/spookyswap",
            headers="Content-Type: application/json\r\n",
            version="",
            body=b"",
        )
        response_kwargs = dict(
            version="",
            status_code=200,
            status_text="",
            headers="",
            body=b"",
        )

        # block request with None response.
        request_kwargs[
            "url"
        ] = "https://api.thegraph.com/subgraphs/name/matthewlilley/fantom-blocks"
        request_kwargs["body"] = json.dumps({"query": block_from_timestamp_q}).encode(
            "utf-8"
        )
        response_kwargs["body"] = b""

        with caplog.at_level(
            logging.ERROR,
            logger="aea.test_agent_name.packages.valory.skills.apy_estimation_abci",
        ):
            self.behaviour.act_wrapper()
            self.mock_http_request(request_kwargs, response_kwargs)
        assert "[test_agent_name] Could not get block from fantom" in caplog.text

        caplog.clear()
        time.sleep(SLEEP_TIME_TWEAK + 0.01)
        self.behaviour.act_wrapper()

        # block request.
        request_kwargs[
            "url"
        ] = "https://api.thegraph.com/subgraphs/name/matthewlilley/fantom-blocks"
        request_kwargs["body"] = json.dumps({"query": block_from_timestamp_q}).encode(
            "utf-8"
        )
        res = {"data": {"blocks": [{"timestamp": "1", "number": "3830367"}]}}
        response_kwargs["body"] = json.dumps(res).encode("utf-8")
        self.behaviour.act_wrapper()
        self.mock_http_request(request_kwargs, response_kwargs)

        # ETH price request with None response.
        request_kwargs[
            "url"
        ] = "https://api.thegraph.com/subgraphs/name/eerieeight/spookyswap"
        request_kwargs["body"] = json.dumps({"query": eth_price_usd_q}).encode("utf-8")
        response_kwargs["body"] = b""

        with caplog.at_level(
            logging.ERROR,
            logger="aea.test_agent_name.packages.valory.skills.apy_estimation_abci",
        ):
            self.behaviour.act_wrapper()
            self.mock_http_request(request_kwargs, response_kwargs)
        assert (
            "[test_agent_name] Could not get ETH price for block "
            "{'timestamp': '1', 'number': '3830367'} from spookyswap" in caplog.text
        )

        caplog.clear()
        time.sleep(SLEEP_TIME_TWEAK + 0.01)
        self.behaviour.act_wrapper()

        # block request.
        request_kwargs[
            "url"
        ] = "https://api.thegraph.com/subgraphs/name/matthewlilley/fantom-blocks"
        request_kwargs["body"] = json.dumps({"query": block_from_timestamp_q}).encode(
            "utf-8"
        )
        res = {"data": {"blocks": [{"timestamp": "1", "number": "3830367"}]}}
        response_kwargs["body"] = json.dumps(res).encode("utf-8")
        self.behaviour.act_wrapper()
        self.mock_http_request(request_kwargs, response_kwargs)

        # ETH price request.
        request_kwargs[
            "url"
        ] = "https://api.thegraph.com/subgraphs/name/eerieeight/spookyswap"
        request_kwargs["body"] = json.dumps({"query": eth_price_usd_q}).encode("utf-8")
        res = {"data": {"bundles": [{"ethPrice": "0.8973548"}]}}
        response_kwargs["body"] = json.dumps(res).encode("utf-8")
        self.behaviour.act_wrapper()
        self.mock_http_request(request_kwargs, response_kwargs)

        # top pairs data with None response.
        request_kwargs["body"] = json.dumps({"query": pairs_q}).encode("utf-8")
        response_kwargs["body"] = b""

        with caplog.at_level(
            logging.ERROR,
            logger="aea.test_agent_name.packages.valory.skills.apy_estimation_abci",
        ):
            self.behaviour.act_wrapper()
            self.mock_http_request(request_kwargs, response_kwargs)
        assert (
            "[test_agent_name] Could not get pool data for block {'timestamp': '1', 'number': '3830367'} "
            "from spookyswap" in caplog.text
        )

        caplog.clear()
        time.sleep(SLEEP_TIME_TWEAK + 0.01)
        self.behaviour.act_wrapper()

    def test_fetch_behaviour_stop_iteration(
        self,
        monkeypatch: MonkeyPatch,
        tmp_path: PosixPath,
        caplog: LogCaptureFixture,
        no_action: Callable[[Any], None],
    ) -> None:
        """Test `FetchBehaviour`'s `async_act` after all the timestamps have been generated."""
        self.skill.skill_context.state.period.abci_app._last_timestamp = datetime.now()

        # fast-forward to fetch behaviour.
        self.fast_forward_to_state(
            self.behaviour, FetchBehaviour.state_id, self.period_state
        )
        # set history duration to a negative value in order to raise a `StopIteration`.
        cast(FetchBehaviour, self.behaviour.current_state).params.history_duration = -1

        # test empty retrieved history.
        with caplog.at_level(
            logging.ERROR,
            logger="aea.test_agent_name.packages.valory.skills.apy_estimation_abci",
        ):
            self.behaviour.act_wrapper()
        assert "Could not download any historical data!" in caplog.text
        self.mock_a2a_transaction()
        self._test_done_flag_set()
        self.end_round()

        # fast-forward to fetch behaviour.
        self.fast_forward_to_state(
            self.behaviour, FetchBehaviour.state_id, self.period_state
        )

        # test with retrieved history and valid save path.
        cast(FetchBehaviour, self.behaviour.current_state)._pairs_hist = [
            {"test": "test"}
        ]
        self.behaviour.context._agent_context._data_dir = tmp_path  # type: ignore
        self.behaviour.act_wrapper()
        self.mock_a2a_transaction()
        self._test_done_flag_set()
        self.end_round()
        state = cast(BaseState, self.behaviour.current_state)
        assert state.state_id == TransformBehaviour.state_id

        # fast-forward to fetch behaviour.
        self.fast_forward_to_state(
            self.behaviour, FetchBehaviour.state_id, self.period_state
        )

    def test_clean_up(
        self,
    ) -> None:
        """Test clean-up."""
        self.fast_forward_to_state(
            self.behaviour, FetchBehaviour.state_id, self.period_state
        )

        self.behaviour.context.spooky_subgraph._retries_attempted = 1
        self.behaviour.context.fantom_subgraph._retries_attempted = 1
        assert self.behaviour.current_state is not None
        self.behaviour.current_state.clean_up()
        assert self.behaviour.context.spooky_subgraph._retries_attempted == 0
        assert self.behaviour.context.fantom_subgraph._retries_attempted == 0


class TestTransformBehaviour(APYEstimationFSMBehaviourBaseCase):
    """Test TransformBehaviour."""

    behaviour_class = TransformBehaviour
    next_behaviour_class = PreprocessBehaviour

    def _fast_forward(self, tmp_path: PosixPath, ipfs_succeed: bool = True) -> None:
        """Setup `TestTransformBehaviour`."""
        # Set data directory to a temporary path for tests.
        self.behaviour.context._agent_context._data_dir = tmp_path  # type: ignore

        # Send historical data to IPFS and get the hash.
        if ipfs_succeed:
            hash_ = cast(BaseState, self.behaviour.current_state).send_to_ipfs(
                os.path.join(tmp_path, "historical_data.json"),
                {"test": "test"},
                SupportedFiletype.JSON,
            )
        else:
            hash_ = "test"

        self.fast_forward_to_state(
            self.behaviour,
            self.behaviour_class.state_id,
            PeriodState(
                StateDB(
                    initial_period=0,
                    initial_data=dict(
                        most_voted_randomness=0, most_voted_history=hash_
                    ),
                )
            ),
        )

        assert (
            cast(APYEstimationBaseState, self.behaviour.current_state).state_id
            == self.behaviour_class.state_id
        )

    def test_setup(self, tmp_path: PosixPath) -> None:
        """Test behaviour setup."""
        self._fast_forward(tmp_path)
        self.behaviour.context.task_manager.start()
        cast(TransformBehaviour, self.behaviour.current_state).setup()

    def test_task_not_ready(
        self,
        monkeypatch: MonkeyPatch,
        caplog: LogCaptureFixture,
        tmp_path: PosixPath,
        transform_task_result: pd.DataFrame,
    ) -> None:
        """Run test for `transform_behaviour` when task result is not ready."""
        self._fast_forward(tmp_path)
        monkeypatch.setattr(
            TaskManager,
            "get_task_result",
            lambda *_: DummyAsyncResult(transform_task_result, ready=False),
        )

        with caplog.at_level(
            logging.DEBUG,
            logger="aea.test_agent_name.packages.valory.skills.apy_estimation_abci",
        ):
            self.behaviour.context.task_manager.start()

            cast(
                TransformBehaviour, self.behaviour.current_state
            ).params.sleep_time = SLEEP_TIME_TWEAK
            self.behaviour.act_wrapper()

            # Sleep to wait for the behaviour that is also sleeping.
            time.sleep(SLEEP_TIME_TWEAK + 0.01)

            # Continue the `async_act` after the sleep of the Behaviour.
            self.behaviour.act_wrapper()

        assert (
            "[test_agent_name] Entered in the 'transform' behaviour state"
            in caplog.text
        )

        assert (
            "[test_agent_name] The transform task is not finished yet." in caplog.text
        )

        self.end_round()

    @pytest.mark.parametrize("ipfs_succeed", (True, False))
    def test_transform_behaviour(
        self,
        monkeypatch: MonkeyPatch,
        tmp_path: PosixPath,
        transform_task_result: pd.DataFrame,
        ipfs_succeed: bool,
    ) -> None:
        """Run test for `transform_behaviour`."""
        self._fast_forward(tmp_path, ipfs_succeed)

        monkeypatch.setattr(
            "packages.valory.skills.apy_estimation_abci.tasks.transform_hist_data",
            lambda _: transform_task_result,
        )
        monkeypatch.setattr(
            self._skill._skill_context._agent_context._task_manager,  # type: ignore
            "get_task_result",
            lambda *_: DummyAsyncResult(transform_task_result),
        )
        monkeypatch.setattr(
            self._skill._skill_context._agent_context._task_manager,  # type: ignore
            "enqueue_task",
            lambda *_, **__: 3,
        )

        self.behaviour.act_wrapper()
        self.mock_a2a_transaction()
        self._test_done_flag_set()
        self.end_round()

        state = cast(BaseState, self.behaviour.current_state)
        assert state.state_id == self.next_behaviour_class.state_id


class TestPreprocessBehaviour(APYEstimationFSMBehaviourBaseCase):
    """Test PreprocessBehaviour."""

    behaviour_class = PreprocessBehaviour
    next_behaviour_class = RandomnessBehaviour

    @pytest.mark.parametrize("data_found", (True, False))
    def test_preprocess_behaviour(
        self,
        data_found: bool,
        transformed_historical_data_no_datetime_conversion: pd.DataFrame,
        tmp_path: PosixPath,
    ) -> None:
        """Run test for `preprocess_behaviour`."""
        initial_data_dir = self.behaviour.context._agent_context._data_dir  # type: ignore
        self.behaviour.context._agent_context._data_dir = tmp_path  # type: ignore
        # Increase the amount of dummy data for the train-test split.
        transformed_historical_data = pd.DataFrame(
            np.repeat(
                transformed_historical_data_no_datetime_conversion.values, 3, axis=0
            ),
            columns=transformed_historical_data_no_datetime_conversion.columns,
        )

        hash_ = (
            cast(BaseState, self.behaviour.current_state).send_to_ipfs(
                os.path.join(tmp_path, "transformed_historical_data.csv"),
                transformed_historical_data,
                SupportedFiletype.CSV,
            )
            if data_found
            else "non_existing"
        )

        self.fast_forward_to_state(
            self.behaviour,
            self.behaviour_class.state_id,
            PeriodState(
                StateDB(initial_period=0, initial_data=dict(most_voted_transform=hash_))
            ),
        )

        state = cast(BaseState, self.behaviour.current_state)
        assert state.state_id == self.behaviour_class.state_id

        self.behaviour.act_wrapper()
        self.mock_a2a_transaction()
        self._test_done_flag_set()
        self.end_round()
        state = cast(BaseState, self.behaviour.current_state)
        assert state.state_id == self.next_behaviour_class.state_id
        self.behaviour.context._agent_context._data_dir = initial_data_dir  # type: ignore


class TestPrepareBatchBehaviour(APYEstimationFSMBehaviourBaseCase):
    """Test `PrepareBatchBehaviour`."""

    behaviour_class = PrepareBatchBehaviour
    next_behaviour_class = UpdateForecasterBehaviour

    def _fast_forward(
        self,
        tmp_path: PosixPath,
        transformed_historical_data: pd.DataFrame,
        batch: ResponseItemType,
        ipfs_succeed: bool = True,
    ) -> None:
        """Setup `PrepareBatchBehaviour`."""
        # Set data directory to a temporary path for tests.
        self.behaviour.context._agent_context._data_dir = tmp_path  # type: ignore

        # Create a dictionary with all the dummy data to send to IPFS.
        data_to_send = {
            "hist": {
                "filepath": os.path.join(tmp_path, "latest_observation.csv"),
                "obj": transformed_historical_data.iloc[[0]].reset_index(drop=True),
                "filetype": SupportedFiletype.CSV,
            },
            "batch": {
                "filepath": os.path.join(tmp_path, "historical_data_batch_0.json"),
                "obj": batch,
                "filetype": SupportedFiletype.JSON,
            },
        }

        # Send dummy data to IPFS and get the hashes.
        if ipfs_succeed:
            hashes = {}
            for item_name, item_args in data_to_send.items():
                hashes[item_name] = cast(
                    BaseState, self.behaviour.current_state
                ).send_to_ipfs(**item_args)
        else:
            hashes = {item_name: "test" for item_name, _ in data_to_send.items()}

        # fast-forward to the `PrepareBatchBehaviour` state.
        self.fast_forward_to_state(
            self.behaviour,
            self.behaviour_class.state_id,
            PeriodState(
                StateDB(
                    initial_period=0,
                    initial_data=dict(
                        latest_observation_hist_hash=hashes["hist"],
                        most_voted_batch=hashes["batch"],
                        latest_observation_timestamp=0,
                    ),
                )
            ),
        )

        assert (
            cast(APYEstimationBaseState, self.behaviour.current_state).state_id
            == self.behaviour_class.state_id
        )

    def test_prepare_batch_behaviour_setup(
        self,
        tmp_path: PosixPath,
        transformed_historical_data_no_datetime_conversion: pd.DataFrame,
        batch: ResponseItemType,
    ) -> None:
        """Test behaviour setup."""
        self._fast_forward(
            tmp_path, transformed_historical_data_no_datetime_conversion, batch
        )
        cast(PrepareBatchBehaviour, self.behaviour.current_state).setup()

    @pytest.mark.parametrize("ipfs_succeed", (True, False))
    def test_prepare_batch_behaviour(
        self,
        tmp_path: PosixPath,
        transformed_historical_data_no_datetime_conversion: pd.DataFrame,
        batch: ResponseItemType,
        ipfs_succeed: bool,
    ) -> None:
        """Run test for `preprocess_behaviour`."""
        self._fast_forward(
            tmp_path,
            transformed_historical_data_no_datetime_conversion,
            batch,
            ipfs_succeed,
        )

        state = cast(BaseState, self.behaviour.current_state)
        assert state.state_id == self.behaviour_class.state_id

        self.behaviour.act_wrapper()
        self.mock_a2a_transaction()
        self._test_done_flag_set()
        self.end_round()
        state = cast(BaseState, self.behaviour.current_state)
        assert state.state_id == self.next_behaviour_class.state_id


class TestRandomnessBehaviour(APYEstimationFSMBehaviourBaseCase):
    """Test RandomnessBehaviour."""

    randomness_behaviour_class = RandomnessBehaviour  # type: ignore
    next_behaviour_class = OptimizeBehaviour

    drand_response = {
        "round": 1416669,
        "randomness": "f6be4bf1fa229f22340c1a5b258f809ac4af558200775a67dacb05f0cb258a11",
        "signature": (
            "b44d00516f46da3a503f9559a634869b6dc2e5d839e46ec61a090e3032172954929a5"
            "d9bd7197d7739fe55db770543c71182562bd0ad20922eb4fe6b8a1062ed21df3b68de"
            "44694eb4f20b35262fa9d63aa80ad3f6172dd4d33a663f21179604"
        ),
        "previous_signature": (
            "903c60a4b937a804001032499a855025573040cb86017c38e2b1c3725286756ce8f33"
            "61188789c17336beaf3f9dbf84b0ad3c86add187987a9a0685bc5a303e37b008fba8c"
            "44f02a416480dd117a3ff8b8075b1b7362c58af195573623187463"
        ),
    }

    def test_randomness_behaviour(
        self,
    ) -> None:
        """Test RandomnessBehaviour."""

        self.fast_forward_to_state(
            self.behaviour,
            self.randomness_behaviour_class.state_id,
            self.period_state,
        )
        assert (
            cast(
                BaseState,
                cast(BaseState, self.behaviour.current_state),
            ).state_id
            == self.randomness_behaviour_class.state_id
        )
        self.behaviour.act_wrapper()
        self.mock_http_request(
            request_kwargs=dict(
                method="GET",
                headers="",
                version="",
                body=b"",
                url="https://drand.cloudflare.com/public/latest",
            ),
            response_kwargs=dict(
                version="",
                status_code=200,
                status_text="",
                headers="",
                body=json.dumps(self.drand_response).encode("utf-8"),
            ),
        )

        self.behaviour.act_wrapper()
        self.mock_a2a_transaction()
        self._test_done_flag_set()
        self.end_round()

        state = cast(BaseState, self.behaviour.current_state)
        assert state.state_id == self.next_behaviour_class.state_id

    def test_invalid_drand_value(
        self,
    ) -> None:
        """Test invalid drand values."""
        self.fast_forward_to_state(
            self.behaviour,
            self.randomness_behaviour_class.state_id,
            self.period_state,
        )
        assert (
            cast(
                BaseState,
                cast(BaseState, self.behaviour.current_state),
            ).state_id
            == self.randomness_behaviour_class.state_id
        )
        self.behaviour.act_wrapper()

        drand_invalid = self.drand_response.copy()
        drand_invalid["randomness"] = binascii.hexlify(b"randomness_hex").decode()
        self.mock_http_request(
            request_kwargs=dict(
                method="GET",
                headers="",
                version="",
                body=b"",
                url="https://drand.cloudflare.com/public/latest",
            ),
            response_kwargs=dict(
                version="",
                status_code=200,
                status_text="",
                headers="",
                body=json.dumps(drand_invalid).encode(),
            ),
        )

    def test_invalid_response(
        self,
    ) -> None:
        """Test invalid json response."""
        self.fast_forward_to_state(
            self.behaviour,
            self.randomness_behaviour_class.state_id,
            self.period_state,
        )
        assert (
            cast(
                BaseState,
                cast(BaseState, self.behaviour.current_state),
            ).state_id
            == self.randomness_behaviour_class.state_id
        )
        cast(
            RandomnessBehaviour, self.behaviour.current_state
        ).params.sleep_time = SLEEP_TIME_TWEAK

        self.behaviour.act_wrapper()

        self.mock_http_request(
            request_kwargs=dict(
                method="GET",
                headers="",
                version="",
                body=b"",
                url="https://drand.cloudflare.com/public/latest",
            ),
            response_kwargs=dict(
                version="", status_code=200, status_text="", headers="", body=b""
            ),
        )
        self.behaviour.act_wrapper()
        time.sleep(SLEEP_TIME_TWEAK + 0.01)
        self.behaviour.act_wrapper()

    def test_max_retries_reached(
        self,
    ) -> None:
        """Test with max retries reached."""
        self.fast_forward_to_state(
            self.behaviour,
            self.randomness_behaviour_class.state_id,
            self.period_state,
        )
        assert (
            cast(
                BaseState,
                cast(BaseState, self.behaviour.current_state),
            ).state_id
            == self.randomness_behaviour_class.state_id
        )
        with mock.patch.object(
            self.behaviour.context.randomness_api,
            "is_retries_exceeded",
            return_value=True,
        ):
            self.behaviour.act_wrapper()
            state = cast(BaseState, self.behaviour.current_state)
            assert state.state_id == self.randomness_behaviour_class.state_id
            self._test_done_flag_set()

    def test_clean_up(
        self,
    ) -> None:
        """Test when `observed` value is none."""
        self.fast_forward_to_state(
            self.behaviour,
            self.randomness_behaviour_class.state_id,
            self.period_state,
        )
        assert (
            cast(
                BaseState,
                cast(BaseState, self.behaviour.current_state),
            ).state_id
            == self.randomness_behaviour_class.state_id
        )
        self.behaviour.context.randomness_api._retries_attempted = 1
        assert self.behaviour.current_state is not None
        self.behaviour.current_state.clean_up()
        assert self.behaviour.context.randomness_api._retries_attempted == 0


class TestOptimizeBehaviour(APYEstimationFSMBehaviourBaseCase):
    """Test OptimizeBehaviour."""

    behaviour_class = OptimizeBehaviour
    next_behaviour_class = TrainBehaviour

    def _fast_forward(
        self,
        tmp_path: PosixPath,
        ipfs_succeed: bool = True,
    ) -> None:
        """Setup `OptimizeBehaviour`."""
        # Set data directory to a temporary path for tests.
        self.behaviour.context._agent_context._data_dir = tmp_path.parts[0]  # type: ignore
        cast(OptimizeBehaviour, self.behaviour.current_state).params.pair_ids[
            0
        ] = os.path.join(*tmp_path.parts[1:])

        # Create a dictionary with all the dummy data to send to IPFS.
        data_to_send = {}
        for split in ("train", "test"):
            data_to_send[split] = {
                "filepath": os.path.join(tmp_path, f"y_{split}.csv"),
                "obj": pd.DataFrame([i for i in range(5)]),
                "filetype": SupportedFiletype.CSV,
            }

        # Send dummy data to IPFS and get the hashes.
        if ipfs_succeed:
            hashes = {}
            for item_name, item_args in data_to_send.items():
                hashes[item_name] = cast(
                    BaseState, self.behaviour.current_state
                ).send_to_ipfs(**item_args)
        else:
            hashes = {item_name: "test" for item_name, _ in data_to_send.items()}

        # fast-forward to the `OptimizeBehaviour` state.
        self.fast_forward_to_state(
            self.behaviour,
            self.behaviour_class.state_id,
            PeriodState(
                StateDB(
                    initial_period=0,
                    initial_data=dict(
                        most_voted_randomness=0,
                        most_voted_split=hashes["train"] + hashes["test"],
                    ),
                )
            ),
        )

        assert (
            cast(APYEstimationBaseState, self.behaviour.current_state).state_id
            == self.behaviour_class.state_id
        )

    def test_setup(
        self,
        monkeypatch: MonkeyPatch,
        tmp_path: PosixPath,
        optimize_task_result_empty: optuna.Study,
    ) -> None:
        """Test behaviour setup."""
        self._fast_forward(tmp_path)

        monkeypatch.setattr(TaskManager, "enqueue_task", lambda *_, **__: 0)
        monkeypatch.setattr(
            TaskManager,
            "get_task_result",
            lambda *_: DummyAsyncResult(optimize_task_result_empty),
        )
        cast(APYEstimationBaseState, self.behaviour.current_state).setup()

    def test_task_not_ready(
        self,
        monkeypatch: MonkeyPatch,
        tmp_path: PosixPath,
        optimize_task_result_empty: optuna.Study,
    ) -> None:
        """Run test for behaviour when task result is not ready."""
        self._fast_forward(tmp_path)

        monkeypatch.setattr(TaskManager, "enqueue_task", lambda *_, **__: 0)
        monkeypatch.setattr(
            TaskManager,
            "get_task_result",
            lambda *_: DummyAsyncResult(optimize_task_result_empty, ready=False),
        )

        cast(
            OptimizeBehaviour, self.behaviour.current_state
        ).params.sleep_time = SLEEP_TIME_TWEAK
        self.behaviour.act_wrapper()
        time.sleep(SLEEP_TIME_TWEAK + 0.01)
        self.behaviour.act_wrapper()

        assert (
            cast(APYEstimationBaseState, self.behaviour.current_state).state_id
            == self.behaviour_class.state_id
        )

    def test_optimize_behaviour_value_error(
        self,
        monkeypatch: MonkeyPatch,
        tmp_path: PosixPath,
        caplog: LogCaptureFixture,
        optimize_task_result_empty: optuna.Study,
    ) -> None:
        """Run test for `optimize_behaviour` when `ValueError` is raised."""
        self._fast_forward(tmp_path)

        monkeypatch.setattr(TaskManager, "enqueue_task", lambda *_, **__: 3)
        monkeypatch.setattr(
            TaskManager,
            "get_task_result",
            lambda *_: DummyAsyncResult(optimize_task_result_empty),
        )

        # test ValueError handling.
        with caplog.at_level(
            logging.WARNING,
            logger="aea.test_agent_name.packages.valory.skills.apy_estimation_abci",
        ):
            self.behaviour.act_wrapper()

        assert (
            "The optimization could not be done! "
            "Please make sure that there is a sufficient number of data for the optimization procedure. "
            "Setting best parameters randomly!"
        ) in caplog.text

    @pytest.mark.parametrize("ipfs_succeed", (True, False))
    def test_optimize_behaviour(
        self,
        monkeypatch: MonkeyPatch,
        tmp_path: PosixPath,
        optimize_task_result: optuna.Study,
        ipfs_succeed: bool,
    ) -> None:
        """Run test for `optimize_behaviour`."""
        self._fast_forward(tmp_path, ipfs_succeed)

        monkeypatch.setattr(TaskManager, "enqueue_task", lambda *_, **__: 3)
        monkeypatch.setattr(
            TaskManager,
            "get_task_result",
            lambda *_: DummyAsyncResult(optimize_task_result),
        )

        self.behaviour.act_wrapper()
        self.mock_a2a_transaction()
        self._test_done_flag_set()
        self.end_round()

        state = cast(BaseState, self.behaviour.current_state)
        assert state.state_id == self.next_behaviour_class.state_id


class TestTrainBehaviour(APYEstimationFSMBehaviourBaseCase):
    """Test TrainBehaviour."""

    behaviour_class = TrainBehaviour
    next_behaviour_class = _TestBehaviour

    def _fast_forward(
        self,
        tmp_path: PosixPath,
        ipfs_succeed: bool = True,
        full_training: bool = False,
    ) -> None:
        """Setup `TestTrainBehaviour`."""
        # Set data directory to a temporary path for tests.
        self.behaviour.context._agent_context._data_dir = tmp_path.parts[0]  # type: ignore
        cast(OptimizeBehaviour, self.behaviour.current_state).params.pair_ids[
            0
        ] = os.path.join(*tmp_path.parts[1:])

        # Create a dictionary with all the dummy data to send to IPFS.
        data_to_send = {
            "params": {
                "filepath": os.path.join(tmp_path, "best_params.json"),
                "obj": {"p": 1, "q": 1, "d": 1, "m": 1},
                "filetype": SupportedFiletype.JSON,
            }
        }
        for split in ("train", "test"):
            data_to_send[split] = {
                "filepath": os.path.join(tmp_path, f"y_{split}.csv"),
                "obj": pd.DataFrame([i for i in range(5)]),
                "filetype": SupportedFiletype.CSV,
            }

        # Send dummy data to IPFS and get the hashes.
        if ipfs_succeed:
            hashes = {}
            for item_name, item_args in data_to_send.items():
                hashes[item_name] = cast(
                    BaseState, self.behaviour.current_state
                ).send_to_ipfs(**item_args)
        else:
            hashes = {item_name: "test" for item_name, _ in data_to_send.items()}

        # fast-forward to the `TrainBehaviour` state.
        self.fast_forward_to_state(
            self.behaviour,
            self.behaviour_class.state_id,
            PeriodState(
                StateDB(
                    initial_period=0,
                    initial_data=dict(
                        full_training=full_training,
                        most_voted_params=hashes["params"],
                        most_voted_split=hashes["train"] + hashes["test"],
                    ),
                )
            ),
        )

        assert (
            cast(APYEstimationBaseState, self.behaviour.current_state).state_id
            == self.behaviour_class.state_id
        )

    @pytest.mark.parametrize(
        "full_training, ipfs_succeed", product((True, False), repeat=2)
    )
    def test_setup(
        self,
        monkeypatch: MonkeyPatch,
        tmp_path: PosixPath,
        no_action: Callable[[Any], None],
        ipfs_succeed: bool,
        full_training: bool,
    ) -> None:
        """Test behaviour setup."""
        self._fast_forward(tmp_path, ipfs_succeed, full_training)

        monkeypatch.setattr(TaskManager, "enqueue_task", lambda *_, **__: 0)
        monkeypatch.setattr(TaskManager, "get_task_result", lambda *_: no_action)

        cast(APYEstimationBaseState, self.behaviour.current_state).setup()

    def test_task_not_ready(
        self,
        monkeypatch: MonkeyPatch,
        tmp_path: PosixPath,
    ) -> None:
        """Run test for behaviour when task result is not ready."""
        self._fast_forward(tmp_path)

        self.behaviour.context.task_manager.start()

        monkeypatch.setattr(AsyncResult, "ready", lambda *_: False)
        cast(
            TrainBehaviour, self.behaviour.current_state
        ).params.sleep_time = SLEEP_TIME_TWEAK
        self.behaviour.act_wrapper()
        time.sleep(SLEEP_TIME_TWEAK + 0.01)
        self.behaviour.act_wrapper()

        assert (
            cast(APYEstimationBaseState, self.behaviour.current_state).state_id
            == self.behaviour_class.state_id
        )

    @pytest.mark.parametrize("ipfs_succeed", (True, False))
    def test_train_behaviour(
        self,
        monkeypatch: MonkeyPatch,
        tmp_path: PosixPath,
        train_task_result: Pipeline,
        ipfs_succeed: bool,
    ) -> None:
        """Run test for `optimize_behaviour`."""
        self._fast_forward(tmp_path, ipfs_succeed)

        monkeypatch.setattr(TaskManager, "enqueue_task", lambda *_, **__: 3)
        monkeypatch.setattr(
            TaskManager,
            "get_task_result",
            lambda *_: DummyAsyncResult(train_task_result),
        )

        # act.
        self.behaviour.act_wrapper()
        self.mock_a2a_transaction()
        self._test_done_flag_set()
        self.end_round()

        state = cast(BaseState, self.behaviour.current_state)
        assert state.state_id == self.next_behaviour_class.state_id


class TestTestBehaviour(APYEstimationFSMBehaviourBaseCase):
    """Test TestBehaviour."""

    behaviour_class = _TestBehaviour
    next_behaviour_class = TrainBehaviour

    def _fast_forward(
        self,
        tmp_path: PosixPath,
        ipfs_succeed: bool = True,
    ) -> None:
        """Setup `TestTrainBehaviour`."""
        # Set data directory to a temporary path for tests.
        self.behaviour.context._agent_context._data_dir = tmp_path.parts[0]  # type: ignore
        cast(OptimizeBehaviour, self.behaviour.current_state).params.pair_ids[
            0
        ] = os.path.join(*tmp_path.parts[1:])

        # Create a dictionary with all the dummy data to send to IPFS.
        data_to_send = {
            "model": {
                "filepath": os.path.join(tmp_path, "forecaster.joblib"),
                "obj": DummyPipeline(),
                "filetype": SupportedFiletype.PM_PIPELINE,
            }
        }
        for split in ("train", "test"):
            data_to_send[split] = {
                "filepath": os.path.join(tmp_path, f"y_{split}.csv"),
                "obj": pd.DataFrame([i for i in range(5)]),
                "filetype": SupportedFiletype.CSV,
            }

        # Send dummy data to IPFS and get the hashes.
        if ipfs_succeed:
            hashes = {}
            for item_name, item_args in data_to_send.items():
                hashes[item_name] = cast(
                    BaseState, self.behaviour.current_state
                ).send_to_ipfs(**item_args)
        else:
            hashes = {item_name: "test" for item_name, _ in data_to_send.items()}

        # fast-forward to the `TestBehaviour` state.
        self.fast_forward_to_state(
            self.behaviour,
            self.behaviour_class.state_id,
            PeriodState(
                StateDB(
                    initial_period=0,
                    initial_data=dict(
                        pair_name="test",
                        most_voted_model=hashes["model"],
                        most_voted_split=hashes["train"] + hashes["test"],
                    ),
                )
            ),
        )

        assert (
            cast(APYEstimationBaseState, self.behaviour.current_state).state_id
            == self.behaviour_class.state_id
        )

    @pytest.mark.parametrize("ipfs_succeed", (True, False))
    def test_setup(
        self,
        monkeypatch: MonkeyPatch,
        tmp_path: PosixPath,
        ipfs_succeed: bool,
        no_action: Callable[[Any], None],
    ) -> None:
        """Test behaviour setup."""
        self._fast_forward(tmp_path, ipfs_succeed)

        monkeypatch.setattr(TaskManager, "enqueue_task", lambda *_, **__: 0)
        monkeypatch.setattr(TaskManager, "get_task_result", lambda *_: no_action)

        cast(APYEstimationBaseState, self.behaviour.current_state).setup()

    def test_task_not_ready(
        self,
        monkeypatch: MonkeyPatch,
        tmp_path: PosixPath,
        no_action: Callable[[Any], None],
    ) -> None:
        """Run test for behaviour when task result is not ready."""
        self._fast_forward(tmp_path)

        self.behaviour.context.task_manager.start()
        monkeypatch.setattr(AsyncResult, "ready", lambda *_: False)
        cast(
            _TestBehaviour, self.behaviour.current_state
        ).params.sleep_time = SLEEP_TIME_TWEAK
        self.behaviour.act_wrapper()
        time.sleep(SLEEP_TIME_TWEAK + 0.01)
        self.behaviour.act_wrapper()

        assert (
            cast(APYEstimationBaseState, self.behaviour.current_state).state_id
            == self.behaviour_class.state_id
        )

    @pytest.mark.parametrize("ipfs_succeed", (True, False))
    def test_test_behaviour(
        self,
        monkeypatch: MonkeyPatch,
        tmp_path: PosixPath,
        ipfs_succeed: bool,
        test_task_result: Dict[str, str],
    ) -> None:
        """Run test for `optimize_behaviour`."""
        self._fast_forward(tmp_path, ipfs_succeed)

        monkeypatch.setattr(TaskManager, "enqueue_task", lambda *_, **__: 3)
        monkeypatch.setattr(
            TaskManager,
            "get_task_result",
            lambda *_: DummyAsyncResult(test_task_result),
        )

        # test act.
        self.behaviour.act_wrapper()
        self.mock_a2a_transaction()
        self._test_done_flag_set()
        self.end_round()

        state = cast(BaseState, self.behaviour.current_state)
        assert state.state_id == self.next_behaviour_class.state_id


class TestUpdateForecasterBehaviour(APYEstimationFSMBehaviourBaseCase):
    """Test `UpdateForecasterBehaviour`."""

    behaviour_class = UpdateForecasterBehaviour
    next_behaviour_class = EstimateBehaviour

    def _fast_forward(self, tmp_path: PosixPath, ipfs_succeed: bool = True) -> None:
        """Setup `TestUpdateForecasterBehaviour`."""
        # Set data directory to a temporary path for tests.
        self.behaviour.context._agent_context._data_dir = tmp_path.parts[0]  # type: ignore
        cast(OptimizeBehaviour, self.behaviour.current_state).params.pair_ids[
            0
        ] = os.path.join(*tmp_path.parts[1:])

        # Create a dictionary with all the dummy data to send to IPFS.
        data_to_send = {
            "model": {
                "filepath": os.path.join(tmp_path, "fully_trained_forecaster.joblib"),
                "obj": DummyPipeline(),
                "filetype": SupportedFiletype.PM_PIPELINE,
            },
            "observation": {
                "filepath": os.path.join(tmp_path, "latest_observation.csv"),
                "obj": pd.DataFrame({"APY": [0, 1]}),
                "filetype": SupportedFiletype.CSV,
            },
        }

        # Send dummy data to IPFS and get the hashes.
        if ipfs_succeed:
            hashes = {}
            for item_name, item_args in data_to_send.items():
                hashes[item_name] = cast(
                    BaseState, self.behaviour.current_state
                ).send_to_ipfs(**item_args)
        else:
            hashes = {item_name: "test" for item_name, _ in data_to_send.items()}

        # fast-forward to the `TestBehaviour` state.
        self.fast_forward_to_state(
            self.behaviour,
            self.behaviour_class.state_id,
            PeriodState(
                StateDB(
                    initial_period=0,
                    initial_data=dict(
                        most_voted_model=hashes["model"],
                        latest_observation_hist_hash=hashes["observation"],
                    ),
                )
            ),
        )

        assert (
            cast(APYEstimationBaseState, self.behaviour.current_state).state_id
            == self.behaviour_class.state_id
        )

    @pytest.mark.parametrize("ipfs_succeed", (True, False))
    def test_update_forecaster_setup(
        self,
        tmp_path: PosixPath,
        ipfs_succeed: bool,
    ) -> None:
        """Run test for `UpdateForecasterBehaviour`'s setup method."""
        self._fast_forward(tmp_path, ipfs_succeed)
        cast(UpdateForecasterBehaviour, self.behaviour.current_state).setup()

    @pytest.mark.parametrize("ipfs_succeed", (True, False))
    def test_update_forecaster_behaviour(
        self,
        tmp_path: PosixPath,
        monkeypatch: MonkeyPatch,
        ipfs_succeed: bool,
    ) -> None:
        """Run test for `UpdateForecasterBehaviour`."""
        self._fast_forward(tmp_path, ipfs_succeed)

        self.behaviour.act_wrapper()
        self.mock_a2a_transaction()
        self._test_done_flag_set()
        self.end_round()
        state = cast(UpdateForecasterBehaviour, self.behaviour.current_state)
        assert state.state_id == self.next_behaviour_class.state_id


class TestEstimateBehaviour(APYEstimationFSMBehaviourBaseCase):
    """Test EstimateBehaviour."""

    behaviour_class = EstimateBehaviour
    next_behaviour_class = FreshModelResetBehaviour

    def _fast_forward(self, tmp_path: PosixPath, ipfs_succeed: bool) -> None:
        """Setup `TestTransformBehaviour`."""
        # Set data directory to a temporary path for tests.
        self.behaviour.context._agent_context._data_dir = tmp_path  # type: ignore

        # Send historical data to IPFS and get the hash.
        if ipfs_succeed:
            hash_ = cast(BaseState, self.behaviour.current_state).send_to_ipfs(
                os.path.join(tmp_path, "fully_trained_forecaster.joblib"),
                DummyPipeline(),
                SupportedFiletype.PM_PIPELINE,
            )
        else:
            hash_ = "test"

        self.fast_forward_to_state(
            self.behaviour,
            self.behaviour_class.state_id,
            PeriodState(
                StateDB(
                    initial_period=0,
                    initial_data=dict(pair_name="test", most_voted_model=hash_),
                )
            ),
        )

        assert (
            cast(APYEstimationBaseState, self.behaviour.current_state).state_id
            == self.behaviour_class.state_id
        )

    @pytest.mark.parametrize("ipfs_succeed", (True, False))
    def test_estimate_behaviour(
        self,
        monkeypatch: MonkeyPatch,
        tmp_path: PosixPath,
        ipfs_succeed: bool,
    ) -> None:
        """Run test for `EstimateBehaviour`."""
        self._fast_forward(tmp_path, ipfs_succeed)

        self.behaviour.act_wrapper()
        self.mock_a2a_transaction()
        self._test_done_flag_set()
        self.end_round()
        state = cast(BaseState, self.behaviour.current_state)
        assert state.state_id == self.next_behaviour_class.state_id


class TestCycleResetBehaviour(APYEstimationFSMBehaviourBaseCase):
    """Test CycleResetBehaviour."""

    behaviour_class = CycleResetBehaviour
    next_behaviour_class = FetchBatchBehaviour

    def test_reset_behaviour(
        self,
        monkeypatch: MonkeyPatch,
        no_action: Callable[[Any], None],
    ) -> None:
        """Test reset behaviour."""
        self.fast_forward_to_state(
            behaviour=self.behaviour,
            state_id=self.behaviour_class.state_id,
            period_state=PeriodState(
                StateDB(initial_period=0, initial_data=dict(most_voted_estimate=8.1))
            ),
        )
        state = cast(BaseState, self.behaviour.current_state)
        assert state.state_id == self.behaviour_class.state_id

        monkeypatch.setattr(BenchmarkTool, "save", lambda _: no_action)
        monkeypatch.setattr(AbciApp, "last_timestamp", datetime.now())
        cast(
            CycleResetBehaviour, self.behaviour.current_state
        ).params.observation_interval = SLEEP_TIME_TWEAK
        self.behaviour.act_wrapper()
        time.sleep(SLEEP_TIME_TWEAK + 0.01)
        self.behaviour.act_wrapper()

        self.mock_a2a_transaction()
        self._test_done_flag_set()
        self.end_round()

        state = cast(BaseState, self.behaviour.current_state)
        assert state.state_id == self.next_behaviour_class.state_id

    def test_reset_behaviour_without_most_voted_estimate(
        self,
        monkeypatch: MonkeyPatch,
        no_action: Callable[[Any], None],
        caplog: LogCaptureFixture,
    ) -> None:
        """Test reset behaviour without most voted estimate."""
        self.fast_forward_to_state(
            behaviour=self.behaviour,
            state_id=self.behaviour_class.state_id,
            period_state=PeriodState(
                StateDB(initial_period=0, initial_data=dict(most_voted_estimate=None))
            ),
        )
        state = cast(BaseState, self.behaviour.current_state)
        assert state.state_id == self.behaviour_class.state_id

        monkeypatch.setattr(BenchmarkTool, "save", lambda _: no_action)
        monkeypatch.setattr(AbciApp, "last_timestamp", datetime.now())

        self.behaviour.context.params.observation_interval = 0.1

        with caplog.at_level(
            logging.INFO,
            logger="aea.test_agent_name.packages.valory.skills.apy_estimation_abci",
        ):
            self.behaviour.act_wrapper()
            cast(
                CycleResetBehaviour, self.behaviour.current_state
            ).params.sleep_time = SLEEP_TIME_TWEAK
            time.sleep(SLEEP_TIME_TWEAK + 0.01)
            self.behaviour.act_wrapper()

        assert (
            "[test_agent_name] Entered in the 'cycle_reset' behaviour state"
            in caplog.text
        )
        assert (
            "[test_agent_name] Finalized estimate not available. Resetting!"
            in caplog.text
        )

        self.mock_a2a_transaction()
        self._test_done_flag_set()
        self.end_round()

        state = cast(BaseState, self.behaviour.current_state)
        assert state.state_id == self.next_behaviour_class.state_id


class TestFreshModelResetBehaviour(APYEstimationFSMBehaviourBaseCase):
    """Test FreshModelResetBehaviour."""

    behaviour_class = FreshModelResetBehaviour
    next_behaviour_class = FetchBehaviour

    def test_fresh_model_reset_behaviour(self, caplog: LogCaptureFixture) -> None:
        """Run test for `ResetBehaviour`."""
        self.fast_forward_to_state(
            behaviour=self.behaviour,
            state_id=self.behaviour_class.state_id,
            period_state=PeriodState(StateDB(initial_period=0, initial_data={})),
        )
        state = cast(BaseState, self.behaviour.current_state)
        assert state.state_id == self.behaviour_class.state_id

        with caplog.at_level(
            logging.INFO,
            logger="aea.test_agent_name.packages.valory.skills.apy_estimation_abci",
        ):
            self.behaviour.act_wrapper()

        assert (
            "[test_agent_name] Entered in the 'fresh_model_reset' behaviour state"
            in caplog.text
        )
        assert (
            "[test_agent_name] Resetting to create a fresh forecasting model!"
            in caplog.text
        )

        self.mock_a2a_transaction()
        self._test_done_flag_set()
        self.end_round()

        state = cast(BaseState, self.behaviour.current_state)
        assert state.state_id == self.next_behaviour_class.state_id
