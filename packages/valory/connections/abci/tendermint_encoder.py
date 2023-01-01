# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2023 Valory AG
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
"""Encode AEA messages into Tendermint protobuf messages."""
# pylint: disable=no-member
from typing import Callable, Optional, Union, cast

from packages.valory.connections.abci.tendermint.abci.types_pb2 import (  # type: ignore
    ConsensusParams,
    Event,
    EventAttribute,
    Request,
    Response,
    ResponseApplySnapshotChunk,
    ResponseBeginBlock,
    ResponseCheckTx,
    ResponseCommit,
    ResponseDeliverTx,
    ResponseEcho,
    ResponseEndBlock,
    ResponseException,
    ResponseFlush,
    ResponseInfo,
    ResponseInitChain,
    ResponseListSnapshots,
    ResponseLoadSnapshotChunk,
    ResponseOfferSnapshot,
    ResponseQuery,
    ResponseSetOption,
    Snapshot,
    ValidatorUpdate,
)
from packages.valory.connections.abci.tendermint.crypto.proof_pb2 import (  # type: ignore
    ProofOp,
    ProofOps,
)
from packages.valory.protocols.abci import AbciMessage
from packages.valory.protocols.abci.custom_types import (
    ConsensusParams as CustomConsensusParams,
)
from packages.valory.protocols.abci.custom_types import Event as CustomEvent
from packages.valory.protocols.abci.custom_types import (
    EventAttribute as CustomEventAttribute,
)
from packages.valory.protocols.abci.custom_types import ProofOp as CustomProofOp
from packages.valory.protocols.abci.custom_types import ProofOps as CustomProofOps
from packages.valory.protocols.abci.custom_types import Snapshot as CustomSnapshot
from packages.valory.protocols.abci.custom_types import (
    ValidatorUpdate as CustomValidatorUpdate,
)


class _TendermintProtocolEncoder:
    """
    Decoder called by the server to process requests *towards* the TCP connection with Tendermint.

    It translates from the AEA's ABCI protocol messages into Tendermint's ABCI Protobuf messages.
    """

    @classmethod
    def process(cls, message: AbciMessage) -> Optional[Union[Request, Response]]:
        """Encode an AbciMessage object into either Request or Response protobuf objects."""
        # from "(request|response)_type", get 'type'
        handler: Callable[[AbciMessage], Union[Request, Response]] = getattr(
            cls, message.performative.value, cls.no_match
        )
        return handler(message)

    @classmethod
    def response_exception(cls, message: AbciMessage) -> Response:
        """
        Process the response exception.

        :param message: the response.
        :return: the ABCI protobuf object.
        """
        exception = ResponseException()
        exception.error = message.error
        response = Response(exception=exception)
        return response

    @classmethod
    def response_echo(cls, message: AbciMessage) -> Response:
        """
        Process the response echo.

        :param message: the response.
        :return: the ABCI protobuf object.
        """
        echo = ResponseEcho()
        echo.message = message.message
        response = Response(echo=echo)
        return response

    @classmethod
    def response_set_option(cls, message: AbciMessage) -> Response:
        """
        Process the response set_option.

        :param message: the response.
        :return: the ABCI protobuf object.
        """
        set_option = ResponseSetOption()
        set_option.code = message.code
        set_option.log = message.log
        set_option.info = message.info
        response = Response(set_option=set_option)
        return response

    @classmethod
    def response_info(cls, message: AbciMessage) -> Response:
        """
        Process the response info.

        :param message: the response.
        :return: the ABCI protobuf object.
        """
        info = ResponseInfo()
        info.data = message.info_data
        info.version = message.version
        info.app_version = message.app_version
        info.last_block_height = message.last_block_height
        info.last_block_app_hash = message.last_block_app_hash
        response = Response(info=info)
        return response

    @classmethod
    def response_flush(cls, _message: AbciMessage) -> Response:
        """
        Process the response flush.

        :param _message: the response.
        :return: the ABCI protobuf object.
        """
        response = Response(flush=ResponseFlush())
        return response

    @classmethod
    def response_init_chain(cls, message: AbciMessage) -> Response:
        """
        Process the response init_chain.

        :param message: the response.
        :return: the ABCI protobuf object.
        """
        init_chain = ResponseInitChain()

        if message.consensus_params is not None:
            consensus_params_pb = cls._encode_consensus_params(message.consensus_params)
            init_chain.consensus_params.CopyFrom(consensus_params_pb)

        validators_pb = [
            cls._encode_validator_update(vu)
            for vu in list(message.validators.validator_updates)
        ]
        init_chain.validators.extend(validators_pb)

        init_chain.app_hash = message.app_hash

        response = Response(init_chain=init_chain)
        return response

    @classmethod
    def response_query(cls, message: AbciMessage) -> Response:
        """
        Process the response query.

        :param message: the response.
        :return: the ABCI protobuf object.
        """
        query = ResponseQuery()

        query.code = message.code
        query.log = message.log
        query.info = message.info
        query.index = message.index
        query.key = message.key
        query.value = message.value

        proof_ops_pb = cls._encode_proof_ops(message.proof_ops)
        query.proof_ops.CopyFrom(proof_ops_pb)

        query.height = message.height
        query.codespace = message.codespace

        response = Response(query=query)
        return response

    @classmethod
    def response_check_tx(cls, message: AbciMessage) -> Response:
        """
        Process the response check_tx.

        :param message: the response.
        :return: the ABCI protobuf object.
        """
        check_tx = ResponseCheckTx()

        check_tx.code = message.code
        check_tx.data = message.data
        check_tx.log = message.log
        check_tx.info = message.info
        check_tx.gas_wanted = message.gas_wanted
        check_tx.gas_used = message.gas_used

        events_pb = [cls._encode_event(e) for e in message.events.events]
        check_tx.events.extend(events_pb)

        check_tx.codespace = message.codespace

        response = Response(check_tx=check_tx)
        return response

    @classmethod
    def response_deliver_tx(cls, message: AbciMessage) -> Response:
        """
        Process the response deliver_tx.

        :param message: the response.
        :return: the ABCI protobuf object.
        """
        deliver_tx = ResponseDeliverTx()

        deliver_tx.code = message.code
        deliver_tx.data = message.data
        deliver_tx.log = message.log
        deliver_tx.info = message.info
        deliver_tx.gas_wanted = message.gas_wanted
        deliver_tx.gas_used = message.gas_used

        events_pb = [cls._encode_event(e) for e in message.events.events]
        deliver_tx.events.extend(events_pb)

        deliver_tx.codespace = message.codespace

        response = Response(deliver_tx=deliver_tx)
        return response

    @classmethod
    def response_begin_block(cls, message: AbciMessage) -> Response:
        """
        Process the response begin_block.

        :param message: the response.
        :return: the ABCI protobuf object.
        """
        begin_block = ResponseBeginBlock()

        events_pb = [cls._encode_event(e) for e in message.events.events]
        begin_block.events.extend(events_pb)

        response = Response(begin_block=begin_block)
        return response

    @classmethod
    def response_end_block(cls, message: AbciMessage) -> Response:
        """
        Process the response end_block.

        :param message: the response.
        :return: the ABCI protobuf object.
        """
        end_block = ResponseEndBlock()

        if (
            message.is_set("consensus_param_updates")
            and message.consensus_param_updates is not None
        ):
            consensus_params_updates = cast(
                ConsensusParams, message.consensus_param_updates
            )
            consensus_params_pb = cls._encode_consensus_params(consensus_params_updates)
            end_block.consensus_param_updates.CopyFrom(consensus_params_pb)

        validator_updates_pb = [
            cls._encode_validator_update(vu)
            for vu in message.validator_updates.validator_updates
        ]
        end_block.validator_updates.extend(validator_updates_pb)

        events_pb = [cls._encode_event(e) for e in message.events.events]
        end_block.events.extend(events_pb)

        response = Response(end_block=end_block)
        return response

    @classmethod
    def response_commit(cls, message: AbciMessage) -> Response:
        """
        Process the response commit.

        :param message: the response.
        :return: the ABCI protobuf object.
        """
        commit = ResponseCommit()
        commit.data = message.data
        commit.retain_height = message.retain_height
        return Response(commit=commit)

    @classmethod
    def response_list_snapshots(cls, message: AbciMessage) -> Response:
        """
        Process the response list_snapshots.

        :param message: the response.
        :return: the ABCI protobuf object.
        """
        list_snapshots = ResponseListSnapshots()
        snapshots_pb = [
            cls._encode_snapshot(snapshot) for snapshot in message.snapshots.snapshots
        ]
        list_snapshots.snapshots.extend(snapshots_pb)
        return Response(list_snapshots=list_snapshots)

    @classmethod
    def response_offer_snapshot(cls, message: AbciMessage) -> Response:
        """
        Process the response offer_snapshot.

        :param message: the response.
        :return: the ABCI protobuf object.
        """
        offer_snapshot = ResponseOfferSnapshot()
        offer_snapshot.result = message.result.result_type.value
        return Response(offer_snapshot=offer_snapshot)

    @classmethod
    def response_load_snapshot_chunk(cls, message: AbciMessage) -> Response:
        """
        Process the response load_snapshot_chunk.

        :param message: the response.
        :return: the ABCI protobuf object.
        """
        load_snapshot_chunk = ResponseLoadSnapshotChunk()
        load_snapshot_chunk.chunk = message.chunk
        return Response(load_snapshot_chunk=load_snapshot_chunk)

    @classmethod
    def response_apply_snapshot_chunk(cls, message: AbciMessage) -> Response:
        """
        Process the response apply_snapshot_chunk.

        :param message: the response.
        :return: the ABCI protobuf object.
        """
        apply_snapshot_chunk = ResponseApplySnapshotChunk()
        apply_snapshot_chunk.result = message.result.result_type.value
        apply_snapshot_chunk.refetch_chunks.extend(message.refetch_chunks)
        apply_snapshot_chunk.reject_senders.extend(message.reject_senders)
        return Response(apply_snapshot_chunk=apply_snapshot_chunk)

    @classmethod
    def no_match(cls, _request: Request) -> None:  # pragma: nocover
        """No match."""
        return None

    @classmethod
    def _encode_consensus_params(
        cls, consensus_params: CustomConsensusParams
    ) -> ConsensusParams:
        consensus_params_pb = ConsensusParams()
        CustomConsensusParams.encode(consensus_params_pb, consensus_params)
        return consensus_params_pb

    @classmethod
    def _encode_validator_update(
        cls, validator_update: CustomValidatorUpdate
    ) -> ValidatorUpdate:
        validator_update_pb = ValidatorUpdate()
        CustomValidatorUpdate.encode(validator_update_pb, validator_update)
        return validator_update_pb

    @classmethod
    def _encode_event(cls, event: CustomEvent) -> Event:

        attributes_pb = []
        for attribute in event.attributes:
            attribute_pb = EventAttribute()
            CustomEventAttribute.encode(attribute_pb, attribute)
            attributes_pb.append(attribute_pb)

        event_pb = Event()
        event_pb.type = event.type_
        event_pb.attributes.extend(attributes_pb)
        return event_pb

    @classmethod
    def _encode_proof_ops(cls, proof_ops: CustomProofOps) -> ProofOps:

        ops_pb = []
        for proof_op in proof_ops.proof_ops:
            proof_op_pb = ProofOp()
            CustomProofOp.encode(proof_op_pb, proof_op)
            ops_pb.append(proof_op_pb)

        proof_ops_pb = ProofOps()
        proof_ops_pb.ops.extend(ops_pb)
        return proof_ops_pb

    @classmethod
    def _encode_snapshot(cls, snapshot: CustomSnapshot) -> Event:
        snapshot_pb = Snapshot()
        CustomSnapshot.encode(snapshot_pb, snapshot)
        return snapshot_pb
