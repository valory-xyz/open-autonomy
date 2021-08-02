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
"""Encode AEA messages into Tendermint protobuf messages."""
from typing import Callable, Optional, Union

from packages.valory.connections.abci.tendermint.abci.types_pb2 import (
    BlockParams,
    ConsensusParams,
    Event,
    Request,
    Response,
    ResponseBeginBlock,
    ResponseCommit,
    ResponseEndBlock,
    ResponseFlush,
    ResponseInfo,
    ResponseInitChain,
    ValidatorUpdate,
)
from packages.valory.connections.abci.tendermint.types.params_pb2 import (
    EvidenceParams,
    ValidatorParams,
)
from packages.valory.protocols.abci import AbciMessage
from packages.valory.protocols.abci.custom_types import BlockParams as CustomBlockParams
from packages.valory.protocols.abci.custom_types import (
    ConsensusParams as CustomConsensusParams,
)
from packages.valory.protocols.abci.custom_types import Event as CustomEvent
from packages.valory.protocols.abci.custom_types import (
    EvidenceParams as CustomEvidenceParams,
)
from packages.valory.protocols.abci.custom_types import (
    ValidatorParams as CustomValidatorParams,
)
from packages.valory.protocols.abci.custom_types import (
    ValidatorUpdate as CustomValidatorUpdate,
)
from packages.valory.protocols.abci.custom_types import (
    VersionParams as CustomVersionParams,
)


class _TendermintProtocolEncoder:
    """
    Decoder called by the server to process requests *towards* the TCP connection with Tendermint.

    It translates from the AEA's ABCI protocol messages into Tendermint's ABCI Protobuf messages.
    """

    @classmethod
    def process(cls, message: AbciMessage) -> Optional[Union[Request, Response]]:
        """Encode an AbciMessage object into either Request or Respose protobuf objects."""
        # from "(request|response)_type", get 'type'
        handler: Callable[[AbciMessage], Union[Request, Response]] = getattr(
            cls, message.performative.value, cls.no_match
        )
        return handler(message)

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

        if message.is_set("consensus_param_updates"):
            consensus_params_pb = ConsensusParams()
            CustomConsensusParams.encode(
                consensus_params_pb, message.consensus_param_updates
            )
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
    def no_match(cls, _request: Request) -> None:
        return None

    @classmethod
    def _encode_consensus_params(cls, consensus_params: CustomConsensusParams):
        consensus_params_pb = ConsensusParams()
        return CustomConsensusParams.encode(consensus_params_pb, consensus_params)

    @classmethod
    def _encode_block_params(cls, block_params: CustomBlockParams):
        block_params_pb = BlockParams()
        return CustomBlockParams.encode(block_params_pb, block_params)

    @classmethod
    def _encode_evidence_params(cls, evidence_params: CustomEvidenceParams):
        evidence_params_pb = EvidenceParams()
        return CustomEvidenceParams.encode(evidence_params_pb, evidence_params)

    @classmethod
    def _encode_validator_params(cls, validator_params: CustomValidatorParams):
        validator_params_pb = ValidatorParams()
        return CustomValidatorParams.encode(validator_params_pb, validator_params)

    @classmethod
    def _encode_version_params(cls, version_params: CustomVersionParams):
        version_params_pb = ValidatorUpdate()
        return CustomVersionParams.encode(version_params_pb, version_params)

    @classmethod
    def _encode_validator_update(cls, validator_update: CustomValidatorUpdate):
        validator_update_pb = ValidatorUpdate()
        return CustomValidatorUpdate.encode(validator_update_pb, validator_update)

    @classmethod
    def _encode_event(cls, event: CustomEvent):
        event_pb = Event()
        return CustomEvent.encode(event_pb, event)
