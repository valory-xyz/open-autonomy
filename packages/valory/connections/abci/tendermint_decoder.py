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
"""Decode AEA messages from Tendermint protobuf messages."""

# isort: skip_file  # noqa

from typing import Callable, Optional, Tuple, cast

from aea.exceptions import enforce
from google.protobuf.timestamp_pb2 import (  # pylint: disable=no-name-in-module
    Timestamp as TimestampPb,
)

from packages.valory.connections.abci.dialogues import AbciDialogue, AbciDialogues
from packages.valory.connections.abci.tendermint.abci.types_pb2 import (  # type: ignore
    Evidence as EvidencePb,
)
from packages.valory.connections.abci.tendermint.abci.types_pb2 import (  # type: ignore
    LastCommitInfo as LastCommitInfoPb,
)
from packages.valory.connections.abci.tendermint.abci.types_pb2 import Request  # type: ignore
from packages.valory.connections.abci.tendermint.abci.types_pb2 import (  # type: ignore
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
    Snapshot,
    Timestamp,
    Validator,
    ValidatorUpdates,
    ValidatorUpdate,
)


from packages.valory.connections.abci.tendermint.abci.types_pb2 import (  # type: ignore # isort:skip
    ConsensusParams as ConsensusParamsPb,
)
from packages.valory.connections.abci.tendermint.abci.types_pb2 import (  # type: ignore # isort:skip
    ValidatorUpdate as ValidatorUpdatePb,
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
    ) -> Optional[Tuple[AbciMessage, AbciDialogue]]:
        """Process an ABCI request or response."""
        is_request = isinstance(message, Request)
        enforce(is_request, "only Request messages are allowed")
        message_type = f"request_{message.WhichOneof('value')}"
        handler: Callable[
            [Request, AbciDialogues, str], Optional[Tuple[AbciMessage, AbciDialogue]]
        ] = getattr(cls, message_type, cls.no_match)
        result = handler(message, dialogues, counterparty)
        return result

    @classmethod
    def request_echo(
        cls, request: Request, dialogues: AbciDialogues, counterparty: str
    ) -> Tuple[AbciMessage, AbciDialogue]:
        """
        Decode an echo request.

        :param request: the request.
        :param dialogues: the dialogues object.
        :param counterparty: the counterparty.
        :return: the AbciMessage request.
        """
        echo = request.echo
        abci_message, abci_dialogue = dialogues.create(
            performative=AbciMessage.Performative.REQUEST_ECHO,
            counterparty=counterparty,
            message=echo.message,
        )
        return cast(AbciMessage, abci_message), cast(AbciDialogue, abci_dialogue)

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
    def request_set_option(
        cls, request: Request, dialogues: AbciDialogues, counterparty: str
    ) -> Tuple[AbciMessage, AbciDialogue]:
        """
        Decode a set_option request.

        :param request: the request.
        :param dialogues: the dialogues object.
        :param counterparty: the counterparty.
        :return: the AbciMessage request.
        """
        set_option = request.set_option
        abci_message, abci_dialogue = dialogues.create(
            performative=AbciMessage.Performative.REQUEST_SET_OPTION,
            counterparty=counterparty,
            option_key=set_option.key,
            option_value=set_option.value,
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
        validators = ValidatorUpdates(
            [
                cls._decode_validator_update(validator_update_pb)
                for validator_update_pb in list(init_chain.validators)
            ]
        )
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
        cls, _request: Request, dialogues: AbciDialogues, counterparty: str
    ) -> Tuple[AbciMessage, AbciDialogue]:
        """Decode a list_snapshots request."""
        abci_message, abci_dialogue = dialogues.create(
            performative=AbciMessage.Performative.REQUEST_LIST_SNAPSHOTS,
            counterparty=counterparty,
        )
        return cast(AbciMessage, abci_message), cast(AbciDialogue, abci_dialogue)

    @classmethod
    def request_offer_snapshot(
        cls, request: Request, dialogues: AbciDialogues, counterparty: str
    ) -> Tuple[AbciMessage, AbciDialogue]:
        """Decode a offer_snapshot request."""
        offer_snapshot = request.offer_snapshot
        abci_message, abci_dialogue = dialogues.create(
            performative=AbciMessage.Performative.REQUEST_OFFER_SNAPSHOT,
            counterparty=counterparty,
            snapshot=Snapshot(
                offer_snapshot.snapshot.height,
                offer_snapshot.snapshot.format,
                offer_snapshot.snapshot.chunks,
                offer_snapshot.snapshot.hash,
                offer_snapshot.snapshot.metadata,
            ),
            app_hash=offer_snapshot.app_hash,
        )
        return cast(AbciMessage, abci_message), cast(AbciDialogue, abci_dialogue)

    @classmethod
    def request_load_snapshot_chunk(
        cls, request: Request, dialogues: AbciDialogues, counterparty: str
    ) -> Tuple[AbciMessage, AbciDialogue]:
        """Decode a load_snapshot_chunk request."""
        load_snapshot_chunk = request.load_snapshot_chunk
        abci_message, abci_dialogue = dialogues.create(
            performative=AbciMessage.Performative.REQUEST_LOAD_SNAPSHOT_CHUNK,
            counterparty=counterparty,
            height=load_snapshot_chunk.height,
            format=load_snapshot_chunk.format,
            chunk_index=load_snapshot_chunk.chunk,
        )
        return cast(AbciMessage, abci_message), cast(AbciDialogue, abci_dialogue)

    @classmethod
    def request_apply_snapshot_chunk(
        cls, request: Request, dialogues: AbciDialogues, counterparty: str
    ) -> Tuple[AbciMessage, AbciDialogue]:
        """Decode a apply_snapshot_chunk request."""
        apply_snapshot_chunk = request.apply_snapshot_chunk
        abci_message, abci_dialogue = dialogues.create(
            performative=AbciMessage.Performative.REQUEST_APPLY_SNAPSHOT_CHUNK,
            counterparty=counterparty,
            index=apply_snapshot_chunk.index,
            chunk=apply_snapshot_chunk.chunk,
            chunk_sender=apply_snapshot_chunk.sender,
        )
        return cast(AbciMessage, abci_message), cast(AbciDialogue, abci_dialogue)

    @classmethod
    def no_match(
        cls, _request: Request, _dialogues: AbciDialogues, _counterparty: str
    ) -> None:  # pragma: nocover
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
    def _decode_validator_update(
        cls, validator_update_pb: ValidatorUpdatePb
    ) -> ValidatorUpdate:
        """Decode a ValidatorUpdate object."""
        return ValidatorUpdate.decode(validator_update_pb)

    @classmethod
    def _decode_header(cls, header_tendermint_pb: HeaderPb) -> Header:
        """Decode a Header object."""
        return Header.decode(header_tendermint_pb)

    @classmethod
    def _decode_block_id(cls, block_id_pb: BlockIDPb) -> BlockID:  # pragma: nocover
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
    def _decode_validator(
        cls, validator_pb: ValidatorPb
    ) -> Validator:  # pragma: nocover
        """Decode a Validator object."""
        return Validator(validator_pb.address, validator_pb.power)

    @classmethod
    def _decode_evidence(cls, evidence_pb: EvidencePb) -> Evidence:  # pragma: nocover
        """Decode an Evidence object."""
        return Evidence.decode(evidence_pb)
