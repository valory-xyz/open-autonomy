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

"""This module contains the handler for the 'abci' skill."""
from typing import Any, Optional, cast

from aea.exceptions import enforce

from packages.valory.protocols.abci import AbciMessage
from packages.valory.protocols.abci.custom_types import Events
from packages.valory.skills.abstract_abci.handlers import ABCIHandler
from packages.valory.skills.price_estimation_abci.dialogues import AbciDialogue
from packages.valory.skills.price_estimation_abci.models import (
    Block,
    Blockchain,
    Round,
    Transaction,
)


OK_CODE = 0
ERROR_CODE = 1


def exception_to_info_msg(exception: Exception) -> str:
    """Trnasform an exception to an info string message."""
    return f"{exception.__class__.__name__}: {str(exception)}"


class ABCIPriceEstimationHandler(ABCIHandler):
    """ABCI handler."""

    SUPPORTED_PROTOCOL = AbciMessage.protocol_id

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the handler."""
        super().__init__(*args, **kwargs)

        self.current_round = Round()
        self.blockchain = Blockchain()

        # set on 'begin_block', populated on 'deliver_tx', unset and saved on 'end_block'
        self.current_block: Optional[Block] = None

    def begin_block(  # pylint: disable=no-self-use
        self, message: AbciMessage, dialogue: AbciDialogue
    ) -> AbciMessage:
        """Handle the 'begin_block' request."""
        self.current_block = Block(message.header)
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
        except Exception as exception:  # pylint: disable=broad-except
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
            enforce(self.current_block is not None, "current_block is None")
            cast(Block, self.current_block).add_transaction(transaction)
            # return deliver_tx success
            return super().deliver_tx(message, dialogue)
        except Exception as exception:  # pylint: disable=broad-except
            return self._deliver_tx_failed(
                message, dialogue, exception_to_info_msg(exception)
            )

    def end_block(  # pylint: disable=no-self-use
        self, message: AbciMessage, dialogue: AbciDialogue
    ) -> AbciMessage:
        """Handle the 'end_block' request."""
        self.blockchain.add_block(cast(Block, self.current_block))
        return super().end_block(message, dialogue)

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
