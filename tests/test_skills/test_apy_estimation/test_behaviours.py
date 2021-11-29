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

"""Tests for valory/apy_estimation skill's behaviours."""

import json
import logging
import time
from copy import copy
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Tuple, Type, cast
from unittest import mock
from unittest.mock import patch

import pytest
from aea.exceptions import AEAActException
from aea.helpers.transaction.base import SignedMessage
from aea.test_tools.test_skill import BaseSkillTestCase

from packages.open_aea.protocols.signing import SigningMessage
from packages.valory.connections.http_client.connection import (
    PUBLIC_ID as HTTP_CLIENT_PUBLIC_ID,
)
from packages.valory.protocols.abci import AbciMessage  # noqa: F401
from packages.valory.protocols.http import HttpMessage
from packages.valory.skills.abstract_round_abci.base import (
    AbstractRound,
    BasePeriodState,
    BaseTxPayload,
    OK_CODE,
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
from packages.valory.skills.apy_estimation.behaviours import (
    APYEstimationConsensusBehaviour,
    FetchBehaviour,
    RegistrationBehaviour,
    TendermintHealthcheckBehaviour,
    TransformBehaviour,
)
from packages.valory.skills.apy_estimation.rounds import Event, PeriodState

from tests.conftest import ROOT_DIR


class APYEstimationFSMBehaviourBaseCase(BaseSkillTestCase):
    """Base case for testing APYEstimation FSMBehaviour."""

    path_to_skill = Path(ROOT_DIR, "packages", "valory", "skills", "apy_estimation")

    apy_estimation_behaviour: APYEstimationConsensusBehaviour
    ledger_handler: LedgerApiHandler
    http_handler: HttpHandler
    contract_handler: ContractApiHandler
    signing_handler: SigningHandler
    old_tx_type_to_payload_cls: Dict[str, Type[BaseTxPayload]]

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
        current_state = cast(BaseState, current_state)
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
        time.sleep(1)
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
        time.sleep(1)
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
        time.sleep(1)
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
            PeriodState(),
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


class TestFetchBehaviour(APYEstimationFSMBehaviourBaseCase):
    """Test FetchBehaviour."""

    def test_fetch_behaviour(
        self,
        monkeypatch,
        top_n_pairs_q,
        block_from_timestamp_q,
        eth_price_usd_q,
        pairs_q,
        pool_fields: Tuple[str, ...],
    ) -> None:
        """Run tests."""
        self.fast_forward_to_state(
            self.apy_estimation_behaviour,
            FetchBehaviour.state_id,
            PeriodState(),
        )

        request_kwargs = dict(
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

        # top pairs' ids request.
        # with mock.patch(
        #         'packages.valory.skills.apy_estimation.behaviours.top_n_pairs_q',
        #         new_callable=lambda *x: top_n_pairs_q
        # ):
        self.apy_estimation_behaviour.act_wrapper()
        self.apy_estimation_behaviour.context.logger.info(top_n_pairs_q)
        request_kwargs["body"] = json.dumps(top_n_pairs_q).encode("utf-8")
        res = {"data": {"pairs": [{"id": "x0"}, {"id": "x2"}]}}
        response_kwargs["body"] = json.dumps(res).encode("utf-8")
        self.mock_http_request(request_kwargs, response_kwargs)

        request_kwargs = dict(
            method="POST",
            url="https://api.thegraph.com/subgraphs/name/matthewlilley/fantom-blocks",
            headers="Content-Type: application/json\r\n",
            version="",
        )

        # # block request.
        # self.apy_estimation_behaviour.act_wrapper()
        # # TOFIX: mock timestamp in gen_unix_timestamps
        # request_kwargs['body'] = json.dumps(block_from_timestamp_q).encode("utf-8")
        # res = {"data": {"blocks": [{'timestamp': '1', 'number': '1'}]}}
        # response_kwargs['body'] = json.dumps(res).encode("utf-8")
        # self.mock_http_request(request_kwargs, response_kwargs)

        # ETH price request.
        self.apy_estimation_behaviour.act_wrapper()
        monkeypatch.setattr(
            "packages.valory.skills.apy_estimation.behaviours.eth_price_usd_q",
            eth_price_usd_q,
        )
        request_kwargs["body"] = eth_price_usd_q
        res = {"data": {"bundles": [{"ethPrice": "0.8973548"}]}}
        response_kwargs["body"] = json.dumps(res).encode("utf-8")
        self.mock_http_request(request_kwargs, response_kwargs)

        # top pairs data.
        self.apy_estimation_behaviour.act_wrapper()
        monkeypatch.setattr(
            "packages.valory.skills.apy_estimation.behaviours.pairs_q", pairs_q
        )
        request_kwargs["body"] = pairs_q
        res = {
            "data": {
                "pairs": [
                    {field: dummy_value for field in pool_fields}
                    for dummy_value in ("dum1", "dum2")
                ]
            }
        }
        response_kwargs["body"] = json.dumps(res).encode("utf-8")
        self.mock_http_request(request_kwargs, response_kwargs)

        self.mock_a2a_transaction()
        self._test_done_flag_set()
        self.end_round()
        state = cast(BaseState, self.apy_estimation_behaviour.current_state)
        assert state.state_id == TransformBehaviour.state_id


class TestTransformBehaviour(APYEstimationFSMBehaviourBaseCase):
    """Test FetchBehaviour."""

    def test_transform_behaviour(self):
        """Run test for `transform_behaviour`."""
        # TODO
        assert False


class TestPreprocessBehaviour(APYEstimationFSMBehaviourBaseCase):
    """Test PreprocessBehaviour."""

    def test_preprocess_behaviour(self):
        """Run test for `preprocess_behaviour`."""
        # TODO
        assert False


class TestOptimizeBehaviour(APYEstimationFSMBehaviourBaseCase):
    """Test OptimizeBehaviour."""

    def test_optimize_behaviour(self):
        """Run test for `optimize_behaviour`."""
        # TODO
        assert False


class TestTrainBehaviour(APYEstimationFSMBehaviourBaseCase):
    """Test TrainBehaviour."""

    def test_train_behaviour(self):
        """Run test for `train_behaviour`."""
        # TODO
        assert False


class TestTestBehaviour(APYEstimationFSMBehaviourBaseCase):
    """Test TestBehaviour."""

    def test_test_behaviour(self):
        """Run test for `test_behaviour`."""
        # TODO
        assert False


class TestEstimateBehaviour(APYEstimationFSMBehaviourBaseCase):
    """Test EstimateBehaviour."""

    def test_estimate_behaviour(self):
        """Run test for `estimate_behaviour`."""
        # TODO
        assert False
