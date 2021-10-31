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

"""This module contains the handlers for the 'counter_client' skill."""
# isort: skip_file # noqa
from typing import Optional, cast

from aea.configurations.data_types import PublicId
from aea.protocols.base import Message
from aea.skills.base import Handler

from packages.valory.protocols.http import (  # type: ignore # pylint: disable=no-name-in-module,import-error
    HttpMessage,
)
from packages.valory.skills.counter_client.dialogues import HttpDialogue, HttpDialogues
from packages.valory.skills.counter_client.utils import curdatetime, decode_value


class HttpHandler(Handler):
    """The HTTP response handler."""

    SUPPORTED_PROTOCOL = HttpMessage.protocol_id  # type: Optional[PublicId]

    def setup(self) -> None:
        """Set up the handler."""

    def handle(self, message: Message) -> None:
        """Handle a message."""
        http_message = cast(HttpMessage, message)

        # recover dialogue
        http_dialogues = cast(HttpDialogues, self.context.http_dialogues)
        http_dialogue = cast(
            Optional[HttpDialogue], http_dialogues.update(http_message)
        )
        if http_dialogue is None:
            self.context.logger.error(
                "something went wrong when adding the incoming HTTP message to the dialogue."
            )
            return

        if (
            http_message.performative != HttpMessage.Performative.RESPONSE
            or http_message.status_code != 200
        ):
            self.context.logger.info(
                f"response not valid: performative={http_message.performative}, "
                f"status_code={http_message.status_code}"
            )
            return

        request_nonce = http_dialogue.dialogue_label.dialogue_reference[0]
        callback_name = self.context.state.request_to_handler.pop(request_nonce, None)
        if callback_name is None:  # pragma: nocover
            return
        callback = getattr(self, callback_name, None)
        if callback is None:  # pragma: nocover
            return
        callback(http_message)

    def abci_query(self, message: HttpMessage) -> None:
        """Handle abci_query responses."""
        value = decode_value(message)
        has_changed = value != self.context.state.count
        self.context.logger.info(
            f"[{curdatetime()}] The counter value is: {value}."
            + ("Updating current state" if has_changed else "")
        )
        if has_changed:
            self.context.state.count = value

    def broadcast_tx_commit(self, _message: HttpMessage) -> None:
        """Handle broadcast_tx_commit responses."""
        self.context.logger.debug(f"[{curdatetime()}] Transaction completed.")

    def teardown(self) -> None:
        """Tear down the handler."""
