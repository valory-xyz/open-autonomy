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

"""Serialization module for abci protocol."""

# pylint: disable=too-many-statements,too-many-locals,no-member,too-few-public-methods,redefined-builtin
from typing import Any, Dict, cast

from aea.mail.base_pb2 import DialogueMessage
from aea.mail.base_pb2 import Message as ProtobufMessage
from aea.protocols.base import Message, Serializer

from packages.valory.protocols.abci import abci_pb2
from packages.valory.protocols.abci.custom_types import (
    CheckTxType,
    ConsensusParams,
    Events,
    Evidences,
    Header,
    LastCommitInfo,
    ProofOps,
    Result,
    SnapShots,
    Snapshot,
    Timestamp,
    ValidatorUpdates,
)
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
        elif performative_id == AbciMessage.Performative.REQUEST_SET_OPTION:
            performative = abci_pb2.AbciMessage.Request_Set_Option_Performative()  # type: ignore
            option_key = msg.option_key
            performative.option_key = option_key
            option_value = msg.option_value
            performative.option_value = option_value
            abci_msg.request_set_option.CopyFrom(performative)
        elif performative_id == AbciMessage.Performative.REQUEST_INIT_CHAIN:
            performative = abci_pb2.AbciMessage.Request_Init_Chain_Performative()  # type: ignore
            time = msg.time
            Timestamp.encode(performative.time, time)
            chain_id = msg.chain_id
            performative.chain_id = chain_id
            if msg.is_set("consensus_params"):
                performative.consensus_params_is_set = True
                consensus_params = msg.consensus_params
                ConsensusParams.encode(performative.consensus_params, consensus_params)
            validators = msg.validators
            ValidatorUpdates.encode(performative.validators, validators)
            app_state_bytes = msg.app_state_bytes
            performative.app_state_bytes = app_state_bytes
            initial_height = msg.initial_height
            performative.initial_height = initial_height
            abci_msg.request_init_chain.CopyFrom(performative)
        elif performative_id == AbciMessage.Performative.REQUEST_QUERY:
            performative = abci_pb2.AbciMessage.Request_Query_Performative()  # type: ignore
            query_data = msg.query_data
            performative.query_data = query_data
            path = msg.path
            performative.path = path
            height = msg.height
            performative.height = height
            prove = msg.prove
            performative.prove = prove
            abci_msg.request_query.CopyFrom(performative)
        elif performative_id == AbciMessage.Performative.REQUEST_BEGIN_BLOCK:
            performative = abci_pb2.AbciMessage.Request_Begin_Block_Performative()  # type: ignore
            hash = msg.hash
            performative.hash = hash
            header = msg.header
            Header.encode(performative.header, header)
            last_commit_info = msg.last_commit_info
            LastCommitInfo.encode(performative.last_commit_info, last_commit_info)
            byzantine_validators = msg.byzantine_validators
            Evidences.encode(performative.byzantine_validators, byzantine_validators)
            abci_msg.request_begin_block.CopyFrom(performative)
        elif performative_id == AbciMessage.Performative.REQUEST_CHECK_TX:
            performative = abci_pb2.AbciMessage.Request_Check_Tx_Performative()  # type: ignore
            tx = msg.tx
            performative.tx = tx
            type = msg.type
            CheckTxType.encode(performative.type, type)
            abci_msg.request_check_tx.CopyFrom(performative)
        elif performative_id == AbciMessage.Performative.REQUEST_DELIVER_TX:
            performative = abci_pb2.AbciMessage.Request_Deliver_Tx_Performative()  # type: ignore
            tx = msg.tx
            performative.tx = tx
            abci_msg.request_deliver_tx.CopyFrom(performative)
        elif performative_id == AbciMessage.Performative.REQUEST_END_BLOCK:
            performative = abci_pb2.AbciMessage.Request_End_Block_Performative()  # type: ignore
            height = msg.height
            performative.height = height
            abci_msg.request_end_block.CopyFrom(performative)
        elif performative_id == AbciMessage.Performative.REQUEST_COMMIT:
            performative = abci_pb2.AbciMessage.Request_Commit_Performative()  # type: ignore
            abci_msg.request_commit.CopyFrom(performative)
        elif performative_id == AbciMessage.Performative.REQUEST_LIST_SNAPSHOTS:
            performative = abci_pb2.AbciMessage.Request_List_Snapshots_Performative()  # type: ignore
            abci_msg.request_list_snapshots.CopyFrom(performative)
        elif performative_id == AbciMessage.Performative.REQUEST_OFFER_SNAPSHOT:
            performative = abci_pb2.AbciMessage.Request_Offer_Snapshot_Performative()  # type: ignore
            snapshot = msg.snapshot
            Snapshot.encode(performative.snapshot, snapshot)
            app_hash = msg.app_hash
            performative.app_hash = app_hash
            abci_msg.request_offer_snapshot.CopyFrom(performative)
        elif performative_id == AbciMessage.Performative.REQUEST_LOAD_SNAPSHOT_CHUNK:
            performative = abci_pb2.AbciMessage.Request_Load_Snapshot_Chunk_Performative()  # type: ignore
            height = msg.height
            performative.height = height
            format = msg.format
            performative.format = format
            chunk_index = msg.chunk_index
            performative.chunk_index = chunk_index
            abci_msg.request_load_snapshot_chunk.CopyFrom(performative)
        elif performative_id == AbciMessage.Performative.REQUEST_APPLY_SNAPSHOT_CHUNK:
            performative = abci_pb2.AbciMessage.Request_Apply_Snapshot_Chunk_Performative()  # type: ignore
            index = msg.index
            performative.index = index
            chunk = msg.chunk
            performative.chunk = chunk
            chunk_sender = msg.chunk_sender
            performative.chunk_sender = chunk_sender
            abci_msg.request_apply_snapshot_chunk.CopyFrom(performative)
        elif performative_id == AbciMessage.Performative.RESPONSE_EXCEPTION:
            performative = abci_pb2.AbciMessage.Response_Exception_Performative()  # type: ignore
            error = msg.error
            performative.error = error
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
            info_data = msg.info_data
            performative.info_data = info_data
            version = msg.version
            performative.version = version
            app_version = msg.app_version
            performative.app_version = app_version
            last_block_height = msg.last_block_height
            performative.last_block_height = last_block_height
            last_block_app_hash = msg.last_block_app_hash
            performative.last_block_app_hash = last_block_app_hash
            abci_msg.response_info.CopyFrom(performative)
        elif performative_id == AbciMessage.Performative.RESPONSE_SET_OPTION:
            performative = abci_pb2.AbciMessage.Response_Set_Option_Performative()  # type: ignore
            code = msg.code
            performative.code = code
            log = msg.log
            performative.log = log
            info = msg.info
            performative.info = info
            abci_msg.response_set_option.CopyFrom(performative)
        elif performative_id == AbciMessage.Performative.RESPONSE_INIT_CHAIN:
            performative = abci_pb2.AbciMessage.Response_Init_Chain_Performative()  # type: ignore
            if msg.is_set("consensus_params"):
                performative.consensus_params_is_set = True
                consensus_params = msg.consensus_params
                ConsensusParams.encode(performative.consensus_params, consensus_params)
            validators = msg.validators
            ValidatorUpdates.encode(performative.validators, validators)
            app_hash = msg.app_hash
            performative.app_hash = app_hash
            abci_msg.response_init_chain.CopyFrom(performative)
        elif performative_id == AbciMessage.Performative.RESPONSE_QUERY:
            performative = abci_pb2.AbciMessage.Response_Query_Performative()  # type: ignore
            code = msg.code
            performative.code = code
            log = msg.log
            performative.log = log
            info = msg.info
            performative.info = info
            index = msg.index
            performative.index = index
            key = msg.key
            performative.key = key
            value = msg.value
            performative.value = value
            proof_ops = msg.proof_ops
            ProofOps.encode(performative.proof_ops, proof_ops)
            height = msg.height
            performative.height = height
            codespace = msg.codespace
            performative.codespace = codespace
            abci_msg.response_query.CopyFrom(performative)
        elif performative_id == AbciMessage.Performative.RESPONSE_BEGIN_BLOCK:
            performative = abci_pb2.AbciMessage.Response_Begin_Block_Performative()  # type: ignore
            events = msg.events
            Events.encode(performative.events, events)
            abci_msg.response_begin_block.CopyFrom(performative)
        elif performative_id == AbciMessage.Performative.RESPONSE_CHECK_TX:
            performative = abci_pb2.AbciMessage.Response_Check_Tx_Performative()  # type: ignore
            code = msg.code
            performative.code = code
            data = msg.data
            performative.data = data
            log = msg.log
            performative.log = log
            info = msg.info
            performative.info = info
            gas_wanted = msg.gas_wanted
            performative.gas_wanted = gas_wanted
            gas_used = msg.gas_used
            performative.gas_used = gas_used
            events = msg.events
            Events.encode(performative.events, events)
            codespace = msg.codespace
            performative.codespace = codespace
            abci_msg.response_check_tx.CopyFrom(performative)
        elif performative_id == AbciMessage.Performative.RESPONSE_DELIVER_TX:
            performative = abci_pb2.AbciMessage.Response_Deliver_Tx_Performative()  # type: ignore
            code = msg.code
            performative.code = code
            data = msg.data
            performative.data = data
            log = msg.log
            performative.log = log
            info = msg.info
            performative.info = info
            gas_wanted = msg.gas_wanted
            performative.gas_wanted = gas_wanted
            gas_used = msg.gas_used
            performative.gas_used = gas_used
            events = msg.events
            Events.encode(performative.events, events)
            codespace = msg.codespace
            performative.codespace = codespace
            abci_msg.response_deliver_tx.CopyFrom(performative)
        elif performative_id == AbciMessage.Performative.RESPONSE_END_BLOCK:
            performative = abci_pb2.AbciMessage.Response_End_Block_Performative()  # type: ignore
            validator_updates = msg.validator_updates
            ValidatorUpdates.encode(performative.validator_updates, validator_updates)
            if msg.is_set("consensus_param_updates"):
                performative.consensus_param_updates_is_set = True
                consensus_param_updates = msg.consensus_param_updates
                ConsensusParams.encode(
                    performative.consensus_param_updates, consensus_param_updates
                )
            events = msg.events
            Events.encode(performative.events, events)
            abci_msg.response_end_block.CopyFrom(performative)
        elif performative_id == AbciMessage.Performative.RESPONSE_COMMIT:
            performative = abci_pb2.AbciMessage.Response_Commit_Performative()  # type: ignore
            data = msg.data
            performative.data = data
            retain_height = msg.retain_height
            performative.retain_height = retain_height
            abci_msg.response_commit.CopyFrom(performative)
        elif performative_id == AbciMessage.Performative.RESPONSE_LIST_SNAPSHOTS:
            performative = abci_pb2.AbciMessage.Response_List_Snapshots_Performative()  # type: ignore
            snapshots = msg.snapshots
            SnapShots.encode(performative.snapshots, snapshots)
            abci_msg.response_list_snapshots.CopyFrom(performative)
        elif performative_id == AbciMessage.Performative.RESPONSE_OFFER_SNAPSHOT:
            performative = abci_pb2.AbciMessage.Response_Offer_Snapshot_Performative()  # type: ignore
            result = msg.result
            Result.encode(performative.result, result)
            abci_msg.response_offer_snapshot.CopyFrom(performative)
        elif performative_id == AbciMessage.Performative.RESPONSE_LOAD_SNAPSHOT_CHUNK:
            performative = abci_pb2.AbciMessage.Response_Load_Snapshot_Chunk_Performative()  # type: ignore
            chunk = msg.chunk
            performative.chunk = chunk
            abci_msg.response_load_snapshot_chunk.CopyFrom(performative)
        elif performative_id == AbciMessage.Performative.RESPONSE_APPLY_SNAPSHOT_CHUNK:
            performative = abci_pb2.AbciMessage.Response_Apply_Snapshot_Chunk_Performative()  # type: ignore
            result = msg.result
            Result.encode(performative.result, result)
            refetch_chunks = msg.refetch_chunks
            performative.refetch_chunks.extend(refetch_chunks)
            reject_senders = msg.reject_senders
            performative.reject_senders.extend(reject_senders)
            abci_msg.response_apply_snapshot_chunk.CopyFrom(performative)
        elif performative_id == AbciMessage.Performative.DUMMY:
            performative = abci_pb2.AbciMessage.Dummy_Performative()  # type: ignore
            dummy_consensus_params = msg.dummy_consensus_params
            ConsensusParams.encode(
                performative.dummy_consensus_params, dummy_consensus_params
            )
            abci_msg.dummy.CopyFrom(performative)
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
        elif performative_id == AbciMessage.Performative.REQUEST_SET_OPTION:
            option_key = abci_pb.request_set_option.option_key
            performative_content["option_key"] = option_key
            option_value = abci_pb.request_set_option.option_value
            performative_content["option_value"] = option_value
        elif performative_id == AbciMessage.Performative.REQUEST_INIT_CHAIN:
            pb2_time = abci_pb.request_init_chain.time
            time = Timestamp.decode(pb2_time)
            performative_content["time"] = time
            chain_id = abci_pb.request_init_chain.chain_id
            performative_content["chain_id"] = chain_id
            if abci_pb.request_init_chain.consensus_params_is_set:
                pb2_consensus_params = abci_pb.request_init_chain.consensus_params
                consensus_params = ConsensusParams.decode(pb2_consensus_params)
                performative_content["consensus_params"] = consensus_params
            pb2_validators = abci_pb.request_init_chain.validators
            validators = ValidatorUpdates.decode(pb2_validators)
            performative_content["validators"] = validators
            app_state_bytes = abci_pb.request_init_chain.app_state_bytes
            performative_content["app_state_bytes"] = app_state_bytes
            initial_height = abci_pb.request_init_chain.initial_height
            performative_content["initial_height"] = initial_height
        elif performative_id == AbciMessage.Performative.REQUEST_QUERY:
            query_data = abci_pb.request_query.query_data
            performative_content["query_data"] = query_data
            path = abci_pb.request_query.path
            performative_content["path"] = path
            height = abci_pb.request_query.height
            performative_content["height"] = height
            prove = abci_pb.request_query.prove
            performative_content["prove"] = prove
        elif performative_id == AbciMessage.Performative.REQUEST_BEGIN_BLOCK:
            hash = abci_pb.request_begin_block.hash
            performative_content["hash"] = hash
            pb2_header = abci_pb.request_begin_block.header
            header = Header.decode(pb2_header)
            performative_content["header"] = header
            pb2_last_commit_info = abci_pb.request_begin_block.last_commit_info
            last_commit_info = LastCommitInfo.decode(pb2_last_commit_info)
            performative_content["last_commit_info"] = last_commit_info
            pb2_byzantine_validators = abci_pb.request_begin_block.byzantine_validators
            byzantine_validators = Evidences.decode(pb2_byzantine_validators)
            performative_content["byzantine_validators"] = byzantine_validators
        elif performative_id == AbciMessage.Performative.REQUEST_CHECK_TX:
            tx = abci_pb.request_check_tx.tx
            performative_content["tx"] = tx
            pb2_type = abci_pb.request_check_tx.type
            type = CheckTxType.decode(pb2_type)
            performative_content["type"] = type
        elif performative_id == AbciMessage.Performative.REQUEST_DELIVER_TX:
            tx = abci_pb.request_deliver_tx.tx
            performative_content["tx"] = tx
        elif performative_id == AbciMessage.Performative.REQUEST_END_BLOCK:
            height = abci_pb.request_end_block.height
            performative_content["height"] = height
        elif performative_id == AbciMessage.Performative.REQUEST_COMMIT:
            pass
        elif performative_id == AbciMessage.Performative.REQUEST_LIST_SNAPSHOTS:
            pass
        elif performative_id == AbciMessage.Performative.REQUEST_OFFER_SNAPSHOT:
            pb2_snapshot = abci_pb.request_offer_snapshot.snapshot
            snapshot = Snapshot.decode(pb2_snapshot)
            performative_content["snapshot"] = snapshot
            app_hash = abci_pb.request_offer_snapshot.app_hash
            performative_content["app_hash"] = app_hash
        elif performative_id == AbciMessage.Performative.REQUEST_LOAD_SNAPSHOT_CHUNK:
            height = abci_pb.request_load_snapshot_chunk.height
            performative_content["height"] = height
            format = abci_pb.request_load_snapshot_chunk.format
            performative_content["format"] = format
            chunk_index = abci_pb.request_load_snapshot_chunk.chunk_index
            performative_content["chunk_index"] = chunk_index
        elif performative_id == AbciMessage.Performative.REQUEST_APPLY_SNAPSHOT_CHUNK:
            index = abci_pb.request_apply_snapshot_chunk.index
            performative_content["index"] = index
            chunk = abci_pb.request_apply_snapshot_chunk.chunk
            performative_content["chunk"] = chunk
            chunk_sender = abci_pb.request_apply_snapshot_chunk.chunk_sender
            performative_content["chunk_sender"] = chunk_sender
        elif performative_id == AbciMessage.Performative.RESPONSE_EXCEPTION:
            error = abci_pb.response_exception.error
            performative_content["error"] = error
        elif performative_id == AbciMessage.Performative.RESPONSE_ECHO:
            message = abci_pb.response_echo.message
            performative_content["message"] = message
        elif performative_id == AbciMessage.Performative.RESPONSE_FLUSH:
            pass
        elif performative_id == AbciMessage.Performative.RESPONSE_INFO:
            info_data = abci_pb.response_info.info_data
            performative_content["info_data"] = info_data
            version = abci_pb.response_info.version
            performative_content["version"] = version
            app_version = abci_pb.response_info.app_version
            performative_content["app_version"] = app_version
            last_block_height = abci_pb.response_info.last_block_height
            performative_content["last_block_height"] = last_block_height
            last_block_app_hash = abci_pb.response_info.last_block_app_hash
            performative_content["last_block_app_hash"] = last_block_app_hash
        elif performative_id == AbciMessage.Performative.RESPONSE_SET_OPTION:
            code = abci_pb.response_set_option.code
            performative_content["code"] = code
            log = abci_pb.response_set_option.log
            performative_content["log"] = log
            info = abci_pb.response_set_option.info
            performative_content["info"] = info
        elif performative_id == AbciMessage.Performative.RESPONSE_INIT_CHAIN:
            if abci_pb.response_init_chain.consensus_params_is_set:
                pb2_consensus_params = abci_pb.response_init_chain.consensus_params
                consensus_params = ConsensusParams.decode(pb2_consensus_params)
                performative_content["consensus_params"] = consensus_params
            pb2_validators = abci_pb.response_init_chain.validators
            validators = ValidatorUpdates.decode(pb2_validators)
            performative_content["validators"] = validators
            app_hash = abci_pb.response_init_chain.app_hash
            performative_content["app_hash"] = app_hash
        elif performative_id == AbciMessage.Performative.RESPONSE_QUERY:
            code = abci_pb.response_query.code
            performative_content["code"] = code
            log = abci_pb.response_query.log
            performative_content["log"] = log
            info = abci_pb.response_query.info
            performative_content["info"] = info
            index = abci_pb.response_query.index
            performative_content["index"] = index
            key = abci_pb.response_query.key
            performative_content["key"] = key
            value = abci_pb.response_query.value
            performative_content["value"] = value
            pb2_proof_ops = abci_pb.response_query.proof_ops
            proof_ops = ProofOps.decode(pb2_proof_ops)
            performative_content["proof_ops"] = proof_ops
            height = abci_pb.response_query.height
            performative_content["height"] = height
            codespace = abci_pb.response_query.codespace
            performative_content["codespace"] = codespace
        elif performative_id == AbciMessage.Performative.RESPONSE_BEGIN_BLOCK:
            pb2_events = abci_pb.response_begin_block.events
            events = Events.decode(pb2_events)
            performative_content["events"] = events
        elif performative_id == AbciMessage.Performative.RESPONSE_CHECK_TX:
            code = abci_pb.response_check_tx.code
            performative_content["code"] = code
            data = abci_pb.response_check_tx.data
            performative_content["data"] = data
            log = abci_pb.response_check_tx.log
            performative_content["log"] = log
            info = abci_pb.response_check_tx.info
            performative_content["info"] = info
            gas_wanted = abci_pb.response_check_tx.gas_wanted
            performative_content["gas_wanted"] = gas_wanted
            gas_used = abci_pb.response_check_tx.gas_used
            performative_content["gas_used"] = gas_used
            pb2_events = abci_pb.response_check_tx.events
            events = Events.decode(pb2_events)
            performative_content["events"] = events
            codespace = abci_pb.response_check_tx.codespace
            performative_content["codespace"] = codespace
        elif performative_id == AbciMessage.Performative.RESPONSE_DELIVER_TX:
            code = abci_pb.response_deliver_tx.code
            performative_content["code"] = code
            data = abci_pb.response_deliver_tx.data
            performative_content["data"] = data
            log = abci_pb.response_deliver_tx.log
            performative_content["log"] = log
            info = abci_pb.response_deliver_tx.info
            performative_content["info"] = info
            gas_wanted = abci_pb.response_deliver_tx.gas_wanted
            performative_content["gas_wanted"] = gas_wanted
            gas_used = abci_pb.response_deliver_tx.gas_used
            performative_content["gas_used"] = gas_used
            pb2_events = abci_pb.response_deliver_tx.events
            events = Events.decode(pb2_events)
            performative_content["events"] = events
            codespace = abci_pb.response_deliver_tx.codespace
            performative_content["codespace"] = codespace
        elif performative_id == AbciMessage.Performative.RESPONSE_END_BLOCK:
            pb2_validator_updates = abci_pb.response_end_block.validator_updates
            validator_updates = ValidatorUpdates.decode(pb2_validator_updates)
            performative_content["validator_updates"] = validator_updates
            if abci_pb.response_end_block.consensus_param_updates_is_set:
                pb2_consensus_param_updates = (
                    abci_pb.response_end_block.consensus_param_updates
                )
                consensus_param_updates = ConsensusParams.decode(
                    pb2_consensus_param_updates
                )
                performative_content[
                    "consensus_param_updates"
                ] = consensus_param_updates
            pb2_events = abci_pb.response_end_block.events
            events = Events.decode(pb2_events)
            performative_content["events"] = events
        elif performative_id == AbciMessage.Performative.RESPONSE_COMMIT:
            data = abci_pb.response_commit.data
            performative_content["data"] = data
            retain_height = abci_pb.response_commit.retain_height
            performative_content["retain_height"] = retain_height
        elif performative_id == AbciMessage.Performative.RESPONSE_LIST_SNAPSHOTS:
            pb2_snapshots = abci_pb.response_list_snapshots.snapshots
            snapshots = SnapShots.decode(pb2_snapshots)
            performative_content["snapshots"] = snapshots
        elif performative_id == AbciMessage.Performative.RESPONSE_OFFER_SNAPSHOT:
            pb2_result = abci_pb.response_offer_snapshot.result
            result = Result.decode(pb2_result)
            performative_content["result"] = result
        elif performative_id == AbciMessage.Performative.RESPONSE_LOAD_SNAPSHOT_CHUNK:
            chunk = abci_pb.response_load_snapshot_chunk.chunk
            performative_content["chunk"] = chunk
        elif performative_id == AbciMessage.Performative.RESPONSE_APPLY_SNAPSHOT_CHUNK:
            pb2_result = abci_pb.response_apply_snapshot_chunk.result
            result = Result.decode(pb2_result)
            performative_content["result"] = result
            refetch_chunks = abci_pb.response_apply_snapshot_chunk.refetch_chunks
            refetch_chunks_tuple = tuple(refetch_chunks)
            performative_content["refetch_chunks"] = refetch_chunks_tuple
            reject_senders = abci_pb.response_apply_snapshot_chunk.reject_senders
            reject_senders_tuple = tuple(reject_senders)
            performative_content["reject_senders"] = reject_senders_tuple
        elif performative_id == AbciMessage.Performative.DUMMY:
            pb2_dummy_consensus_params = abci_pb.dummy.dummy_consensus_params
            dummy_consensus_params = ConsensusParams.decode(pb2_dummy_consensus_params)
            performative_content["dummy_consensus_params"] = dummy_consensus_params
        else:
            raise ValueError("Performative not valid: {}.".format(performative_id))

        return AbciMessage(
            message_id=message_id,
            dialogue_reference=dialogue_reference,
            target=target,
            performative=performative,
            **performative_content
        )
