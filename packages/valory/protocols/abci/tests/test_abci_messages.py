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

"""Test messages module for abci protocol."""

# pylint: disable=too-many-statements,too-many-locals,no-member,too-few-public-methods,redefined-builtin
from typing import List

from aea.test_tools.test_protocol import BaseProtocolMessagesTestCase

from packages.valory.protocols.abci.custom_types import (
    BlockID,
    BlockParams,
    CheckTxType,
    CheckTxTypeEnum,
    ConsensusParams,
    ConsensusVersion,
    Duration,
    Event,
    EventAttribute,
    Events,
    Evidence,
    EvidenceParams,
    EvidenceType,
    Evidences,
    Header,
    LastCommitInfo,
    PartSetHeader,
    ProofOp,
    ProofOps,
    PublicKey,
    Result,
    ResultType,
    SnapShots,
    Snapshot,
    Timestamp,
    Validator,
    ValidatorParams,
    ValidatorUpdate,
    ValidatorUpdates,
    VersionParams,
    VoteInfo,
)
from packages.valory.protocols.abci.message import AbciMessage


event = Event("type", [EventAttribute(b"key", b"value", True)])
events = Events([event, event])

header = Header(
    ConsensusVersion(0, 0),
    "chain_id",
    0,
    Timestamp(0, 0),
    BlockID(b"hash", PartSetHeader(0, b"hash")),
    b"last_commit_hash",
    b"data_hash",
    b"validators_hash",
    b"next_validators_hash",
    b"consensus_hash",
    b"app_hash",
    b"last_results_hash",
    b"evidence_hash",
    b"proposer_address",
)

validator = Validator(b"address", 0)
last_commit_info = LastCommitInfo(
    0,
    [
        VoteInfo(validator, True),
        VoteInfo(validator, False),
    ],
)

consensus_params = ConsensusParams(
    BlockParams(0, 0),
    EvidenceParams(0, Duration(0, 0), 0),
    ValidatorParams(["pub_key"]),
    VersionParams(0),
)

evidences = Evidences(
    [
        Evidence(EvidenceType.UNKNOWN, validator, 0, Timestamp(0, 0), 0),
        Evidence(EvidenceType.DUPLICATE_VOTE, validator, 0, Timestamp(0, 0), 0),
    ]
)


validators = ValidatorUpdates(
    [
        ValidatorUpdate(
            PublicKey(b"pub_key_bytes", PublicKey.PublicKeyType.ed25519), 1
        ),
        ValidatorUpdate(
            PublicKey(b"pub_key_bytes", PublicKey.PublicKeyType.secp256k1), 2
        ),
    ]
)
snapshot = Snapshot(0, 0, 0, b"hash", b"metadata")
snapshots = SnapShots([snapshot, snapshot])
proof_ops = (
    ProofOps(
        [
            ProofOp("type", b"key", b"data"),
            ProofOp("type", b"key", b"data"),
        ]
    ),
)


class TestMessageAbci(BaseProtocolMessagesTestCase):
    """Test for the 'abci' protocol message."""

    MESSAGE_CLASS = AbciMessage

    def build_messages(self) -> List[AbciMessage]:  # type: ignore[override]
        """Build the messages to be used for testing."""
        return [
            AbciMessage(
                performative=AbciMessage.Performative.REQUEST_ECHO,
                message="some str",
            ),
            AbciMessage(
                performative=AbciMessage.Performative.REQUEST_FLUSH,
            ),
            AbciMessage(
                performative=AbciMessage.Performative.REQUEST_INFO,
                version="some str",
                block_version=12,
                p2p_version=12,
            ),
            AbciMessage(
                performative=AbciMessage.Performative.REQUEST_SET_OPTION,
                option_key="some str",
                option_value="some str",
            ),
            AbciMessage(
                performative=AbciMessage.Performative.REQUEST_INIT_CHAIN,
                time=Timestamp(seconds=1, nanos=1),
                chain_id="some str",
                consensus_params=consensus_params,
                validators=validators,
                app_state_bytes=b"some_bytes",
                initial_height=12,
            ),
            AbciMessage(
                performative=AbciMessage.Performative.REQUEST_QUERY,
                query_data=b"some_bytes",
                path="some str",
                height=12,
                prove=True,
            ),
            AbciMessage(
                performative=AbciMessage.Performative.REQUEST_BEGIN_BLOCK,
                hash=b"some_bytes",
                header=header,
                last_commit_info=last_commit_info,
                byzantine_validators=evidences,
            ),
            AbciMessage(
                performative=AbciMessage.Performative.REQUEST_CHECK_TX,
                tx=b"some_bytes",
                type=CheckTxType(CheckTxTypeEnum.NEW),
            ),
            AbciMessage(
                performative=AbciMessage.Performative.REQUEST_DELIVER_TX,
                tx=b"some_bytes",
            ),
            AbciMessage(
                performative=AbciMessage.Performative.REQUEST_END_BLOCK,
                height=12,
            ),
            AbciMessage(
                performative=AbciMessage.Performative.REQUEST_COMMIT,
            ),
            AbciMessage(
                performative=AbciMessage.Performative.REQUEST_LIST_SNAPSHOTS,
            ),
            AbciMessage(
                performative=AbciMessage.Performative.REQUEST_OFFER_SNAPSHOT,
                snapshot=Snapshot(0, 0, 0, b"hash", b"metadata"),
                app_hash=b"some_bytes",
            ),
            AbciMessage(
                performative=AbciMessage.Performative.REQUEST_LOAD_SNAPSHOT_CHUNK,
                height=12,
                format=12,
                chunk_index=12,
            ),
            AbciMessage(
                performative=AbciMessage.Performative.REQUEST_APPLY_SNAPSHOT_CHUNK,
                index=12,
                chunk=b"some_bytes",
                chunk_sender="some str",
            ),
            AbciMessage(
                performative=AbciMessage.Performative.RESPONSE_EXCEPTION,
                error="some str",
            ),
            AbciMessage(
                performative=AbciMessage.Performative.RESPONSE_ECHO,
                message="some str",
            ),
            AbciMessage(
                performative=AbciMessage.Performative.RESPONSE_FLUSH,
            ),
            AbciMessage(
                performative=AbciMessage.Performative.RESPONSE_INFO,
                info_data="some str",
                version="some str",
                app_version=12,
                last_block_height=12,
                last_block_app_hash=b"some_bytes",
            ),
            AbciMessage(
                performative=AbciMessage.Performative.RESPONSE_SET_OPTION,
                code=12,
                log="some str",
                info="some str",
            ),
            AbciMessage(
                performative=AbciMessage.Performative.RESPONSE_INIT_CHAIN,
                consensus_params=consensus_params,
                validators=validators,
                app_hash=b"some_bytes",
            ),
            AbciMessage(
                performative=AbciMessage.Performative.RESPONSE_QUERY,
                code=12,
                log="some str",
                info="some str",
                index=12,
                key=b"some_bytes",
                value=b"some_bytes",
                proof_ops=ProofOps(
                    [
                        ProofOp("type", b"key", b"data"),
                        ProofOp("type", b"key", b"data"),
                    ]
                ),
                height=12,
                codespace="some str",
            ),
            AbciMessage(
                performative=AbciMessage.Performative.RESPONSE_BEGIN_BLOCK,
                events=events,
            ),
            AbciMessage(
                performative=AbciMessage.Performative.RESPONSE_CHECK_TX,
                code=12,
                data=b"some_bytes",
                log="some str",
                info="some str",
                gas_wanted=12,
                gas_used=12,
                events=events,
                codespace="some str",
            ),
            AbciMessage(
                performative=AbciMessage.Performative.RESPONSE_DELIVER_TX,
                code=12,
                data=b"some_bytes",
                log="some str",
                info="some str",
                gas_wanted=12,
                gas_used=12,
                events=events,
                codespace="some str",
            ),
            AbciMessage(
                performative=AbciMessage.Performative.RESPONSE_END_BLOCK,
                validator_updates=validators,
                consensus_param_updates=consensus_params,
                events=events,
            ),
            AbciMessage(
                performative=AbciMessage.Performative.RESPONSE_COMMIT,
                data=b"some_bytes",
                retain_height=12,
            ),
            AbciMessage(
                performative=AbciMessage.Performative.RESPONSE_LIST_SNAPSHOTS,
                snapshots=snapshots,
            ),
            AbciMessage(
                performative=AbciMessage.Performative.RESPONSE_OFFER_SNAPSHOT,
                result=Result(ResultType.UNKNOWN),
            ),
            AbciMessage(
                performative=AbciMessage.Performative.RESPONSE_LOAD_SNAPSHOT_CHUNK,
                chunk=b"some_bytes",
            ),
            AbciMessage(
                performative=AbciMessage.Performative.RESPONSE_APPLY_SNAPSHOT_CHUNK,
                result=Result(ResultType.UNKNOWN),
                refetch_chunks=(12,),
                reject_senders=("some str",),
            ),
            AbciMessage(
                performative=AbciMessage.Performative.DUMMY,
                dummy_consensus_params=consensus_params,
            ),
        ]

    def build_inconsistent(self) -> List[AbciMessage]:  # type: ignore[override]
        """Build inconsistent messages to be used for testing."""
        return [
            AbciMessage(
                performative=AbciMessage.Performative.REQUEST_ECHO,
                # skip content: message
            ),
            AbciMessage(
                performative=AbciMessage.Performative.REQUEST_INFO,
                # skip content: version
                block_version=12,
                p2p_version=12,
            ),
            AbciMessage(
                performative=AbciMessage.Performative.REQUEST_SET_OPTION,
                # skip content: option_key
                option_value="some str",
            ),
            AbciMessage(
                performative=AbciMessage.Performative.REQUEST_INIT_CHAIN,
                # skip content: time,app_state_bytes
                chain_id="some str",
                consensus_params=consensus_params,
                validators=validators,
                initial_height=12,
            ),
            AbciMessage(
                performative=AbciMessage.Performative.REQUEST_QUERY,
                # skip content: query_data
                path="some str",
                height=12,
                prove=True,
            ),
            AbciMessage(
                performative=AbciMessage.Performative.REQUEST_BEGIN_BLOCK,
                # skip content: hash
                header=header,
                last_commit_info=last_commit_info,
                byzantine_validators=evidences,
            ),
            AbciMessage(
                performative=AbciMessage.Performative.REQUEST_CHECK_TX,
                # skip content: tx
                type=CheckTxType(CheckTxTypeEnum.NEW),
            ),
            AbciMessage(
                performative=AbciMessage.Performative.REQUEST_DELIVER_TX,
                # skip content: tx
            ),
            AbciMessage(
                performative=AbciMessage.Performative.REQUEST_END_BLOCK,
                # skip content: height
            ),
            AbciMessage(
                performative=AbciMessage.Performative.REQUEST_OFFER_SNAPSHOT,
                # skip content: snapshot
                app_hash=b"some_bytes",
            ),
            AbciMessage(
                performative=AbciMessage.Performative.REQUEST_LOAD_SNAPSHOT_CHUNK,
                # skip content: height
                format=12,
                chunk_index=12,
            ),
            AbciMessage(
                performative=AbciMessage.Performative.REQUEST_APPLY_SNAPSHOT_CHUNK,
                # skip content: index
                chunk=b"some_bytes",
                chunk_sender="some str",
            ),
            AbciMessage(
                performative=AbciMessage.Performative.RESPONSE_EXCEPTION,
                # skip content: error
            ),
            AbciMessage(
                performative=AbciMessage.Performative.RESPONSE_ECHO,
                # skip content: message
            ),
            AbciMessage(
                performative=AbciMessage.Performative.RESPONSE_INFO,
                # skip content: info_data
                version="some str",
                app_version=12,
                last_block_height=12,
                last_block_app_hash=b"some_bytes",
            ),
            AbciMessage(
                performative=AbciMessage.Performative.RESPONSE_SET_OPTION,
                # skip content: code
                log="some str",
                info="some str",
            ),
            AbciMessage(
                performative=AbciMessage.Performative.RESPONSE_INIT_CHAIN,
                # skip content: consensus_params, validators
                app_hash=b"some_bytes",
            ),
            AbciMessage(
                performative=AbciMessage.Performative.RESPONSE_QUERY,
                # skip content: code
                log="some str",
                info="some str",
                index=12,
                key=b"some_bytes",
                value=b"some_bytes",
                proof_ops=proof_ops,
                height=12,
                codespace="some str",
            ),
            AbciMessage(
                performative=AbciMessage.Performative.RESPONSE_BEGIN_BLOCK,
                # skip content: events
            ),
            AbciMessage(
                performative=AbciMessage.Performative.RESPONSE_CHECK_TX,
                # skip content: code
                data=b"some_bytes",
                log="some str",
                info="some str",
                gas_wanted=12,
                gas_used=12,
                events=events,
                codespace="some str",
            ),
            AbciMessage(
                performative=AbciMessage.Performative.RESPONSE_DELIVER_TX,
                # skip content: code
                data=b"some_bytes",
                log="some str",
                info="some str",
                gas_wanted=12,
                gas_used=12,
                events=events,
                codespace="some str",
            ),
            AbciMessage(
                performative=AbciMessage.Performative.RESPONSE_END_BLOCK,
                # skip content: validator_updates
                consensus_param_updates=consensus_params,
                events=events,
            ),
            AbciMessage(
                performative=AbciMessage.Performative.RESPONSE_COMMIT,
                # skip content: data
                retain_height=12,
            ),
            AbciMessage(
                performative=AbciMessage.Performative.RESPONSE_LIST_SNAPSHOTS,
                # skip content: snapshots
            ),
            AbciMessage(
                performative=AbciMessage.Performative.RESPONSE_OFFER_SNAPSHOT,
                # skip content: result
            ),
            AbciMessage(
                performative=AbciMessage.Performative.RESPONSE_LOAD_SNAPSHOT_CHUNK,
                # skip content: chunk
            ),
            AbciMessage(
                performative=AbciMessage.Performative.RESPONSE_APPLY_SNAPSHOT_CHUNK,
                # skip content: result
                refetch_chunks=(12,),
                reject_senders=("some str",),
            ),
            AbciMessage(
                performative=AbciMessage.Performative.DUMMY,
                # skip content: dummy_consensus_params
            ),
        ]
