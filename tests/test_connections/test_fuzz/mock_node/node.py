#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2022 Valory AG
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
"""Used for mocking a tendermint node"""
# flake8: noqa:D102

import logging
from typing import List, Tuple

from aea.exceptions import enforce
from google.protobuf import timestamp_pb2

import packages.valory.connections.abci.tendermint.abci.types_pb2 as abci_types  # type: ignore
import packages.valory.connections.abci.tendermint.crypto.keys_pb2 as keys_types  # type: ignore
import packages.valory.connections.abci.tendermint.types.types_pb2 as tendermint_types  # type: ignore
import packages.valory.connections.abci.tendermint.version.types_pb2 as version_type  # type: ignore
from packages.valory.protocols.abci.custom_types import (
    BlockParams,
    ConsensusParams,
    Duration,
    EvidenceParams,
    PublicKey,
    Snapshot,
    Timestamp,
    ValidatorParams,
    ValidatorUpdate,
    VersionParams,
)

from .channels.base import BaseChannel


_default_logger = logging.getLogger(__name__)

logging.basicConfig()


class MockNode:
    """Mocks a Tendermint Node"""

    def __init__(self, channel: BaseChannel) -> None:
        self.logger = _default_logger
        self.logger.setLevel(logging.DEBUG)

        enforce(channel is not None, "channel is None")

        self.channel = channel

    def connect(self) -> None:
        """Connect the node."""
        self.channel.connect()

    def disconnect(self) -> None:
        """Disconnect the node."""
        self.channel.disconnect()

    def info(self, version: str, block_version: int, p2p_version: int) -> bool:
        request = abci_types.RequestInfo()
        request.version = version
        request.block_version = block_version
        request.p2p_version = p2p_version

        self.logger.info(
            f"Calling info with version={version}, block_version={block_version}, p2p_version={p2p_version}"
        )

        response = self.channel.send_info(request)

        self.logger.info(f"Received response {str(response)}")

        return True

    def echo(self, message: str) -> bool:
        request = abci_types.RequestEcho()
        request.message = message

        self.logger.info(f"Calling echo with message={message}")

        response = self.channel.send_echo(request)

        self.logger.info(f"Received response {str(response)}")
        return True

    def flush(self) -> bool:
        request = abci_types.RequestFlush()

        self.logger.info("Sending flush req")

        response = self.channel.send_flush(request)

        self.logger.info(f"Received response {str(response)}")

        return True

    def set_option(self, key: str, value: str) -> bool:
        request = abci_types.RequestSetOption()
        request.key = key
        request.value = value

        self.logger.info(f"Calling set_options with key={key} value={value}")

        response = self.channel.send_set_option(request)

        self.logger.info(f"Received response {str(response)}")

        return True

    def deliver_tx(self, tx: bytes) -> bool:
        request = abci_types.RequestDeliverTx()
        request.tx = tx

        self.logger.info(f"Calling deliver_tx with tx={tx!r}")

        response = self.channel.send_deliver_tx(request)

        self.logger.info(f"Received response {str(response)}")

        return True

    def check_tx(self, tx: bytes, is_new_check: bool) -> bool:
        request = abci_types.RequestCheckTx()
        request.tx = tx
        request.type = 1 if is_new_check else 0

        self.logger.info(f"Calling check_tx with tx={tx!r} and is_new={is_new_check}")

        response = self.channel.send_check_tx(request)

        self.logger.info(f"Received response {str(response)}")

        return response

    def query(self, data: bytes, path: str, height: int, prove: bool) -> bool:
        request = abci_types.RequestQuery()
        request.data = data
        request.path = path
        request.height = height
        request.prove = prove

        self.logger.info(
            f"Calling query with data={data!r} and path={path} height={height} prove={prove}"
        )

        response = self.channel.send_query(request)

        self.logger.info(f"Received response {str(response)}")

        return True

    def commit(self) -> bool:
        request = abci_types.RequestCommit()

        self.logger.info("Calling commit")

        response = self.channel.send_commit(request)

        self.logger.info(f"Received response {str(response)}")

        return True

    def init_chain(
        self,
        time_seconds: int,
        time_nanos: int,
        chain_id: str,
        block_max_bytes: int,
        block_max_gas: int,
        evidence_max_age_num_blocks: int,
        evidence_max_age_seconds: int,
        evidence_max_age_nanos: int,
        evidence_max_bytes: int,
        pub_key_types: List[str],
        app_version: int,
        validator_pub_keys: List[Tuple[bytes, str]],
        validator_power: List[int],
        app_state_bytes: bytes,
        initial_height: int,
    ) -> bool:
        request = abci_types.RequestInitChain()

        timestamp = timestamp_pb2.Timestamp()
        Timestamp.encode(timestamp, Timestamp(time_seconds, time_nanos))
        request.time.CopyFrom(timestamp)

        request.chain_id = chain_id

        block_params = BlockParams(block_max_bytes, block_max_gas)
        duration = Duration(evidence_max_age_seconds, evidence_max_age_nanos)
        evidence_params = EvidenceParams(
            evidence_max_age_num_blocks, duration, evidence_max_bytes
        )
        validator_params = ValidatorParams(pub_key_types)
        version_params = VersionParams(app_version)
        consensus_params = abci_types.ConsensusParams()
        ConsensusParams.encode(
            consensus_params,
            ConsensusParams(
                block_params, evidence_params, validator_params, version_params
            ),
        )
        request.consensus_params.CopyFrom(consensus_params)

        enforce(
            validator_pub_keys.__len__() == validator_power.__len__(),
            "pubkeys should have same length as power",
        )

        pub_keys = [
            PublicKey(bs, PublicKey.PublicKeyType(tp)) for bs, tp in validator_pub_keys
        ]
        validator_updates = [
            ValidatorUpdate(pk, vp) for pk, vp in zip(pub_keys, validator_power)
        ]
        validator_updates_pb = []

        for validator_update_object in validator_updates:
            validator_update_protobuf_object = abci_types.ValidatorUpdate()
            pub_key = keys_types.PublicKey()

            PublicKey.encode(pub_key, validator_update_object.pub_key)
            validator_update_protobuf_object.power = validator_update_object.power
            validator_update_protobuf_object.pub_key.CopyFrom(pub_key)

            validator_updates_pb.append(validator_update_protobuf_object)

        request.validators.extend(validator_updates_pb)

        request.app_state_bytes = app_state_bytes
        request.initial_height = initial_height

        self.logger.info(
            f"""Calling init_chain
                time_seconds={time_seconds}
                time_nanos={time_nanos}
                chain_id={chain_id}
                block_max_bytes={block_max_bytes}
                block_max_gas={block_max_gas}
                evidence_max_age_num_blocks={evidence_max_age_num_blocks}
                evidence_max_age_seconds={evidence_max_age_seconds}
                evidence_max_age_nanos={evidence_max_age_nanos}
                evidence_max_bytes={evidence_max_bytes}
                pub_key_types={pub_key_types}
                app_version={app_version}
                validator_pub_keys={validator_pub_keys}
                validator_power={validator_power}
                app_state_bytes={app_state_bytes!r}
                initial_height={initial_height}
            """
        )

        response = self.channel.send_init_chain(request)

        self.logger.info(f"Received response {str(response)}")

        return True

    def begin_block(
        self,
        hash_: bytes,
        consen_ver_block: int,
        consen_ver_app: int,
        chain_id: str,
        height: int,
        time_seconds: int,
        time_nanos: int,
        last_block_id_hash: bytes,
        last_commit_hash: bytes,
        data_hash: bytes,
        validators_hash: bytes,
        next_validators_hash: bytes,
        next_validators_part_header_total: int,
        next_validators_part_header_hash: bytes,
        header_consensus_hash: bytes,
        header_app_hash: bytes,
        header_last_results_hash: bytes,
        header_evidence_hash: bytes,
        header_proposer_address: bytes,
        last_commit_round: int,
        last_commit_info_votes: List[Tuple[bytes, int]],
        last_commit_info_signed_last_block: List[bool],
        evidence_type: List[int],
        evidence_validator_address: List[bytes],
        evidence_validator_power: List[int],
        evidence_height: List[int],
        evidence_time_seconds: List[int],
        evidence_time_nanos: List[int],
        evidence_total_voting_power: List[int],
    ) -> bool:
        consensus_version = version_type.Consensus()
        consensus_version.block = consen_ver_block
        consensus_version.app = consen_ver_app

        part_set_header = tendermint_types.PartSetHeader()
        part_set_header.total = next_validators_part_header_total
        part_set_header.hash = next_validators_part_header_hash

        block_id = tendermint_types.BlockID()
        block_id.hash = last_block_id_hash
        block_id.part_set_header.CopyFrom(part_set_header)

        time = timestamp_pb2.Timestamp()
        time.seconds = time_seconds
        time.nanos = time_nanos

        header = tendermint_types.Header()
        header.version.CopyFrom(consensus_version)
        header.chain_id = chain_id
        header.height = height
        header.time.CopyFrom(time)
        header.last_block_id.CopyFrom(block_id)
        header.last_commit_hash = last_commit_hash
        header.data_hash = data_hash
        header.validators_hash = validators_hash
        header.next_validators_hash = next_validators_hash
        header.consensus_hash = header_consensus_hash
        header.app_hash = header_app_hash
        header.last_results_hash = header_last_results_hash
        header.evidence_hash = header_evidence_hash
        header.proposer_address = header_proposer_address

        enforce(
            last_commit_info_signed_last_block.__len__()
            == last_commit_info_signed_last_block.__len__(),
            "last_commit_info_signed_last_block should have same length last_commit_info_signed_last_block",
        )

        vote_infos = []
        for i in range(last_commit_info_votes.__len__()):
            validator = abci_types.Validator()
            validator.address = last_commit_info_votes[i][0]
            validator.power = last_commit_info_votes[i][1]

            vote_info = abci_types.VoteInfo()
            vote_info.validator.CopyFrom(validator)
            vote_info.signed_last_block = last_commit_info_signed_last_block[i]

            vote_infos.append(vote_info)

        last_commit_info = abci_types.LastCommitInfo()
        last_commit_info.round = last_commit_round
        last_commit_info.votes.extend(vote_infos)

        enforce(
            {
                evidence_validator_address.__len__(),
                evidence_validator_power.__len__(),
                evidence_height.__len__(),
                evidence_time_seconds.__len__(),
                evidence_time_nanos.__len__(),
                evidence_total_voting_power.__len__(),
                evidence_type.__len__(),
            }.__len__()
            == 1,
            "evidence_* lists should have same length",
        )

        evidences = []

        for i in range(evidence_type.__len__()):
            validator = abci_types.Validator()
            validator.address = evidence_validator_address[i]
            validator.power = evidence_validator_power[i]

            time = timestamp_pb2.Timestamp()
            time.seconds = evidence_time_seconds[i]
            time.nanos = evidence_time_nanos[i]

            evidence = abci_types.Evidence()
            evidence.type = evidence_type[i] % 3
            evidence.height = evidence_height[i]
            evidence.total_voting_power = evidence_total_voting_power[i]
            evidence.time.CopyFrom(time)
            evidence.validator.CopyFrom(validator)

            evidences.append(evidence)

        request = abci_types.RequestBeginBlock()
        request.hash = hash_
        request.header.CopyFrom(header)
        request.last_commit_info.CopyFrom(last_commit_info)
        request.byzantine_validators.extend(evidences)

        self.logger.info(
            f"""
            Calling begin_block
            hash_: {hash_!r}
            consen_ver_block={consen_ver_block}
            consen_ver_app={consen_ver_app}
            chain_id={chain_id}
            height={height}
            time_seconds={time_seconds}"
            time_nanos={time_nanos}
            last_block_id_hash={last_block_id_hash!r}
            last_commit_hash={last_commit_hash!r}
            data_hash={data_hash!r}
            validators_hash={validators_hash!r}"
            next_validators_hash={next_validators_hash!r}
            next_validators_part_header_total={next_validators_part_header_total}
            next_validators_part_header_hash={next_validators_part_header_hash!r}
            header_consensus_hash={header_consensus_hash!r}
            header_app_hash={header_app_hash!r}
            header_last_results_hash={header_last_results_hash!r}
            header_evidence_hash={header_evidence_hash!r}
            header_proposer_address={header_proposer_address!r}
            last_commit_round={last_commit_round}
            last_commit_info_votes={last_commit_info_votes}
            last_commit_info_signed_last_block={last_commit_info_signed_last_block}
            evidence_type={evidence_type}
            evidence_validator_address={evidence_validator_address}
            evidence_validator_power={evidence_validator_power}
            evidence_height={evidence_height}
            evidence_time_seconds={evidence_time_seconds}
            evidence_time_nanos={evidence_time_nanos}
            evidence_total_voting_power={evidence_total_voting_power}
            """
        )

        response = self.channel.send_begin_block(request)

        self.logger.info(f"Received response {str(response)}")

        return True

    def end_block(self, height: int) -> bool:
        request = abci_types.RequestEndBlock()
        request.height = height

        self.logger.info(f"Calling end_block height={height}")

        response = self.channel.send_end_block(request)

        self.logger.info(f"Received response {str(response)}")

        return response

    def list_snapshots(self) -> bool:
        request = abci_types.RequestListSnapshots()

        self.logger.info("Calling list snapshots")

        response = self.channel.send_list_snapshots(request)

        self.logger.info(f"Received response {str(response)}")

        return response

    def offer_snapshot(
        self,
        height: int,
        format_: int,
        chunks: int,
        hash_: bytes,
        metadata: bytes,
        app_hash: bytes,
    ) -> bool:
        snapshot = abci_types.Snapshot()
        Snapshot.encode(snapshot, Snapshot(height, format_, chunks, hash_, metadata))

        request = abci_types.RequestOfferSnapshot()
        request.snapshot.CopyFrom(snapshot)
        request.app_hash = app_hash

        self.logger.info(
            f"Calling offer snapshot height={height},format_={format_},"
            f"chunks={chunks},hash_={hash_!r},metadata={metadata!r},app_hash={app_hash!r}"
        )

        response = self.channel.send_offer_snapshot(request)

        self.logger.info(f"Received response {str(response)}")

        return response

    def load_snapshot_chunk(self, height: int, format_: int, chunk: int) -> bool:
        request = abci_types.RequestLoadSnapshotChunk()
        request.height = height
        request.format = format_
        request.chunk = chunk

        self.logger.info(
            f"Calling load snapshot chunk height={height} format={format_} chunk={chunk}"
        )

        response = self.channel.send_load_snapshot_chunk(request)

        self.logger.info(f"Received response {str(response)}")

        return response

    def apply_snapshot_chunk(self, index: int, chunk: bytes, sender: str) -> bool:
        request = abci_types.RequestApplySnapshotChunk()
        request.index = index
        request.chunk = chunk
        request.sender = sender

        self.logger.info(
            f"Calling load snapshot chunk index={index} chunk={chunk!r} sender={sender}"
        )

        response = self.channel.send_apply_snapshot_chunk(request)

        self.logger.info(f"Received response {str(response)}")

        return response
