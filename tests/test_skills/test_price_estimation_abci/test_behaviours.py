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

"""Tests for valory/price_estimation_abci skill's behaviours."""
import json
import logging
from pathlib import Path
from typing import cast
from unittest.mock import patch

import pytest
from aea.exceptions import AEAActException
from aea.helpers.transaction.base import SignedMessage
from aea.test_tools.test_skill import BaseSkillTestCase

from packages.fetchai.connections.http_client.connection import (
    PUBLIC_ID as HTTP_CLIENT_PUBLIC_ID,
)
from packages.fetchai.protocols.http import HttpMessage
from packages.fetchai.protocols.signing import SigningMessage
from packages.valory.connections.abci.connection import (  # noqa: F401
    PUBLIC_ID as ABCI_SERVER_PUBLIC_ID,
)
from packages.valory.protocols.abci import AbciMessage  # noqa: F401
from packages.valory.skills.abstract_round_abci.base import OK_CODE, _MetaPayload
from packages.valory.skills.abstract_round_abci.behaviour_utils import BaseState
from packages.valory.skills.abstract_round_abci.behaviours import AbstractRoundBehaviour
from packages.valory.skills.price_estimation_abci.behaviours import (
    PriceEstimationConsensusBehaviour,
    RegistrationBehaviour,
    TendermintHealthcheckBehaviour,
)
from packages.valory.skills.price_estimation_abci.handlers import (
    HttpHandler,
    SigningHandler,
)

from tests.conftest import ROOT_DIR


class PriceEstimationFSMBehaviourBaseCase(BaseSkillTestCase):
    """Base case for testing PriceEstimation FSMBehaviour."""

    path_to_skill = Path(
        ROOT_DIR, "packages", "valory", "skills", "price_estimation_abci"
    )

    @classmethod
    def setup(cls):
        """Setup the test class."""
        super().setup()
        cls._skill.skill_context._agent_context.identity._default_address_key = (
            "ethereum"
        )
        cls._skill.skill_context._agent_context._default_ledger_id = "ethereum"
        cls.price_estimation_behaviour = cast(
            PriceEstimationConsensusBehaviour,
            cls._skill.skill_context.behaviours.main,
        )
        cls.http_handler = cast(HttpHandler, cls._skill.skill_context.handlers.http)
        cls.signing_handler = cast(
            SigningHandler, cls._skill.skill_context.handlers.signing
        )
        cls.price_estimation_behaviour.setup()
        cls._skill.skill_context.state.setup()
        assert (
            cls.price_estimation_behaviour.current
            == cls.price_estimation_behaviour.initial_state
        )

    @staticmethod
    def fast_forward_to_state(behaviour: AbstractRoundBehaviour, state_id: str) -> None:
        """Fast forward the FSM to a state."""
        next_state = behaviour.get_state(state_id)
        assert next_state is not None, f"State {state_id} not found"
        behaviour.current = cast(BaseState, next_state).state_id

    @classmethod
    def teardown(cls) -> None:
        """Teardown the test class."""
        _MetaPayload.transaction_type_to_payload_cls = {}


class TestTendermintHealthcheckBehaviour(PriceEstimationFSMBehaviourBaseCase):
    """Test case to test TendermintHealthcheckBehaviour."""

    def test_tendermint_healthcheck_not_live(self):
        """Test the tendermint health check does not finish if not healthy."""
        assert (
            self.price_estimation_behaviour.current
            == TendermintHealthcheckBehaviour.state_id
        )
        self.price_estimation_behaviour.act_wrapper()
        self.assert_quantity_in_outbox(1)
        actual_http_message = self.get_message_from_outbox()
        has_attributes, error_str = self.message_has_attributes(
            actual_message=actual_http_message,
            message_type=HttpMessage,
            performative=HttpMessage.Performative.REQUEST,
            to=str(HTTP_CLIENT_PUBLIC_ID),
            sender=str(self.skill.skill_context.skill_id),
            method="GET",
            url=self.skill.skill_context.params.tendermint_url + "/health",
            headers="",
            version="",
            body=b"",
        )
        assert has_attributes, error_str
        self.price_estimation_behaviour.act_wrapper()
        self.assert_quantity_in_outbox(0)
        incoming_message = self.build_incoming_message(
            message_type=HttpMessage,
            dialogue_reference=(actual_http_message.dialogue_reference[0], "stub"),
            performative=HttpMessage.Performative.RESPONSE,
            target=actual_http_message.message_id,
            message_id=-1,
            to=str(self.skill.skill_context.skill_id),
            sender=str(HTTP_CLIENT_PUBLIC_ID),
            version="",
            status_code=500,
            status_text="",
            headers="",
            body=b"",
        )
        self.http_handler.handle(incoming_message)
        with patch.object(
            self.price_estimation_behaviour.context.logger, "log"
        ) as mock_logger:
            self.price_estimation_behaviour.act_wrapper()
        mock_logger.assert_any_call(
            logging.ERROR, "Tendermint not running, trying again!"
        )
        state = self.price_estimation_behaviour.get_state(
            TendermintHealthcheckBehaviour.state_id
        )
        assert not state.is_done()

    def test_tendermint_healthcheck_not_live_raises(self):
        """Test the tendermint health check raises if not healthy for too long."""
        assert (
            self.price_estimation_behaviour.current
            == TendermintHealthcheckBehaviour.state_id
        )
        self.skill.skill_context.params._count_healthcheck = (
            self.skill.skill_context.params._max_healthcheck + 1
        )
        with pytest.raises(AEAActException, match="Tendermint node did not come live!"):
            self.price_estimation_behaviour.act_wrapper()

    def test_tendermint_healthcheck_live(self):
        """Test the tendermint health check does finish if healthy."""
        assert (
            self.price_estimation_behaviour.current
            == TendermintHealthcheckBehaviour.state_id
        )
        self.price_estimation_behaviour.act_wrapper()
        self.assert_quantity_in_outbox(1)
        actual_http_message = self.get_message_from_outbox()
        has_attributes, error_str = self.message_has_attributes(
            actual_message=actual_http_message,
            message_type=HttpMessage,
            performative=HttpMessage.Performative.REQUEST,
            to=str(HTTP_CLIENT_PUBLIC_ID),
            sender=str(self.skill.skill_context.skill_id),
            method="GET",
            url=self.skill.skill_context.params.tendermint_url + "/health",
            headers="",
            version="",
            body=b"",
        )
        assert has_attributes, error_str
        self.price_estimation_behaviour.act_wrapper()
        self.assert_quantity_in_outbox(0)
        incoming_message = self.build_incoming_message(
            message_type=HttpMessage,
            dialogue_reference=(actual_http_message.dialogue_reference[0], "stub"),
            performative=HttpMessage.Performative.RESPONSE,
            target=actual_http_message.message_id,
            message_id=-1,
            to=str(self.skill.skill_context.skill_id),
            sender=str(HTTP_CLIENT_PUBLIC_ID),
            version="",
            status_code=200,
            status_text="",
            headers="",
            body=json.dumps({}).encode("utf-8"),
        )
        self.http_handler.handle(incoming_message)
        with patch.object(
            self.price_estimation_behaviour.context.logger, "log"
        ) as mock_logger:
            self.price_estimation_behaviour.act_wrapper()
        mock_logger.assert_any_call(logging.INFO, "Tendermint running.")
        state = self.price_estimation_behaviour.get_state(
            TendermintHealthcheckBehaviour.state_id
        )
        assert state.is_done()


class TestRegistrationBehaviour(PriceEstimationFSMBehaviourBaseCase):
    """Test case to test RegistrationBehaviour."""

    def test_registration(self):
        """Test registration."""
        self.fast_forward_to_state(
            self.price_estimation_behaviour, RegistrationBehaviour.state_id
        )
        assert self.price_estimation_behaviour.current == RegistrationBehaviour.state_id
        self.price_estimation_behaviour.act_wrapper()
        self.assert_quantity_in_decision_making_queue(1)
        actual_signing_message = self.get_message_from_decision_maker_inbox()
        has_attributes, error_str = self.message_has_attributes(
            actual_message=actual_signing_message,
            message_type=SigningMessage,
            performative=SigningMessage.Performative.SIGN_MESSAGE,
            to="dummy_decision_maker_address",
            sender=str(self.skill.skill_context.skill_id),
        )
        assert has_attributes, error_str
        incoming_message = self.build_incoming_message(
            message_type=SigningMessage,
            dialogue_reference=(actual_signing_message.dialogue_reference[0], "stub"),
            performative=SigningMessage.Performative.SIGNED_MESSAGE,
            target=actual_signing_message.message_id,
            message_id=-1,
            to=str(self.skill.skill_context.skill_id),
            sender="dummy_decision_maker_address",
            signed_message=SignedMessage(ledger_id="ethereum", body="stub_signature"),
        )
        self.signing_handler.handle(incoming_message)
        self.price_estimation_behaviour.act_wrapper()
        self.assert_quantity_in_outbox(1)
        actual_http_message = self.get_message_from_outbox()
        has_attributes, error_str = self.message_has_attributes(
            actual_message=actual_http_message,
            message_type=HttpMessage,
            performative=HttpMessage.Performative.REQUEST,
            to=str(HTTP_CLIENT_PUBLIC_ID),
            sender=str(self.skill.skill_context.skill_id),
            method="GET",
            headers="",
            version="",
            body=b"",
        )
        assert has_attributes, error_str
        incoming_message = self.build_incoming_message(
            message_type=HttpMessage,
            dialogue_reference=(actual_http_message.dialogue_reference[0], "stub"),
            performative=HttpMessage.Performative.RESPONSE,
            target=actual_http_message.message_id,
            message_id=-1,
            to=str(self.skill.skill_context.skill_id),
            sender=str(HTTP_CLIENT_PUBLIC_ID),
            version="",
            status_code=200,
            status_text="",
            headers="",
            body=json.dumps({"result": {"deliver_tx": {"code": OK_CODE}}}).encode(
                "utf-8"
            ),
        )
        self.http_handler.handle(incoming_message)
        self.price_estimation_behaviour.act_wrapper()
        state = self.price_estimation_behaviour.get_state(
            RegistrationBehaviour.state_id
        )
        assert not state.is_done()
        # for sender in ["sender_a", "sender_b", "sender_c", "sender_d"]:  # noqa: E800
        #     incoming_message = self.build_incoming_message(  # noqa: E800
        #         message_type=AbciMessage,  # noqa: E800
        #         dialogue_reference=("stub", ""),  # noqa: E800
        #         performative=AbciMessage.Performative.REQUEST_DELIVER_TX,  # noqa: E800
        #         target=0,  # noqa: E800
        #         message_id=1,  # noqa: E800
        #         to=str(self.skill.skill_context.skill_id),  # noqa: E800
        #         sender=str(ABCI_SERVER_PUBLIC_ID),  # noqa: E800
        #         tx=,  # noqa: E800
        #     )  # noqa: E800
        #     self.http_handler.handle(incoming_message)  # noqa: E800
        # self.price_estimation_behaviour.act_wrapper()  # noqa: E800
        # assert state.is_done()  # noqa: E800
