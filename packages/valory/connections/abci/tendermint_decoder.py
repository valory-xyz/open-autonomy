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
"""Decode AEA messages from Tendermint protobuf messages."""

# isort: skip_file  # noqa

from typing import Callable, Tuple, cast

from aea.exceptions import enforce
from google.protobuf.timestamp_pb2 import Timestamp as TimestampPb

from packages.valory.connections.abci.dialogues import AbciDialogue, AbciDialogues
from packages.valory.connections.abci.tendermint.abci.types_pb2 import (  # type: ignore
    Evidence as EvidencePb,
)
from packages.valory.connections.abci.tendermint.abci.types_pb2 import (
    LastCommitInfo as LastCommitInfoPb,
)
from packages.valory.connections.abci.tendermint.abci.types_pb2 import Request
from packages.valory.connections.abci.tendermint.abci.types_pb2 import (
    Validator as ValidatorPb,
)
from packages.valory.connections.abci.tendermint.types.types_pb2 import (  # type: ignore
    Header as HeaderPb,
)
from packages.valory.protocols.abci import AbciMessage
from packages.valory.protocols.abci.custom_types import (
    BlockID,
    CheckTxType,
    CheckTxTypeEnum,
    ConsensusParams,
    Evidence,
    Evidences,
    Header,
    LastCommitInfo,
    PartSetHeader,
    Timestamp,
    Validator,
    ValidatorUpdates,
)


from packages.valory.connections.abci.tendermint.abci.types_pb2 import (  # isort:skip
    ConsensusParams as ConsensusParamsPb,
)


from packages.valory.connections.abci.tendermint.types.types_pb2 import (  # type: ignore
    BlockID as BlockIDPb,
)


class _TendermintProtocolDecoder:
    """
    Decoder called by the server to process requests from the TCP connection with Tendermint.

    It translates from Tendermint's ABCI Protobuf messages into the AEA's ABCI protocol messages.
    """

    @classmethod
    def process(
        cls, message: Request, dialogues: AbciDialogues, counterparty: str
    ) -> Tuple[AbciMessage, AbciDialogue]:
        """Process an ABCI request or response."""
        is_request = isinstance(message, Request)
        enforce(is_request, "only Request messages are allowed")
        message_type = f"request_{message.WhichOneof('value')}"
        handler: Callable[
            [Request, AbciDialogues, str], Tuple[AbciMessage, AbciDialogue]
        ] = getattr(cls, message_type, cls.no_match)
        abci_message, abci_dialogue = handler(message, dialogues, counterparty)
        return abci_message, abci_dialogue

    @classmethod
    def request_flush(
        cls, _request: Request, dialogues: AbciDialogues, counterparty: str
    ) -> Tuple[AbciMessage, AbciDialogue]:
        """
        Decode a flush request.

        :param _request: the request.
        :param dialogues: the dialogues object.
        :param counterparty: the counterparty.
        :return: the AbciMessage request.
        """
        abci_message, abci_dialogue = dialogues.create(
            performative=AbciMessage.Performative.REQUEST_FLUSH,
            counterparty=counterparty,
        )
        return cast(AbciMessage, abci_message), cast(AbciDialogue, abci_dialogue)

    @classmethod
    def request_info(
        cls, request: Request, dialogues: AbciDialogues, counterparty: str
    ) -> Tuple[AbciMessage, AbciDialogue]:
        """
        Decode a info request.

        :param request: the request.
        :param dialogues: the dialogues object.
        :param counterparty: the counterparty.
        :return: the AbciMessage request.
        """
        info = request.info
        abci_message, abci_dialogue = dialogues.create(
            performative=AbciMessage.Performative.REQUEST_INFO,
            counterparty=counterparty,
            version=info.version,
            block_version=info.block_version,
            p2p_version=info.p2p_version,
        )
        return cast(AbciMessage, abci_message), cast(AbciDialogue, abci_dialogue)

    @classmethod
    def request_init_chain(
        cls, request: Request, dialogues: AbciDialogues, counterparty: str
    ) -> Tuple[AbciMessage, AbciDialogue]:
        """
        Decode a init_chain request.

        :param request: the request.
        :param dialogues: the dialogues object.
        :param counterparty: the counterparty.
        :return: the AbciMessage request.
        """
        init_chain = request.init_chain
        timestamp = cls._decode_timestamp(init_chain.time)
        chain_id = init_chain.chain_id
        consensus_params = (
            cls._decode_consensus_params(init_chain.consensus_params)
            if init_chain.consensus_params is not None
            else None
        )
        validators = ValidatorUpdates(init_chain.validators)
        app_state_bytes = init_chain.app_state_bytes
        initial_height = init_chain.initial_height

        abci_message, abci_dialogue = dialogues.create(
            performative=AbciMessage.Performative.REQUEST_INIT_CHAIN,
            counterparty=counterparty,
            time=timestamp,
            chain_id=chain_id,
            validators=validators,
            app_state_bytes=app_state_bytes,
            initial_height=initial_height,
        )
        if consensus_params is not None:
            abci_message.set("consensus_params", consensus_params)
        return cast(AbciMessage, abci_message), cast(AbciDialogue, abci_dialogue)

    @classmethod
    def request_begin_block(
        cls, request: Request, dialogues: AbciDialogues, counterparty: str
    ) -> Tuple[AbciMessage, AbciDialogue]:
        """
        Decode a begin_block request.

        :param request: the request.
        :param dialogues: the dialogues object.
        :param counterparty: the counterparty.
        :return: the AbciMessage request.
        """
        begin_block = request.begin_block
        hash_ = begin_block.hash
        header = cls._decode_header(begin_block.header)
        last_commit_info = cls._decode_last_commit_info(begin_block.last_commit_info)
        evidences = [
            cls._decode_evidence(byzantine_validator)
            for byzantine_validator in list(begin_block.byzantine_validators)
        ]
        abci_message, abci_dialogue = dialogues.create(
            performative=AbciMessage.Performative.REQUEST_BEGIN_BLOCK,
            counterparty=counterparty,
            hash=hash_,
            header=header,
            last_commit_info=last_commit_info,
            byzantine_validators=Evidences(evidences),
        )
        return cast(AbciMessage, abci_message), cast(AbciDialogue, abci_dialogue)

    @classmethod
    def request_check_tx(
        cls, request: Request, dialogues: AbciDialogues, counterparty: str
    ) -> Tuple[AbciMessage, AbciDialogue]:
        """
        Decode a check_tx request.

        :param request: the request.
        :param dialogues: the dialogues object.
        :param counterparty: the counterparty.
        :return: the AbciMessage request.
        """
        check_tx = request.check_tx
        transaction = check_tx.tx
        check_tx_type = CheckTxType(CheckTxTypeEnum(check_tx.type))
        abci_message, abci_dialogue = dialogues.create(
            performative=AbciMessage.Performative.REQUEST_CHECK_TX,
            counterparty=counterparty,
            tx=transaction,
            type=check_tx_type,
        )
        return cast(AbciMessage, abci_message), cast(AbciDialogue, abci_dialogue)

    @classmethod
    def request_deliver_tx(
        cls, request: Request, dialogues: AbciDialogues, counterparty: str
    ) -> Tuple[AbciMessage, AbciDialogue]:
        """
        Decode a deliver_tx request.

        :param request: the request.
        :param dialogues: the dialogues object.
        :param counterparty: the counterparty.
        :return: the AbciMessage request.
        """
        abci_message, abci_dialogue = dialogues.create(
            performative=AbciMessage.Performative.REQUEST_DELIVER_TX,
            counterparty=counterparty,
            tx=request.deliver_tx.tx,
        )
        return cast(AbciMessage, abci_message), cast(AbciDialogue, abci_dialogue)

    @classmethod
    def request_query(
        cls, request: Request, dialogues: AbciDialogues, counterparty: str
    ) -> Tuple[AbciMessage, AbciDialogue]:
        """
        Decode a query request.

        :param request: the request.
        :param dialogues: the dialogues object.
        :param counterparty: the counterparty.
        :return: the AbciMessage request.
        """
        abci_message, abci_dialogue = dialogues.create(
            performative=AbciMessage.Performative.REQUEST_QUERY,
            counterparty=counterparty,
            query_data=request.query.data,
            path=request.query.path,
            height=request.query.height,
            prove=request.query.prove,
        )
        return cast(AbciMessage, abci_message), cast(AbciDialogue, abci_dialogue)

    @classmethod
    def request_commit(
        cls, _request: Request, dialogues: AbciDialogues, counterparty: str
    ) -> Tuple[AbciMessage, AbciDialogue]:
        """
        Decode a commit request.

        :param _request: the request.
        :param dialogues: the dialogues object.
        :param counterparty: the counterparty.
        :return: the AbciMessage request.
        """
        abci_message, abci_dialogue = dialogues.create(
            performative=AbciMessage.Performative.REQUEST_COMMIT,
            counterparty=counterparty,
        )
        return cast(AbciMessage, abci_message), cast(AbciDialogue, abci_dialogue)

    @classmethod
    def request_end_block(
        cls, request: Request, dialogues: AbciDialogues, counterparty: str
    ) -> Tuple[AbciMessage, AbciDialogue]:
        """
        Decode an end_block request.

        :param request: the request.
        :param dialogues: the dialogues object.
        :param counterparty: the counterparty.
        :return: the AbciMessage request.
        """
        abci_message, abci_dialogue = dialogues.create(
            performative=AbciMessage.Performative.REQUEST_END_BLOCK,
            counterparty=counterparty,
            height=request.end_block.height,
        )
        return cast(AbciMessage, abci_message), cast(AbciDialogue, abci_dialogue)

    @classmethod
    def request_list_snapshots(
        cls, request: Request, dialogues: AbciDialogues, counterparty: str
    ) -> Tuple[AbciMessage, AbciDialogue]:
        """Decode a list_snapshots request."""
        raise NotImplementedError

    @classmethod
    def request_offer_snapshot(
        cls, request: Request, dialogues: AbciDialogues, counterparty: str
    ) -> Tuple[AbciMessage, AbciDialogue]:
        """Decode a offer_snapshot request."""
        raise NotImplementedError

    @classmethod
    def request_load_snapshot_chunk(
        cls, request: Request, dialogues: AbciDialogues, counterparty: str
    ) -> Tuple[AbciMessage, AbciDialogue]:
        """Decode a load_snapshot_chunk request."""
        raise NotImplementedError

    @classmethod
    def request_apply_snapshot_chunk(
        cls, request: Request, dialogues: AbciDialogues, counterparty: str
    ) -> Tuple[AbciMessage, AbciDialogue]:
        """Decode a apply_snapshot_chunk request."""
        raise NotImplementedError

    @classmethod
    def no_match(
        cls, _request: Request, _dialogues: AbciDialogues, _counterparty: str
    ) -> None:
        """Handle the case in which the request is not supported."""
        return None

    @classmethod
    def _decode_timestamp(cls, timestamp_tendermint_pb: TimestampPb) -> Timestamp:
        """Decode a timestamp object."""
        return Timestamp(
            timestamp_tendermint_pb.seconds,
            timestamp_tendermint_pb.nanos,
        )

    @classmethod
    def _decode_consensus_params(
        cls, consensus_params_tendermint_pb: ConsensusParamsPb
    ) -> ConsensusParams:
        """Decode a ConsensusParams object."""
        return ConsensusParams.decode(consensus_params_tendermint_pb)

    @classmethod
    def _decode_header(cls, header_tendermint_pb: HeaderPb) -> Header:
        """Decode a Header object."""
        return Header.decode(header_tendermint_pb)

    @classmethod
    def _decode_block_id(cls, block_id_pb: BlockIDPb) -> BlockID:
        """Decode a Block ID object."""
        part_set_header_pb = block_id_pb.part_set_header
        part_set_header = PartSetHeader(
            part_set_header_pb.index, part_set_header_pb.bytes
        )
        return BlockID(block_id_pb.hash, part_set_header)

    @classmethod
    def _decode_last_commit_info(
        cls, last_commit_info_tendermint_pb: LastCommitInfoPb
    ) -> LastCommitInfo:
        """Decode a LastCommitInfo object."""
        return LastCommitInfo.decode(last_commit_info_tendermint_pb)

    @classmethod
    def _decode_validator(cls, validator_pb: ValidatorPb) -> Validator:
        """Decode a Validator object."""
        return Validator(validator_pb.address, validator_pb.power)

    @classmethod
    def _decode_evidence(cls, evidence_pb: EvidencePb) -> Evidence:
        """Decode an Evidence object."""
        return Evidence.decode(evidence_pb)
