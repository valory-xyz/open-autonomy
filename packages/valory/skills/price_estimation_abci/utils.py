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

"""This module contains utility functions for the 'price_estimation_abci' skill."""
import json
from typing import Dict, Optional, cast

from aea.skills.base import SkillContext

from packages.fetchai.connections.http_client.connection import (
    PUBLIC_ID as HTTP_CLIENT_PUBLIC_ID,  # type: ignore # pylint: disable=no-name-in-module,import-error; type: ignore
)
from packages.fetchai.protocols.http import HttpMessage
from packages.valory.skills.price_estimation_abci.dialogues import HttpDialogues


def _send_http_request_message(
    context: SkillContext,
    method: str,
    url: str,
    content: Dict = None,
    handler_callback: Optional[str] = None,
) -> None:
    """
    Send an http request message from the skill context.

    This method is skill-specific, and therefore
    should not be used elsewhere.

    :param context: the skill context.
    :param method: the http request method (i.e. 'GET' or 'POST').
    :param url: the url to send the message to.
    :param content: the payload.
    :param handler_callback: the handler callback. It must match
        the name of the method to be called in the handler.
    """
    # context
    http_dialogues = cast(HttpDialogues, context.http_dialogues)

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
    # send
    context.outbox.put_message(message=request_http_message)
    request_nonce = http_dialogue.dialogue_label.dialogue_reference[0]
    context.state.request_to_handler[request_nonce] = handler_callback
