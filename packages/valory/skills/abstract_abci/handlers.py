# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2024 Valory AG
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

"""This module contains the handler for the 'abci' skill."""
from typing import List, cast

from aea.protocols.base import Message
from aea.skills.base import Handler

from packages.valory.connections.abci.connection import PUBLIC_ID
from packages.valory.protocols.abci import AbciMessage
from packages.valory.protocols.abci.custom_types import (
    Events,
    ProofOps,
    Result,
    ResultType,
    SnapShots,
    ValidatorUpdates,
)
from packages.valory.protocols.abci.dialogues import AbciDialogue, AbciDialogues


ERROR_CODE = 1


class ABCIHandler(Handler):
    """
    Default ABCI handler.

    This abstract skill provides a template of an ABCI application managed by an
    AEA. This abstract Handler replies to ABCI requests with default responses.
    In another skill, extend the class and override the request handlers
    to implement a custom behaviour.
    """

    SUPPORTED_PROTOCOL = AbciMessage.protocol_id

    def setup(self) -> None:
        """Set up the handler."""
        self.context.logger.debug(
            f"ABCI Handler: setup method called. Using {PUBLIC_ID}."
        )

    def handle(self, message: Message) -> None:
        """
        Handle the message.

        :param message: the message.
        """
        abci_message = cast(AbciMessage, message)

        # recover dialogue
        abci_dialogues = cast(AbciDialogues, self.context.abci_dialogues)
        abci_dialogue = cast(AbciDialogue, abci_dialogues.update(message))

        if abci_dialogue is None:
            self.log_exception(abci_message, "Invalid dialogue.")
            return

        performative = message.performative.value

        # handle message
        request_type = performative.replace("request_", "")
        self.context.logger.debug(f"Received ABCI request of type {request_type}")
        handler = getattr(self, request_type, None)
        if handler is None:  # pragma: nocover
            self.context.logger.warning(
                f"Cannot handle request '{request_type}', ignoring..."
            )
            return

        self.context.logger.debug(
            "ABCI Handler: message={}, sender={}".format(message, message.sender)
        )
        response = handler(message, abci_dialogue)
        self.context.outbox.put_message(message=response)

    def teardown(self) -> None:
        """Teardown the handler."""
        self.context.logger.debug("ABCI Handler: teardown method called.")

    def log_exception(self, message: AbciMessage, error_message: str) -> None:
        """Log a response exception."""
        self.context.logger.error(
            f"An exception occurred: {error_message} for message: {message}"
        )

    def echo(  # pylint: disable=no-self-use
        self, message: AbciMessage, dialogue: AbciDialogue
    ) -> AbciMessage:
        """
        Handle a message of REQUEST_ECHO performative.

        :param message: the ABCI request.
        :param dialogue: the ABCI dialogue.
        :return: the response.
        """
        reply = dialogue.reply(
            performative=AbciMessage.Performative.RESPONSE_ECHO,
            target_message=message,
            message=message.message,
        )
        return cast(AbciMessage, reply)

    def info(  # pylint: disable=no-self-use
        self, message: AbciMessage, dialogue: AbciDialogue
    ) -> AbciMessage:
        """
        Handle a message of REQUEST_INFO performative.

        :param message: the ABCI request.
        :param dialogue: the ABCI dialogue.
        :return: the response.
        """
        info_data = ""
        version = ""
        app_version = 0
        last_block_height = 0
        last_block_app_hash = b""
        reply = dialogue.reply(
            performative=AbciMessage.Performative.RESPONSE_INFO,
            target_message=message,
            info_data=info_data,
            version=version,
            app_version=app_version,
            last_block_height=last_block_height,
            last_block_app_hash=last_block_app_hash,
        )
        return cast(AbciMessage, reply)

    def flush(  # pylint: disable=no-self-use
        self,
        message: AbciMessage,
        dialogue: AbciDialogue,
    ) -> AbciMessage:
        """
        Handle a message of REQUEST_FLUSH performative.

        :param message: the ABCI request.
        :param dialogue: the ABCI dialogue.
        :return: the response.
        """
        reply = dialogue.reply(
            performative=AbciMessage.Performative.RESPONSE_FLUSH,
            target_message=message,
        )
        return cast(AbciMessage, reply)

    def set_option(  # pylint: disable=no-self-use
        self,
        message: AbciMessage,
        dialogue: AbciDialogue,
    ) -> AbciMessage:
        """
        Handle a message of REQUEST_SET_OPTION performative.

        :param message: the ABCI request.
        :param dialogue: the ABCI dialogue.
        :return: the response.
        """
        reply = dialogue.reply(
            performative=AbciMessage.Performative.RESPONSE_SET_OPTION,
            target_message=message,
            code=ERROR_CODE,
            log="operation not supported",
            info="operation not supported",
        )
        return cast(AbciMessage, reply)

    def init_chain(  # pylint: disable=no-self-use
        self, message: AbciMessage, dialogue: AbciDialogue
    ) -> AbciMessage:
        """
        Handle a message of REQUEST_INIT_CHAIN performative.

        :param message: the ABCI request.
        :param dialogue: the ABCI dialogue.
        :return: the response.
        """
        validators: List = []
        app_hash = b""
        reply = dialogue.reply(
            performative=AbciMessage.Performative.RESPONSE_INIT_CHAIN,
            target_message=message,
            validators=ValidatorUpdates(validators),
            app_hash=app_hash,
        )
        return cast(AbciMessage, reply)

    def query(  # pylint: disable=no-self-use
        self, message: AbciMessage, dialogue: AbciDialogue
    ) -> AbciMessage:
        """
        Handle a message of REQUEST_QUERY performative.

        :param message: the ABCI request.
        :param dialogue: the ABCI dialogue.
        :return: the response.
        """
        reply = dialogue.reply(
            performative=AbciMessage.Performative.RESPONSE_QUERY,
            target_message=message,
            code=ERROR_CODE,
            log="operation not supported",
            info="operation not supported",
            index=0,
            key=b"",
            value=b"",
            proof_ops=ProofOps([]),
            height=0,
            codespace="",
        )
        return cast(AbciMessage, reply)

    def check_tx(  # pylint: disable=no-self-use
        self, message: AbciMessage, dialogue: AbciDialogue
    ) -> AbciMessage:
        """
        Handle a message of REQUEST_CHECK_TX performative.

        :param message: the ABCI request.
        :param dialogue: the ABCI dialogue.
        :return: the response.
        """
        reply = dialogue.reply(
            performative=AbciMessage.Performative.RESPONSE_CHECK_TX,
            target_message=message,
            code=ERROR_CODE,
            data=b"",
            log="operation not supported",
            info="operation not supported",
            gas_wanted=0,
            gas_used=0,
            events=Events([]),
            codespace="",
        )
        return cast(AbciMessage, reply)

    def deliver_tx(  # pylint: disable=no-self-use
        self, message: AbciMessage, dialogue: AbciDialogue
    ) -> AbciMessage:
        """
        Handle a message of REQUEST_DELIVER_TX performative.

        :param message: the ABCI request.
        :param dialogue: the ABCI dialogue.
        :return: the response.
        """
        reply = dialogue.reply(
            performative=AbciMessage.Performative.RESPONSE_DELIVER_TX,
            target_message=message,
            code=ERROR_CODE,
            data=b"",
            log="operation not supported",
            info="operation not supported",
            gas_wanted=0,
            gas_used=0,
            events=Events([]),
            codespace="",
        )
        return cast(AbciMessage, reply)

    def begin_block(  # pylint: disable=no-self-use
        self, message: AbciMessage, dialogue: AbciDialogue
    ) -> AbciMessage:
        """
        Handle a message of REQUEST_BEGIN_BLOCK performative.

        :param message: the ABCI request.
        :param dialogue: the ABCI dialogue.
        :return: the response.
        """
        reply = dialogue.reply(
            performative=AbciMessage.Performative.RESPONSE_BEGIN_BLOCK,
            target_message=message,
            events=Events([]),
        )
        return cast(AbciMessage, reply)

    def end_block(  # pylint: disable=no-self-use
        self, message: AbciMessage, dialogue: AbciDialogue
    ) -> AbciMessage:
        """
        Handle a message of REQUEST_END_BLOCK performative.

        :param message: the ABCI request.
        :param dialogue: the ABCI dialogue.
        :return: the response.
        """
        reply = dialogue.reply(
            performative=AbciMessage.Performative.RESPONSE_END_BLOCK,
            target_message=message,
            validator_updates=ValidatorUpdates([]),
            events=Events([]),
        )
        return cast(AbciMessage, reply)

    def commit(  # pylint: disable=no-self-use
        self, message: AbciMessage, dialogue: AbciDialogue
    ) -> AbciMessage:
        """
        Handle a message of REQUEST_COMMIT performative.

        :param message: the ABCI request.
        :param dialogue: the ABCI dialogue.
        :return: the response.
        """
        reply = dialogue.reply(
            performative=AbciMessage.Performative.RESPONSE_COMMIT,
            target_message=message,
            data=b"",
            retain_height=0,
        )
        return cast(AbciMessage, reply)

    def list_snapshots(  # pylint: disable=no-self-use
        self,
        message: AbciMessage,
        dialogue: AbciDialogue,
    ) -> AbciMessage:
        """
        Handle a message of REQUEST_LIST_SNAPSHOT performative.

        :param message: the ABCI request.
        :param dialogue: the ABCI dialogue.
        :return: the response.
        """
        reply = dialogue.reply(
            performative=AbciMessage.Performative.RESPONSE_LIST_SNAPSHOTS,
            target_message=message,
            snapshots=SnapShots([]),
        )
        return cast(AbciMessage, reply)

    def offer_snapshot(  # pylint: disable=no-self-use
        self,
        message: AbciMessage,
        dialogue: AbciDialogue,
    ) -> AbciMessage:
        """
        Handle a message of REQUEST_OFFER_SNAPSHOT performative.

        :param message: the ABCI request.
        :param dialogue: the ABCI dialogue.
        :return: the response.
        """
        reply = dialogue.reply(
            performative=AbciMessage.Performative.RESPONSE_OFFER_SNAPSHOT,
            target_message=message,
            result=Result(ResultType.REJECT),  # by default, we reject
        )
        return cast(AbciMessage, reply)

    def load_snapshot_chunk(  # pylint: disable=no-self-use
        self,
        message: AbciMessage,
        dialogue: AbciDialogue,
    ) -> AbciMessage:
        """
        Handle a message of REQUEST_LOAD_SNAPSHOT_CHUNK performative.

        :param message: the ABCI request.
        :param dialogue: the ABCI dialogue.
        :return: the response.
        """
        reply = dialogue.reply(
            performative=AbciMessage.Performative.RESPONSE_LOAD_SNAPSHOT_CHUNK,
            target_message=message,
            chunk=b"",
        )
        return cast(AbciMessage, reply)

    def apply_snapshot_chunk(  # pylint: disable=no-self-use
        self,
        message: AbciMessage,
        dialogue: AbciDialogue,
    ) -> AbciMessage:
        """
        Handle a message of REQUEST_APPLY_SNAPSHOT_CHUNK performative.

        :param message: the ABCI request.
        :param dialogue: the ABCI dialogue.
        :return: the response.
        """
        reply = dialogue.reply(
            performative=AbciMessage.Performative.RESPONSE_APPLY_SNAPSHOT_CHUNK,
            target_message=message,
            result=Result(ResultType.REJECT),
            refetch_chunks=tuple(),
            reject_senders=tuple(),
        )
        return cast(AbciMessage, reply)
