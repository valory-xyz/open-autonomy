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
"""This module contains the behaviours for the 'counter_client' skill."""
# isort:skip_file  # noqa
import json
from abc import ABC
from typing import Dict, Optional, cast

from aea.skills.base import Behaviour
from aea.skills.behaviours import TickerBehaviour

from packages.valory.connections.http_client.connection import (  # type: ignore # pylint: disable=no-name-in-module,import-error
    PUBLIC_ID as HTTP_CLIENT_PUBLIC_ID,  # type: ignore
)
from packages.valory.protocols.http import HttpMessage  # type: ignore # pylint: disable=no-name-in-module,import-error

# type: ignore # pylint: disable=no-name-in-module,import-error
from packages.valory.skills.counter_client.dialogues import HttpDialogues
from packages.valory.skills.counter_client.handlers import curdatetime


class BaseBehaviour(Behaviour, ABC):
    """Abstract base behaviour for this skill."""

    is_programmatically_defined = True

    @property
    def tendermint_url(self) -> str:
        """Get the Tendermint url."""
        return cast(str, "http://" + self.context.params.tendermint_url)

    def send_http_request_message(
        self,
        method: str,
        url: str,
        content: Dict = None,
        handler_callback: Optional[str] = None,
    ) -> None:
        """
        Send an http request message.

        :param method: the http request method (i.e. 'GET' or 'POST').
        :param url: the url to send the message to.
        :param content: the payload.
        :param handler_callback: the handler callback. It must match
            the name of the method to be called in the handler.
        """
        # context
        http_dialogues = cast(HttpDialogues, self.context.http_dialogues)

        # http request message
        request_http_message, http_dialogue = http_dialogues.create(
            counterparty=str(HTTP_CLIENT_PUBLIC_ID),
            performative=HttpMessage.Performative.REQUEST,
            method=method,
            url=url,
            headers="",
            version="",
            body=b""
            if content is None
            else json.dumps(content, sort_keys=True).encode("utf-8"),
        )
        # send
        self.context.outbox.put_message(message=request_http_message)
        request_nonce = http_dialogue.dialogue_label.dialogue_reference[0]
        self.context.state.request_to_handler[request_nonce] = handler_callback


class MonitorBehaviour(TickerBehaviour, BaseBehaviour):
    """Send an ABCI query periodically."""

    def query(self) -> None:
        """Send a query request."""
        self.send_http_request_message(
            "GET", self.tendermint_url + "/abci_query", handler_callback="abci_query"
        )

    def act(self) -> None:
        """Do the action."""
        self.query()

    def setup(self) -> None:
        """Set up the behaviour."""

    def teardown(self) -> None:
        """Tear down the behaviour."""


class IncrementerBehaviour(TickerBehaviour, BaseBehaviour):
    """Send a transaction"""

    def send_transaction(self) -> None:
        """Send a query request."""
        next_count = self.context.state.count + 1
        self.context.logger.info(
            f"[{curdatetime()}] Sending transaction with new count: {next_count}"
        )
        self.send_http_request_message(
            "GET",
            self.tendermint_url + "/broadcast_tx_commit?tx=0x{:02x}".format(next_count),
            handler_callback="broadcast_tx_commit",
        )

    def act(self) -> None:
        """Do the action."""
        self.send_transaction()

    def setup(self) -> None:
        """Set up the behaviour."""

    def teardown(self) -> None:
        """Tear down the behaviour."""
