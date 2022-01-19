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

"""Tests for valory/apy_estimation_abci skill's behaviours."""
import binascii
import importlib
import json
import logging
import os
import re
import time
from copy import copy
from datetime import datetime
from multiprocessing.pool import AsyncResult
from pathlib import Path, PosixPath
from typing import Any, Callable, Dict, FrozenSet, Tuple, Type, Union, cast
from unittest import mock
from unittest.mock import patch
from uuid import uuid4

import joblib
import numpy as np
import optuna
import pandas as pd
import pytest
from _pytest.logging import LogCaptureFixture
from _pytest.monkeypatch import MonkeyPatch
from aea.exceptions import AEAActException
from aea.helpers.ipfs.base import IPFSHashOnly
from aea.helpers.transaction.base import SignedMessage
from aea.skills.tasks import TaskManager
from aea.test_tools.test_skill import BaseSkillTestCase
from aea_cli_ipfs.ipfs_utils import IPFSTool
from pmdarima import ARIMA
from pmdarima.pipeline import Pipeline
from pmdarima.preprocessing import FourierFeaturizer

from packages.open_aea.protocols.signing import SigningMessage
from packages.valory.connections.http_client.connection import (
    PUBLIC_ID as HTTP_CLIENT_PUBLIC_ID,
)
from packages.valory.protocols.abci import AbciMessage  # noqa: F401
from packages.valory.protocols.http import HttpMessage
from packages.valory.skills.abstract_round_abci.base import (
    AbciApp,
    AbstractRound,
    BasePeriodState,
    BaseTxPayload,
    OK_CODE,
    StateDB,
    _MetaPayload,
)
from packages.valory.skills.abstract_round_abci.behaviour_utils import BaseState
from packages.valory.skills.abstract_round_abci.behaviours import AbstractRoundBehaviour
from packages.valory.skills.abstract_round_abci.handlers import (
    ContractApiHandler,
    HttpHandler,
    LedgerApiHandler,
    SigningHandler,
)
from packages.valory.skills.abstract_round_abci.models import ApiSpecs
from packages.valory.skills.abstract_round_abci.utils import BenchmarkTool
from packages.valory.skills.apy_estimation_abci.behaviours import (
    APYEstimationBaseState,
    APYEstimationConsensusBehaviour,
    CycleResetBehaviour,
    EstimateBehaviour,
    FetchBatchBehaviour,
    FetchBehaviour,
    FreshModelResetBehaviour,
    OptimizeBehaviour,
    PrepareBatchBehaviour,
    PreprocessBehaviour,
    RandomnessBehaviour,
    RegistrationBehaviour,
    ResetBehaviour,
    TendermintHealthcheckBehaviour,
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
from tests.test_skills.test_apy_estimation.conftest import DummyPipeline


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
class APYEstimationFSMBehaviourBaseCase(BaseSkillTestCase):
    """Base case for testing APYEstimation FSMBehaviour."""

    path_to_skill = Path(
        ROOT_DIR, "packages", "valory", "skills", "apy_estimation_abci"
    )

    apy_estimation_behaviour: APYEstimationConsensusBehaviour
    ledger_handler: LedgerApiHandler
    http_handler: HttpHandler
    contract_handler: ContractApiHandler
    signing_handler: SigningHandler
    old_tx_type_to_payload_cls: Dict[str, Type[BaseTxPayload]]
    participants: FrozenSet[str] = frozenset()
    behaviour_class: Type[APYEstimationBaseState]
    next_behaviour_class: Type[APYEstimationBaseState]
    period_state: PeriodState

    @classmethod
    def setup(cls, **kwargs: Any) -> None:
        """Setup the test class."""
        # we need to store the current value of the meta-class attribute
        # _MetaPayload.transaction_type_to_payload_cls, and restore it
        # in the teardown function. We do a shallow copy so we avoid
        # to modify the old mapping during the execution of the tests.
        cls.old_tx_type_to_payload_cls = copy(
            _MetaPayload.transaction_type_to_payload_cls
        )
        _MetaPayload.transaction_type_to_payload_cls = {}
        super().setup()
        assert cls._skill.skill_context._agent_context is not None
        cls._skill.skill_context._agent_context.identity._default_address_key = (
            "ethereum"
        )
        cls._skill.skill_context._agent_context._default_ledger_id = "ethereum"
        cls.apy_estimation_behaviour = cast(
            APYEstimationConsensusBehaviour,
            cls._skill.skill_context.behaviours.main,
        )
        cls.http_handler = cast(HttpHandler, cls._skill.skill_context.handlers.http)
        cls.signing_handler = cast(
            SigningHandler, cls._skill.skill_context.handlers.signing
        )
        cls.contract_handler = cast(
            ContractApiHandler, cls._skill.skill_context.handlers.contract_api
        )
        cls.ledger_handler = cast(
            LedgerApiHandler, cls._skill.skill_context.handlers.ledger_api
        )

        cls.apy_estimation_behaviour.setup()
        cls._skill.skill_context.state.setup()
        assert (
            cast(BaseState, cls.apy_estimation_behaviour.current_state).state_id
            == cls.apy_estimation_behaviour.initial_state_cls.state_id
        )
        cls.period_state = PeriodState(
            StateDB(
                initial_period=0,
                initial_data={"full_training": False, "pair_name": "test"},
            )
        )

    def create_enough_participants(self) -> None:
        """Create enough participants."""
        self.participants = frozenset(
            {self.skill.skill_context.agent_address, "a_1", "a_2"}
        )

    def fast_forward_to_state(
        self,
        behaviour: AbstractRoundBehaviour,
        state_id: str,
        period_state: BasePeriodState,
    ) -> None:
        """Fast forward the FSM to a state."""
        next_state = {s.state_id: s for s in behaviour.behaviour_states}[state_id]
        assert next_state is not None, f"State {state_id} not found"
        next_state = cast(Type[BaseState], next_state)
        behaviour.current_state = next_state(
            name=next_state.state_id, skill_context=behaviour.context
        )
        self.skill.skill_context.state.period.abci_app._round_results.append(
            period_state
        )
        if next_state.matching_round is not None:
            self.skill.skill_context.state.period.abci_app._current_round = (
                next_state.matching_round(
                    period_state, self.skill.skill_context.params.consensus_params
                )
            )

    def mock_http_request(self, request_kwargs: Dict, response_kwargs: Dict) -> None:
        """
        Mock http request.

        :param request_kwargs: keyword arguments for request check.
        :param response_kwargs: keyword arguments for mock response.
        """

        self.assert_quantity_in_outbox(1)
        actual_http_message = self.get_message_from_outbox()
        assert actual_http_message is not None, "No message in outbox."
        has_attributes, error_str = self.message_has_attributes(
            actual_message=actual_http_message,
            message_type=HttpMessage,
            performative=HttpMessage.Performative.REQUEST,
            to=str(HTTP_CLIENT_PUBLIC_ID),
            sender=str(self.skill.skill_context.skill_id),
            **request_kwargs,
        )
        assert has_attributes, error_str
        self.apy_estimation_behaviour.act_wrapper()
        self.assert_quantity_in_outbox(0)
        incoming_message = self.build_incoming_message(
            message_type=HttpMessage,
            dialogue_reference=(actual_http_message.dialogue_reference[0], "stub"),
            performative=HttpMessage.Performative.RESPONSE,
            target=actual_http_message.message_id,
            message_id=-1,
            to=str(self.skill.skill_context.skill_id),
            sender=str(HTTP_CLIENT_PUBLIC_ID),
            **response_kwargs,
        )
        self.http_handler.handle(incoming_message)
        self.apy_estimation_behaviour.act_wrapper()

    def mock_signing_request(self, request_kwargs: Dict, response_kwargs: Dict) -> None:
        """Mock signing request."""
        self.assert_quantity_in_decision_making_queue(1)
        actual_signing_message = self.get_message_from_decision_maker_inbox()
        assert actual_signing_message is not None, "No message in outbox."
        has_attributes, error_str = self.message_has_attributes(
            actual_message=actual_signing_message,
            message_type=SigningMessage,
            to="dummy_decision_maker_address",
            sender=str(self.skill.skill_context.skill_id),
            **request_kwargs,
        )
        assert has_attributes, error_str
        incoming_message = self.build_incoming_message(
            message_type=SigningMessage,
            dialogue_reference=(actual_signing_message.dialogue_reference[0], "stub"),
            target=actual_signing_message.message_id,
            message_id=-1,
            to=str(self.skill.skill_context.skill_id),
            sender="dummy_decision_maker_address",
            **response_kwargs,
        )
        self.signing_handler.handle(incoming_message)
        self.apy_estimation_behaviour.act_wrapper()

    def mock_a2a_transaction(
        self,
    ) -> None:
        """Performs mock a2a transaction."""

        self.mock_signing_request(
            request_kwargs=dict(
                performative=SigningMessage.Performative.SIGN_MESSAGE,
            ),
            response_kwargs=dict(
                performative=SigningMessage.Performative.SIGNED_MESSAGE,
                signed_message=SignedMessage(
                    ledger_id="ethereum", body="stub_signature"
                ),
            ),
        )

        self.mock_http_request(
            request_kwargs=dict(
                method="GET",
                headers="",
                version="",
                body=b"",
            ),
            response_kwargs=dict(
                version="",
                status_code=200,
                status_text="",
                headers="",
                body=json.dumps({"result": {"hash": ""}}).encode("utf-8"),
            ),
        )
        self.mock_http_request(
            request_kwargs=dict(
                method="GET",
                headers="",
                version="",
                body=b"",
            ),
            response_kwargs=dict(
                version="",
                status_code=200,
                status_text="",
                headers="",
                body=json.dumps({"result": {"tx_result": {"code": OK_CODE}}}).encode(
                    "utf-8"
                ),
            ),
        )

    def end_round(
        self,
    ) -> None:
        """Ends round early to cover `wait_for_end` generator."""
        current_state = cast(BaseState, self.apy_estimation_behaviour.current_state)
        if current_state is None:
            return
        if current_state.matching_round is None:
            return
        abci_app = current_state.context.state.period.abci_app
        old_round = abci_app._current_round
        abci_app._last_round = old_round
        abci_app._current_round = abci_app.transition_function[
            current_state.matching_round
        ][Event.DONE](abci_app.state, abci_app.consensus_params)
        abci_app._previous_rounds.append(old_round)
        self.apy_estimation_behaviour._process_current_round()

    def _test_done_flag_set(self) -> None:
        """Test that, when round ends, the 'done' flag is set."""
        current_state = cast(BaseState, self.apy_estimation_behaviour.current_state)
        assert not current_state.is_done()
        with mock.patch.object(
            self.apy_estimation_behaviour.context.state, "period"
        ) as mock_period:
            mock_period.last_round_id = cast(
                AbstractRound, current_state.matching_round
            ).round_id
            current_state.act_wrapper()
            assert current_state.is_done()

    @classmethod
    def teardown(cls) -> None:
        """Teardown the test class."""
        _MetaPayload.transaction_type_to_payload_cls = cls.old_tx_type_to_payload_cls  # type: ignore


class TestAPYEstimationBaseState(APYEstimationFSMBehaviourBaseCase):
    """Tests for `APYEstimationBaseState`."""

    ipfs_tool = IPFSTool()

    def test_send_file_to_ipfs_node(self, tmp_path: PosixPath) -> None:
        """Test `send_file_to_ipfs_node`."""
        filepath = os.path.join(tmp_path, "test")

        with open(filepath, "w") as f:
            f.write("test")

        hash_ = cast(
            APYEstimationBaseState, self.apy_estimation_behaviour.current_state
        ).send_file_to_ipfs_node(filepath)
        assert isinstance(hash_, str)
        assert len(hash_) == 46

    def test_download_from_ipfs_node(self, tmp_path: PosixPath) -> None:
        """Test `download_from_ipfs_node`."""
        filename = "test"
        filepath = os.path.join(tmp_path, filename)

        with open(filepath, "w") as f:
            f.write("test")

        _, hash_, _ = self.ipfs_tool.add(filepath)
        os.remove(filepath)

        cast(
            APYEstimationBaseState, self.apy_estimation_behaviour.current_state
        )._download_from_ipfs_node(hash_, str(tmp_path), filename)

        with open(filepath, "r") as f:
            assert f.read() == "test"

    def test_get_and_read_json(self, tmp_path: PosixPath) -> None:
        """Test `get_and_read_json`"""
        save_filepath = os.path.join(tmp_path, "save")
        download_folder = os.path.join(tmp_path, "download")
        os.makedirs(download_folder, exist_ok=True)
        save_json_data = {"test": "test"}

        with open(save_filepath, "w") as f:
            json.dump(save_json_data, f)

        _, hash_, _ = self.ipfs_tool.add(save_filepath)
        os.remove(save_filepath)

        download_json_data = cast(
            APYEstimationBaseState, self.apy_estimation_behaviour.current_state
        ).get_and_read_json(hash_, download_folder, "save")

        assert download_json_data == save_json_data

    def test_get_and_read_hist(
        self,
        tmp_path: PosixPath,
        transformed_historical_data_no_datetime_conversion: pd.DataFrame,
    ) -> None:
        """Test `get_and_read_hist`."""
        save_filepath = os.path.join(tmp_path, "save")
        download_folder = os.path.join(tmp_path, "download")
        os.makedirs(download_folder, exist_ok=True)
        save_csv_data = transformed_historical_data_no_datetime_conversion
        save_csv_data.to_csv(save_filepath, index=False)

        _, hash_, _ = self.ipfs_tool.add(save_filepath)
        os.remove(save_filepath)
        download_csv_data = cast(
            APYEstimationBaseState, self.apy_estimation_behaviour.current_state
        ).get_and_read_hist(hash_, download_folder, "save")

        save_csv_data["block_timestamp"] = pd.to_datetime(
            save_csv_data["block_timestamp"], unit="s"
        )

        pd.testing.assert_frame_equal(download_csv_data, save_csv_data)

    def test_get_and_read_csv(self, tmp_path: PosixPath) -> None:
        """Test `get_and_read_csv`."""
        save_filepath = os.path.join(tmp_path, "save")
        download_folder = os.path.join(tmp_path, "download")
        os.makedirs(download_folder, exist_ok=True)
        save_csv_data = pd.DataFrame({"test": ["test"]})
        save_csv_data.to_csv(save_filepath, index=False)

        _, hash_, _ = self.ipfs_tool.add(save_filepath)
        os.remove(save_filepath)
        download_csv_data = cast(
            APYEstimationBaseState, self.apy_estimation_behaviour.current_state
        ).get_and_read_csv(hash_, download_folder, "save")

        pd.testing.assert_frame_equal(download_csv_data, save_csv_data)

    def test_get_and_read_forecaster(self, tmp_path: PosixPath) -> None:
        """Test `get_and_read_forecaster`."""
        save_filepath = os.path.join(tmp_path, "save")
        download_folder = os.path.join(tmp_path, "download")
        os.makedirs(download_folder, exist_ok=True)

        saved_forecaster = Pipeline(
            [
                ("fourier", FourierFeaturizer(0, 0)),
                (
                    "arima",
                    ARIMA((1, 1, 1), suppress_warnings=True),
                ),
            ]
        )
        pipeline_steps_saved = saved_forecaster.get_params()["steps"]
        fourier_saved = pipeline_steps_saved[0][1].get_params()
        arima_saved = pipeline_steps_saved[1][1].get_params()

        joblib.dump(saved_forecaster, save_filepath)

        _, hash_, _ = self.ipfs_tool.add(save_filepath)
        os.remove(save_filepath)
        downloaded_forecaster = cast(
            APYEstimationBaseState, self.apy_estimation_behaviour.current_state
        ).get_and_read_forecaster(hash_, download_folder, "save")

        pipeline_steps_downloaded = downloaded_forecaster.get_params()["steps"]
        fourier_downloaded = pipeline_steps_downloaded[0][1].get_params()
        arima_downloaded = pipeline_steps_downloaded[1][1].get_params()

        assert fourier_saved == fourier_downloaded
        assert arima_saved == arima_downloaded


class TestTendermintHealthcheckBehaviour(APYEstimationFSMBehaviourBaseCase):
    """Test case to test TendermintHealthcheckBehaviour."""

    def test_tendermint_healthcheck_not_live(self) -> None:
        """Test the tendermint health check does not finish if not healthy."""
        assert (
            cast(
                BaseState,
                cast(BaseState, self.apy_estimation_behaviour.current_state),
            ).state_id
            == TendermintHealthcheckBehaviour.state_id
        )

        cast(
            TendermintHealthcheckBehaviour, self.apy_estimation_behaviour.current_state
        ).params.sleep_time = SLEEP_TIME_TWEAK

        self.apy_estimation_behaviour.act_wrapper()

        with patch.object(
            self.apy_estimation_behaviour.context.logger, "log"
        ) as mock_logger:
            self.mock_http_request(
                request_kwargs=dict(
                    method="GET",
                    url=self.skill.skill_context.params.tendermint_url + "/health",
                    headers="",
                    version="",
                    body=b"",
                ),
                response_kwargs=dict(
                    version="",
                    status_code=500,
                    status_text="",
                    headers="",
                    body=b"",
                ),
            )
        mock_logger.assert_any_call(
            logging.ERROR,
            "Tendermint not running yet, trying again!",
        )
        time.sleep(SLEEP_TIME_TWEAK + 0.01)
        self.apy_estimation_behaviour.act_wrapper()

    def test_tendermint_healthcheck_not_live_raises(self) -> None:
        """Test the tendermint health check raises if not healthy for too long."""
        assert (
            cast(
                BaseState,
                cast(BaseState, self.apy_estimation_behaviour.current_state),
            ).state_id
            == TendermintHealthcheckBehaviour.state_id
        )
        with mock.patch.object(
            self.apy_estimation_behaviour.current_state,
            "_is_timeout_expired",
            return_value=True,
        ):
            with pytest.raises(
                AEAActException, match="Tendermint node did not come live!"
            ):
                self.apy_estimation_behaviour.act_wrapper()

    def test_tendermint_healthcheck_live_and_no_status(self) -> None:
        """Test the tendermint health check does finish if healthy."""
        assert (
            cast(
                BaseState,
                cast(BaseState, self.apy_estimation_behaviour.current_state),
            ).state_id
            == TendermintHealthcheckBehaviour.state_id
        )

        cast(
            TendermintHealthcheckBehaviour, self.apy_estimation_behaviour.current_state
        ).params.sleep_time = SLEEP_TIME_TWEAK

        self.apy_estimation_behaviour.act_wrapper()
        self.mock_http_request(
            request_kwargs=dict(
                method="GET",
                url=self.skill.skill_context.params.tendermint_url + "/health",
                headers="",
                version="",
                body=b"",
            ),
            response_kwargs=dict(
                version="",
                status_code=200,
                status_text="",
                headers="",
                body=json.dumps({"status": 1}).encode("utf-8"),
            ),
        )
        with patch.object(
            self.apy_estimation_behaviour.context.logger, "log"
        ) as mock_logger:
            self.mock_http_request(
                request_kwargs=dict(
                    method="GET",
                    url=self.skill.skill_context.params.tendermint_url + "/status",
                    headers="",
                    version="",
                    body=b"",
                ),
                response_kwargs=dict(
                    version="", status_code=500, status_text="", headers="", body=b""
                ),
            )
        mock_logger.assert_any_call(
            logging.ERROR, "Tendermint not accepting transactions yet, trying again!"
        )
        state = cast(BaseState, self.apy_estimation_behaviour.current_state)
        assert state.state_id == TendermintHealthcheckBehaviour.state_id
        time.sleep(SLEEP_TIME_TWEAK + 0.01)
        self.apy_estimation_behaviour.act_wrapper()

    def test_tendermint_healthcheck_live_and_status(self) -> None:
        """Test the tendermint health check does finish if healthy."""
        assert (
            cast(
                BaseState,
                cast(BaseState, self.apy_estimation_behaviour.current_state),
            ).state_id
            == TendermintHealthcheckBehaviour.state_id
        )
        self.apy_estimation_behaviour.act_wrapper()
        self.mock_http_request(
            request_kwargs=dict(
                method="GET",
                url=self.skill.skill_context.params.tendermint_url + "/health",
                headers="",
                version="",
                body=b"",
            ),
            response_kwargs=dict(
                version="",
                status_code=200,
                status_text="",
                headers="",
                body=json.dumps({"status": 1}).encode("utf-8"),
            ),
        )
        with patch.object(
            self.apy_estimation_behaviour.context.logger, "log"
        ) as mock_logger:
            current_height = self.apy_estimation_behaviour.context.state.period.height
            self.mock_http_request(
                request_kwargs=dict(
                    method="GET",
                    url=self.skill.skill_context.params.tendermint_url + "/status",
                    headers="",
                    version="",
                    body=b"",
                ),
                response_kwargs=dict(
                    version="",
                    status_code=200,
                    status_text="",
                    headers="",
                    body=json.dumps(
                        {
                            "result": {
                                "sync_info": {"latest_block_height": current_height}
                            }
                        }
                    ).encode("utf-8"),
                ),
            )
        mock_logger.assert_any_call(logging.INFO, "local height == remote height; done")
        state = cast(BaseState, self.apy_estimation_behaviour.current_state)
        assert state.state_id == RegistrationBehaviour.state_id

    def test_tendermint_healthcheck_height_differs(self) -> None:
        """Test the tendermint health check does finish if local-height != remote-height."""
        assert (
            cast(
                BaseState,
                cast(BaseState, self.apy_estimation_behaviour.current_state),
            ).state_id
            == TendermintHealthcheckBehaviour.state_id
        )
        cast(
            TendermintHealthcheckBehaviour,
            self.apy_estimation_behaviour.current_state,
        )._check_started = datetime.now()
        cast(
            TendermintHealthcheckBehaviour,
            self.apy_estimation_behaviour.current_state,
        )._is_healthy = True

        cast(
            TendermintHealthcheckBehaviour, self.apy_estimation_behaviour.current_state
        ).params.sleep_time = SLEEP_TIME_TWEAK

        self.apy_estimation_behaviour.act_wrapper()
        with patch.object(
            self.apy_estimation_behaviour.context.logger, "log"
        ) as mock_logger:
            current_height = self.apy_estimation_behaviour.context.state.period.height
            new_different_height = current_height + 1
            self.mock_http_request(
                request_kwargs=dict(
                    method="GET",
                    url=self.skill.skill_context.params.tendermint_url + "/status",
                    headers="",
                    version="",
                    body=b"",
                ),
                response_kwargs=dict(
                    version="",
                    status_code=200,
                    status_text="",
                    headers="",
                    body=json.dumps(
                        {
                            "result": {
                                "sync_info": {
                                    "latest_block_height": new_different_height
                                }
                            }
                        }
                    ).encode("utf-8"),
                ),
            )
        mock_logger.assert_any_call(
            logging.INFO, "local height != remote height; retrying..."
        )
        state = cast(BaseState, self.apy_estimation_behaviour.current_state)
        assert state.state_id == TendermintHealthcheckBehaviour.state_id
        time.sleep(SLEEP_TIME_TWEAK + 0.01)
        self.apy_estimation_behaviour.act_wrapper()


class TestRegistrationBehaviour(APYEstimationFSMBehaviourBaseCase):
    """Base test case to test RegistrationBehaviour."""

    behaviour_class = RegistrationBehaviour
    next_behaviour_class = FetchBehaviour

    def test_registration(self) -> None:
        """Test registration."""
        self.fast_forward_to_state(
            self.apy_estimation_behaviour,
            self.behaviour_class.state_id,
            self.period_state,
        )
        assert (
            cast(
                BaseState,
                cast(BaseState, self.apy_estimation_behaviour.current_state),
            ).state_id
            == self.behaviour_class.state_id
        )
        self.apy_estimation_behaviour.act_wrapper()
        self.mock_a2a_transaction()
        self._test_done_flag_set()

        self.end_round()
        state = cast(BaseState, self.apy_estimation_behaviour.current_state)
        assert state.state_id == self.next_behaviour_class.state_id


class TestFetchAndBatchBehaviours(APYEstimationFSMBehaviourBaseCase):
    """Test FetchBehaviour and FetchBatchBehaviour."""

    behaviour_class = FetchBehaviour
    next_behaviour_class = TransformBehaviour

    @pytest.mark.parametrize("batch_flag", (True, False))
    def test_setup(self, monkeypatch: MonkeyPatch, batch_flag: bool) -> None:
        """Test behaviour setup."""
        self.skill.skill_context.state.period.abci_app._last_timestamp = datetime.now()

        self.fast_forward_to_state(
            self.apy_estimation_behaviour,
            self.behaviour_class.state_id,
            self.period_state,
        )
        cast(
            FetchBehaviour, self.apy_estimation_behaviour.current_state
        ).batch = batch_flag

        monkeypatch.setattr(os.path, "join", lambda *_: "")
        cast(
            APYEstimationBaseState, self.apy_estimation_behaviour.current_state
        ).setup()

    def test_handle_response(self, caplog: LogCaptureFixture) -> None:
        """Test `handle_response`."""
        self.fast_forward_to_state(
            self.apy_estimation_behaviour,
            self.behaviour_class.state_id,
            self.period_state,
        )

        # test with empty response.
        specs = ApiSpecs(
            url="test",
            api_id="test",
            method="GET",
            name="test",
            skill_context=self.apy_estimation_behaviour.context,
        )

        with pytest.raises(Exception):
            cast(
                FetchBehaviour, self.apy_estimation_behaviour.current_state
            )._handle_response(None, "test_context", ("", 0), specs)
            with caplog.at_level(
                logging.ERROR,
                logger="aea.test_agent_name.packages.valory.skills.apy_estimation_abci",
            ):
                assert (
                    "[test_agent_name] Could not get test_context from test"
                    in caplog.text
                )

        assert specs._retries_attempted == 1

        caplog.clear()
        with caplog.at_level(
            logging.INFO,
            logger="aea.test_agent_name.packages.valory.skills.apy_estimation_abci",
        ):
            cast(
                FetchBehaviour, self.apy_estimation_behaviour.current_state
            )._handle_response({"test": [4, 5]}, "test", ("test", 0), specs)
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
            FetchBehaviour, self.apy_estimation_behaviour.current_state
        ).params.history_duration
        self.skill.skill_context.state.period.abci_app._last_timestamp = (
            datetime.utcfromtimestamp(1618735147 + history_duration * 30 * 24 * 60 * 60)
        )

        self.fast_forward_to_state(
            self.apy_estimation_behaviour, FetchBehaviour.state_id, self.period_state
        )
        cast(
            FetchBehaviour, self.apy_estimation_behaviour.current_state
        ).params.pair_ids = ["0xec454eda10accdd66209c57af8c12924556f3abd"]

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
        self.apy_estimation_behaviour.act_wrapper()
        self.mock_http_request(request_kwargs, response_kwargs)

        # ETH price request.
        request_kwargs[
            "url"
        ] = "https://api.thegraph.com/subgraphs/name/eerieeight/spookyswap"
        request_kwargs["body"] = json.dumps({"query": eth_price_usd_q}).encode("utf-8")
        res = {"data": {"bundles": [{"ethPrice": "0.8973548"}]}}
        response_kwargs["body"] = json.dumps(res).encode("utf-8")
        self.apy_estimation_behaviour.act_wrapper()
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
        self.apy_estimation_behaviour.act_wrapper()
        self.mock_http_request(request_kwargs, response_kwargs)

        self.end_round()
        state = cast(BaseState, self.apy_estimation_behaviour.current_state)
        assert state.state_id == TransformBehaviour.state_id

    def test_fetch_behaviour_retries_exceeded(self, monkeypatch: MonkeyPatch) -> None:
        """Run tests for exceeded retries."""
        self.skill.skill_context.state.period.abci_app._last_timestamp = datetime.now()

        self.fast_forward_to_state(
            self.apy_estimation_behaviour, FetchBehaviour.state_id, self.period_state
        )

        subgraphs_sorted_by_utilization_moment: Tuple[Any, ...] = (
            self.apy_estimation_behaviour.context.spooky_subgraph,
            self.apy_estimation_behaviour.context.fantom_subgraph,
            self.apy_estimation_behaviour.context.spooky_subgraph,
            self.apy_estimation_behaviour.context.spooky_subgraph,
        )

        for subgraph in subgraphs_sorted_by_utilization_moment:
            monkeypatch.setattr(subgraph, "is_retries_exceeded", lambda *_: True)
            with pytest.raises(
                AEAActException, match="Cannot continue FetchBehaviour."
            ):
                self.apy_estimation_behaviour.act_wrapper()
                self.apy_estimation_behaviour.act_wrapper()

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
            FetchBehaviour, self.apy_estimation_behaviour.current_state
        ).params.history_duration
        self.skill.skill_context.state.period.abci_app._last_timestamp = (
            datetime.utcfromtimestamp(1618735147 + history_duration * 30 * 24 * 60 * 60)
        )
        self.fast_forward_to_state(
            self.apy_estimation_behaviour, FetchBehaviour.state_id, self.period_state
        )
        cast(
            FetchBehaviour, self.apy_estimation_behaviour.current_state
        ).params.pair_ids = ["0xec454eda10accdd66209c57af8c12924556f3abd"]
        cast(
            FetchBehaviour, self.apy_estimation_behaviour.current_state
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
            self.apy_estimation_behaviour.act_wrapper()
            self.mock_http_request(request_kwargs, response_kwargs)
        assert "[test_agent_name] Could not get block from fantom" in caplog.text

        caplog.clear()
        time.sleep(SLEEP_TIME_TWEAK + 0.01)
        self.apy_estimation_behaviour.act_wrapper()

        # block request.
        request_kwargs[
            "url"
        ] = "https://api.thegraph.com/subgraphs/name/matthewlilley/fantom-blocks"
        request_kwargs["body"] = json.dumps({"query": block_from_timestamp_q}).encode(
            "utf-8"
        )
        res = {"data": {"blocks": [{"timestamp": "1", "number": "3830367"}]}}
        response_kwargs["body"] = json.dumps(res).encode("utf-8")
        self.apy_estimation_behaviour.act_wrapper()
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
            self.apy_estimation_behaviour.act_wrapper()
            self.mock_http_request(request_kwargs, response_kwargs)
        assert (
            "[test_agent_name] Could not get ETH price for block "
            "{'timestamp': '1', 'number': '3830367'} from spookyswap" in caplog.text
        )

        caplog.clear()
        time.sleep(SLEEP_TIME_TWEAK + 0.01)
        self.apy_estimation_behaviour.act_wrapper()

        # block request.
        request_kwargs[
            "url"
        ] = "https://api.thegraph.com/subgraphs/name/matthewlilley/fantom-blocks"
        request_kwargs["body"] = json.dumps({"query": block_from_timestamp_q}).encode(
            "utf-8"
        )
        res = {"data": {"blocks": [{"timestamp": "1", "number": "3830367"}]}}
        response_kwargs["body"] = json.dumps(res).encode("utf-8")
        self.apy_estimation_behaviour.act_wrapper()
        self.mock_http_request(request_kwargs, response_kwargs)

        # ETH price request.
        request_kwargs[
            "url"
        ] = "https://api.thegraph.com/subgraphs/name/eerieeight/spookyswap"
        request_kwargs["body"] = json.dumps({"query": eth_price_usd_q}).encode("utf-8")
        res = {"data": {"bundles": [{"ethPrice": "0.8973548"}]}}
        response_kwargs["body"] = json.dumps(res).encode("utf-8")
        self.apy_estimation_behaviour.act_wrapper()
        self.mock_http_request(request_kwargs, response_kwargs)

        # top pairs data with None response.
        request_kwargs["body"] = json.dumps({"query": pairs_q}).encode("utf-8")
        response_kwargs["body"] = b""

        with caplog.at_level(
            logging.ERROR,
            logger="aea.test_agent_name.packages.valory.skills.apy_estimation_abci",
        ):
            self.apy_estimation_behaviour.act_wrapper()
            self.mock_http_request(request_kwargs, response_kwargs)
        assert (
            "[test_agent_name] Could not get pool data for block {'timestamp': '1', 'number': '3830367'} "
            "(Showing first example) from spookyswap" in caplog.text
        )

        caplog.clear()
        time.sleep(SLEEP_TIME_TWEAK + 0.01)
        self.apy_estimation_behaviour.act_wrapper()

    def test_fetch_behaviour_stop_iteration(
        self,
        monkeypatch: MonkeyPatch,
        tmp_path: PosixPath,
        no_action: Callable[[Any], None],
    ) -> None:
        """Test `FetchBehaviour`'s `async_act` after all the timestamps have been generated."""
        self.skill.skill_context.state.period.abci_app._last_timestamp = datetime.now()

        # fast-forward to fetch behaviour.
        self.fast_forward_to_state(
            self.apy_estimation_behaviour, FetchBehaviour.state_id, self.period_state
        )
        # set history duration to a negative value in order to raise a `StopIteration`.
        cast(
            FetchBehaviour, self.apy_estimation_behaviour.current_state
        ).params.history_duration = -1

        # test empty retrieved history.
        with pytest.raises(AEAActException, match="Cannot continue FetchBehaviour."):
            self.apy_estimation_behaviour.act_wrapper()

        # fast-forward to fetch behaviour.
        self.fast_forward_to_state(
            self.apy_estimation_behaviour, FetchBehaviour.state_id, self.period_state
        )

        # test with retrieved history and non-existing save path.
        cast(
            FetchBehaviour, self.apy_estimation_behaviour.current_state
        )._pairs_hist = [{"": ""}]
        save_path = os.path.join("non", "existing")
        monkeypatch.setattr(os.path, "join", lambda *_: save_path)
        monkeypatch.setattr(os, "makedirs", lambda *_, **__: no_action)
        with pytest.raises(AEAActException):
            self.apy_estimation_behaviour.act_wrapper()

        importlib.reload(os.path)
        # fast-forward to fetch behaviour.
        self.fast_forward_to_state(
            self.apy_estimation_behaviour, FetchBehaviour.state_id, self.period_state
        )

        # test with retrieved history and valid save path.
        importlib.reload(os.path)
        cast(
            FetchBehaviour, self.apy_estimation_behaviour.current_state
        )._pairs_hist = [{"test": "test"}]
        initial_data_dir = self.apy_estimation_behaviour.context._agent_context._data_dir  # type: ignore
        self.apy_estimation_behaviour.context._agent_context._data_dir = tmp_path  # type: ignore
        self.apy_estimation_behaviour.act_wrapper()
        self.mock_a2a_transaction()
        self._test_done_flag_set()
        self.end_round()
        state = cast(BaseState, self.apy_estimation_behaviour.current_state)
        assert state.state_id == TransformBehaviour.state_id

        # fast-forward to fetch behaviour.
        self.fast_forward_to_state(
            self.apy_estimation_behaviour, FetchBehaviour.state_id, self.period_state
        )

        # test with non-serializable retrieved history and valid save path.
        cast(
            FetchBehaviour, self.apy_estimation_behaviour.current_state
        )._pairs_hist = [
            b"non-serializable"  # type: ignore
        ]
        with pytest.raises(
            AEAActException,
            match="TypeError: Object of type bytes is not JSON serializable",
        ):
            self.apy_estimation_behaviour.act_wrapper()

        self.apy_estimation_behaviour.context._agent_context._data_dir = initial_data_dir  # type: ignore

    def test_clean_up(
        self,
    ) -> None:
        """Test clean-up."""
        self.fast_forward_to_state(
            self.apy_estimation_behaviour, FetchBehaviour.state_id, self.period_state
        )

        self.apy_estimation_behaviour.context.spooky_subgraph._retries_attempted = 1
        self.apy_estimation_behaviour.context.fantom_subgraph._retries_attempted = 1
        assert self.apy_estimation_behaviour.current_state is not None
        self.apy_estimation_behaviour.current_state.clean_up()
        assert (
            self.apy_estimation_behaviour.context.spooky_subgraph._retries_attempted
            == 0
        )
        assert (
            self.apy_estimation_behaviour.context.fantom_subgraph._retries_attempted
            == 0
        )


class TestTransformBehaviour(APYEstimationFSMBehaviourBaseCase):
    """Test TransformBehaviour."""

    behaviour_class = TransformBehaviour
    next_behaviour_class = PreprocessBehaviour

    def test_setup(self) -> None:
        """Test behaviour setup."""
        self.fast_forward_to_state(
            self.apy_estimation_behaviour,
            self.behaviour_class.state_id,
            PeriodState(
                StateDB(
                    initial_period=0,
                    initial_data=dict(
                        most_voted_randomness=0, most_voted_history="test"
                    ),
                )
            ),
        )

        self.apy_estimation_behaviour.current_state.get_and_read_json = lambda *_: {"test": "test"}  # type: ignore

        self.apy_estimation_behaviour.context.task_manager.start()
        cast(TransformBehaviour, self.apy_estimation_behaviour.current_state).setup()

        # Test with `None` pairs' history.
        self.apy_estimation_behaviour.current_state.get_and_read_json = lambda *_: None  # type: ignore
        self.apy_estimation_behaviour.context.task_manager.start()
        with pytest.raises(RuntimeError, match="Cannot continue TransformBehaviour."):
            cast(
                TransformBehaviour, self.apy_estimation_behaviour.current_state
            ).setup()

    def test_task_not_ready(
        self,
        monkeypatch: MonkeyPatch,
        caplog: LogCaptureFixture,
        transform_task_result: pd.DataFrame,
    ) -> None:
        """Run test for `transform_behaviour` when task result is not ready."""
        self.fast_forward_to_state(
            self.apy_estimation_behaviour,
            self.behaviour_class.state_id,
            PeriodState(
                StateDB(
                    initial_period=0,
                    initial_data=dict(
                        most_voted_randomness=0, most_voted_history="test"
                    ),
                )
            ),
        )
        monkeypatch.setattr(
            TaskManager,
            "get_task_result",
            lambda *_: DummyAsyncResult(transform_task_result, ready=False),
        )
        self.apy_estimation_behaviour.current_state.get_and_read_json = lambda *_: {"test": "test"}  # type: ignore

        with caplog.at_level(
            logging.DEBUG,
            logger="aea.test_agent_name.packages.valory.skills.apy_estimation_abci",
        ):
            self.apy_estimation_behaviour.context.task_manager.start()

            cast(
                TransformBehaviour, self.apy_estimation_behaviour.current_state
            ).params.sleep_time = SLEEP_TIME_TWEAK
            self.apy_estimation_behaviour.act_wrapper()

            # Sleep to wait for the behaviour that is also sleeping.
            time.sleep(SLEEP_TIME_TWEAK + 0.01)

            # Continue the `async_act` after the sleep of the Behaviour.
            self.apy_estimation_behaviour.act_wrapper()

        assert (
            "[test_agent_name] Entered in the 'transform' behaviour state"
            in caplog.text
        )

        assert (
            "[test_agent_name] The transform task is not finished yet." in caplog.text
        )

        importlib.reload(os.path)
        self.end_round()

    def test_transform_behaviour_waiting_for_task(
        self,
        monkeypatch: MonkeyPatch,
        transform_task_result: pd.DataFrame,
        tmp_path: PosixPath,
    ) -> None:
        """Run test for `test_transform_behaviour when it is waiting for the task to finish`."""

        n_wait_loops = 2

        with mock.patch(
            "packages.valory.skills.apy_estimation_abci.tasks.transform_hist_data",
            return_value=transform_task_result,
        ):
            with mock.patch.object(
                self._skill._skill_context._agent_context._task_manager,  # type: ignore
                "get_task_result",
                new_callable=lambda: (
                    lambda *_: DummyAsyncResult(transform_task_result, ready=False)
                ),
            ):
                with mock.patch.object(
                    self._skill._skill_context._agent_context._task_manager,  # type: ignore
                    "enqueue_task",
                    return_value=3,
                ):
                    initial_data_dir = self.apy_estimation_behaviour.context._agent_context._data_dir  # type: ignore
                    self.apy_estimation_behaviour.context._agent_context._data_dir = tmp_path  # type: ignore
                    with open(
                        os.path.join(
                            self.apy_estimation_behaviour.context._get_agent_context().data_dir,
                            "transformed_historical_data.csv",
                        ),
                        "w+",
                    ) as fp:
                        fp.write("")

                        # Fast-forward to state.
                        self.fast_forward_to_state(
                            self.apy_estimation_behaviour,
                            self.behaviour_class.state_id,
                            PeriodState(
                                StateDB(
                                    initial_period=0,
                                    initial_data=dict(most_voted_history="test"),
                                )
                            ),
                        )

                        # Decrease the sleep time for faster testing.
                        cast(
                            TransformBehaviour,
                            self.apy_estimation_behaviour.current_state,
                        ).params.sleep_time = SLEEP_TIME_TWEAK

                        self.apy_estimation_behaviour.current_state.get_and_read_json = lambda *_: {}  # type: ignore

                        # Run the Behaviour for the first time, with a non-ready `DummyAsyncResult`.
                        self.apy_estimation_behaviour.act_wrapper()
                        # Get the uuid of the `DummyAsyncResult`.
                        res_id = cast(
                            DummyAsyncResult,
                            cast(
                                TransformBehaviour,
                                self.apy_estimation_behaviour.current_state,
                            )._async_result,
                        ).id
                        # Sleep to wait for the behaviour that is also sleeping.
                        time.sleep(SLEEP_TIME_TWEAK + 0.01)
                        # Continue the `async_act` after the sleep of the Behaviour.
                        self.apy_estimation_behaviour.act_wrapper()

                        # Loop to simulate the Behaviour waiting for the result to be ready.
                        # The uuid should be the same all the time through the loop,
                        # because otherwise it would mean that a new `DummyAsyncResult` has been generated,
                        # which would mean that the `setup` method has been called again.
                        for _ in range(n_wait_loops):
                            self.apy_estimation_behaviour.act_wrapper()
                            assert (
                                res_id
                                == cast(
                                    DummyAsyncResult,
                                    cast(
                                        TransformBehaviour,
                                        self.apy_estimation_behaviour.current_state,
                                    )._async_result,
                                ).id
                            )
                            time.sleep(SLEEP_TIME_TWEAK + 0.01)
                            self.apy_estimation_behaviour.act_wrapper()

                        # Simulate the result being eventually ready.
                        cast(
                            DummyAsyncResult,
                            cast(
                                TransformBehaviour,
                                self.apy_estimation_behaviour.current_state,
                            )._async_result,
                        )._ready = True

                        self.apy_estimation_behaviour.act_wrapper()

                        self.mock_a2a_transaction()
                        self._test_done_flag_set()
                        self.end_round()
                        self.apy_estimation_behaviour.context._agent_context._data_dir = (  # type: ignore
                            initial_data_dir
                        )

    def test_async_result_none(
        self,
        monkeypatch: MonkeyPatch,
        tmp_path: PosixPath,
        transform_task_result: pd.DataFrame,
    ) -> None:
        """Run test for `transform_behaviour`."""
        self.fast_forward_to_state(
            self.apy_estimation_behaviour,
            self.behaviour_class.state_id,
            PeriodState(
                StateDB(
                    initial_period=0,
                    initial_data=dict(
                        most_voted_randomness=0, most_voted_history="test"
                    ),
                )
            ),
        )

        monkeypatch.setattr(
            "packages.valory.skills.apy_estimation_abci.tasks.transform_hist_data",
            lambda _: transform_task_result,
        )
        monkeypatch.setattr(
            self._skill._skill_context._agent_context._task_manager,  # type: ignore
            "get_task_result",
            lambda *_: None,
        )
        monkeypatch.setattr(
            self._skill._skill_context._agent_context._task_manager,  # type: ignore
            "enqueue_task",
            lambda *_, **__: 3,
        )

        self.apy_estimation_behaviour.context._agent_context._data_dir = tmp_path  # type: ignore
        self.apy_estimation_behaviour.current_state.get_and_read_json = lambda *_: {"test": "test"}  # type: ignore

        with pytest.raises(
            AEAActException, match="Cannot continue TransformBehaviour."
        ):
            self.apy_estimation_behaviour.act_wrapper()
        self.end_round()

    def test_transform_behaviour(
        self,
        tmp_path: PosixPath,
        transform_task_result: pd.DataFrame,
    ) -> None:
        """Run test for `transform_behaviour`."""
        self.fast_forward_to_state(
            self.apy_estimation_behaviour,
            self.behaviour_class.state_id,
            PeriodState(
                StateDB(
                    initial_period=0,
                    initial_data=dict(
                        most_voted_randomness=0, most_voted_history="test"
                    ),
                )
            ),
        )

        with mock.patch(
            "packages.valory.skills.apy_estimation_abci.tasks.transform_hist_data",
            return_value=transform_task_result,
        ):
            with mock.patch.object(
                self._skill._skill_context._agent_context._task_manager,  # type: ignore
                "get_task_result",
                new_callable=lambda: (
                    lambda *_: DummyAsyncResult(transform_task_result)
                ),
            ):
                with mock.patch.object(
                    self._skill._skill_context._agent_context._task_manager,  # type: ignore
                    "enqueue_task",
                    return_value=3,
                ):
                    initial_data_dir = self.apy_estimation_behaviour.context._agent_context._data_dir  # type: ignore
                    self.apy_estimation_behaviour.context._agent_context._data_dir = tmp_path  # type: ignore
                    self.apy_estimation_behaviour.current_state.get_and_read_json = lambda *_: {"test": "test"}  # type: ignore
                    with open(
                        os.path.join(
                            self.apy_estimation_behaviour.context._get_agent_context().data_dir,
                            "transformed_historical_data.csv",
                        ),
                        "w+",
                    ) as fp:
                        fp.write("")

                    self.apy_estimation_behaviour.act_wrapper()

                    self.mock_a2a_transaction()
                    self._test_done_flag_set()
                    self.end_round()
                    self.apy_estimation_behaviour.context._agent_context._data_dir = initial_data_dir  # type: ignore


class TestPreprocessBehaviour(APYEstimationFSMBehaviourBaseCase):
    """Test PreprocessBehaviour."""

    behaviour_class = PreprocessBehaviour
    next_behaviour_class = RandomnessBehaviour

    def test_preprocess_behaviour(
        self,
        transformed_historical_data: pd.DataFrame,
        tmp_path: PosixPath,
    ) -> None:
        """Run test for `preprocess_behaviour`."""
        initial_data_dir = self.apy_estimation_behaviour.context._agent_context._data_dir  # type: ignore
        self.apy_estimation_behaviour.context._agent_context._data_dir = tmp_path  # type: ignore
        # Increase the amount of dummy data for the train-test split.
        transformed_historical_data = pd.DataFrame(
            np.repeat(transformed_historical_data.values, 3, axis=0),
            columns=transformed_historical_data.columns,
        )

        self.fast_forward_to_state(
            self.apy_estimation_behaviour,
            self.behaviour_class.state_id,
            PeriodState(
                StateDB(
                    initial_period=0, initial_data=dict(most_voted_transform="test")
                )
            ),
        )
        self.apy_estimation_behaviour.current_state.get_and_read_hist = (  # type: ignore
            lambda *_: transformed_historical_data
        )
        state = cast(BaseState, self.apy_estimation_behaviour.current_state)
        assert state.state_id == self.behaviour_class.state_id

        self.apy_estimation_behaviour.act_wrapper()
        self.mock_a2a_transaction()
        self._test_done_flag_set()
        self.end_round()
        state = cast(BaseState, self.apy_estimation_behaviour.current_state)
        assert state.state_id == self.next_behaviour_class.state_id
        self.apy_estimation_behaviour.context._agent_context._data_dir = initial_data_dir  # type: ignore


class TestPrepareBatchBehaviour(APYEstimationFSMBehaviourBaseCase):
    """Test `PrepareBatchBehaviour`."""

    behaviour_class = PrepareBatchBehaviour
    next_behaviour_class = UpdateForecasterBehaviour

    def _pre_setup_patching(
        self,
        tmp_path: PosixPath,
        transformed_historical_data: pd.DataFrame,
        batch: ResponseItemType,
    ) -> None:
        """Patching to be performed before setup."""
        self.apy_estimation_behaviour.context._agent_context._data_dir = tmp_path  # type: ignore

        self.fast_forward_to_state(
            self.apy_estimation_behaviour,
            self.behaviour_class.state_id,
            PeriodState(
                StateDB(
                    initial_period=0,
                    initial_data=dict(
                        latest_observation_hist_hash="x0",
                        most_voted_batch="x1",
                        latest_observation_timestamp=0,
                    ),
                )
            ),
        )

        self.apy_estimation_behaviour.current_state.get_and_read_hist = lambda *_: transformed_historical_data.iloc[  # type: ignore
            [0]
        ].reset_index(
            drop=True
        )
        self.apy_estimation_behaviour.current_state.get_and_read_json = lambda *_: batch  # type: ignore

    def test_prepare_batch_behaviour_setup(
        self,
        tmp_path: PosixPath,
        transformed_historical_data: pd.DataFrame,
        batch: ResponseItemType,
    ) -> None:
        """Test behaviour setup."""
        self._pre_setup_patching(tmp_path, transformed_historical_data, batch)
        cast(PrepareBatchBehaviour, self.apy_estimation_behaviour.current_state).setup()

    def test_prepare_batch_behaviour(
        self,
        tmp_path: PosixPath,
        transformed_historical_data: pd.DataFrame,
        batch: ResponseItemType,
    ) -> None:
        """Run test for `preprocess_behaviour`."""
        self._pre_setup_patching(tmp_path, transformed_historical_data, batch)

        state = cast(BaseState, self.apy_estimation_behaviour.current_state)
        assert state.state_id == self.behaviour_class.state_id

        self.apy_estimation_behaviour.act_wrapper()
        self.mock_a2a_transaction()
        self._test_done_flag_set()
        self.end_round()
        state = cast(BaseState, self.apy_estimation_behaviour.current_state)
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
            self.apy_estimation_behaviour,
            self.randomness_behaviour_class.state_id,
            self.period_state,
        )
        assert (
            cast(
                BaseState,
                cast(BaseState, self.apy_estimation_behaviour.current_state),
            ).state_id
            == self.randomness_behaviour_class.state_id
        )
        self.apy_estimation_behaviour.act_wrapper()
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

        self.apy_estimation_behaviour.act_wrapper()
        self.mock_a2a_transaction()
        self._test_done_flag_set()
        self.end_round()

        state = cast(BaseState, self.apy_estimation_behaviour.current_state)
        assert state.state_id == self.next_behaviour_class.state_id

    def test_invalid_drand_value(
        self,
    ) -> None:
        """Test invalid drand values."""
        self.fast_forward_to_state(
            self.apy_estimation_behaviour,
            self.randomness_behaviour_class.state_id,
            self.period_state,
        )
        assert (
            cast(
                BaseState,
                cast(BaseState, self.apy_estimation_behaviour.current_state),
            ).state_id
            == self.randomness_behaviour_class.state_id
        )
        self.apy_estimation_behaviour.act_wrapper()

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
            self.apy_estimation_behaviour,
            self.randomness_behaviour_class.state_id,
            self.period_state,
        )
        assert (
            cast(
                BaseState,
                cast(BaseState, self.apy_estimation_behaviour.current_state),
            ).state_id
            == self.randomness_behaviour_class.state_id
        )
        cast(
            RandomnessBehaviour, self.apy_estimation_behaviour.current_state
        ).params.sleep_time = SLEEP_TIME_TWEAK

        self.apy_estimation_behaviour.act_wrapper()

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
        self.apy_estimation_behaviour.act_wrapper()
        time.sleep(SLEEP_TIME_TWEAK + 0.01)
        self.apy_estimation_behaviour.act_wrapper()

    def test_max_retries_reached(
        self,
    ) -> None:
        """Test with max retries reached."""
        self.fast_forward_to_state(
            self.apy_estimation_behaviour,
            self.randomness_behaviour_class.state_id,
            self.period_state,
        )
        assert (
            cast(
                BaseState,
                cast(BaseState, self.apy_estimation_behaviour.current_state),
            ).state_id
            == self.randomness_behaviour_class.state_id
        )
        with mock.patch.object(
            self.apy_estimation_behaviour.context.randomness_api,
            "is_retries_exceeded",
            return_value=True,
        ):
            self.apy_estimation_behaviour.act_wrapper()
            state = cast(BaseState, self.apy_estimation_behaviour.current_state)
            assert state.state_id == self.randomness_behaviour_class.state_id
            self._test_done_flag_set()

    def test_clean_up(
        self,
    ) -> None:
        """Test when `observed` value is none."""
        self.fast_forward_to_state(
            self.apy_estimation_behaviour,
            self.randomness_behaviour_class.state_id,
            self.period_state,
        )
        assert (
            cast(
                BaseState,
                cast(BaseState, self.apy_estimation_behaviour.current_state),
            ).state_id
            == self.randomness_behaviour_class.state_id
        )
        self.apy_estimation_behaviour.context.randomness_api._retries_attempted = 1
        assert self.apy_estimation_behaviour.current_state is not None
        self.apy_estimation_behaviour.current_state.clean_up()
        assert (
            self.apy_estimation_behaviour.context.randomness_api._retries_attempted == 0
        )


class TestOptimizeBehaviour(APYEstimationFSMBehaviourBaseCase):
    """Test OptimizeBehaviour."""

    behaviour_class = OptimizeBehaviour
    next_behaviour_class = TrainBehaviour

    def test_setup(
        self, monkeypatch: MonkeyPatch, no_action: Callable[[Any], None]
    ) -> None:
        """Test behaviour setup."""
        self.fast_forward_to_state(
            self.apy_estimation_behaviour,
            self.behaviour_class.state_id,
            PeriodState(
                StateDB(
                    initial_period=0,
                    initial_data=dict(most_voted_randomness=0, most_voted_split="test"),
                )
            ),
        )

        self.apy_estimation_behaviour.current_state.get_and_read_csv = lambda *_: pd.DataFrame()  # type: ignore
        monkeypatch.setattr(TaskManager, "enqueue_task", lambda *_, **__: 0)
        monkeypatch.setattr(TaskManager, "get_task_result", lambda *_: no_action)
        cast(
            APYEstimationBaseState, self.apy_estimation_behaviour.current_state
        ).setup()

    def test_task_not_ready(
        self, monkeypatch: MonkeyPatch, no_action: Callable[[Any], None]
    ) -> None:
        """Run test for behaviour when task result is not ready."""
        self.fast_forward_to_state(
            self.apy_estimation_behaviour,
            self.behaviour_class.state_id,
            PeriodState(
                StateDB(
                    initial_period=0,
                    initial_data=dict(most_voted_randomness=0, most_voted_split="test"),
                )
            ),
        )

        assert (
            cast(
                APYEstimationBaseState, self.apy_estimation_behaviour.current_state
            ).state_id
            == self.behaviour_class.state_id
        )

        self.apy_estimation_behaviour.current_state.get_and_read_csv = lambda *_: pd.DataFrame()  # type: ignore
        self.apy_estimation_behaviour.context.task_manager.start()

        monkeypatch.setattr(AsyncResult, "ready", lambda *_: False)

        cast(
            OptimizeBehaviour, self.apy_estimation_behaviour.current_state
        ).params.sleep_time = SLEEP_TIME_TWEAK
        self.apy_estimation_behaviour.act_wrapper()
        time.sleep(SLEEP_TIME_TWEAK + 0.01)
        self.apy_estimation_behaviour.act_wrapper()

        assert (
            cast(
                APYEstimationBaseState, self.apy_estimation_behaviour.current_state
            ).state_id
            == self.behaviour_class.state_id
        )

    def test_optimize_behaviour_result_none(
        self, monkeypatch: MonkeyPatch, caplog: LogCaptureFixture
    ) -> None:
        """Run test for `optimize_behaviour` when `_async_result` is `None`."""
        self.fast_forward_to_state(
            self.apy_estimation_behaviour,
            self.behaviour_class.state_id,
            PeriodState(
                StateDB(
                    initial_period=0,
                    initial_data=dict(most_voted_randomness=0, most_voted_split="test"),
                )
            ),
        )

        self.apy_estimation_behaviour.current_state.get_and_read_csv = lambda *_: pd.DataFrame()  # type: ignore
        monkeypatch.setattr(TaskManager, "enqueue_task", lambda *_, **__: 0)
        monkeypatch.setattr(TaskManager, "get_task_result", lambda *_: None)

        with pytest.raises(AEAActException, match="Cannot continue OptimizationTask"):
            cast(
                OptimizeBehaviour, self.apy_estimation_behaviour.current_state
            ).params.sleep_time = SLEEP_TIME_TWEAK
            self.apy_estimation_behaviour.act_wrapper()
            time.sleep(SLEEP_TIME_TWEAK + 0.01)
            self.apy_estimation_behaviour.act_wrapper()

    def test_optimize_behaviour_value_error(
        self,
        monkeypatch: MonkeyPatch,
        tmp_path: PosixPath,
        caplog: LogCaptureFixture,
        optimize_task_result_empty: optuna.Study,
    ) -> None:
        """Run test for `optimize_behaviour` when `ValueError` is raised."""
        self.fast_forward_to_state(
            self.apy_estimation_behaviour,
            self.behaviour_class.state_id,
            PeriodState(
                StateDB(
                    initial_period=0,
                    initial_data=dict(most_voted_randomness=0, most_voted_split="test"),
                )
            ),
        )

        self.apy_estimation_behaviour.current_state.get_and_read_csv = lambda *_: pd.DataFrame()  # type: ignore
        self.apy_estimation_behaviour.context._agent_context._data_dir = tmp_path.parts[0]  # type: ignore
        cast(
            OptimizeBehaviour, self.apy_estimation_behaviour.current_state
        ).params.pair_ids[0] = os.path.join(*tmp_path.parts[1:])
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
            self.apy_estimation_behaviour.act_wrapper()

        assert (
            "The optimization could not be done! "
            "Please make sure that there is a sufficient number of data for the optimization procedure. "
            "Setting best parameters randomly!"
        ) in caplog.text

    def test_optimize_behaviour_type_error(
        self,
        monkeypatch: MonkeyPatch,
        tmp_path: PosixPath,
        optimize_task_result_non_serializable: optuna.Study,
    ) -> None:
        """Run test for `optimize_behaviour` when `TypeError` is raised."""
        self.fast_forward_to_state(
            self.apy_estimation_behaviour,
            self.behaviour_class.state_id,
            PeriodState(
                StateDB(
                    initial_period=0,
                    initial_data=dict(most_voted_randomness=0, most_voted_split="test"),
                )
            ),
        )

        save_path = os.path.join(tmp_path, "test")
        monkeypatch.setattr(os.path, "join", lambda *_: save_path)
        monkeypatch.setattr(pd, "read_csv", lambda _: pd.DataFrame())
        monkeypatch.setattr(TaskManager, "enqueue_task", lambda *_, **__: 3)
        monkeypatch.setattr(
            TaskManager,
            "get_task_result",
            lambda *_: DummyAsyncResult(optimize_task_result_non_serializable),
        )

        # test TypeError handling.
        with pytest.raises(AEAActException):
            self.apy_estimation_behaviour.act_wrapper()

    def test_optimize_behaviour_os_error(
        self,
        monkeypatch: MonkeyPatch,
        optimize_task_result: optuna.Study,
    ) -> None:
        """Run test for `optimize_behaviour` when `OSError` is raised."""
        self.fast_forward_to_state(
            self.apy_estimation_behaviour,
            self.behaviour_class.state_id,
            PeriodState(
                StateDB(
                    initial_period=0,
                    initial_data=dict(most_voted_randomness=0, most_voted_split="test"),
                )
            ),
        )

        monkeypatch.setattr(os.path, "join", lambda *_: "")
        monkeypatch.setattr(pd, "read_csv", lambda _: pd.DataFrame())
        monkeypatch.setattr(TaskManager, "enqueue_task", lambda *_, **__: 3)
        monkeypatch.setattr(
            TaskManager,
            "get_task_result",
            lambda *_: DummyAsyncResult(optimize_task_result),
        )

        # test OSError handling.
        with pytest.raises(AEAActException):
            self.apy_estimation_behaviour.act_wrapper()

    def test_optimize_behaviour(
        self,
        monkeypatch: MonkeyPatch,
        tmp_path: PosixPath,
        optimize_task_result: optuna.Study,
    ) -> None:
        """Run test for `optimize_behaviour`."""
        self.fast_forward_to_state(
            self.apy_estimation_behaviour,
            self.behaviour_class.state_id,
            PeriodState(
                StateDB(
                    initial_period=0,
                    initial_data=dict(most_voted_randomness=0, most_voted_split="test"),
                )
            ),
        )

        initial_data_dir = self.apy_estimation_behaviour.context._agent_context._data_dir  # type: ignore
        self.apy_estimation_behaviour.context._agent_context._data_dir = tmp_path.parts[0]  # type: ignore
        cast(
            OptimizeBehaviour, self.apy_estimation_behaviour.current_state
        ).params.pair_ids[0] = os.path.join(*tmp_path.parts[1:])
        self.apy_estimation_behaviour.current_state.get_and_read_csv = lambda *_: pd.DataFrame()  # type: ignore
        monkeypatch.setattr(TaskManager, "enqueue_task", lambda *_, **__: 3)
        monkeypatch.setattr(
            TaskManager,
            "get_task_result",
            lambda *_: DummyAsyncResult(optimize_task_result),
        )
        monkeypatch.setattr(
            IPFSHashOnly,
            "get",
            lambda *_: "f6be4bf1fa229f22340c1a5b258f809ac4af558200775a67dacb05f0cb258a11",
        )

        self.apy_estimation_behaviour.act_wrapper()

        self.mock_a2a_transaction()
        self._test_done_flag_set()
        self.end_round()

        state = cast(BaseState, self.apy_estimation_behaviour.current_state)
        assert state.state_id == self.next_behaviour_class.state_id
        self.apy_estimation_behaviour.context._agent_context._data_dir = initial_data_dir  # type: ignore


class TestTrainBehaviour(APYEstimationFSMBehaviourBaseCase):
    """Test TrainBehaviour."""

    behaviour_class = TrainBehaviour
    next_behaviour_class = _TestBehaviour

    @pytest.mark.parametrize("full_training", (True, False))
    def test_setup(
        self,
        monkeypatch: MonkeyPatch,
        tmp_path: PosixPath,
        no_action: Callable[[Any], None],
        full_training: bool,
    ) -> None:
        """Test behaviour setup."""
        self.fast_forward_to_state(
            self.apy_estimation_behaviour,
            self.behaviour_class.state_id,
            PeriodState(
                StateDB(
                    initial_period=0,
                    initial_data=dict(
                        full_training=full_training,
                        most_voted_params="test",
                        most_voted_split="test",
                    ),
                )
            ),
        )

        initial_data_dir = self.apy_estimation_behaviour.context._agent_context._data_dir  # type: ignore
        self.apy_estimation_behaviour.context._agent_context._data_dir = tmp_path.parts[0]  # type: ignore
        importlib.reload(os.path)
        cast(
            OptimizeBehaviour, self.apy_estimation_behaviour.current_state
        ).params.pair_ids[0] = os.path.join(*tmp_path.parts[1:])

        best_params = {"p": 1, "q": 1, "d": 1, "m": 1}
        self.apy_estimation_behaviour.current_state.get_and_read_json = lambda *_: best_params  # type: ignore
        self.apy_estimation_behaviour.current_state.get_and_read_csv = lambda *_: pd.DataFrame(  # type: ignore
            [i for i in range(5)]
        )

        monkeypatch.setattr(TaskManager, "enqueue_task", lambda *_, **__: 0)
        monkeypatch.setattr(TaskManager, "get_task_result", lambda *_: no_action)
        cast(
            APYEstimationBaseState, self.apy_estimation_behaviour.current_state
        ).setup()
        self.apy_estimation_behaviour.context._agent_context._data_dir = initial_data_dir  # type: ignore

    def test_task_not_ready(
        self,
        monkeypatch: MonkeyPatch,
        tmp_path: PosixPath,
    ) -> None:
        """Run test for behaviour when task result is not ready."""
        self.fast_forward_to_state(
            self.apy_estimation_behaviour,
            self.behaviour_class.state_id,
            PeriodState(
                StateDB(
                    initial_period=0,
                    initial_data=dict(
                        full_training=False,
                        most_voted_params="test",
                        most_voted_split="test",
                    ),
                )
            ),
        )

        assert (
            cast(
                APYEstimationBaseState, self.apy_estimation_behaviour.current_state
            ).state_id
            == self.behaviour_class.state_id
        )

        initial_data_dir = self.apy_estimation_behaviour.context._agent_context._data_dir  # type: ignore
        self.apy_estimation_behaviour.context._agent_context._data_dir = tmp_path.parts[0]  # type: ignore
        importlib.reload(os.path)
        cast(
            OptimizeBehaviour, self.apy_estimation_behaviour.current_state
        ).params.pair_ids[0] = os.path.join(*tmp_path.parts[1:])

        best_params = {"p": 1, "q": 1, "d": 1, "m": 1}
        self.apy_estimation_behaviour.current_state.get_and_read_json = lambda *_: best_params  # type: ignore
        self.apy_estimation_behaviour.current_state.get_and_read_csv = lambda *_: pd.DataFrame(  # type: ignore
            [i for i in range(5)]
        )
        self.apy_estimation_behaviour.context.task_manager.start()

        monkeypatch.setattr(AsyncResult, "ready", lambda *_: False)
        cast(
            TrainBehaviour, self.apy_estimation_behaviour.current_state
        ).params.sleep_time = SLEEP_TIME_TWEAK
        self.apy_estimation_behaviour.act_wrapper()
        time.sleep(SLEEP_TIME_TWEAK + 0.01)
        self.apy_estimation_behaviour.act_wrapper()

        assert (
            cast(
                APYEstimationBaseState, self.apy_estimation_behaviour.current_state
            ).state_id
            == self.behaviour_class.state_id
        )
        self.apy_estimation_behaviour.context._agent_context._data_dir = initial_data_dir  # type: ignore

    def test_async_result_none(
        self,
        monkeypatch: MonkeyPatch,
        tmp_path: PosixPath,
        train_task_result: Pipeline,
    ) -> None:
        """Run test for `TrainBehaviour` with `None` `_async_result`."""
        self.fast_forward_to_state(
            self.apy_estimation_behaviour,
            self.behaviour_class.state_id,
            PeriodState(
                StateDB(
                    initial_period=0,
                    initial_data=dict(
                        full_training=False,
                        most_voted_params="test",
                        most_voted_split="test",
                    ),
                )
            ),
        )

        monkeypatch.setattr(
            "packages.valory.skills.apy_estimation_abci.tasks.train_forecaster",
            lambda _: train_task_result,
        )
        monkeypatch.setattr(
            self._skill._skill_context._agent_context._task_manager,  # type: ignore
            "get_task_result",
            lambda *_: None,
        )
        monkeypatch.setattr(
            self._skill._skill_context._agent_context._task_manager,  # type: ignore
            "enqueue_task",
            lambda *_, **__: 3,
        )

        self.apy_estimation_behaviour.context._agent_context._data_dir = tmp_path.parts[0]  # type: ignore
        cast(
            TrainBehaviour, self.apy_estimation_behaviour.current_state
        ).params.pair_ids[0] = os.path.join(*tmp_path.parts[1:])

        best_params = {"p": 1, "q": 1, "d": 1, "m": 1}
        self.apy_estimation_behaviour.current_state.get_and_read_json = lambda *_: best_params  # type: ignore
        self.apy_estimation_behaviour.current_state.get_and_read_csv = lambda *_: pd.DataFrame(  # type: ignore
            [i for i in range(5)]
        )

        with pytest.raises(AEAActException, match="Cannot continue TrainTask."):
            self.apy_estimation_behaviour.act_wrapper()
        self.end_round()

    def test_train_behaviour(
        self,
        monkeypatch: MonkeyPatch,
        no_action: Callable[[Any], None],
        tmp_path: PosixPath,
        train_task_result: Pipeline,
    ) -> None:
        """Run test for `optimize_behaviour`."""
        self.fast_forward_to_state(
            self.apy_estimation_behaviour,
            self.behaviour_class.state_id,
            PeriodState(
                StateDB(
                    initial_period=0,
                    initial_data=dict(
                        full_training=False,
                        most_voted_params="test",
                        most_voted_split="test",
                    ),
                )
            ),
        )
        # patching for setup.
        initial_data_dir = self.apy_estimation_behaviour.context._agent_context._data_dir  # type: ignore
        self.apy_estimation_behaviour.context._agent_context._data_dir = tmp_path.parts[0]  # type: ignore
        importlib.reload(os.path)
        cast(
            OptimizeBehaviour, self.apy_estimation_behaviour.current_state
        ).params.pair_ids[0] = os.path.join(*tmp_path.parts[1:])

        best_params = {"p": 1, "q": 1, "d": 1, "m": 1}
        self.apy_estimation_behaviour.current_state.get_and_read_json = lambda *_: best_params  # type: ignore
        self.apy_estimation_behaviour.current_state.get_and_read_csv = lambda *_: pd.DataFrame(  # type: ignore
            [i for i in range(5)]
        )
        monkeypatch.setattr(TaskManager, "enqueue_task", lambda *_, **__: 3)
        monkeypatch.setattr(
            TaskManager,
            "get_task_result",
            lambda *_: DummyAsyncResult(train_task_result),
        )

        # act.
        self.apy_estimation_behaviour.act_wrapper()

        self.mock_a2a_transaction()
        self._test_done_flag_set()
        self.end_round()
        self.apy_estimation_behaviour.context._agent_context._data_dir = initial_data_dir  # type: ignore


class TestTestBehaviour(APYEstimationFSMBehaviourBaseCase):
    """Test TestBehaviour."""

    behaviour_class = _TestBehaviour
    next_behaviour_class = EstimateBehaviour

    def test_setup(
        self,
        monkeypatch: MonkeyPatch,
        no_action: Callable[[Any], None],
    ) -> None:
        """Test behaviour setup."""
        self.fast_forward_to_state(
            self.apy_estimation_behaviour,
            self.behaviour_class.state_id,
            PeriodState(
                StateDB(
                    initial_period=0,
                    initial_data=dict(
                        pair_name="test",
                        most_voted_split="test",
                        most_voted_model="test",
                    ),
                )
            ),
        )
        self.apy_estimation_behaviour.current_state.get_and_read_csv = lambda *_: pd.DataFrame(  # type: ignore
            [i for i in range(5)]
        )
        self.apy_estimation_behaviour.current_state.get_and_read_forecaster = lambda *_: DummyPipeline()  # type: ignore

        monkeypatch.setattr(TaskManager, "enqueue_task", lambda *_, **__: 0)
        monkeypatch.setattr(TaskManager, "get_task_result", lambda *_: no_action)
        cast(
            APYEstimationBaseState, self.apy_estimation_behaviour.current_state
        ).setup()

    def test_task_not_ready(
        self, monkeypatch: MonkeyPatch, no_action: Callable[[Any], None]
    ) -> None:
        """Run test for behaviour when task result is not ready."""
        self.fast_forward_to_state(
            self.apy_estimation_behaviour,
            self.behaviour_class.state_id,
            PeriodState(
                StateDB(
                    initial_period=0,
                    initial_data=dict(
                        pair_name="test",
                        most_voted_split="test",
                        most_voted_model="test",
                    ),
                )
            ),
        )

        assert (
            cast(
                APYEstimationBaseState, self.apy_estimation_behaviour.current_state
            ).state_id
            == self.behaviour_class.state_id
        )

        self.apy_estimation_behaviour.current_state.get_and_read_csv = lambda *_: pd.DataFrame(  # type: ignore
            [i for i in range(5)]
        )
        self.apy_estimation_behaviour.current_state.get_and_read_forecaster = lambda *_: DummyPipeline()  # type: ignore
        self.apy_estimation_behaviour.context.task_manager.start()

        monkeypatch.setattr(AsyncResult, "ready", lambda *_: False)
        cast(
            _TestBehaviour, self.apy_estimation_behaviour.current_state
        ).params.sleep_time = SLEEP_TIME_TWEAK
        self.apy_estimation_behaviour.act_wrapper()
        time.sleep(SLEEP_TIME_TWEAK + 0.01)
        self.apy_estimation_behaviour.act_wrapper()

        assert (
            cast(
                APYEstimationBaseState, self.apy_estimation_behaviour.current_state
            ).state_id
            == self.behaviour_class.state_id
        )

    def test_os_error_handling(
        self,
        monkeypatch: MonkeyPatch,
        no_action: Callable[[Any], None],
        test_task_result: Dict[str, str],
    ) -> None:
        """Run test for `optimize_behaviour`."""
        self.fast_forward_to_state(
            self.apy_estimation_behaviour,
            self.behaviour_class.state_id,
            PeriodState(
                StateDB(
                    initial_period=0,
                    initial_data=dict(
                        pair_name="test",
                        most_voted_split="test",
                        most_voted_model="test",
                    ),
                )
            ),
        )
        # patching for setup.
        monkeypatch.setattr(os.path, "join", lambda *_: "")
        monkeypatch.setattr(
            pd, "read_csv", lambda _: pd.DataFrame({"y": [1, 2, 3, 4, 5]})
        )
        monkeypatch.setattr(joblib, "load", lambda *_: DummyPipeline())
        monkeypatch.setattr(TaskManager, "enqueue_task", lambda *_, **__: 0)
        monkeypatch.setattr(
            TaskManager,
            "get_task_result",
            lambda *_: DummyAsyncResult(test_task_result),
        )

        monkeypatch.setattr(IPFSHashOnly, "get", lambda *_: "x0")
        monkeypatch.setattr(
            BaseState, "send_a2a_transaction", lambda *_: iter([0, 1, 2])
        )
        monkeypatch.setattr(BaseState, "wait_until_round_end", lambda _: no_action)

        # test act for `OSError` handling.
        with pytest.raises(
            AEAActException, match=re.escape("[Errno 2] No such file or directory: ''")
        ):
            self.apy_estimation_behaviour.act_wrapper()

    def test_type_error_handling(
        self,
        monkeypatch: MonkeyPatch,
        no_action: Callable[[Any], None],
        tmp_path: PosixPath,
        test_task_result_non_serializable: bytes,
    ) -> None:
        """Run test for `optimize_behaviour`."""
        self.fast_forward_to_state(
            self.apy_estimation_behaviour,
            self.behaviour_class.state_id,
            PeriodState(
                StateDB(
                    initial_period=0,
                    initial_data=dict(
                        pair_name="test",
                        most_voted_split="test",
                        most_voted_model="test",
                    ),
                )
            ),
        )
        self.apy_estimation_behaviour.current_state.get_and_read_csv = lambda *_: pd.DataFrame(  # type: ignore
            [i for i in range(5)]
        )
        self.apy_estimation_behaviour.current_state.get_and_read_forecaster = lambda *_: DummyPipeline()  # type: ignore
        # patching for setup.
        monkeypatch.setattr(TaskManager, "enqueue_task", lambda *_, **__: 0)
        monkeypatch.setattr(
            TaskManager,
            "get_task_result",
            lambda *_: DummyAsyncResult(test_task_result_non_serializable),
        )

        initial_data_dir = self.apy_estimation_behaviour.context._agent_context._data_dir  # type: ignore
        self.apy_estimation_behaviour.context._agent_context._data_dir = tmp_path.parts[0]  # type: ignore
        importlib.reload(os.path)
        cast(
            OptimizeBehaviour, self.apy_estimation_behaviour.current_state
        ).params.pair_ids[0] = os.path.join(*tmp_path.parts[1:])
        monkeypatch.setattr(IPFSHashOnly, "get", lambda *_: "x0")
        monkeypatch.setattr(
            BaseState, "send_a2a_transaction", lambda *_: iter([0, 1, 2])
        )
        monkeypatch.setattr(BaseState, "wait_until_round_end", lambda _: no_action)

        # test act for `TypeError` handling.
        with pytest.raises(
            AEAActException,
            match=re.escape("Object of type bytes is not JSON serializable"),
        ):
            self.apy_estimation_behaviour.act_wrapper()
        self.apy_estimation_behaviour.context._agent_context._data_dir = initial_data_dir  # type: ignore

    def test_async_result_none(
        self,
        monkeypatch: MonkeyPatch,
        tmp_path: PosixPath,
        test_task_result: Dict[str, str],
    ) -> None:
        """Run test for `TestBehaviour` with `None` `_async_result`."""
        self.fast_forward_to_state(
            self.apy_estimation_behaviour,
            self.behaviour_class.state_id,
            PeriodState(
                StateDB(
                    initial_period=0,
                    initial_data=dict(
                        pair_name="test",
                        most_voted_split="test",
                        most_voted_model="test",
                    ),
                )
            ),
        )
        # patching for setup.
        self.apy_estimation_behaviour.current_state.get_and_read_csv = lambda *_: pd.DataFrame(  # type: ignore
            [i for i in range(5)]
        )
        self.apy_estimation_behaviour.current_state.get_and_read_forecaster = lambda *_: DummyPipeline()  # type: ignore
        monkeypatch.setattr(TaskManager, "enqueue_task", lambda *_, **__: 0)
        monkeypatch.setattr(TaskManager, "get_task_result", lambda *_: None)

        with pytest.raises(AEAActException, match="Cannot continue TestTask."):
            self.apy_estimation_behaviour.act_wrapper()
        self.end_round()

    def test_test_behaviour(
        self,
        monkeypatch: MonkeyPatch,
        no_action: Callable[[Any], None],
        tmp_path: PosixPath,
        test_task_result: Dict[str, str],
    ) -> None:
        """Run test for `optimize_behaviour`."""
        self.fast_forward_to_state(
            self.apy_estimation_behaviour,
            self.behaviour_class.state_id,
            PeriodState(
                StateDB(
                    initial_period=0,
                    initial_data=dict(
                        pair_name="test",
                        most_voted_split="test",
                        most_voted_model="test",
                    ),
                )
            ),
        )
        # patching for setup.
        self.apy_estimation_behaviour.current_state.get_and_read_csv = lambda *_: pd.DataFrame(  # type: ignore
            [i for i in range(5)]
        )
        self.apy_estimation_behaviour.current_state.get_and_read_forecaster = lambda *_: DummyPipeline()  # type: ignore
        monkeypatch.setattr(TaskManager, "enqueue_task", lambda *_, **__: 0)
        monkeypatch.setattr(
            TaskManager,
            "get_task_result",
            lambda *_: DummyAsyncResult(test_task_result),
        )

        # changes for act.
        initial_data_dir = self.apy_estimation_behaviour.context._agent_context._data_dir  # type: ignore
        self.apy_estimation_behaviour.context._agent_context._data_dir = tmp_path.parts[0]  # type: ignore
        importlib.reload(os.path)
        cast(
            OptimizeBehaviour, self.apy_estimation_behaviour.current_state
        ).params.pair_ids[0] = os.path.join(*tmp_path.parts[1:])

        # test act.
        self.apy_estimation_behaviour.act_wrapper()

        self.mock_a2a_transaction()
        self._test_done_flag_set()
        self.end_round()
        self.apy_estimation_behaviour.context._agent_context._data_dir = initial_data_dir  # type: ignore


class TestUpdateForecasterBehaviour(APYEstimationFSMBehaviourBaseCase):
    """Test `UpdateForecasterBehaviour`."""

    behaviour_class = UpdateForecasterBehaviour
    next_behaviour_class = EstimateBehaviour

    def _pre_setup_patching(self, tmp_path: PosixPath) -> None:
        """Patching to be performed before setup."""
        self.apy_estimation_behaviour.context._agent_context._data_dir = tmp_path.parts[0]  # type: ignore
        cast(
            OptimizeBehaviour, self.apy_estimation_behaviour.current_state
        ).params.pair_ids[0] = os.path.join(*tmp_path.parts[1:])

        self.fast_forward_to_state(
            self.apy_estimation_behaviour,
            self.behaviour_class.state_id,
            PeriodState(
                StateDB(
                    initial_period=0,
                    initial_data=dict(
                        most_voted_model="x1", latest_observation_hist_hash="x3"
                    ),
                )
            ),
        )
        state = cast(BaseState, self.apy_estimation_behaviour.current_state)
        assert state.state_id == self.behaviour_class.state_id

        self.apy_estimation_behaviour.current_state.get_and_read_csv = lambda *_: pd.DataFrame({"APY": [0, 1]})  # type: ignore
        self.apy_estimation_behaviour.current_state.get_and_read_forecaster = (  # type: ignore
            lambda *_: DummyPipeline
        )

    def test_update_forecaster_setup(
        self,
        tmp_path: PosixPath,
    ) -> None:
        """Run test for `UpdateForecasterBehaviour`'s setup method."""
        self._pre_setup_patching(tmp_path)
        cast(
            UpdateForecasterBehaviour, self.apy_estimation_behaviour.current_state
        ).setup()

    @staticmethod
    def _temporarily_save_dummy_forecaster(tmp_path: str) -> None:
        """Save a dummy forecaster to te given `tmp_path`."""
        # Store the results.
        order = (1, 1, 1)

        # The Pipeline is deterministic.
        forecaster = Pipeline(
            [
                ("fourier", FourierFeaturizer(0)),
                (
                    "arima",
                    ARIMA(order),
                ),
            ]
        )

        joblib.dump(forecaster, tmp_path)

    def test_update_forecaster_behaviour(
        self,
        tmp_path: PosixPath,
        monkeypatch: MonkeyPatch,
        no_action: Callable[[Any], None],
    ) -> None:
        """Run test for `UpdateForecasterBehaviour`."""
        self._pre_setup_patching(tmp_path)

        forecaster_save_path = os.path.join(tmp_path, "fully_trained_forecaster.joblib")
        self._temporarily_save_dummy_forecaster(forecaster_save_path)
        monkeypatch.setattr(joblib, "dump", no_action)

        self.apy_estimation_behaviour.act_wrapper()
        self.mock_a2a_transaction()
        self._test_done_flag_set()
        self.end_round()
        state = cast(
            UpdateForecasterBehaviour, self.apy_estimation_behaviour.current_state
        )
        assert state.state_id == self.next_behaviour_class.state_id


class TestEstimateBehaviour(APYEstimationFSMBehaviourBaseCase):
    """Test EstimateBehaviour."""

    behaviour_class = EstimateBehaviour
    next_behaviour_class = FreshModelResetBehaviour

    def test_estimate_behaviour(
        self,
        monkeypatch: MonkeyPatch,
    ) -> None:
        """Run test for `EstimateBehaviour`."""
        self.fast_forward_to_state(
            self.apy_estimation_behaviour,
            self.behaviour_class.state_id,
            PeriodState(
                StateDB(
                    initial_period=0,
                    initial_data=dict(pair_name="test", most_voted_model="test"),
                )
            ),
        )
        state = cast(BaseState, self.apy_estimation_behaviour.current_state)
        assert state.state_id == self.behaviour_class.state_id

        self.apy_estimation_behaviour.current_state.get_and_read_forecaster = (  # type: ignore
            lambda *_: DummyPipeline
        )
        # the line below overcomes the limitation of the `EstimateBehaviour` to predict more than one steps forward.
        monkeypatch.setattr(DummyPipeline, "predict", lambda *_: [0])

        self.apy_estimation_behaviour.act_wrapper()
        self.mock_a2a_transaction()
        self._test_done_flag_set()
        self.end_round()
        state = cast(BaseState, self.apy_estimation_behaviour.current_state)
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
            behaviour=self.apy_estimation_behaviour,
            state_id=self.behaviour_class.state_id,
            period_state=PeriodState(
                StateDB(initial_period=0, initial_data=dict(most_voted_estimate=8.1))
            ),
        )
        state = cast(BaseState, self.apy_estimation_behaviour.current_state)
        assert state.state_id == self.behaviour_class.state_id

        monkeypatch.setattr(BenchmarkTool, "save", lambda _: no_action)
        monkeypatch.setattr(AbciApp, "last_timestamp", datetime.now())
        cast(
            CycleResetBehaviour, self.apy_estimation_behaviour.current_state
        ).params.observation_interval = SLEEP_TIME_TWEAK
        self.apy_estimation_behaviour.act_wrapper()
        time.sleep(SLEEP_TIME_TWEAK + 0.01)
        self.apy_estimation_behaviour.act_wrapper()

        self.mock_a2a_transaction()
        self._test_done_flag_set()
        self.end_round()

        state = cast(BaseState, self.apy_estimation_behaviour.current_state)
        assert state.state_id == self.next_behaviour_class.state_id

    def test_reset_behaviour_without_most_voted_estimate(
        self,
        monkeypatch: MonkeyPatch,
        no_action: Callable[[Any], None],
        caplog: LogCaptureFixture,
    ) -> None:
        """Test reset behaviour without most voted estimate."""
        self.fast_forward_to_state(
            behaviour=self.apy_estimation_behaviour,
            state_id=self.behaviour_class.state_id,
            period_state=PeriodState(
                StateDB(initial_period=0, initial_data=dict(most_voted_estimate=None))
            ),
        )
        state = cast(BaseState, self.apy_estimation_behaviour.current_state)
        assert state.state_id == self.behaviour_class.state_id

        monkeypatch.setattr(BenchmarkTool, "save", lambda _: no_action)
        monkeypatch.setattr(AbciApp, "last_timestamp", datetime.now())

        self.apy_estimation_behaviour.context.params.observation_interval = 0.1

        with caplog.at_level(
            logging.INFO,
            logger="aea.test_agent_name.packages.valory.skills.apy_estimation_abci",
        ):
            self.apy_estimation_behaviour.act_wrapper()
            cast(
                CycleResetBehaviour, self.apy_estimation_behaviour.current_state
            ).params.sleep_time = SLEEP_TIME_TWEAK
            time.sleep(SLEEP_TIME_TWEAK + 0.01)
            self.apy_estimation_behaviour.act_wrapper()

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

        state = cast(BaseState, self.apy_estimation_behaviour.current_state)
        assert state.state_id == self.next_behaviour_class.state_id


class TestFreshModelResetBehaviour(APYEstimationFSMBehaviourBaseCase):
    """Test FreshModelResetBehaviour."""

    behaviour_class = FreshModelResetBehaviour
    next_behaviour_class = FetchBehaviour

    def test_fresh_model_reset_behaviour(self, caplog: LogCaptureFixture) -> None:
        """Run test for `ResetBehaviour`."""
        self.fast_forward_to_state(
            behaviour=self.apy_estimation_behaviour,
            state_id=self.behaviour_class.state_id,
            period_state=PeriodState(StateDB(initial_period=0, initial_data={})),
        )
        state = cast(BaseState, self.apy_estimation_behaviour.current_state)
        assert state.state_id == self.behaviour_class.state_id

        with caplog.at_level(
            logging.INFO,
            logger="aea.test_agent_name.packages.valory.skills.apy_estimation_abci",
        ):
            self.apy_estimation_behaviour.act_wrapper()

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

        state = cast(BaseState, self.apy_estimation_behaviour.current_state)
        assert state.state_id == self.next_behaviour_class.state_id


class TestResetBehaviour(APYEstimationFSMBehaviourBaseCase):
    """Test ResetBehaviour."""

    behaviour_class = ResetBehaviour
    next_behaviour_class = RegistrationBehaviour

    def test_reset_behaviour(self, caplog: LogCaptureFixture) -> None:
        """Run test for `ResetBehaviour`."""
        self.fast_forward_to_state(
            behaviour=self.apy_estimation_behaviour,
            state_id=self.behaviour_class.state_id,
            period_state=PeriodState(StateDB(initial_period=0, initial_data={})),
        )
        state = cast(BaseState, self.apy_estimation_behaviour.current_state)
        assert state.state_id == self.behaviour_class.state_id

        with caplog.at_level(
            logging.INFO,
            logger="aea.test_agent_name.packages.valory.skills.apy_estimation_abci",
        ):
            self.apy_estimation_behaviour.act_wrapper()

        assert "[test_agent_name] Entered in the 'reset' behaviour state" in caplog.text
        assert "[test_agent_name] Period 0 was not finished. Resetting!" in caplog.text

        self.mock_a2a_transaction()
        self._test_done_flag_set()
        self.end_round()

        state = cast(BaseState, self.apy_estimation_behaviour.current_state)
        assert state.state_id == self.next_behaviour_class.state_id
