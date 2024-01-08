# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2024 valory
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

"""Serialization module for ipfs protocol."""

# pylint: disable=too-many-statements,too-many-locals,no-member,too-few-public-methods,redefined-builtin
from typing import Any, Dict, cast

from aea.mail.base_pb2 import DialogueMessage  # type: ignore
from aea.mail.base_pb2 import Message as ProtobufMessage  # type: ignore
from aea.protocols.base import Message  # type: ignore
from aea.protocols.base import Serializer  # type: ignore

from packages.valory.protocols.ipfs import ipfs_pb2  # type: ignore
from packages.valory.protocols.ipfs.message import IpfsMessage  # type: ignore


class IpfsSerializer(Serializer):
    """Serialization for the 'ipfs' protocol."""

    @staticmethod
    def encode(msg: Message) -> bytes:
        """
        Encode a 'Ipfs' message into bytes.

        :param msg: the message object.
        :return: the bytes.
        """
        msg = cast(IpfsMessage, msg)
        message_pb = ProtobufMessage()
        dialogue_message_pb = DialogueMessage()
        ipfs_msg = ipfs_pb2.IpfsMessage()  # type: ignore

        dialogue_message_pb.message_id = msg.message_id
        dialogue_reference = msg.dialogue_reference
        dialogue_message_pb.dialogue_starter_reference = dialogue_reference[0]
        dialogue_message_pb.dialogue_responder_reference = dialogue_reference[1]
        dialogue_message_pb.target = msg.target

        performative_id = msg.performative
        if performative_id == IpfsMessage.Performative.STORE_FILES:
            performative = ipfs_pb2.IpfsMessage.Store_Files_Performative()  # type: ignore
            files = msg.files
            performative.files.update(files)
            if msg.is_set("timeout"):
                performative.timeout_is_set = True
                timeout = msg.timeout
                performative.timeout = timeout
            ipfs_msg.store_files.CopyFrom(performative)
        elif performative_id == IpfsMessage.Performative.IPFS_HASH:
            performative = ipfs_pb2.IpfsMessage.Ipfs_Hash_Performative()  # type: ignore
            ipfs_hash = msg.ipfs_hash
            performative.ipfs_hash = ipfs_hash
            ipfs_msg.ipfs_hash.CopyFrom(performative)
        elif performative_id == IpfsMessage.Performative.GET_FILES:
            performative = ipfs_pb2.IpfsMessage.Get_Files_Performative()  # type: ignore
            ipfs_hash = msg.ipfs_hash
            performative.ipfs_hash = ipfs_hash
            if msg.is_set("timeout"):
                performative.timeout_is_set = True
                timeout = msg.timeout
                performative.timeout = timeout
            ipfs_msg.get_files.CopyFrom(performative)
        elif performative_id == IpfsMessage.Performative.FILES:
            performative = ipfs_pb2.IpfsMessage.Files_Performative()  # type: ignore
            files = msg.files
            performative.files.update(files)
            ipfs_msg.files.CopyFrom(performative)
        elif performative_id == IpfsMessage.Performative.ERROR:
            performative = ipfs_pb2.IpfsMessage.Error_Performative()  # type: ignore
            reason = msg.reason
            performative.reason = reason
            ipfs_msg.error.CopyFrom(performative)
        else:
            raise ValueError("Performative not valid: {}".format(performative_id))

        dialogue_message_pb.content = ipfs_msg.SerializeToString()

        message_pb.dialogue_message.CopyFrom(dialogue_message_pb)
        message_bytes = message_pb.SerializeToString()
        return message_bytes

    @staticmethod
    def decode(obj: bytes) -> Message:
        """
        Decode bytes into a 'Ipfs' message.

        :param obj: the bytes object.
        :return: the 'Ipfs' message.
        """
        message_pb = ProtobufMessage()
        ipfs_pb = ipfs_pb2.IpfsMessage()  # type: ignore
        message_pb.ParseFromString(obj)
        message_id = message_pb.dialogue_message.message_id
        dialogue_reference = (
            message_pb.dialogue_message.dialogue_starter_reference,
            message_pb.dialogue_message.dialogue_responder_reference,
        )
        target = message_pb.dialogue_message.target

        ipfs_pb.ParseFromString(message_pb.dialogue_message.content)
        performative = ipfs_pb.WhichOneof("performative")
        performative_id = IpfsMessage.Performative(str(performative))
        performative_content = dict()  # type: Dict[str, Any]
        if performative_id == IpfsMessage.Performative.STORE_FILES:
            files = ipfs_pb.store_files.files
            files_dict = dict(files)
            performative_content["files"] = files_dict
            if ipfs_pb.store_files.timeout_is_set:
                timeout = ipfs_pb.store_files.timeout
                performative_content["timeout"] = timeout
        elif performative_id == IpfsMessage.Performative.IPFS_HASH:
            ipfs_hash = ipfs_pb.ipfs_hash.ipfs_hash
            performative_content["ipfs_hash"] = ipfs_hash
        elif performative_id == IpfsMessage.Performative.GET_FILES:
            ipfs_hash = ipfs_pb.get_files.ipfs_hash
            performative_content["ipfs_hash"] = ipfs_hash
            if ipfs_pb.get_files.timeout_is_set:
                timeout = ipfs_pb.get_files.timeout
                performative_content["timeout"] = timeout
        elif performative_id == IpfsMessage.Performative.FILES:
            files = ipfs_pb.files.files
            files_dict = dict(files)
            performative_content["files"] = files_dict
        elif performative_id == IpfsMessage.Performative.ERROR:
            reason = ipfs_pb.error.reason
            performative_content["reason"] = reason
        else:
            raise ValueError("Performative not valid: {}.".format(performative_id))

        return IpfsMessage(
            message_id=message_id,
            dialogue_reference=dialogue_reference,
            target=target,
            performative=performative,
            **performative_content
        )
