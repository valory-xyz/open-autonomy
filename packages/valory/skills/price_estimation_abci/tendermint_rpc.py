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

"""Wrappers to Tendermint RPC messages (via HTTP)."""
import json
from abc import ABC
from functools import partial
from typing import Dict, Tuple, cast

from aea.skills.base import Behaviour

from packages.fetchai.connections.http_client.connection import (
    PUBLIC_ID as HTTP_CLIENT_PUBLIC_ID,  # type: ignore # pylint: disable=no-name-in-module,import-error; type: ignore
)
from packages.fetchai.protocols.http import HttpMessage
from packages.valory.skills.price_estimation_abci.behaviours_utils import AsyncBehaviour
from packages.valory.skills.price_estimation_abci.dialogues import (
    HttpDialogue,
    HttpDialogues,
)
from packages.valory.skills.price_estimation_abci.models import OK_CODE


class BehaviourUtils(Behaviour, ABC):
    """MixIn for behaviours with several utility methods."""

    is_programmatically_defined = True

    def do_request(
        self, request_message: HttpMessage, http_dialogue: HttpDialogue
    ) -> HttpMessage:
        """
        Do a request and wait the response, asynchronously.

        :param request_message: The request message
        :param http_dialogue: the HTTP dialogue associated to the request
        :yield: wait the response message
        :return: the response message
        """
        self.context.outbox.put_message(message=request_message)
        request_nonce = http_dialogue.dialogue_label.dialogue_reference[0]

        def write_message(self_, message):
            self_ = cast(AsyncBehaviour, self_)
            self_.try_send(message)

        self.context.state.request_id_to_callback[request_nonce] = partial(
            write_message, self
        )

        response = yield
        return response

    def broadcast_tx_commit(self, tx_bytes: bytes) -> HttpMessage:
        """Send a broadcast_tx_commit request."""
        request_message, http_dialogue = self._build_http_request_message(
            "GET",
            self.context.params.tendermint_url
            + f"/broadcast_tx_commit?tx=0x{tx_bytes.hex()}",
        )
        result = yield from self.do_request(request_message, http_dialogue)
        return result

    def _build_http_request_message(
        self,
        method: str,
        url: str,
        content: Dict = None,
    ) -> Tuple[HttpMessage, HttpDialogue]:
        """
        Send an http request message from the skill context.

        This method is skill-specific, and therefore
        should not be used elsewhere.

        :param method: the http request method (i.e. 'GET' or 'POST').
        :param url: the url to send the message to.
        :param content: the payload.
        :return: the http message and the http dialogue
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
            body=b"" if content is None else json.dumps(content).encode("utf-8"),
        )
        request_http_message = cast(HttpMessage, request_http_message)
        http_dialogue = cast(HttpDialogue, http_dialogue)
        return request_http_message, http_dialogue

    @classmethod
    def _check_transaction_delivered(cls, response: HttpMessage) -> bool:
        """Check deliver_tx response was successful."""
        json_body = json.loads(response.body)
        deliver_tx_response = json_body["result"]["deliver_tx"]
        return deliver_tx_response["code"] == OK_CODE
