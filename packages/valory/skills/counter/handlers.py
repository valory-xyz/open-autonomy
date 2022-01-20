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

"""This module contains the handler for the 'abci' skill."""
import struct
from typing import Any, cast

from packages.valory.protocols.abci import AbciMessage
from packages.valory.protocols.abci.custom_types import Events, ProofOps
from packages.valory.skills.abstract_abci.handlers import ABCIHandler
from packages.valory.skills.counter.dialogues import AbciDialogue


OK_CODE = 0
ERROR_CODE = 1


def encode_number(value: int) -> bytes:
    """Encode an integer (big-endian)."""
    return struct.pack(">I", value)


def decode_number(raw: bytes) -> int:
    """Decode an integer (little-endian)."""
    return int.from_bytes(raw, byteorder="big")


class ABCICounterHandler(ABCIHandler):
    """ABCI counter handler.

    Handles ABCI messages from a Tendermint node and implements the ABCI
    Counter app.
    """

    SUPPORTED_PROTOCOL = AbciMessage.protocol_id

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the handler."""
        super().__init__(*args, **kwargs)
        self.tx_count = 0
        self.last_block_height = 0

    def info(self, message: AbciMessage, dialogue: AbciDialogue) -> AbciMessage:
        """
        Handle a message of REQUEST_INFO performative.

        :param message: the ABCI request.
        :param dialogue: the ABCI dialogue.
        :return: the response.
        """
        reply = dialogue.reply(
            performative=AbciMessage.Performative.RESPONSE_INFO,
            target_message=message,
            info_data="",
            version=message.version,
            app_version=0,
            last_block_height=0,
            last_block_app_hash=b"",
        )
        return cast(AbciMessage, reply)

    def init_chain(self, message: AbciMessage, dialogue: AbciDialogue) -> AbciMessage:
        """
        Handle a message of REQUEST_INIT_CHAIN performative.

        :param message: the ABCI request.
        :param dialogue: the ABCI dialogue.
        :return: the response.
        """
        self.tx_count = 0
        self.last_block_height = 0
        return super().init_chain(message, dialogue)

    def query(self, message: AbciMessage, dialogue: AbciDialogue) -> AbciMessage:
        """
        Handle a message of REQUEST_QUERY performative.

        :param message: the ABCI request.
        :param dialogue: the ABCI dialogue.
        :return: the response.
        """
        value = encode_number(self.tx_count)
        log = f"value: {self.tx_count}"
        reply = dialogue.reply(
            performative=AbciMessage.Performative.RESPONSE_QUERY,
            code=OK_CODE,
            log=log,
            info="",
            index=0,
            key=b"",
            value=value,
            proof_ops=ProofOps([]),
            height=self.last_block_height,
            codespace="",
        )
        return cast(AbciMessage, reply)

    def check_tx(self, message: AbciMessage, dialogue: AbciDialogue) -> AbciMessage:
        """
        Handle a message of REQUEST_CHECK_TX performative.

        :param message: the ABCI request.
        :param dialogue: the ABCI dialogue.
        :return: the response.
        """
        value = decode_number(message.tx)
        if value == (self.tx_count + 1):
            code = OK_CODE
            log = "valid transaction."
            info = "OK: the next count is a unitary increment."
        else:
            code = ERROR_CODE
            log = "invalid transaction."
            info = "ERROR: the next count must be a unitary increment."

        reply = dialogue.reply(
            performative=AbciMessage.Performative.RESPONSE_CHECK_TX,
            code=code,
            data=b"",
            log=log,
            info=info,
            gas_wanted=0,
            gas_used=0,
            events=Events([]),
            codespace="",
        )
        return cast(AbciMessage, reply)

    def deliver_tx(self, message: AbciMessage, dialogue: AbciDialogue) -> AbciMessage:
        """
        Handle a message of REQUEST_DELIVER_TX performative.

        :param message: the ABCI request.
        :param dialogue: the ABCI dialogue.
        :return: the response.
        """
        self.tx_count += 1
        self.context.logger.info(f"The new count is: {self.tx_count}")
        reply = dialogue.reply(
            performative=AbciMessage.Performative.RESPONSE_DELIVER_TX,
            code=OK_CODE,
            data=b"",
            log="",
            info="",
            gas_wanted=0,
            gas_used=0,
            events=Events([]),
            codespace="",
        )
        return cast(AbciMessage, reply)

    def commit(self, message: AbciMessage, dialogue: AbciDialogue) -> AbciMessage:
        """
        Handle a message of REQUEST_COMMIT performative.

        :param message: the ABCI request.
        :param dialogue: the ABCI dialogue.
        :return: the response.
        """
        hash_ = struct.pack(">Q", self.tx_count)
        reply = dialogue.reply(
            performative=AbciMessage.Performative.RESPONSE_COMMIT,
            data=hash_,
            retain_height=0,
        )
        return cast(AbciMessage, reply)
