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

"""This module contains the handler for the 'price_estimation_abci' skill."""
from typing import Optional, cast

from aea.configurations.data_types import PublicId
from aea.protocols.base import Message
from aea.skills.base import Handler

from packages.fetchai.protocols.http import HttpMessage
from packages.fetchai.protocols.signing import SigningMessage
from packages.fetchai.protocols.signing.dialogues import SigningDialogue
from packages.valory.skills.abstract_round_abci.handlers import ABCIRoundHandler
from packages.valory.skills.price_estimation_abci.behaviours import (
    PriceEstimationConsensusBehaviour,
    RegistrationBehaviour,
)
from packages.valory.skills.price_estimation_abci.dialogues import (
    HttpDialogue,
    HttpDialogues,
    SigningDialogues,
)


ABCIPriceEstimationHandler = ABCIRoundHandler


class HttpHandler(Handler):
    """The HTTP response handler."""

    SUPPORTED_PROTOCOL = HttpMessage.protocol_id  # type: Optional[PublicId]

    def setup(self) -> None:
        """Set up the handler."""

    def teardown(self) -> None:
        """Tear down the handler."""

    def handle(self, message: Message) -> None:
        """Handle a message."""
        http_message = cast(HttpMessage, message)

        # recover dialogue
        http_dialogues = cast(HttpDialogues, self.context.http_dialogues)
        http_dialogue = cast(
            Optional[HttpDialogue], http_dialogues.update(http_message)
        )
        if http_dialogue is None:
            self._handle_unidentified_dialogue(http_message)
            return

        if http_message.performative != HttpMessage.Performative.RESPONSE:
            self._handle_no_requests(http_message)
            return

        request_nonce = http_dialogue.dialogue_label.dialogue_reference[0]
        callback = self.context.requests.request_id_to_callback.pop(request_nonce, None)
        if callback is None:
            self._handle_no_callback(http_message, http_dialogue)
            return

        if http_message.status_code != 200:
            self.context.logger.info(
                f"response not valid: performative={http_message.performative}, "
                f"status_code={http_message.status_code}"
            )
            callback(http_message)
            return

        callback(http_message)

    def _handle_unidentified_dialogue(self, msg: Message) -> None:
        """
        Handle an unidentified dialogue.

        :param msg: the unidentified message to be handled
        """
        self.context.logger.info(
            "received invalid message={}, unidentified dialogue.".format(msg)
        )

    def _handle_no_callback(self, _message: Message, dialogue: HttpDialogue) -> None:
        """
        Handle no callback found.

        :param _message: the message to be handled
        :param dialogue: the http dialogue
        """
        request_nonce = dialogue.dialogue_label.dialogue_reference[0]
        self.context.logger.warning(
            f"callback not specified for request with nonce {request_nonce}"
        )

    def _handle_no_requests(self, message: HttpMessage) -> None:
        """
        Handle HTTP responses.

        Log an error message saying that the handler did not expect requests
        but only responses.

        :param message: the message
        """
        self.context.logger.warning(
            "invalid message={}, expected HTTP response, got HTTP request.".format(
                message
            )
        )


class SigningHandler(Handler):
    """Implement the transaction handler."""

    SUPPORTED_PROTOCOL = SigningMessage.protocol_id  # type: Optional[PublicId]

    def setup(self) -> None:
        """Implement the setup for the handler."""

    def teardown(self) -> None:
        """Implement the handler teardown."""

    def handle(self, message: Message) -> None:
        """
        Implement the reaction to a message.

        :param message: the message
        """
        signing_msg = cast(SigningMessage, message)

        # recover dialogue
        signing_dialogues = cast(SigningDialogues, self.context.signing_dialogues)
        signing_dialogue = cast(
            Optional[SigningDialogue], signing_dialogues.update(signing_msg)
        )
        if signing_dialogue is None:
            self._handle_unidentified_dialogue(signing_msg)
            return

        # handle message
        if signing_msg.performative is SigningMessage.Performative.SIGNED_MESSAGE:
            self._handle_signed_message(signing_msg, signing_dialogue)
        elif signing_msg.performative is SigningMessage.Performative.ERROR:
            self._handle_error(signing_msg, signing_dialogue)
        else:
            self._handle_invalid(signing_msg, signing_dialogue)

    def _handle_signed_message(
        self, signing_msg: SigningMessage, signing_dialogue: SigningDialogue
    ) -> None:
        self.context.logger.info("transaction signing was successful.")
        self.context.logger.debug(f"signing success for {signing_dialogue}")
        fsm_behaviour = cast(
            PriceEstimationConsensusBehaviour, self.context.behaviours.main
        )
        current_state_name = cast(str, fsm_behaviour.current)
        registration_state = cast(
            RegistrationBehaviour, fsm_behaviour.get_state(current_state_name)
        )
        # send failure
        registration_state.try_send(signing_msg.signed_message)

    def _handle_unidentified_dialogue(self, signing_msg: SigningMessage) -> None:
        """
        Handle an unidentified dialogue.

        :param signing_msg: the message
        """
        self.context.logger.info(
            "received invalid signing message={}, unidentified dialogue.".format(
                signing_msg
            )
        )

    def _handle_error(
        self, signing_msg: SigningMessage, signing_dialogue: SigningDialogue
    ) -> None:
        """
        Handle an oef search message.

        :param signing_msg: the signing message
        :param signing_dialogue: the dialogue
        """
        self.context.logger.info(
            "transaction signing was not successful. Error_code={} in dialogue={}".format(
                signing_msg.error_code, signing_dialogue
            )
        )
        signing_msg_ = cast(
            Optional[SigningMessage], signing_dialogue.last_outgoing_message
        )
        if (
            signing_msg_ is not None
            and signing_msg_.performative
            == SigningMessage.Performative.SIGN_TRANSACTION
        ):
            fsm_behaviour = cast(
                PriceEstimationConsensusBehaviour, self.context.behaviours.main
            )
            current_state_name = cast(str, fsm_behaviour.current)
            registration_state = cast(
                RegistrationBehaviour, fsm_behaviour.get_state(current_state_name)
            )
            # send failure
            registration_state.try_send(None)

    def _handle_invalid(
        self, signing_msg: SigningMessage, signing_dialogue: SigningDialogue
    ) -> None:
        """
        Handle an oef search message.

        :param signing_msg: the signing message
        :param signing_dialogue: the dialogue
        """
        self.context.logger.warning(
            "cannot handle signing message of performative={} in dialogue={}.".format(
                signing_msg.performative, signing_dialogue
            )
        )
