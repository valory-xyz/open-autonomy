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

"""Tests for valory/counter_client skill's behaviours."""

# pylint: skip-file

import json
import platform
from pathlib import Path
from typing import Any, cast

import pytest
from aea.test_tools.test_skill import BaseSkillTestCase

from packages.valory.connections.http_client.connection import (
    PUBLIC_ID as HTTP_CLIENT_PUBLIC_ID,
)
from packages.valory.skills.counter_client.behaviours import BaseBehaviour
from packages.valory.skills.counter_client.handlers import HttpHandler, HttpMessage


PACKAGE_DIR = Path(__file__).parent.parent


class BaseTestClass(BaseSkillTestCase):
    """Base test class."""

    path_to_skill = PACKAGE_DIR

    behaviour: BaseBehaviour
    behaviour_name: str
    http_handler: HttpHandler

    @classmethod
    def setup_class(cls, **kwargs: Any) -> None:
        """Setup the test class."""
        super().setup_class()
        assert cls._skill.skill_context._agent_context is not None
        cls._skill.skill_context._agent_context.identity._default_address_key = (
            "ethereum"
        )
        self._skill.skill_context._agent_context._default_ledger_id = "ethereum"
        self.behaviour = getattr(
            self._skill.skill_context.behaviours, self.behaviour_name
        )

        self.http_handler = cast(
            HttpHandler, self._skill.skill_context.handlers.http_handler
        )


class TestIncrementerBehaviour(BaseTestClass):
    """Test IncrementerBehaviour."""

    behaviour_name = "incrementer"

    @pytest.mark.skipif(platform.system() == "Windows", reason="Flaky on Windows.")
    def test_run(
        self,
    ) -> None:
        """Run tests."""

        self.behaviour.act_wrapper()
        self.assert_quantity_in_outbox(1)

        actual_message = self.get_message_from_outbox()
        assert actual_message is not None, "No message in outbox."
        has_attr, msg = self.message_has_attributes(
            actual_message=actual_message,
            message_type=HttpMessage,
            to=str(HTTP_CLIENT_PUBLIC_ID),
            sender=str(self.skill.skill_context.skill_id),
            method="GET",
            headers="",
            url=self.behaviour.tendermint_url + "/broadcast_tx_commit?tx=0x01",
        )

        assert has_attr, msg
        incoming_message = self.build_incoming_message(
            message_type=HttpMessage,
            dialogue_reference=(actual_message.dialogue_reference[0], "stub"),
            performative=HttpMessage.Performative.RESPONSE,
            target=actual_message.message_id,
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
        self.assert_quantity_in_outbox(0)


class TestMonitorBehaviour(BaseTestClass):
    """Test MonitorBehaviour."""

    behaviour_name = "monitor"

    @pytest.mark.skipif(platform.system() == "Windows", reason="Flaky on Windows.")
    def test_run(
        self,
    ) -> None:
        """Run tests."""

        self.behaviour.act_wrapper()
        self.assert_quantity_in_outbox(1)

        actual_message = self.get_message_from_outbox()
        assert actual_message is not None, "No message in outbox."
        has_attr, msg = self.message_has_attributes(
            actual_message=actual_message,
            message_type=HttpMessage,
            to=str(HTTP_CLIENT_PUBLIC_ID),
            sender=str(self.skill.skill_context.skill_id),
            method="GET",
            headers="",
            url=self.behaviour.tendermint_url + "/abci_query",
        )

        assert has_attr, msg
        incoming_message = self.build_incoming_message(
            message_type=HttpMessage,
            dialogue_reference=(actual_message.dialogue_reference[0], "stub"),
            performative=HttpMessage.Performative.RESPONSE,
            target=actual_message.message_id,
            message_id=-1,
            to=str(self.skill.skill_context.skill_id),
            sender=str(HTTP_CLIENT_PUBLIC_ID),
            version="",
            status_code=200,
            status_text="",
            headers="",
            body=json.dumps({"result": {"response": {"value": "AAAACg=="}}}).encode(
                "utf-8"
            ),
        )
        self.http_handler.handle(incoming_message)
        self.assert_quantity_in_outbox(0)


class TestHttpHandler(BaseTestClass):
    """Test `handle` method from HttpHandle."""

    behaviour_name = "monitor"

    @pytest.mark.skipif(platform.system() == "Windows", reason="Flaky on Windows.")
    def test_handle(
        self,
    ) -> None:
        """Run tests."""

        self.behaviour.act_wrapper()
        self.assert_quantity_in_outbox(1)

        actual_message = self.get_message_from_outbox()
        assert actual_message is not None, "No message in outbox."
        has_attr, msg = self.message_has_attributes(
            actual_message=actual_message,
            message_type=HttpMessage,
            to=str(HTTP_CLIENT_PUBLIC_ID),
            sender=str(self.skill.skill_context.skill_id),
            method="GET",
            headers="",
            url=self.behaviour.tendermint_url + "/abci_query",
        )

        assert has_attr, msg
        incoming_message = self.build_incoming_message(
            message_type=HttpMessage,
            dialogue_reference=("stub", "stub"),
            performative=HttpMessage.Performative.RESPONSE,
            target=actual_message.message_id,
            message_id=-1,
            to=str(self.skill.skill_context.skill_id),
            sender=str(HTTP_CLIENT_PUBLIC_ID),
            version="",
            status_code=200,
            status_text="",
            headers="",
            body=json.dumps({"result": {"response": {"value": "AAAACg=="}}}).encode(
                "utf-8"
            ),
        )
        self.http_handler.handle(incoming_message)

        incoming_message = self.build_incoming_message(
            message_type=HttpMessage,
            dialogue_reference=(actual_message.dialogue_reference[0], "stub"),
            performative=HttpMessage.Performative.RESPONSE,
            target=actual_message.message_id,
            message_id=-1,
            to=str(self.skill.skill_context.skill_id),
            sender=str(HTTP_CLIENT_PUBLIC_ID),
            version="",
            status_code=201,
            status_text="",
            headers="",
            body=json.dumps({"result": {"response": {"value": "AAAACg=="}}}).encode(
                "utf-8"
            ),
        )
        self.http_handler.handle(incoming_message)
