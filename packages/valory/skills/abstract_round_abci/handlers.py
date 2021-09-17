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

"""This module contains the handler for the 'abstract_round_abci' skill."""
from abc import ABC
from typing import Optional, cast

from aea.configurations.data_types import PublicId
from aea.crypto.ledger_apis import LedgerApis
from aea.exceptions import enforce
from aea.protocols.base import Message
from aea.protocols.dialogue.base import Dialogue
from aea.skills.base import Handler, SkillContext

from packages.fetchai.protocols.contract_api import ContractApiMessage
from packages.fetchai.protocols.http import HttpMessage
from packages.fetchai.protocols.ledger_api import LedgerApiMessage
from packages.fetchai.protocols.signing import SigningMessage
from packages.fetchai.protocols.signing.dialogues import SigningDialogue
from packages.valory.protocols.abci import AbciMessage
from packages.valory.protocols.abci.custom_types import Events
from packages.valory.skills.abstract_abci.handlers import ABCIHandler
from packages.valory.skills.abstract_round_abci.base_models import (
    ERROR_CODE,
    Transaction,
)
from packages.valory.skills.abstract_round_abci.dialogues import (
    AbciDialogue,
    ContractApiDialogue,
    ContractApiDialogues,
    HttpDialogue,
    HttpDialogues,
    LedgerApiDialogue,
    LedgerApiDialogues,
    SigningDialogues,
)


def exception_to_info_msg(exception: Exception) -> str:
    """Trnasform an exception to an info string message."""
    return f"{exception.__class__.__name__}: {str(exception)}"


class HandlerUtils(ABC):  # pylint: disable=too-few-public-methods
    """MixIn class with handler utils."""

    context: SkillContext

    def _handle_no_callback(self, _message: Message, dialogue: Dialogue) -> None:
        """
        Handle no callback found.

        :param _message: the message to be handled
        :param dialogue: the http dialogue
        """
        request_nonce = dialogue.dialogue_label.dialogue_reference[0]
        self.context.logger.warning(
            f"callback not specified for request with nonce {request_nonce}"
        )


class ABCIRoundHandler(HandlerUtils, ABCIHandler):
    """ABCI handler."""

    SUPPORTED_PROTOCOL = AbciMessage.protocol_id

    def info(  # pylint: disable=no-self-use,useless-super-delegation
        self, message: AbciMessage, dialogue: AbciDialogue
    ) -> AbciMessage:
        """Handle the 'info' request."""
        return super().info(message, dialogue)

    def begin_block(  # pylint: disable=no-self-use
        self, message: AbciMessage, dialogue: AbciDialogue
    ) -> AbciMessage:
        """Handle the 'begin_block' request."""
        self.context.state.period.begin_block(message.header)
        return super().begin_block(message, dialogue)

    def check_tx(  # pylint: disable=no-self-use
        self, message: AbciMessage, dialogue: AbciDialogue
    ) -> AbciMessage:
        """Handle the 'check_tx' request."""
        transaction_bytes = message.tx
        # check we can decode the transaction
        try:
            transaction = Transaction.decode(transaction_bytes)
            transaction.verify()
            self.context.state.period.check_is_finished()
        except Exception as exception:  # pylint: disable=broad-except
            self._log_exception(exception)
            return self._check_tx_failed(
                message, dialogue, exception_to_info_msg(exception)
            )

        # return check_tx success
        return super().check_tx(message, dialogue)

    def deliver_tx(  # pylint: disable=no-self-use
        self, message: AbciMessage, dialogue: AbciDialogue
    ) -> AbciMessage:
        """Handle the 'deliver_tx' request."""
        transaction_bytes = message.tx
        try:
            transaction = Transaction.decode(transaction_bytes)
            transaction.verify()
            self.context.state.period.check_is_finished()
            is_valid = self.context.state.period.deliver_tx(transaction)
            enforce(is_valid, "transaction is not valid")
        except Exception as exception:  # pylint: disable=broad-except
            return self._deliver_tx_failed(
                message, dialogue, exception_to_info_msg(exception)
            )
        # return deliver_tx success
        return super().deliver_tx(message, dialogue)

    def end_block(  # pylint: disable=no-self-use
        self, message: AbciMessage, dialogue: AbciDialogue
    ) -> AbciMessage:
        """Handle the 'end_block' request."""
        self.context.state.period.end_block()
        return super().end_block(message, dialogue)

    def commit(  # pylint: disable=no-self-use
        self, message: AbciMessage, dialogue: AbciDialogue
    ) -> AbciMessage:
        """Handle the 'commit' request."""
        self.context.state.period.commit()
        return super().commit(message, dialogue)

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


class HttpHandler(HandlerUtils, Handler):
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

        # http messages can also come from external! so this won't work
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


class SigningHandler(HandlerUtils, Handler):
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

        request_nonce = signing_dialogue.dialogue_label.dialogue_reference[0]
        callback = self.context.requests.request_id_to_callback.pop(request_nonce, None)
        if callback is None:
            self._handle_no_callback(message, signing_dialogue)
            return

        # handle message
        if signing_msg.performative is SigningMessage.Performative.SIGNED_MESSAGE:
            self._handle_signed_message(signing_msg, signing_dialogue)
        elif signing_msg.performative is SigningMessage.Performative.SIGNED_TRANSACTION:
            self._handle_signed_transaction(signing_msg, signing_dialogue)
        elif signing_msg.performative is SigningMessage.Performative.ERROR:
            self._handle_error(signing_msg, signing_dialogue)
        else:
            self._handle_invalid(signing_msg, signing_dialogue)
            return
        callback(signing_msg)

    def _handle_signed_message(
        self, _signing_msg: SigningMessage, signing_dialogue: SigningDialogue
    ) -> None:
        self.context.logger.info("Message signing was successful.")
        self.context.logger.debug(f"signing success for {signing_dialogue}")

    def _handle_signed_transaction(
        self, _signing_msg: SigningMessage, signing_dialogue: SigningDialogue
    ) -> None:
        self.context.logger.info("Transaction signing was successful.")
        self.context.logger.debug(f"signing success for {signing_dialogue}")

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
        Handle a signing error message.

        :param signing_msg: the signing message
        :param signing_dialogue: the dialogue
        """
        self.context.logger.info(
            "transaction signing was not successful. Error_code={} in dialogue={}".format(
                signing_msg.error_code, signing_dialogue
            )
        )

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


class LedgerApiHandler(HandlerUtils, Handler):
    """Implement the ledger handler."""

    SUPPORTED_PROTOCOL = LedgerApiMessage.protocol_id  # type: Optional[PublicId]

    def setup(self) -> None:
        """Implement the setup for the handler."""

    def handle(self, message: Message) -> None:
        """
        Implement the reaction to a message.

        :param message: the message
        :return: None
        """
        ledger_api_msg = cast(LedgerApiMessage, message)

        # recover dialogue
        ledger_api_dialogues = cast(
            LedgerApiDialogues, self.context.ledger_api_dialogues
        )
        ledger_api_dialogue = cast(
            Optional[LedgerApiDialogue], ledger_api_dialogues.update(ledger_api_msg)
        )
        if ledger_api_dialogue is None:
            self._handle_unidentified_dialogue(ledger_api_msg)
            return

        request_nonce = ledger_api_dialogue.dialogue_label.dialogue_reference[0]
        callback = self.context.requests.request_id_to_callback.pop(request_nonce, None)
        if callback is None:
            self._handle_no_callback(message, ledger_api_dialogue)
            return

        # handle message
        if ledger_api_msg.performative is LedgerApiMessage.Performative.BALANCE:
            self._handle_balance(ledger_api_msg)
        elif (
            ledger_api_msg.performative is LedgerApiMessage.Performative.RAW_TRANSACTION
        ):
            self._handle_raw_transaction(ledger_api_msg, ledger_api_dialogue)
        elif (
            ledger_api_msg.performative
            == LedgerApiMessage.Performative.TRANSACTION_DIGEST
        ):
            self._handle_transaction_digest(ledger_api_msg, ledger_api_dialogue)
        elif (
            ledger_api_msg.performative
            == LedgerApiMessage.Performative.TRANSACTION_RECEIPT
        ):
            self._handle_transaction_receipt(ledger_api_msg, ledger_api_dialogue)
        elif ledger_api_msg.performative == LedgerApiMessage.Performative.ERROR:
            self._handle_error(ledger_api_msg, ledger_api_dialogue)
        else:
            self._handle_invalid(ledger_api_msg, ledger_api_dialogue)
            return
        callback(ledger_api_msg)

    def teardown(self) -> None:
        """Implement the handler teardown."""

    def _handle_unidentified_dialogue(self, ledger_api_msg: LedgerApiMessage) -> None:
        """
        Handle an unidentified dialogue.

        :param ledger_api_msg: the message
        """
        self.context.logger.info(
            "received invalid ledger_api message={}, unidentified dialogue.".format(
                ledger_api_msg
            )
        )

    def _handle_balance(self, ledger_api_msg: LedgerApiMessage) -> None:
        """
        Handle a message of balance performative.

        :param ledger_api_msg: the ledger api message
        """
        self.context.logger.info(
            "starting balance on {} ledger={}.".format(
                ledger_api_msg.ledger_id,
                ledger_api_msg.balance,
            )
        )

    def _handle_raw_transaction(
        self, ledger_api_msg: LedgerApiMessage, _ledger_api_dialogue: LedgerApiDialogue
    ) -> None:
        """
        Handle a message of raw_transaction performative.

        :param ledger_api_msg: the ledger api message
        :param _ledger_api_dialogue: the ledger api dialogue
        """
        self.context.logger.info("received raw transaction={}".format(ledger_api_msg))

    def _handle_transaction_digest(
        self, ledger_api_msg: LedgerApiMessage, _ledger_api_dialogue: LedgerApiDialogue
    ) -> None:
        """
        Handle a message of transaction_digest performative.

        :param ledger_api_msg: the ledger api message
        :param _ledger_api_dialogue: the ledger api dialogue
        """
        self.context.logger.info(
            "transaction was successfully submitted. Transaction digest={}".format(
                ledger_api_msg.transaction_digest
            )
        )

    def _handle_transaction_receipt(
        self, ledger_api_msg: LedgerApiMessage, ledger_api_dialogue: LedgerApiDialogue
    ) -> None:
        """
        Handle a message of transaction receipt performative.

        :param ledger_api_msg: the ledger api message
        :param ledger_api_dialogue: the ledger api dialogue
        """
        is_settled = LedgerApis.is_transaction_settled(
            ledger_api_msg.terms.ledger_id, ledger_api_msg.transaction_receipt.receipt
        )
        if is_settled:
            ledger_api_msg_ = cast(
                Optional[LedgerApiMessage], ledger_api_dialogue.last_outgoing_message
            )
            if ledger_api_msg_ is None:
                raise ValueError(  # pragma: nocover
                    "Could not retrieve last ledger_api message"
                )
            self.context.logger.info("transaction confirmed.")
        else:
            self.context.logger.info(
                "transaction_receipt={} not settled or not valid, aborting".format(
                    ledger_api_msg.transaction_receipt
                )
            )

    def _handle_error(
        self, ledger_api_msg: LedgerApiMessage, ledger_api_dialogue: LedgerApiDialogue
    ) -> None:
        """
        Handle a message of error performative.

        :param ledger_api_msg: the ledger api message
        :param ledger_api_dialogue: the ledger api dialogue
        """
        self.context.logger.info(
            "received ledger_api error message={} in dialogue={}.".format(
                ledger_api_msg, ledger_api_dialogue
            )
        )

    def _handle_invalid(
        self, ledger_api_msg: LedgerApiMessage, ledger_api_dialogue: LedgerApiDialogue
    ) -> None:
        """
        Handle a message of invalid performative.

        :param ledger_api_msg: the ledger api message
        :param ledger_api_dialogue: the ledger api dialogue
        """
        self.context.logger.warning(
            "cannot handle ledger_api message of performative={} in dialogue={}.".format(
                ledger_api_msg.performative,
                ledger_api_dialogue,
            )
        )


class ContractApiHandler(HandlerUtils, Handler):
    """Implement the contract api handler."""

    SUPPORTED_PROTOCOL = ContractApiMessage.protocol_id  # type: Optional[PublicId]

    def setup(self) -> None:
        """Implement the setup for the handler."""

    def handle(self, message: Message) -> None:
        """
        Implement the reaction to a message.

        :param message: the message
        :return: None
        """
        contract_api_msg = cast(ContractApiMessage, message)

        # recover dialogue
        contract_api_dialogues = cast(
            ContractApiDialogues, self.context.contract_api_dialogues
        )
        contract_api_dialogue = cast(
            Optional[ContractApiDialogue],
            contract_api_dialogues.update(contract_api_msg),
        )
        if contract_api_dialogue is None:
            self._handle_unidentified_dialogue(contract_api_msg)
            return

        request_nonce = contract_api_dialogue.dialogue_label.dialogue_reference[0]
        callback = self.context.requests.request_id_to_callback.pop(request_nonce, None)
        if callback is None:
            self._handle_no_callback(message, contract_api_dialogue)
            return

        # handle message
        if (
            contract_api_msg.performative
            is ContractApiMessage.Performative.RAW_TRANSACTION
        ):
            self._handle_raw_transaction(contract_api_msg, contract_api_dialogue)
        elif contract_api_msg.performative == ContractApiMessage.Performative.ERROR:
            self._handle_error(contract_api_msg, contract_api_dialogue)
        else:
            self._handle_invalid(contract_api_msg, contract_api_dialogue)
            return
        callback(contract_api_msg)

    def teardown(self) -> None:
        """Implement the handler teardown."""

    def _handle_unidentified_dialogue(
        self, contract_api_msg: ContractApiMessage
    ) -> None:
        """
        Handle an unidentified dialogue.

        :param contract_api_msg: the message
        """
        self.context.logger.info(
            "received invalid contract_api message=%s, unidentified dialogue.",
            contract_api_msg,
        )

    def _handle_raw_transaction(
        self,
        contract_api_msg: ContractApiMessage,
        contract_api_dialogue: ContractApiDialogue,
    ) -> None:
        """
        Handle a message of raw_transaction performative.

        :param contract_api_msg: the contract api message
        :param contract_api_dialogue: the contract api dialogue
        """
        self.context.logger.info(
            "Received raw transaction=%s",
            contract_api_msg,
        )
        self.context.logger.debug(
            "received raw transaction=%s in dialogue=%s.",
            contract_api_msg,
            contract_api_dialogue,
        )

    def _handle_error(
        self,
        contract_api_msg: ContractApiMessage,
        contract_api_dialogue: ContractApiDialogue,
    ) -> None:
        """
        Handle a message of error performative.

        :param contract_api_msg: the ledger api message
        :param contract_api_dialogue: the ledger api dialogue
        """
        self.context.logger.info(
            "received contract_api error message=%s in dialogue=%s.",
            contract_api_msg,
            contract_api_dialogue,
        )

    def _handle_invalid(
        self,
        contract_api_msg: ContractApiMessage,
        contract_api_dialogue: ContractApiDialogue,
    ) -> None:
        """
        Handle a message of invalid performative.

        :param contract_api_msg: the ledger api message
        :param contract_api_dialogue: the ledger api dialogue
        """
        self.context.logger.warning(
            "cannot handle contract_api message of performative=%s in dialogue=%s.",
            contract_api_msg.performative,
            contract_api_dialogue,
        )
