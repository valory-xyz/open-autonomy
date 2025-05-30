# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2025 valory
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

"""Serialization module for tendermint protocol."""

# pylint: disable=too-many-statements,too-many-locals,no-member,too-few-public-methods,redefined-builtin
from typing import Any, Dict, cast

from aea.mail.base_pb2 import DialogueMessage  # type: ignore
from aea.mail.base_pb2 import Message as ProtobufMessage  # type: ignore
from aea.protocols.base import Message  # type: ignore
from aea.protocols.base import Serializer  # type: ignore

from packages.valory.protocols.tendermint import tendermint_pb2  # type: ignore
from packages.valory.protocols.tendermint.custom_types import ErrorCode  # type: ignore
from packages.valory.protocols.tendermint.message import (  # type: ignore
    TendermintMessage,
)


class TendermintSerializer(Serializer):
    """Serialization for the 'tendermint' protocol."""

    @staticmethod
    def encode(msg: Message) -> bytes:
        """
        Encode a 'Tendermint' message into bytes.

        :param msg: the message object.
        :return: the bytes.
        """
        msg = cast(TendermintMessage, msg)
        message_pb = ProtobufMessage()
        dialogue_message_pb = DialogueMessage()
        tendermint_msg = tendermint_pb2.TendermintMessage()  # type: ignore

        dialogue_message_pb.message_id = msg.message_id
        dialogue_reference = msg.dialogue_reference
        dialogue_message_pb.dialogue_starter_reference = dialogue_reference[0]
        dialogue_message_pb.dialogue_responder_reference = dialogue_reference[1]
        dialogue_message_pb.target = msg.target

        performative_id = msg.performative
        if performative_id == TendermintMessage.Performative.GET_GENESIS_INFO:
            performative = tendermint_pb2.TendermintMessage.Get_Genesis_Info_Performative()  # type: ignore
            if msg.is_set("query"):
                performative.query_is_set = True
                query = msg.query
                performative.query = query
            tendermint_msg.get_genesis_info.CopyFrom(performative)
        elif performative_id == TendermintMessage.Performative.GET_RECOVERY_PARAMS:
            performative = tendermint_pb2.TendermintMessage.Get_Recovery_Params_Performative()  # type: ignore
            if msg.is_set("query"):
                performative.query_is_set = True
                query = msg.query
                performative.query = query
            tendermint_msg.get_recovery_params.CopyFrom(performative)
        elif performative_id == TendermintMessage.Performative.GENESIS_INFO:
            performative = tendermint_pb2.TendermintMessage.Genesis_Info_Performative()  # type: ignore
            info = msg.info
            performative.info = info
            tendermint_msg.genesis_info.CopyFrom(performative)
        elif performative_id == TendermintMessage.Performative.RECOVERY_PARAMS:
            performative = tendermint_pb2.TendermintMessage.Recovery_Params_Performative()  # type: ignore
            params = msg.params
            performative.params = params
            tendermint_msg.recovery_params.CopyFrom(performative)
        elif performative_id == TendermintMessage.Performative.ERROR:
            performative = tendermint_pb2.TendermintMessage.Error_Performative()  # type: ignore
            error_code = msg.error_code
            ErrorCode.encode(performative.error_code, error_code)
            error_msg = msg.error_msg
            performative.error_msg = error_msg
            error_data = msg.error_data
            performative.error_data.update(error_data)
            tendermint_msg.error.CopyFrom(performative)
        else:
            raise ValueError("Performative not valid: {}".format(performative_id))

        dialogue_message_pb.content = tendermint_msg.SerializeToString()

        message_pb.dialogue_message.CopyFrom(dialogue_message_pb)
        message_bytes = message_pb.SerializeToString()
        return message_bytes

    @staticmethod
    def decode(obj: bytes) -> Message:
        """
        Decode bytes into a 'Tendermint' message.

        :param obj: the bytes object.
        :return: the 'Tendermint' message.
        """
        message_pb = ProtobufMessage()
        tendermint_pb = tendermint_pb2.TendermintMessage()  # type: ignore
        message_pb.ParseFromString(obj)
        message_id = message_pb.dialogue_message.message_id
        dialogue_reference = (
            message_pb.dialogue_message.dialogue_starter_reference,
            message_pb.dialogue_message.dialogue_responder_reference,
        )
        target = message_pb.dialogue_message.target

        tendermint_pb.ParseFromString(message_pb.dialogue_message.content)
        performative = tendermint_pb.WhichOneof("performative")
        performative_id = TendermintMessage.Performative(str(performative))
        performative_content = dict()  # type: Dict[str, Any]
        if performative_id == TendermintMessage.Performative.GET_GENESIS_INFO:
            if tendermint_pb.get_genesis_info.query_is_set:
                query = tendermint_pb.get_genesis_info.query
                performative_content["query"] = query
        elif performative_id == TendermintMessage.Performative.GET_RECOVERY_PARAMS:
            if tendermint_pb.get_recovery_params.query_is_set:
                query = tendermint_pb.get_recovery_params.query
                performative_content["query"] = query
        elif performative_id == TendermintMessage.Performative.GENESIS_INFO:
            info = tendermint_pb.genesis_info.info
            performative_content["info"] = info
        elif performative_id == TendermintMessage.Performative.RECOVERY_PARAMS:
            params = tendermint_pb.recovery_params.params
            performative_content["params"] = params
        elif performative_id == TendermintMessage.Performative.ERROR:
            pb2_error_code = tendermint_pb.error.error_code
            error_code = ErrorCode.decode(pb2_error_code)
            performative_content["error_code"] = error_code
            error_msg = tendermint_pb.error.error_msg
            performative_content["error_msg"] = error_msg
            error_data = tendermint_pb.error.error_data
            error_data_dict = dict(error_data)
            performative_content["error_data"] = error_data_dict
        else:
            raise ValueError("Performative not valid: {}.".format(performative_id))

        return TendermintMessage(
            message_id=message_id,
            dialogue_reference=dialogue_reference,
            target=target,
            performative=performative,
            **performative_content
        )
