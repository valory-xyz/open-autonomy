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

"""Tests package for the 'valory/abci' protocol."""
from abc import abstractmethod

from packages.valory.protocols.abci import AbciMessage
from packages.valory.protocols.abci.custom_types import (
    BlockID,
    BlockParams,
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
    Timestamp,
    Validator,
    ValidatorParams,
    ValidatorUpdate,
    ValidatorUpdates,
    VersionParams,
    VoteInfo,
)


class BaseTestMessageConstruction:
    """Base class to test message construction for the ABCI protocol."""

    @abstractmethod
    def build_message(self) -> AbciMessage:
        """Build the message to be used for testing."""

    def test_run(self):
        """Run the test."""
        actual_message = self.build_message()
        expected_message = actual_message.decode(actual_message.encode())
        assert expected_message == actual_message


class TestRequestEcho(BaseTestMessageConstruction):
    """Test ABCI request echo."""

    def build_message(self):
        """Build the message."""
        return AbciMessage(
            performative=AbciMessage.Performative.REQUEST_ECHO, message="hello"
        )


class TestResponseEcho(BaseTestMessageConstruction):
    """Test ABCI response echo."""

    def build_message(self):
        """Build the message."""
        return AbciMessage(
            performative=AbciMessage.Performative.RESPONSE_ECHO, message="hello"
        )


class TestRequestFlush(BaseTestMessageConstruction):
    """Test ABCI request flush."""

    def build_message(self) -> AbciMessage:
        """Build the message."""
        return AbciMessage(
            performative=AbciMessage.Performative.REQUEST_FLUSH,
        )


class TestResponseFlush(BaseTestMessageConstruction):
    """Test ABCI response flush."""

    def build_message(self) -> AbciMessage:
        """Build the message."""
        return AbciMessage(
            performative=AbciMessage.Performative.RESPONSE_FLUSH,
        )


class TestRequestInfo(BaseTestMessageConstruction):
    """Test ABCI request info."""

    def build_message(self) -> AbciMessage:
        """Build the message."""
        return AbciMessage(
            performative=AbciMessage.Performative.REQUEST_INFO,
            version="0.1.0",
            block_version=1,
            p2p_version=1,
        )


class TestResponseInfo(BaseTestMessageConstruction):
    """Test ABCI response info."""

    def build_message(self) -> AbciMessage:
        """Build the message."""
        return AbciMessage(
            performative=AbciMessage.Performative.RESPONSE_INFO,
            info_data="info",
            version="0.1.0",
            app_version=1,
            last_block_height=1,
            last_block_app_hash=b"bytes",
        )


class TestRequestInitChain(BaseTestMessageConstruction):
    """Test ABCI request init chain."""

    def build_message(self) -> AbciMessage:
        """Build the message."""
        consensus_params = ConsensusParams(
            BlockParams(0, 0),
            EvidenceParams(0, Duration(0, 0), 0),
            ValidatorParams(["pub_key"]),
            VersionParams(0),
        )

        validators = ValidatorUpdates(
            [
                ValidatorUpdate(b"pub_key_bytes", 1),
                ValidatorUpdate(b"pub_key_bytes", 2),
            ]
        )

        return AbciMessage(
            performative=AbciMessage.Performative.REQUEST_INIT_CHAIN,
            time=Timestamp(0, 0),
            chain_id="1",
            consensus_params=consensus_params,
            validators=validators,
            app_state_bytes=b"bytes",
            initial_height="height",
        )


class TestResponseInitChain(BaseTestMessageConstruction):
    """Test ABCI response init chain."""

    def build_message(self) -> AbciMessage:
        """Build the message."""
        consensus_params = ConsensusParams(
            BlockParams(0, 0),
            EvidenceParams(0, Duration(0, 0), 0),
            ValidatorParams(["pub_key"]),
            VersionParams(0),
        )

        validators = ValidatorUpdates(
            [
                ValidatorUpdate(b"pub_key_bytes", 1),
                ValidatorUpdate(b"pub_key_bytes", 2),
            ]
        )

        return AbciMessage(
            performative=AbciMessage.Performative.RESPONSE_INIT_CHAIN,
            consensus_params=consensus_params,
            validators=validators,
            app_hash=b"app_hash",
        )


class TestRequestQuery(BaseTestMessageConstruction):
    """Test ABCI response query."""

    def build_message(self) -> AbciMessage:
        """Build the message."""
        return AbciMessage(
            performative=AbciMessage.Performative.REQUEST_QUERY,
            query_data=b"bytes",
            path="",
            height=0,
            prove=False,
        )


class TestResponseQuery(BaseTestMessageConstruction):
    """Test ABCI response query."""

    def build_message(self) -> AbciMessage:
        """Build the message."""
        return AbciMessage(
            performative=AbciMessage.Performative.RESPONSE_QUERY,
            code=0,
            log="log",
            info="info",
            index=0,
            key=b"key",
            value=b"value",
            proof_ops=ProofOps(
                [
                    ProofOp("type", b"key", b"data"),
                    ProofOp("type", b"key", b"data"),
                ]
            ),
            height=0,
            codespace="",
        )


class TestRequestBeginBlock(BaseTestMessageConstruction):
    """Test ABCI request begin block."""

    def build_message(self) -> AbciMessage:
        """Build the message."""
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
        )

        validator = Validator(b"address", 0)
        last_commit_info = LastCommitInfo(
            0,
            [
                VoteInfo(validator, True),
                VoteInfo(validator, False),
            ],
        )

        evidences = Evidences(
            [
                Evidence(EvidenceType.UNKNOWN, validator, 0, Timestamp(0, 0), 0),
                Evidence(EvidenceType.DUPLICATE_VOTE, validator, 0, Timestamp(0, 0), 0),
            ]
        )

        return AbciMessage(
            performative=AbciMessage.Performative.REQUEST_BEGIN_BLOCK,
            hash=b"hash",
            header=header,
            last_commit_info=last_commit_info,
            byzantine_validators=evidences,
        )


class TestResponseBeginBlock(BaseTestMessageConstruction):
    """Test ABCI response begin block."""

    def build_message(self) -> AbciMessage:
        """Build the message."""
        event = Event("type", [EventAttribute(b"key", b"value", True)])
        return AbciMessage(
            performative=AbciMessage.Performative.RESPONSE_BEGIN_BLOCK,
            events=Events([event, event]),
        )
