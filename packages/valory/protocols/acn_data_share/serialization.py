# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2023 valory
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

"""Serialization module for acn_data_share protocol."""

# pylint: disable=too-many-statements,too-many-locals,no-member,too-few-public-methods,redefined-builtin
from typing import Any, Dict, cast

from aea.mail.base_pb2 import DialogueMessage  # type: ignore
from aea.mail.base_pb2 import Message as ProtobufMessage  # type: ignore
from aea.protocols.base import Message  # type: ignore
from aea.protocols.base import Serializer  # type: ignore

from packages.valory.protocols.acn_data_share import acn_data_share_pb2  # type: ignore
from packages.valory.protocols.acn_data_share.message import (  # type: ignore
    AcnDataShareMessage,
)


class AcnDataShareSerializer(Serializer):
    """Serialization for the 'acn_data_share' protocol."""

    @staticmethod
    def encode(msg: Message) -> bytes:
        """
        Encode a 'AcnDataShare' message into bytes.

        :param msg: the message object.
        :return: the bytes.
        """
        msg = cast(AcnDataShareMessage, msg)
        message_pb = ProtobufMessage()
        dialogue_message_pb = DialogueMessage()
        acn_data_share_msg = acn_data_share_pb2.AcnDataShareMessage()  # type: ignore

        dialogue_message_pb.message_id = msg.message_id
        dialogue_reference = msg.dialogue_reference
        dialogue_message_pb.dialogue_starter_reference = dialogue_reference[0]
        dialogue_message_pb.dialogue_responder_reference = dialogue_reference[1]
        dialogue_message_pb.target = msg.target

        performative_id = msg.performative
        if performative_id == AcnDataShareMessage.Performative.DATA:
            performative = acn_data_share_pb2.AcnDataShareMessage.Data_Performative()  # type: ignore
            request_id = msg.request_id
            performative.request_id = request_id
            content = msg.content
            performative.content = content
            acn_data_share_msg.data.CopyFrom(performative)
        else:
            raise ValueError("Performative not valid: {}".format(performative_id))

        dialogue_message_pb.content = acn_data_share_msg.SerializeToString()

        message_pb.dialogue_message.CopyFrom(dialogue_message_pb)
        message_bytes = message_pb.SerializeToString()
        return message_bytes

    @staticmethod
    def decode(obj: bytes) -> Message:
        """
        Decode bytes into a 'AcnDataShare' message.

        :param obj: the bytes object.
        :return: the 'AcnDataShare' message.
        """
        message_pb = ProtobufMessage()
        acn_data_share_pb = acn_data_share_pb2.AcnDataShareMessage()  # type: ignore
        message_pb.ParseFromString(obj)
        message_id = message_pb.dialogue_message.message_id
        dialogue_reference = (
            message_pb.dialogue_message.dialogue_starter_reference,
            message_pb.dialogue_message.dialogue_responder_reference,
        )
        target = message_pb.dialogue_message.target

        acn_data_share_pb.ParseFromString(message_pb.dialogue_message.content)
        performative = acn_data_share_pb.WhichOneof("performative")
        performative_id = AcnDataShareMessage.Performative(str(performative))
        performative_content = dict()  # type: Dict[str, Any]
        if performative_id == AcnDataShareMessage.Performative.DATA:
            request_id = acn_data_share_pb.data.request_id
            performative_content["request_id"] = request_id
            content = acn_data_share_pb.data.content
            performative_content["content"] = content
        else:
            raise ValueError("Performative not valid: {}.".format(performative_id))

        return AcnDataShareMessage(
            message_id=message_id,
            dialogue_reference=dialogue_reference,
            target=target,
            performative=performative,
            **performative_content
        )
