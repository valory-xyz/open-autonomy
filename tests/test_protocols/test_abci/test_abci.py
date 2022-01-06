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
import datetime
from abc import abstractmethod
from typing import Callable, Type
from unittest import mock

import pytest
from aea.common import Address
from aea.exceptions import AEAEnforceError
from aea.mail.base import Envelope
from aea.protocols.base import Message
from aea.protocols.dialogue.base import Dialogue as BaseDialogue
from aea.protocols.dialogue.base import DialogueLabel

import packages
from packages.valory.protocols.abci import AbciMessage
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
from packages.valory.protocols.abci.dialogues import AbciDialogue, AbciDialogues
from packages.valory.protocols.abci.message import (
    _default_logger as abci_message_logger,
)


class BaseTestMessageConstruction:
    """Base class to test message construction for the ABCI protocol."""

    @abstractmethod
    def build_message(self) -> AbciMessage:
        """Build the message to be used for testing."""

    def test_run(self) -> None:
        """Run the test."""
        msg = self.build_message()
        msg.to = "receiver"
        envelope = Envelope(to=msg.to, sender="sender", message=msg)
        envelope_bytes = envelope.encode()

        actual_envelope = Envelope.decode(envelope_bytes)
        expected_envelope = envelope

        assert expected_envelope.to == actual_envelope.to
        assert expected_envelope.sender == actual_envelope.sender
        assert (
            expected_envelope.protocol_specification_id
            == actual_envelope.protocol_specification_id
        )
        assert expected_envelope.message != actual_envelope.message

        actual_msg = AbciMessage.serializer.decode(actual_envelope.message_bytes)
        actual_msg.to = actual_envelope.to
        actual_msg.sender = actual_envelope.sender
        expected_msg = msg
        assert expected_msg == actual_msg

    @classmethod
    def _make_consensus_params(cls) -> ConsensusParams:
        """Build a ConsensuParams object."""
        return ConsensusParams(
            BlockParams(0, 0),
            EvidenceParams(0, Duration(0, 0), 0),
            ValidatorParams(["pub_key"]),
            VersionParams(0),
        )

    @classmethod
    def _make_snapshot(cls) -> Snapshot:
        """Build a Snapshot object."""
        return Snapshot(0, 0, 0, b"hash", b"metadata")


class TestRequestEcho(BaseTestMessageConstruction):
    """Test ABCI request abci."""

    def build_message(self) -> AbciMessage:
        """Build the message."""
        return AbciMessage(
            performative=AbciMessage.Performative.REQUEST_ECHO,  # type: ignore
            message="hello",
        )


class TestResponseEcho(BaseTestMessageConstruction):
    """Test ABCI response abci."""

    def build_message(self) -> AbciMessage:
        """Build the message."""
        return AbciMessage(
            performative=AbciMessage.Performative.RESPONSE_ECHO,  # type: ignore
            message="hello",
        )


class TestRequestFlush(BaseTestMessageConstruction):
    """Test ABCI request flush."""

    def build_message(self) -> AbciMessage:
        """Build the message."""
        return AbciMessage(
            performative=AbciMessage.Performative.REQUEST_FLUSH,  # type: ignore
        )


class TestResponseFlush(BaseTestMessageConstruction):
    """Test ABCI response flush."""

    def build_message(self) -> AbciMessage:
        """Build the message."""
        return AbciMessage(
            performative=AbciMessage.Performative.RESPONSE_FLUSH,  # type: ignore
        )


class TestRequestInfo(BaseTestMessageConstruction):
    """Test ABCI request info."""

    def build_message(self) -> AbciMessage:
        """Build the message."""
        return AbciMessage(
            performative=AbciMessage.Performative.REQUEST_INFO,  # type: ignore
            version="0.1.0",
            block_version=1,
            p2p_version=1,
        )


class TestResponseInfo(BaseTestMessageConstruction):
    """Test ABCI response info."""

    def build_message(self) -> AbciMessage:
        """Build the message."""
        return AbciMessage(
            performative=AbciMessage.Performative.RESPONSE_INFO,  # type: ignore
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
        consensus_params = super()._make_consensus_params()

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

        return AbciMessage(
            performative=AbciMessage.Performative.REQUEST_INIT_CHAIN,  # type: ignore
            time=Timestamp(0, 0),
            chain_id="1",
            consensus_params=consensus_params,
            validators=validators,
            app_state_bytes=b"bytes",
            initial_height=0,
        )


class TestResponseInitChain(BaseTestMessageConstruction):
    """Test ABCI response init chain."""

    def build_message(self) -> AbciMessage:
        """Build the message."""
        consensus_params = super()._make_consensus_params()

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

        return AbciMessage(
            performative=AbciMessage.Performative.RESPONSE_INIT_CHAIN,  # type: ignore
            consensus_params=consensus_params,
            validators=validators,
            app_hash=b"app_hash",
        )


class TestRequestQuery(BaseTestMessageConstruction):
    """Test ABCI response query."""

    def build_message(self) -> AbciMessage:
        """Build the message."""
        return AbciMessage(
            performative=AbciMessage.Performative.REQUEST_QUERY,  # type: ignore
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
            performative=AbciMessage.Performative.RESPONSE_QUERY,  # type: ignore
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
            b"evidence_hash",
            b"proposer_address",
        )

        assert header.timestamp == datetime.datetime.fromtimestamp(0)

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
            performative=AbciMessage.Performative.REQUEST_BEGIN_BLOCK,  # type: ignore
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
            performative=AbciMessage.Performative.RESPONSE_BEGIN_BLOCK,  # type: ignore
            events=Events([event, event]),
        )


class TestRequestCheckTx(BaseTestMessageConstruction):
    """Test ABCI request check tx."""

    def build_message(self) -> AbciMessage:
        """Build the message."""
        tx = b"bytes"
        type_ = CheckTxType(CheckTxTypeEnum.NEW)
        return AbciMessage(
            performative=AbciMessage.Performative.REQUEST_CHECK_TX,  # type: ignore
            tx=tx,
            type=type_,
        )


class TestResponseCheckTx(BaseTestMessageConstruction):
    """Test ABCI response check tx."""

    def build_message(self) -> AbciMessage:
        """Build the message."""
        attribute = EventAttribute(b"key", b"value", True)
        event = Event("type", attributes=[attribute, attribute])
        return AbciMessage(
            performative=AbciMessage.Performative.RESPONSE_CHECK_TX,  # type: ignore
            code=0,
            data=b"data",
            log="log",
            info="info",
            gas_wanted=0,
            gas_used=0,
            events=Events([event, event]),
            codespace="codespace",
        )


class TestRequestDeliverTx(BaseTestMessageConstruction):
    """Test ABCI request deliver tx."""

    def build_message(self) -> AbciMessage:
        """Build the message."""
        return AbciMessage(
            performative=AbciMessage.Performative.REQUEST_DELIVER_TX,  # type: ignore
            tx=b"tx",
        )


class TestResponseDeliverTx(BaseTestMessageConstruction):
    """Test ABCI response deliver tx."""

    def build_message(self) -> AbciMessage:
        """Build the message."""
        attribute = EventAttribute(b"key", b"value", True)
        event = Event("type", attributes=[attribute, attribute])
        return AbciMessage(
            performative=AbciMessage.Performative.RESPONSE_DELIVER_TX,  # type: ignore
            code=0,
            data=b"data",
            log="log",
            info="info",
            gas_wanted=0,
            gas_used=0,
            events=Events([event, event]),
            codespace="codespace",
        )


class TestRequestEndBlock(BaseTestMessageConstruction):
    """Test ABCI request end block."""

    def build_message(self) -> AbciMessage:
        """Build the message."""
        return AbciMessage(
            performative=AbciMessage.Performative.REQUEST_END_BLOCK,  # type: ignore
            height=0,
        )


class TestRequestSetOption(BaseTestMessageConstruction):
    """Test ABCI request end block."""

    def build_message(self) -> AbciMessage:
        """Build the message."""
        return AbciMessage(
            performative=AbciMessage.Performative.REQUEST_SET_OPTION,  # type: ignore
            option_key="",
            option_value="",
        )


class TestResponseEndBlock(BaseTestMessageConstruction):
    """Test ABCI response end block."""

    def build_message(self) -> AbciMessage:
        """Build the message."""
        attribute = EventAttribute(b"key", b"value", True)
        event = Event("type", attributes=[attribute, attribute])
        return AbciMessage(
            performative=AbciMessage.Performative.RESPONSE_END_BLOCK,  # type: ignore
            validator_updates=ValidatorUpdates(
                [
                    ValidatorUpdate(
                        PublicKey(b"pub_key_bytes", PublicKey.PublicKeyType.ed25519), 1
                    ),
                    ValidatorUpdate(
                        PublicKey(b"pub_key_bytes", PublicKey.PublicKeyType.secp256k1),
                        2,
                    ),
                ]
            ),
            consensus_param_updates=super()._make_consensus_params(),
            events=Events([event, event]),
        )


class TestRequestCommit(BaseTestMessageConstruction):
    """Test ABCI request commit."""

    def build_message(self) -> AbciMessage:
        """Build the message."""
        return AbciMessage(
            performative=AbciMessage.Performative.REQUEST_COMMIT,  # type: ignore
        )


class TestResponseCommit(BaseTestMessageConstruction):
    """Test ABCI response commit."""

    def build_message(self) -> AbciMessage:
        """Build the message."""
        return AbciMessage(
            performative=AbciMessage.Performative.RESPONSE_COMMIT,  # type: ignore
            data=b"bytes",
            retain_height=0,
        )


class TestRequestListSnapshots(BaseTestMessageConstruction):
    """Test ABCI request list snapshots."""

    def build_message(self) -> AbciMessage:
        """Build the message."""
        return AbciMessage(
            performative=AbciMessage.Performative.REQUEST_LIST_SNAPSHOTS,  # type: ignore
        )


class TestResponseListSnapshots(BaseTestMessageConstruction):
    """Test ABCI response list snapshots."""

    def build_message(self) -> AbciMessage:
        """Build the message."""
        snapshots = SnapShots(
            [
                super()._make_snapshot(),
                super()._make_snapshot(),
            ]
        )
        return AbciMessage(
            performative=AbciMessage.Performative.RESPONSE_LIST_SNAPSHOTS,  # type: ignore
            snapshots=snapshots,
        )


class TestRequestOfferSnapshot(BaseTestMessageConstruction):
    """Test ABCI request offer snapshot."""

    def build_message(self) -> AbciMessage:
        """Build the message."""
        return AbciMessage(
            performative=AbciMessage.Performative.REQUEST_OFFER_SNAPSHOT,  # type: ignore
            snapshot=super()._make_snapshot(),
            app_hash=b"app_hash",
        )


class TestResponseOfferSnapshot(BaseTestMessageConstruction):
    """Test ABCI response offer snapshot."""

    def build_message(self) -> AbciMessage:
        """Build the message."""
        return AbciMessage(
            performative=AbciMessage.Performative.RESPONSE_OFFER_SNAPSHOT,  # type: ignore
            result=Result(ResultType.UNKNOWN),
        )


class TestRequestLoadSnapshotChunk(BaseTestMessageConstruction):
    """Test ABCI request load snapshot chunk."""

    def build_message(self) -> AbciMessage:
        """Build the message."""
        return AbciMessage(
            performative=AbciMessage.Performative.REQUEST_LOAD_SNAPSHOT_CHUNK,  # type: ignore
            height=0,
            format=0,
            chunk_index=0,
        )


class TestResponseLoadSnapshotChunk(BaseTestMessageConstruction):
    """Test ABCI response load snapshot chunk."""

    def build_message(self) -> AbciMessage:
        """Build the message."""
        return AbciMessage(
            performative=AbciMessage.Performative.RESPONSE_LOAD_SNAPSHOT_CHUNK,  # type: ignore
            chunk=b"chunk",
        )


class TestRequestApplySnapshotChunk(BaseTestMessageConstruction):
    """Test ABCI request load snapshot chunk."""

    def build_message(self) -> AbciMessage:
        """Build the message."""
        return AbciMessage(
            performative=AbciMessage.Performative.REQUEST_APPLY_SNAPSHOT_CHUNK,  # type: ignore
            index=0,
            chunk=b"chunk",
            chunk_sender="sender",
        )


class TestResponseApplySnapshotChunk(BaseTestMessageConstruction):
    """Test ABCI response apply snapshot chunk."""

    def build_message(self) -> AbciMessage:
        """Build the message."""
        return AbciMessage(
            performative=AbciMessage.Performative.RESPONSE_APPLY_SNAPSHOT_CHUNK,  # type: ignore
            result=Result(ResultType.REJECT),
            refetch_chunks=(0, 1, 2),
            reject_senders=("sender_1", "sender_2"),
        )


class TestDummy(BaseTestMessageConstruction):
    """Test ABCI request abci."""

    def build_message(self) -> AbciMessage:
        """Build the message."""
        return AbciMessage(
            performative=AbciMessage.Performative.DUMMY,  # type: ignore
            dummy_consensus_params=self._make_consensus_params(),
        )


class TestResponseException(BaseTestMessageConstruction):
    """Test ABCI request abci."""

    def build_message(self) -> AbciMessage:
        """Build the message."""
        return AbciMessage(
            performative=AbciMessage.Performative.RESPONSE_EXCEPTION, error=""  # type: ignore
        )


class TestResponseSetOption(BaseTestMessageConstruction):
    """Test ABCI request end block."""

    def build_message(self) -> AbciMessage:
        """Build the message."""
        return AbciMessage(
            performative=AbciMessage.Performative.RESPONSE_SET_OPTION,  # type: ignore
            code=1,
            log="",
            info="",
        )


@mock.patch.object(
    packages.valory.protocols.abci.message,
    "enforce",
    side_effect=AEAEnforceError("some error"),
)
def test_incorrect_message(mocked_enforce: Callable) -> None:
    """Test that we raise an exception when the message is incorrect."""
    with mock.patch.object(abci_message_logger, "error") as mock_logger:
        AbciMessage(
            message_id=1,
            dialogue_reference=(str(0), ""),
            target=0,
            performative=AbciMessage.Performative.DUMMY,  # type: ignore
        )

        mock_logger.assert_any_call("some error")


def test_performative_string_value() -> None:
    """Test the string valoe of performatives."""

    assert str(AbciMessage.Performative.DUMMY) == "dummy", "The str value must be dummy"
    assert (
        str(AbciMessage.Performative.REQUEST_APPLY_SNAPSHOT_CHUNK)
        == "request_apply_snapshot_chunk"
    ), "The str value must be request_apply_snapshot_chunk"
    assert (
        str(AbciMessage.Performative.REQUEST_BEGIN_BLOCK) == "request_begin_block"
    ), "The str value must be request_begin_block"
    assert (
        str(AbciMessage.Performative.REQUEST_CHECK_TX) == "request_check_tx"
    ), "The str value must be request_check_tx"
    assert (
        str(AbciMessage.Performative.REQUEST_COMMIT) == "request_commit"
    ), "The str value must be request_commit"
    assert (
        str(AbciMessage.Performative.REQUEST_DELIVER_TX) == "request_deliver_tx"
    ), "The str value must be request_deliver_tx"
    assert (
        str(AbciMessage.Performative.REQUEST_ECHO) == "request_echo"
    ), "The str value must be request_echo"
    assert (
        str(AbciMessage.Performative.REQUEST_END_BLOCK) == "request_end_block"
    ), "The str value must be request_end_block"
    assert (
        str(AbciMessage.Performative.REQUEST_FLUSH) == "request_flush"
    ), "The str value must be request_flush"
    assert (
        str(AbciMessage.Performative.REQUEST_INFO) == "request_info"
    ), "The str value must be request_info"
    assert (
        str(AbciMessage.Performative.REQUEST_INIT_CHAIN) == "request_init_chain"
    ), "The str value must be request_init_chain"
    assert (
        str(AbciMessage.Performative.REQUEST_LIST_SNAPSHOTS) == "request_list_snapshots"
    ), "The str value must be request_list_snapshots"
    assert (
        str(AbciMessage.Performative.REQUEST_LOAD_SNAPSHOT_CHUNK)
        == "request_load_snapshot_chunk"
    ), "The str value must be request_load_snapshot_chunk"
    assert (
        str(AbciMessage.Performative.REQUEST_OFFER_SNAPSHOT) == "request_offer_snapshot"
    ), "The str value must be request_offer_snapshot"
    assert (
        str(AbciMessage.Performative.REQUEST_QUERY) == "request_query"
    ), "The str value must be request_query"
    assert (
        str(AbciMessage.Performative.RESPONSE_APPLY_SNAPSHOT_CHUNK)
        == "response_apply_snapshot_chunk"
    ), "The str value must be response_apply_snapshot_chunk"
    assert (
        str(AbciMessage.Performative.RESPONSE_BEGIN_BLOCK) == "response_begin_block"
    ), "The str value must be response_begin_block"
    assert (
        str(AbciMessage.Performative.RESPONSE_CHECK_TX) == "response_check_tx"
    ), "The str value must be response_check_tx"
    assert (
        str(AbciMessage.Performative.RESPONSE_COMMIT) == "response_commit"
    ), "The str value must be response_commit"
    assert (
        str(AbciMessage.Performative.RESPONSE_DELIVER_TX) == "response_deliver_tx"
    ), "The str value must be response_deliver_tx"
    assert (
        str(AbciMessage.Performative.RESPONSE_ECHO) == "response_echo"
    ), "The str value must be response_echo"
    assert (
        str(AbciMessage.Performative.RESPONSE_END_BLOCK) == "response_end_block"
    ), "The str value must be response_end_block"
    assert (
        str(AbciMessage.Performative.RESPONSE_EXCEPTION) == "response_exception"
    ), "The str value must be response_exception"
    assert (
        str(AbciMessage.Performative.RESPONSE_FLUSH) == "response_flush"
    ), "The str value must be response_flush"
    assert (
        str(AbciMessage.Performative.RESPONSE_INFO) == "response_info"
    ), "The str value must be response_info"
    assert (
        str(AbciMessage.Performative.RESPONSE_INIT_CHAIN) == "response_init_chain"
    ), "The str value must be response_init_chain"
    assert (
        str(AbciMessage.Performative.RESPONSE_LIST_SNAPSHOTS)
        == "response_list_snapshots"
    ), "The str value must be response_list_snapshots"
    assert (
        str(AbciMessage.Performative.RESPONSE_LOAD_SNAPSHOT_CHUNK)
        == "response_load_snapshot_chunk"
    ), "The str value must be response_load_snapshot_chunk"
    assert (
        str(AbciMessage.Performative.RESPONSE_OFFER_SNAPSHOT)
        == "response_offer_snapshot"
    ), "The str value must be response_offer_snapshot"
    assert (
        str(AbciMessage.Performative.RESPONSE_QUERY) == "response_query"
    ), "The str value must be response_query"
    assert (
        str(AbciMessage.Performative.RESPONSE_SET_OPTION) == "response_set_option"
    ), "The str value must be response_set_option"
    assert (
        str(AbciMessage.Performative.REQUEST_SET_OPTION) == "request_set_option"
    ), "The str value must be request_set_option"


def test_encoding_unknown_performative() -> None:
    """Test that we raise an exception when the performative is unknown during encoding."""
    msg = AbciMessage(
        performative=AbciMessage.Performative.REQUEST_ECHO, message="Hello"  # type: ignore
    )

    with pytest.raises(ValueError, match="Performative not valid:"):
        with mock.patch.object(AbciMessage.Performative, "__eq__", return_value=False):
            AbciMessage.serializer.encode(msg)


def test_decoding_unknown_performative() -> None:
    """Test that we raise an exception when the performative is unknown during encoding."""
    msg = AbciMessage(
        performative=AbciMessage.Performative.REQUEST_ECHO, message="Hello"  # type: ignore
    )

    encoded_msg = AbciMessage.serializer.encode(msg)
    with pytest.raises(ValueError, match="Performative not valid:"):
        with mock.patch.object(AbciMessage.Performative, "__eq__", return_value=False):
            AbciMessage.serializer.decode(encoded_msg)


class AgentDialogue(AbciDialogue):
    """The dialogue class maintains state of a dialogue and manages it."""

    def __init__(
        self,
        dialogue_label: DialogueLabel,
        self_address: Address,
        role: BaseDialogue.Role,
        message_class: Type[AbciMessage],
    ) -> None:
        """
        Initialize a dialogue.

        :param dialogue_label: the identifier of the dialogue
        :param self_address: the address of the entity for whom this dialogue is maintained
        :param role: the role of the agent this dialogue is maintained for
        :param message_class: the message class
        """
        AbciDialogue.__init__(
            self,
            dialogue_label=dialogue_label,
            self_address=self_address,
            role=role,
            message_class=message_class,
        )


class AgentDialogues(AbciDialogues):
    """The dialogues class keeps track of all dialogues."""

    def __init__(self, self_address: Address) -> None:
        """
        Initialize dialogues.

        :param self_address: the address of the entity for whom this dialogue is maintained
        """

        def role_from_first_message(  # pylint: disable=unused-argument
            message: Message, receiver_address: Address
        ) -> BaseDialogue.Role:
            """Infer the role of the agent from an incoming/outgoing first message

            :param message: an incoming/outgoing first message
            :param receiver_address: the address of the receiving agent
            :return: The role of the agent
            """
            return AbciDialogue.Role.CLIENT

        AbciDialogues.__init__(
            self,
            self_address=self_address,
            role_from_first_message=role_from_first_message,
            dialogue_class=AgentDialogue,
        )


class ServerDialogue(AbciDialogue):
    """The dialogue class maintains state of a dialogue and manages it."""

    def __init__(
        self,
        dialogue_label: DialogueLabel,
        self_address: Address,
        role: BaseDialogue.Role,
        message_class: Type[AbciMessage],
    ) -> None:
        """
        Initialize a dialogue.

        :param dialogue_label: the identifier of the dialogue
        :param self_address: the address of the entity for whom this dialogue is maintained
        :param role: the role of the agent this dialogue is maintained for
        :param message_class: the message class
        """
        AbciDialogue.__init__(
            self,
            dialogue_label=dialogue_label,
            self_address=self_address,
            role=role,
            message_class=message_class,
        )


class ServerDialogues(AbciDialogues):
    """The dialogues class keeps track of all dialogues."""

    def __init__(self, self_address: Address) -> None:
        """
        Initialize dialogues.

        :param self_address: the address of the entity for whom this dialogue is maintained
        """

        def role_from_first_message(  # pylint: disable=unused-argument
            message: Message, receiver_address: Address
        ) -> BaseDialogue.Role:
            """Infer the role of the agent from an incoming/outgoing first message

            :param message: an incoming/outgoing first message
            :param receiver_address: the address of the receiving agent
            :return: The role of the agent
            """
            return AbciDialogue.Role.SERVER

        AbciDialogues.__init__(
            self,
            self_address=self_address,
            role_from_first_message=role_from_first_message,
            dialogue_class=ServerDialogue,
        )


class TestDialogues:
    """Tests abci dialogues."""

    agent_addr: str
    server_addr: str
    agent_dialogues: AgentDialogues
    server_dialogues: ServerDialogues

    @classmethod
    def setup_class(cls) -> None:
        """Set up the test."""
        cls.agent_addr = "agent address"
        cls.server_addr = "server address"
        cls.agent_dialogues = AgentDialogues(cls.agent_addr)
        cls.server_dialogues = ServerDialogues(cls.server_addr)

    def test_create_self_initiated(self) -> None:
        """Test the self initialisation of a dialogue."""
        result = self.agent_dialogues._create_self_initiated(
            dialogue_opponent_addr=self.server_addr,
            dialogue_reference=(str(0), ""),
            role=AbciDialogue.Role.CLIENT,
        )
        assert isinstance(result, AbciDialogue)
        assert result.role == AbciDialogue.Role.CLIENT, "The role must be client."

    def test_create_opponent_initiated(self) -> None:
        """Test the opponent initialisation of a dialogue."""
        result = self.agent_dialogues._create_opponent_initiated(
            dialogue_opponent_addr=self.server_addr,
            dialogue_reference=(str(0), ""),
            role=AbciDialogue.Role.CLIENT,
        )
        assert isinstance(result, AbciDialogue)
        assert result.role == AbciDialogue.Role.CLIENT, "The role must be client."
