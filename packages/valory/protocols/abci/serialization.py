# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021 valory
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

"""Serialization module for abci protocol."""

# pylint: disable=too-many-statements,too-many-locals,no-member,too-few-public-methods,redefined-builtin
from typing import Any, Dict, cast

from aea.mail.base_pb2 import DialogueMessage
from aea.mail.base_pb2 import Message as ProtobufMessage
from aea.protocols.base import Message, Serializer

from packages.valory.protocols.abci import abci_pb2
from packages.valory.protocols.abci.custom_types import Timestamp
from packages.valory.protocols.abci.message import AbciMessage


class AbciSerializer(Serializer):
    """Serialization for the 'abci' protocol."""

    @staticmethod
    def encode(msg: Message) -> bytes:
        """
        Encode a 'Abci' message into bytes.

        :param msg: the message object.
        :return: the bytes.
        """
        msg = cast(AbciMessage, msg)
        message_pb = ProtobufMessage()
        dialogue_message_pb = DialogueMessage()
        abci_msg = abci_pb2.AbciMessage()

        dialogue_message_pb.message_id = msg.message_id
        dialogue_reference = msg.dialogue_reference
        dialogue_message_pb.dialogue_starter_reference = dialogue_reference[0]
        dialogue_message_pb.dialogue_responder_reference = dialogue_reference[1]
        dialogue_message_pb.target = msg.target

        performative_id = msg.performative
        if performative_id == AbciMessage.Performative.REQUEST_ECHO:
            performative = abci_pb2.AbciMessage.Request_Echo_Performative()  # type: ignore
            message = msg.message
            performative.message = message
            abci_msg.request_echo.CopyFrom(performative)
        elif performative_id == AbciMessage.Performative.REQUEST_FLUSH:
            performative = abci_pb2.AbciMessage.Request_Flush_Performative()  # type: ignore
            abci_msg.request_flush.CopyFrom(performative)
        elif performative_id == AbciMessage.Performative.REQUEST_INFO:
            performative = abci_pb2.AbciMessage.Request_Info_Performative()  # type: ignore
            version = msg.version
            performative.version = version
            block_version = msg.block_version
            performative.block_version = block_version
            p2p_version = msg.p2p_version
            performative.p2p_version = p2p_version
            abci_msg.request_info.CopyFrom(performative)
        elif performative_id == AbciMessage.Performative.REQUEST_INIT_CHAIN:
            performative = abci_pb2.AbciMessage.Request_Init_Chain_Performative()  # type: ignore
            time = msg.time
            Timestamp.encode(performative.time, time)
            chain_id = msg.chain_id
            performative.chain_id = chain_id
            consensus_params = msg.consensus_params
            performative.consensus_params.update(consensus_params)
            validators = msg.validators
            performative.validators.update(validators)
            app_state_bytes = msg.app_state_bytes
            performative.app_state_bytes = app_state_bytes
            initial_height = msg.initial_height
            performative.initial_height = initial_height
            abci_msg.request_init_chain.CopyFrom(performative)
        elif performative_id == AbciMessage.Performative.RESPONSE_EXCEPTION:
            performative = abci_pb2.AbciMessage.Response_Exception_Performative()  # type: ignore
            abci_msg.response_exception.CopyFrom(performative)
        elif performative_id == AbciMessage.Performative.RESPONSE_ECHO:
            performative = abci_pb2.AbciMessage.Response_Echo_Performative()  # type: ignore
            message = msg.message
            performative.message = message
            abci_msg.response_echo.CopyFrom(performative)
        elif performative_id == AbciMessage.Performative.RESPONSE_FLUSH:
            performative = abci_pb2.AbciMessage.Response_Flush_Performative()  # type: ignore
            abci_msg.response_flush.CopyFrom(performative)
        elif performative_id == AbciMessage.Performative.RESPONSE_INFO:
            performative = abci_pb2.AbciMessage.Response_Info_Performative()  # type: ignore
            data = msg.data
            performative.data = data
            version = msg.version
            performative.version = version
            app_version = msg.app_version
            performative.app_version = app_version
            last_block_height = msg.last_block_height
            performative.last_block_height = last_block_height
            last_block_app_hash = msg.last_block_app_hash
            performative.last_block_app_hash = last_block_app_hash
            abci_msg.response_info.CopyFrom(performative)
        elif performative_id == AbciMessage.Performative.RESPONSE_INIT_CHAIN:
            performative = abci_pb2.AbciMessage.Response_Init_Chain_Performative()  # type: ignore
            consensus_params = msg.consensus_params
            performative.consensus_params.update(consensus_params)
            validators = msg.validators
            performative.validators.update(validators)
            app_hash = msg.app_hash
            performative.app_hash = app_hash
            abci_msg.response_init_chain.CopyFrom(performative)
        else:
            raise ValueError("Performative not valid: {}".format(performative_id))

        dialogue_message_pb.content = abci_msg.SerializeToString()

        message_pb.dialogue_message.CopyFrom(dialogue_message_pb)
        message_bytes = message_pb.SerializeToString()
        return message_bytes

    @staticmethod
    def decode(obj: bytes) -> Message:
        """
        Decode bytes into a 'Abci' message.

        :param obj: the bytes object.
        :return: the 'Abci' message.
        """
        message_pb = ProtobufMessage()
        abci_pb = abci_pb2.AbciMessage()
        message_pb.ParseFromString(obj)
        message_id = message_pb.dialogue_message.message_id
        dialogue_reference = (
            message_pb.dialogue_message.dialogue_starter_reference,
            message_pb.dialogue_message.dialogue_responder_reference,
        )
        target = message_pb.dialogue_message.target

        abci_pb.ParseFromString(message_pb.dialogue_message.content)
        performative = abci_pb.WhichOneof("performative")
        performative_id = AbciMessage.Performative(str(performative))
        performative_content = dict()  # type: Dict[str, Any]
        if performative_id == AbciMessage.Performative.REQUEST_ECHO:
            message = abci_pb.request_echo.message
            performative_content["message"] = message
        elif performative_id == AbciMessage.Performative.REQUEST_FLUSH:
            pass
        elif performative_id == AbciMessage.Performative.REQUEST_INFO:
            version = abci_pb.request_info.version
            performative_content["version"] = version
            block_version = abci_pb.request_info.block_version
            performative_content["block_version"] = block_version
            p2p_version = abci_pb.request_info.p2p_version
            performative_content["p2p_version"] = p2p_version
        elif performative_id == AbciMessage.Performative.REQUEST_INIT_CHAIN:
            pb2_time = abci_pb.request_init_chain.time
            time = Timestamp.decode(pb2_time)
            performative_content["time"] = time
            chain_id = abci_pb.request_init_chain.chain_id
            performative_content["chain_id"] = chain_id
            consensus_params = abci_pb.request_init_chain.consensus_params
            consensus_params_dict = dict(consensus_params)
            performative_content["consensus_params"] = consensus_params_dict
            validators = abci_pb.request_init_chain.validators
            validators_dict = dict(validators)
            performative_content["validators"] = validators_dict
            app_state_bytes = abci_pb.request_init_chain.app_state_bytes
            performative_content["app_state_bytes"] = app_state_bytes
            initial_height = abci_pb.request_init_chain.initial_height
            performative_content["initial_height"] = initial_height
        elif performative_id == AbciMessage.Performative.RESPONSE_EXCEPTION:
            pass
        elif performative_id == AbciMessage.Performative.RESPONSE_ECHO:
            message = abci_pb.response_echo.message
            performative_content["message"] = message
        elif performative_id == AbciMessage.Performative.RESPONSE_FLUSH:
            pass
        elif performative_id == AbciMessage.Performative.RESPONSE_INFO:
            data = abci_pb.response_info.data
            performative_content["data"] = data
            version = abci_pb.response_info.version
            performative_content["version"] = version
            app_version = abci_pb.response_info.app_version
            performative_content["app_version"] = app_version
            last_block_height = abci_pb.response_info.last_block_height
            performative_content["last_block_height"] = last_block_height
            last_block_app_hash = abci_pb.response_info.last_block_app_hash
            performative_content["last_block_app_hash"] = last_block_app_hash
        elif performative_id == AbciMessage.Performative.RESPONSE_INIT_CHAIN:
            consensus_params = abci_pb.response_init_chain.consensus_params
            consensus_params_dict = dict(consensus_params)
            performative_content["consensus_params"] = consensus_params_dict
            validators = abci_pb.response_init_chain.validators
            validators_dict = dict(validators)
            performative_content["validators"] = validators_dict
            app_hash = abci_pb.response_init_chain.app_hash
            performative_content["app_hash"] = app_hash
        else:
            raise ValueError("Performative not valid: {}.".format(performative_id))

        return AbciMessage(
            message_id=message_id,
            dialogue_reference=dialogue_reference,
            target=target,
            performative=performative,
            **performative_content
        )
