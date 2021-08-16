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
from typing import cast

from aea.exceptions import enforce

from packages.valory.protocols.abci import AbciMessage
from packages.valory.protocols.abci.custom_types import Events
from packages.valory.skills.abstract_abci.handlers import ABCIHandler
from packages.valory.skills.abstract_round_abci.base_models import (
    ERROR_CODE,
    Transaction,
)
from packages.valory.skills.abstract_round_abci.dialogues import AbciDialogue


def exception_to_info_msg(exception: Exception) -> str:
    """Trnasform an exception to an info string message."""
    return f"{exception.__class__.__name__}: {str(exception)}"


class ABCIRoundHandler(ABCIHandler):
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
        # TOFIX: DON'T USE PICKLE! Write a Protobuf type for representing transactions
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

    def _log_exception(self, exception: Exception) -> None:
        """Log an exception."""
        self.context.logger.error(exception_to_info_msg(exception))
