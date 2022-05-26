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

"""This module contains the handler for the 'abstract_round_abci' skill."""
from abc import ABC
from typing import Callable, FrozenSet, Optional, cast, List

from aea.configurations.data_types import PublicId
from aea.protocols.base import Message
from aea.protocols.dialogue.base import Dialogue, Dialogues
from aea.skills.base import Handler

from packages.open_aea.protocols.signing import SigningMessage
from packages.valory.protocols.abci import AbciMessage
from packages.valory.protocols.abci.custom_types import Events, ValidatorUpdates
from packages.valory.protocols.contract_api import ContractApiMessage
from packages.valory.protocols.http import HttpMessage
from packages.valory.protocols.ledger_api import LedgerApiMessage
from packages.valory.skills.abstract_abci.handlers import ABCIHandler
from packages.valory.skills.abstract_round_abci.base import (
    ABCIAppInternalError,
    AddBlockError,
    ERROR_CODE,
    LateArrivingTransaction,
    OK_CODE,
    SignatureNotValidError,
    Transaction,
    TransactionNotValidError,
    TransactionTypeNotRecognizedError,
)
from packages.valory.skills.abstract_round_abci.behaviours import AbstractRoundBehaviour
from packages.valory.skills.abstract_round_abci.dialogues import AbciDialogue
from packages.valory.skills.abstract_round_abci.models import Requests, SharedState


def exception_to_info_msg(exception: Exception) -> str:
    """Transform an exception to an info string message."""
    return f"{exception.__class__.__name__}: {str(exception)}"


class ABCIRoundHandler(ABCIHandler):
    """ABCI handler."""

    SUPPORTED_PROTOCOL = AbciMessage.protocol_id

    def info(  # pylint: disable=no-self-use,useless-super-delegation
        self, message: AbciMessage, dialogue: AbciDialogue
    ) -> AbciMessage:
        """Handle the 'info' request."""
        info_data = ""
        version = ""
        app_version = 0
        last_block_height = self.context.state.period.height
        last_block_app_hash = self.context.state.period_state.app_hash
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

    def init_chain(  # pylint: disable=no-self-use
        self, message: AbciMessage, dialogue: AbciDialogue
    ) -> AbciMessage:
        """
        Handle a message of REQUEST_INIT_CHAIN performative.

        :param message: the ABCI request.
        :param dialogue: the ABCI dialogue.
        :return: the response.
        """
        self.context.state.period.init_chain(message.initial_height)
        validators: List = []
        app_hash = b""
        reply = dialogue.reply(
            performative=AbciMessage.Performative.RESPONSE_INIT_CHAIN,
            target_message=message,
            validators=ValidatorUpdates(validators),
            app_hash=app_hash,
        )
        return cast(AbciMessage, reply)

    def begin_block(  # pylint: disable=no-self-use
        self, message: AbciMessage, dialogue: AbciDialogue
    ) -> AbciMessage:
        """Handle the 'begin_block' request."""
        cast(SharedState, self.context.state).period.begin_block(message.header)
        return super().begin_block(message, dialogue)

    def check_tx(  # pylint: disable=no-self-use
        self, message: AbciMessage, dialogue: AbciDialogue
    ) -> AbciMessage:
        """Handle the 'check_tx' request."""
        transaction_bytes = message.tx
        # check we can decode the transaction
        try:
            transaction = Transaction.decode(transaction_bytes)
            transaction.verify(self.context.default_ledger_id)
            cast(SharedState, self.context.state).period.check_is_finished()
        except (
            SignatureNotValidError,
            TransactionNotValidError,
            TransactionTypeNotRecognizedError,
        ) as exception:
            self._log_exception(exception)
            return self._check_tx_failed(
                message, dialogue, exception_to_info_msg(exception)
            )
        except LateArrivingTransaction as exception:  # pragma: nocover
            self.context.logger.debug(exception_to_info_msg(exception))
            return self._check_tx_failed(
                message, dialogue, exception_to_info_msg(exception)
            )

        # return check_tx success
        reply = dialogue.reply(
            performative=AbciMessage.Performative.RESPONSE_CHECK_TX,
            target_message=message,
            code=OK_CODE,
            data=b"",
            log="",
            info="check_tx succeeded",
            gas_wanted=0,
            gas_used=0,
            events=Events([]),
            codespace="",
        )
        return cast(AbciMessage, reply)

    def deliver_tx(  # pylint: disable=no-self-use
        self, message: AbciMessage, dialogue: AbciDialogue
    ) -> AbciMessage:
        """Handle the 'deliver_tx' request."""
        transaction_bytes = message.tx
        shared_state = cast(SharedState, self.context.state)
        try:
            transaction = Transaction.decode(transaction_bytes)
            transaction.verify(self.context.default_ledger_id)
            shared_state.period.check_is_finished()
            shared_state.period.deliver_tx(transaction)
        except (
            SignatureNotValidError,
            TransactionNotValidError,
            TransactionTypeNotRecognizedError,
        ) as exception:
            self._log_exception(exception)
            return self._deliver_tx_failed(
                message, dialogue, exception_to_info_msg(exception)
            )
        except LateArrivingTransaction as exception:  # pragma: nocover
            self.context.logger.debug(exception_to_info_msg(exception))
            return self._deliver_tx_failed(
                message, dialogue, exception_to_info_msg(exception)
            )

        # return deliver_tx success
        reply = dialogue.reply(
            performative=AbciMessage.Performative.RESPONSE_DELIVER_TX,
            target_message=message,
            code=OK_CODE,
            data=b"",
            log="",
            info="deliver_tx succeeded",
            gas_wanted=0,
            gas_used=0,
            events=Events([]),
            codespace="",
        )
        return cast(AbciMessage, reply)

    def end_block(  # pylint: disable=no-self-use
        self, message: AbciMessage, dialogue: AbciDialogue
    ) -> AbciMessage:
        """Handle the 'end_block' request."""
        cast(SharedState, self.context.state).period.end_block()
        return super().end_block(message, dialogue)

    def commit(  # pylint: disable=no-self-use
        self, message: AbciMessage, dialogue: AbciDialogue
    ) -> AbciMessage:
        """Handle the 'commit' request."""
        try:
            cast(SharedState, self.context.state).period.commit()
        except AddBlockError as exception:
            self._log_exception(exception)
            raise exception
        # return commit success
        reply = dialogue.reply(
            performative=AbciMessage.Performative.RESPONSE_COMMIT,
            target_message=message,
            data=b"",  # self.context.state.period_state.app_hash,
            retain_height=0,
        )
        return cast(AbciMessage, reply)

    @classmethod
    def _check_tx_failed(
        cls, message: AbciMessage, dialogue: AbciDialogue, info: str = ""
    ) -> AbciMessage:
        """Handle a failed check_tx request."""
        reply = dialogue.reply(
            performative=AbciMessage.Performative.RESPONSE_CHECK_TX,
            target_message=message,
            code=ERROR_CODE,
            data=b"",
            log="",
            info=info,
            gas_wanted=0,
            gas_used=0,
            events=Events([]),
            codespace="",
        )
        return cast(AbciMessage, reply)

    @classmethod
    def _deliver_tx_failed(
        cls, message: AbciMessage, dialogue: AbciDialogue, info: str = ""
    ) -> AbciMessage:
        """Handle a failed deliver_tx request."""
        reply = dialogue.reply(
            performative=AbciMessage.Performative.RESPONSE_DELIVER_TX,
            target_message=message,
            code=ERROR_CODE,
            data=b"",
            log="",
            info=info,
            gas_wanted=0,
            gas_used=0,
            events=Events([]),
            codespace="",
        )
        return cast(AbciMessage, reply)

    def _log_exception(self, exception: Exception) -> None:
        """Log an exception."""
        self.context.logger.error(exception_to_info_msg(exception))


class AbstractResponseHandler(Handler, ABC):
    """
    Abstract response Handler.

    This abstract handler works in tandem with the 'Requests' model.
    Whenever a message of 'response' type arrives, the handler
    tries to dispatch it to a pending request previously registered
    in 'Requests' by some other code in the same skill.

    The concrete classes must set the 'allowed_response_performatives'
    class attribute to the (frozen)set of performative the developer
    wants the handler to handle.
    """

    allowed_response_performatives: FrozenSet[Message.Performative]

    def setup(self) -> None:
        """Set up the handler."""

    def teardown(self) -> None:
        """Tear down the handler."""

    def handle(self, message: Message) -> None:
        """
        Handle the response message.

        Steps:
        1. Try to recover the 'dialogues' instance, for the protocol
           of this handler, from the skill context. The attribute name used to
           read the attribute is computed by '_get_dialogues_attribute_name()'
           method. If no dialogues instance is found, log a message and return.
        2. Try to recover the dialogue; if no dialogue is present, log a message
           and return.
        3. Check whether the performative is in the set of allowed performative;
           if not, log a message and return.
        4. Try to recover the callback of the request associated to the response
           from the 'Requests' model; if no callback is present, log a message
           and return.
        5. If the above check have passed, then call the callback with the
           received message.

        :param message: the message to handle.
        """
        protocol_dialogues = self._recover_protocol_dialogues()
        if protocol_dialogues is None:
            self._handle_missing_dialogues()
            return
        protocol_dialogues = cast(Dialogues, protocol_dialogues)

        protocol_dialogue = cast(Optional[Dialogue], protocol_dialogues.update(message))
        if protocol_dialogue is None:
            self._handle_unidentified_dialogue(message)
            return

        if message.performative not in self.allowed_response_performatives:
            self._handle_unallowed_performative(message)
            return

        request_nonce = protocol_dialogue.dialogue_label.dialogue_reference[0]
        ctx_requests = cast(Requests, self.context.requests)

        try:
            callback = cast(
                Callable,
                ctx_requests.request_id_to_callback.pop(request_nonce),
            )
        except KeyError as e:
            raise ABCIAppInternalError(
                f"No callback defined for request with nonce: {request_nonce}"
            ) from e

        self._log_message_handling(message)
        current_state = cast(
            AbstractRoundBehaviour, self.context.behaviours.main
        ).current_state
        callback(message, current_state)

    def _get_dialogues_attribute_name(self) -> str:
        """
        Get dialogues attribute name.

        By convention, the Dialogues model of the skill follows
        the template '{protocol_name}_dialogues'.

        Override this method accordingly if the name of hte Dialogues
        model is different.

        :return: the dialogues attribute name.
        """
        return cast(PublicId, self.SUPPORTED_PROTOCOL).name + "_dialogues"

    def _recover_protocol_dialogues(self) -> Optional[Dialogues]:
        """
        Recover protocol dialogues from supported protocol id.

        :return: the dialogues, or None if the dialogues object was not found.
        """
        attribute = self._get_dialogues_attribute_name()
        return getattr(self.context, attribute, None)

    def _handle_missing_dialogues(self) -> None:
        """Handle missing dialogues in context."""
        expected_attribute_name = self._get_dialogues_attribute_name()
        self.context.logger.info(
            "cannot find Dialogues object in skill context with attribute name: %s",
            expected_attribute_name,
        )

    def _handle_unidentified_dialogue(self, message: Message) -> None:
        """
        Handle an unidentified dialogue.

        :param message: the unidentified message to be handled
        """
        self.context.logger.info(
            "received invalid message: unidentified dialogue. message=%s", message
        )

    def _handle_unallowed_performative(self, message: Message) -> None:
        """
        Handle a message with an unallowed response performative.

        Log an error message saying that the handler did not expect requests
        but only responses.

        :param message: the message
        """
        self.context.logger.warning(
            "received invalid message: unallowed performative. message=%s.", message
        )

    def _log_message_handling(self, message: Message) -> None:
        """Log the handling of the message."""
        self.context.logger.debug(
            "calling registered callback with message=%s", message
        )


class HttpHandler(AbstractResponseHandler):
    """The HTTP response handler."""

    SUPPORTED_PROTOCOL: Optional[PublicId] = HttpMessage.protocol_id
    allowed_response_performatives = frozenset({HttpMessage.Performative.RESPONSE})


class SigningHandler(AbstractResponseHandler):
    """Implement the transaction handler."""

    SUPPORTED_PROTOCOL: Optional[PublicId] = SigningMessage.protocol_id
    allowed_response_performatives = frozenset(
        {
            SigningMessage.Performative.SIGNED_MESSAGE,
            SigningMessage.Performative.SIGNED_TRANSACTION,
            SigningMessage.Performative.ERROR,
        }
    )


class LedgerApiHandler(AbstractResponseHandler):
    """Implement the ledger handler."""

    SUPPORTED_PROTOCOL: Optional[PublicId] = LedgerApiMessage.protocol_id
    allowed_response_performatives = frozenset(
        {
            LedgerApiMessage.Performative.BALANCE,
            LedgerApiMessage.Performative.RAW_TRANSACTION,
            LedgerApiMessage.Performative.TRANSACTION_DIGEST,
            LedgerApiMessage.Performative.TRANSACTION_RECEIPT,
            LedgerApiMessage.Performative.ERROR,
            LedgerApiMessage.Performative.STATE,
        }
    )


class ContractApiHandler(AbstractResponseHandler):
    """Implement the contract api handler."""

    SUPPORTED_PROTOCOL: Optional[PublicId] = ContractApiMessage.protocol_id
    allowed_response_performatives = frozenset(
        {
            ContractApiMessage.Performative.RAW_TRANSACTION,
            ContractApiMessage.Performative.RAW_MESSAGE,
            ContractApiMessage.Performative.ERROR,
            ContractApiMessage.Performative.STATE,
        }
    )
