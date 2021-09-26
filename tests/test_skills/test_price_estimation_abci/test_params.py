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

"""Tests for valory/price_estimation_abci skill."""
import json
import logging
from pathlib import Path
from typing import cast
from unittest.mock import patch

from aea.test_tools.test_skill import BaseSkillTestCase

from packages.fetchai.connections.http_client.connection import (
    PUBLIC_ID as HTTP_CLIENT_PUBLIC_ID,
)
from packages.fetchai.protocols.http import HttpMessage
from packages.valory.skills.price_estimation_abci.behaviours import (
    PriceEstimationConsensusBehaviour,
    TendermintHealthcheck,
)
from packages.valory.skills.price_estimation_abci.handlers import HttpHandler

from tests.conftest import ROOT_DIR


class TestPriceEstimationFSMBehaviour(BaseSkillTestCase):
    """Test GenericStrategy of generic seller."""

    path_to_skill = Path(
        ROOT_DIR, "packages", "valory", "skills", "price_estimation_abci"
    )

    @classmethod
    def setup(cls):
        """Setup the test class."""
        super().setup()
        cls.price_estimation_behaviour = cast(
            PriceEstimationConsensusBehaviour,
            cls._skill.skill_context.behaviours.main,
        )
        cls.http_handler = cast(HttpHandler, cls._skill.skill_context.handlers.http)
        cls.price_estimation_behaviour.setup()
        assert (
            cls.price_estimation_behaviour.current
            == cls.price_estimation_behaviour.initial_state
        )

    def test_tendermint_healthcheck_not_live(self):
        """Test the tendermint health check does not finish if not healthy."""
        assert self.price_estimation_behaviour.current == TendermintHealthcheck.state_id
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
            TendermintHealthcheck.state_id
        )
        assert not state.is_done()

    def test_tendermint_healthcheck_live(self):
        """Test the tendermint health check does finish if healthy."""
        assert self.price_estimation_behaviour.current == TendermintHealthcheck.state_id
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
            TendermintHealthcheck.state_id
        )
        assert state.is_done()
