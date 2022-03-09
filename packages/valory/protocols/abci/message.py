# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 valory
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

"""This module contains abci's message definition."""

# pylint: disable=too-many-statements,too-many-locals,no-member,too-few-public-methods,too-many-branches,not-an-iterable,unidiomatic-typecheck,unsubscriptable-object
import logging
from typing import Any, Optional, Set, Tuple, cast

from aea.configurations.base import PublicId
from aea.exceptions import AEAEnforceError, enforce
from aea.protocols.base import Message

from packages.valory.protocols.abci.custom_types import CheckTxType as CustomCheckTxType
from packages.valory.protocols.abci.custom_types import (
    ConsensusParams as CustomConsensusParams,
)
from packages.valory.protocols.abci.custom_types import Events as CustomEvents
from packages.valory.protocols.abci.custom_types import Evidences as CustomEvidences
from packages.valory.protocols.abci.custom_types import Header as CustomHeader
from packages.valory.protocols.abci.custom_types import (
    LastCommitInfo as CustomLastCommitInfo,
)
from packages.valory.protocols.abci.custom_types import ProofOps as CustomProofOps
from packages.valory.protocols.abci.custom_types import Result as CustomResult
from packages.valory.protocols.abci.custom_types import SnapShots as CustomSnapShots
from packages.valory.protocols.abci.custom_types import Snapshot as CustomSnapshot
from packages.valory.protocols.abci.custom_types import Timestamp as CustomTimestamp
from packages.valory.protocols.abci.custom_types import (
    ValidatorUpdates as CustomValidatorUpdates,
)


_default_logger = logging.getLogger("aea.packages.valory.protocols.abci.message")

DEFAULT_BODY_SIZE = 4


class AbciMessage(Message):
    """A protocol for ABCI requests and responses."""

    protocol_id = PublicId.from_str("valory/abci:0.1.0")
    protocol_specification_id = PublicId.from_str("valory/abci:0.1.0")

    CheckTxType = CustomCheckTxType

    ConsensusParams = CustomConsensusParams

    Events = CustomEvents

    Evidences = CustomEvidences

    Header = CustomHeader

    LastCommitInfo = CustomLastCommitInfo

    ProofOps = CustomProofOps

    Result = CustomResult

    SnapShots = CustomSnapShots

    Snapshot = CustomSnapshot

    Timestamp = CustomTimestamp

    ValidatorUpdates = CustomValidatorUpdates

    class Performative(Message.Performative):
        """Performatives for the abci protocol."""

        DUMMY = "dummy"
        REQUEST_APPLY_SNAPSHOT_CHUNK = "request_apply_snapshot_chunk"
        REQUEST_BEGIN_BLOCK = "request_begin_block"
        REQUEST_CHECK_TX = "request_check_tx"
        REQUEST_COMMIT = "request_commit"
        REQUEST_DELIVER_TX = "request_deliver_tx"
        REQUEST_ECHO = "request_echo"
        REQUEST_END_BLOCK = "request_end_block"
        REQUEST_FLUSH = "request_flush"
        REQUEST_INFO = "request_info"
        REQUEST_INIT_CHAIN = "request_init_chain"
        REQUEST_LIST_SNAPSHOTS = "request_list_snapshots"
        REQUEST_LOAD_SNAPSHOT_CHUNK = "request_load_snapshot_chunk"
        REQUEST_OFFER_SNAPSHOT = "request_offer_snapshot"
        REQUEST_QUERY = "request_query"
        REQUEST_SET_OPTION = "request_set_option"
        RESPONSE_APPLY_SNAPSHOT_CHUNK = "response_apply_snapshot_chunk"
        RESPONSE_BEGIN_BLOCK = "response_begin_block"
        RESPONSE_CHECK_TX = "response_check_tx"
        RESPONSE_COMMIT = "response_commit"
        RESPONSE_DELIVER_TX = "response_deliver_tx"
        RESPONSE_ECHO = "response_echo"
        RESPONSE_END_BLOCK = "response_end_block"
        RESPONSE_EXCEPTION = "response_exception"
        RESPONSE_FLUSH = "response_flush"
        RESPONSE_INFO = "response_info"
        RESPONSE_INIT_CHAIN = "response_init_chain"
        RESPONSE_LIST_SNAPSHOTS = "response_list_snapshots"
        RESPONSE_LOAD_SNAPSHOT_CHUNK = "response_load_snapshot_chunk"
        RESPONSE_OFFER_SNAPSHOT = "response_offer_snapshot"
        RESPONSE_QUERY = "response_query"
        RESPONSE_SET_OPTION = "response_set_option"

        def __str__(self) -> str:
            """Get the string representation."""
            return str(self.value)

    _performatives = {
        "dummy",
        "request_apply_snapshot_chunk",
        "request_begin_block",
        "request_check_tx",
        "request_commit",
        "request_deliver_tx",
        "request_echo",
        "request_end_block",
        "request_flush",
        "request_info",
        "request_init_chain",
        "request_list_snapshots",
        "request_load_snapshot_chunk",
        "request_offer_snapshot",
        "request_query",
        "request_set_option",
        "response_apply_snapshot_chunk",
        "response_begin_block",
        "response_check_tx",
        "response_commit",
        "response_deliver_tx",
        "response_echo",
        "response_end_block",
        "response_exception",
        "response_flush",
        "response_info",
        "response_init_chain",
        "response_list_snapshots",
        "response_load_snapshot_chunk",
        "response_offer_snapshot",
        "response_query",
        "response_set_option",
    }
    __slots__: Tuple[str, ...] = tuple()

    class _SlotsCls:
        __slots__ = (
            "app_hash",
            "app_state_bytes",
            "app_version",
            "block_version",
            "byzantine_validators",
            "chain_id",
            "chunk",
            "chunk_index",
            "chunk_sender",
            "code",
            "codespace",
            "consensus_param_updates",
            "consensus_params",
            "data",
            "dialogue_reference",
            "dummy_consensus_params",
            "error",
            "events",
            "format",
            "gas_used",
            "gas_wanted",
            "hash",
            "header",
            "height",
            "index",
            "info",
            "info_data",
            "initial_height",
            "key",
            "last_block_app_hash",
            "last_block_height",
            "last_commit_info",
            "log",
            "message",
            "message_id",
            "option_key",
            "option_value",
            "p2p_version",
            "path",
            "performative",
            "proof_ops",
            "prove",
            "query_data",
            "refetch_chunks",
            "reject_senders",
            "result",
            "retain_height",
            "snapshot",
            "snapshots",
            "target",
            "time",
            "tx",
            "type",
            "validator_updates",
            "validators",
            "value",
            "version",
        )

    def __init__(
        self,
        performative: Performative,
        dialogue_reference: Tuple[str, str] = ("", ""),
        message_id: int = 1,
        target: int = 0,
        **kwargs: Any,
    ):
        """
        Initialise an instance of AbciMessage.

        :param message_id: the message id.
        :param dialogue_reference: the dialogue reference.
        :param target: the message target.
        :param performative: the message performative.
        :param **kwargs: extra options.
        """
        super().__init__(
            dialogue_reference=dialogue_reference,
            message_id=message_id,
            target=target,
            performative=AbciMessage.Performative(performative),
            **kwargs,
        )

    @property
    def valid_performatives(self) -> Set[str]:
        """Get valid performatives."""
        return self._performatives

    @property
    def dialogue_reference(self) -> Tuple[str, str]:
        """Get the dialogue_reference of the message."""
        enforce(self.is_set("dialogue_reference"), "dialogue_reference is not set.")
        return cast(Tuple[str, str], self.get("dialogue_reference"))

    @property
    def message_id(self) -> int:
        """Get the message_id of the message."""
        enforce(self.is_set("message_id"), "message_id is not set.")
        return cast(int, self.get("message_id"))

    @property
    def performative(self) -> Performative:  # type: ignore # noqa: F821
        """Get the performative of the message."""
        enforce(self.is_set("performative"), "performative is not set.")
        return cast(AbciMessage.Performative, self.get("performative"))

    @property
    def target(self) -> int:
        """Get the target of the message."""
        enforce(self.is_set("target"), "target is not set.")
        return cast(int, self.get("target"))

    @property
    def app_hash(self) -> bytes:
        """Get the 'app_hash' content from the message."""
        enforce(self.is_set("app_hash"), "'app_hash' content is not set.")
        return cast(bytes, self.get("app_hash"))

    @property
    def app_state_bytes(self) -> bytes:
        """Get the 'app_state_bytes' content from the message."""
        enforce(self.is_set("app_state_bytes"), "'app_state_bytes' content is not set.")
        return cast(bytes, self.get("app_state_bytes"))

    @property
    def app_version(self) -> int:
        """Get the 'app_version' content from the message."""
        enforce(self.is_set("app_version"), "'app_version' content is not set.")
        return cast(int, self.get("app_version"))

    @property
    def block_version(self) -> int:
        """Get the 'block_version' content from the message."""
        enforce(self.is_set("block_version"), "'block_version' content is not set.")
        return cast(int, self.get("block_version"))

    @property
    def byzantine_validators(self) -> CustomEvidences:
        """Get the 'byzantine_validators' content from the message."""
        enforce(
            self.is_set("byzantine_validators"),
            "'byzantine_validators' content is not set.",
        )
        return cast(CustomEvidences, self.get("byzantine_validators"))

    @property
    def chain_id(self) -> str:
        """Get the 'chain_id' content from the message."""
        enforce(self.is_set("chain_id"), "'chain_id' content is not set.")
        return cast(str, self.get("chain_id"))

    @property
    def chunk(self) -> bytes:
        """Get the 'chunk' content from the message."""
        enforce(self.is_set("chunk"), "'chunk' content is not set.")
        return cast(bytes, self.get("chunk"))

    @property
    def chunk_index(self) -> int:
        """Get the 'chunk_index' content from the message."""
        enforce(self.is_set("chunk_index"), "'chunk_index' content is not set.")
        return cast(int, self.get("chunk_index"))

    @property
    def chunk_sender(self) -> str:
        """Get the 'chunk_sender' content from the message."""
        enforce(self.is_set("chunk_sender"), "'chunk_sender' content is not set.")
        return cast(str, self.get("chunk_sender"))

    @property
    def code(self) -> int:
        """Get the 'code' content from the message."""
        enforce(self.is_set("code"), "'code' content is not set.")
        return cast(int, self.get("code"))

    @property
    def codespace(self) -> str:
        """Get the 'codespace' content from the message."""
        enforce(self.is_set("codespace"), "'codespace' content is not set.")
        return cast(str, self.get("codespace"))

    @property
    def consensus_param_updates(self) -> Optional[CustomConsensusParams]:
        """Get the 'consensus_param_updates' content from the message."""
        return cast(
            Optional[CustomConsensusParams], self.get("consensus_param_updates")
        )

    @property
    def consensus_params(self) -> Optional[CustomConsensusParams]:
        """Get the 'consensus_params' content from the message."""
        return cast(Optional[CustomConsensusParams], self.get("consensus_params"))

    @property
    def data(self) -> bytes:
        """Get the 'data' content from the message."""
        enforce(self.is_set("data"), "'data' content is not set.")
        return cast(bytes, self.get("data"))

    @property
    def dummy_consensus_params(self) -> CustomConsensusParams:
        """Get the 'dummy_consensus_params' content from the message."""
        enforce(
            self.is_set("dummy_consensus_params"),
            "'dummy_consensus_params' content is not set.",
        )
        return cast(CustomConsensusParams, self.get("dummy_consensus_params"))

    @property
    def error(self) -> str:
        """Get the 'error' content from the message."""
        enforce(self.is_set("error"), "'error' content is not set.")
        return cast(str, self.get("error"))

    @property
    def events(self) -> CustomEvents:
        """Get the 'events' content from the message."""
        enforce(self.is_set("events"), "'events' content is not set.")
        return cast(CustomEvents, self.get("events"))

    @property
    def format(self) -> int:
        """Get the 'format' content from the message."""
        enforce(self.is_set("format"), "'format' content is not set.")
        return cast(int, self.get("format"))

    @property
    def gas_used(self) -> int:
        """Get the 'gas_used' content from the message."""
        enforce(self.is_set("gas_used"), "'gas_used' content is not set.")
        return cast(int, self.get("gas_used"))

    @property
    def gas_wanted(self) -> int:
        """Get the 'gas_wanted' content from the message."""
        enforce(self.is_set("gas_wanted"), "'gas_wanted' content is not set.")
        return cast(int, self.get("gas_wanted"))

    @property
    def hash(self) -> bytes:
        """Get the 'hash' content from the message."""
        enforce(self.is_set("hash"), "'hash' content is not set.")
        return cast(bytes, self.get("hash"))

    @property
    def header(self) -> CustomHeader:
        """Get the 'header' content from the message."""
        enforce(self.is_set("header"), "'header' content is not set.")
        return cast(CustomHeader, self.get("header"))

    @property
    def height(self) -> int:
        """Get the 'height' content from the message."""
        enforce(self.is_set("height"), "'height' content is not set.")
        return cast(int, self.get("height"))

    @property
    def index(self) -> int:
        """Get the 'index' content from the message."""
        enforce(self.is_set("index"), "'index' content is not set.")
        return cast(int, self.get("index"))

    @property
    def info(self) -> str:
        """Get the 'info' content from the message."""
        enforce(self.is_set("info"), "'info' content is not set.")
        return cast(str, self.get("info"))

    @property
    def info_data(self) -> str:
        """Get the 'info_data' content from the message."""
        enforce(self.is_set("info_data"), "'info_data' content is not set.")
        return cast(str, self.get("info_data"))

    @property
    def initial_height(self) -> int:
        """Get the 'initial_height' content from the message."""
        enforce(self.is_set("initial_height"), "'initial_height' content is not set.")
        return cast(int, self.get("initial_height"))

    @property
    def key(self) -> bytes:
        """Get the 'key' content from the message."""
        enforce(self.is_set("key"), "'key' content is not set.")
        return cast(bytes, self.get("key"))

    @property
    def last_block_app_hash(self) -> bytes:
        """Get the 'last_block_app_hash' content from the message."""
        enforce(
            self.is_set("last_block_app_hash"),
            "'last_block_app_hash' content is not set.",
        )
        return cast(bytes, self.get("last_block_app_hash"))

    @property
    def last_block_height(self) -> int:
        """Get the 'last_block_height' content from the message."""
        enforce(
            self.is_set("last_block_height"), "'last_block_height' content is not set."
        )
        return cast(int, self.get("last_block_height"))

    @property
    def last_commit_info(self) -> CustomLastCommitInfo:
        """Get the 'last_commit_info' content from the message."""
        enforce(
            self.is_set("last_commit_info"), "'last_commit_info' content is not set."
        )
        return cast(CustomLastCommitInfo, self.get("last_commit_info"))

    @property
    def log(self) -> str:
        """Get the 'log' content from the message."""
        enforce(self.is_set("log"), "'log' content is not set.")
        return cast(str, self.get("log"))

    @property
    def message(self) -> str:
        """Get the 'message' content from the message."""
        enforce(self.is_set("message"), "'message' content is not set.")
        return cast(str, self.get("message"))

    @property
    def option_key(self) -> str:
        """Get the 'option_key' content from the message."""
        enforce(self.is_set("option_key"), "'option_key' content is not set.")
        return cast(str, self.get("option_key"))

    @property
    def option_value(self) -> str:
        """Get the 'option_value' content from the message."""
        enforce(self.is_set("option_value"), "'option_value' content is not set.")
        return cast(str, self.get("option_value"))

    @property
    def p2p_version(self) -> int:
        """Get the 'p2p_version' content from the message."""
        enforce(self.is_set("p2p_version"), "'p2p_version' content is not set.")
        return cast(int, self.get("p2p_version"))

    @property
    def path(self) -> str:
        """Get the 'path' content from the message."""
        enforce(self.is_set("path"), "'path' content is not set.")
        return cast(str, self.get("path"))

    @property
    def proof_ops(self) -> CustomProofOps:
        """Get the 'proof_ops' content from the message."""
        enforce(self.is_set("proof_ops"), "'proof_ops' content is not set.")
        return cast(CustomProofOps, self.get("proof_ops"))

    @property
    def prove(self) -> bool:
        """Get the 'prove' content from the message."""
        enforce(self.is_set("prove"), "'prove' content is not set.")
        return cast(bool, self.get("prove"))

    @property
    def query_data(self) -> bytes:
        """Get the 'query_data' content from the message."""
        enforce(self.is_set("query_data"), "'query_data' content is not set.")
        return cast(bytes, self.get("query_data"))

    @property
    def refetch_chunks(self) -> Tuple[int, ...]:
        """Get the 'refetch_chunks' content from the message."""
        enforce(self.is_set("refetch_chunks"), "'refetch_chunks' content is not set.")
        return cast(Tuple[int, ...], self.get("refetch_chunks"))

    @property
    def reject_senders(self) -> Tuple[str, ...]:
        """Get the 'reject_senders' content from the message."""
        enforce(self.is_set("reject_senders"), "'reject_senders' content is not set.")
        return cast(Tuple[str, ...], self.get("reject_senders"))

    @property
    def result(self) -> CustomResult:
        """Get the 'result' content from the message."""
        enforce(self.is_set("result"), "'result' content is not set.")
        return cast(CustomResult, self.get("result"))

    @property
    def retain_height(self) -> int:
        """Get the 'retain_height' content from the message."""
        enforce(self.is_set("retain_height"), "'retain_height' content is not set.")
        return cast(int, self.get("retain_height"))

    @property
    def snapshot(self) -> CustomSnapshot:
        """Get the 'snapshot' content from the message."""
        enforce(self.is_set("snapshot"), "'snapshot' content is not set.")
        return cast(CustomSnapshot, self.get("snapshot"))

    @property
    def snapshots(self) -> CustomSnapShots:
        """Get the 'snapshots' content from the message."""
        enforce(self.is_set("snapshots"), "'snapshots' content is not set.")
        return cast(CustomSnapShots, self.get("snapshots"))

    @property
    def time(self) -> CustomTimestamp:
        """Get the 'time' content from the message."""
        enforce(self.is_set("time"), "'time' content is not set.")
        return cast(CustomTimestamp, self.get("time"))

    @property
    def tx(self) -> bytes:
        """Get the 'tx' content from the message."""
        enforce(self.is_set("tx"), "'tx' content is not set.")
        return cast(bytes, self.get("tx"))

    @property
    def type(self) -> CustomCheckTxType:
        """Get the 'type' content from the message."""
        enforce(self.is_set("type"), "'type' content is not set.")
        return cast(CustomCheckTxType, self.get("type"))

    @property
    def validator_updates(self) -> CustomValidatorUpdates:
        """Get the 'validator_updates' content from the message."""
        enforce(
            self.is_set("validator_updates"), "'validator_updates' content is not set."
        )
        return cast(CustomValidatorUpdates, self.get("validator_updates"))

    @property
    def validators(self) -> CustomValidatorUpdates:
        """Get the 'validators' content from the message."""
        enforce(self.is_set("validators"), "'validators' content is not set.")
        return cast(CustomValidatorUpdates, self.get("validators"))

    @property
    def value(self) -> bytes:
        """Get the 'value' content from the message."""
        enforce(self.is_set("value"), "'value' content is not set.")
        return cast(bytes, self.get("value"))

    @property
    def version(self) -> str:
        """Get the 'version' content from the message."""
        enforce(self.is_set("version"), "'version' content is not set.")
        return cast(str, self.get("version"))

    def _is_consistent(self) -> bool:
        """Check that the message follows the abci protocol."""
        try:
            enforce(
                isinstance(self.dialogue_reference, tuple),
                "Invalid type for 'dialogue_reference'. Expected 'tuple'. Found '{}'.".format(
                    type(self.dialogue_reference)
                ),
            )
            enforce(
                isinstance(self.dialogue_reference[0], str),
                "Invalid type for 'dialogue_reference[0]'. Expected 'str'. Found '{}'.".format(
                    type(self.dialogue_reference[0])
                ),
            )
            enforce(
                isinstance(self.dialogue_reference[1], str),
                "Invalid type for 'dialogue_reference[1]'. Expected 'str'. Found '{}'.".format(
                    type(self.dialogue_reference[1])
                ),
            )
            enforce(
                type(self.message_id) is int,
                "Invalid type for 'message_id'. Expected 'int'. Found '{}'.".format(
                    type(self.message_id)
                ),
            )
            enforce(
                type(self.target) is int,
                "Invalid type for 'target'. Expected 'int'. Found '{}'.".format(
                    type(self.target)
                ),
            )

            # Light Protocol Rule 2
            # Check correct performative
            enforce(
                isinstance(self.performative, AbciMessage.Performative),
                "Invalid 'performative'. Expected either of '{}'. Found '{}'.".format(
                    self.valid_performatives, self.performative
                ),
            )

            # Check correct contents
            actual_nb_of_contents = len(self._body) - DEFAULT_BODY_SIZE
            expected_nb_of_contents = 0
            if self.performative == AbciMessage.Performative.REQUEST_ECHO:
                expected_nb_of_contents = 1
                enforce(
                    isinstance(self.message, str),
                    "Invalid type for content 'message'. Expected 'str'. Found '{}'.".format(
                        type(self.message)
                    ),
                )
            elif self.performative == AbciMessage.Performative.REQUEST_FLUSH:
                expected_nb_of_contents = 0
            elif self.performative == AbciMessage.Performative.REQUEST_INFO:
                expected_nb_of_contents = 3
                enforce(
                    isinstance(self.version, str),
                    "Invalid type for content 'version'. Expected 'str'. Found '{}'.".format(
                        type(self.version)
                    ),
                )
                enforce(
                    type(self.block_version) is int,
                    "Invalid type for content 'block_version'. Expected 'int'. Found '{}'.".format(
                        type(self.block_version)
                    ),
                )
                enforce(
                    type(self.p2p_version) is int,
                    "Invalid type for content 'p2p_version'. Expected 'int'. Found '{}'.".format(
                        type(self.p2p_version)
                    ),
                )
            elif self.performative == AbciMessage.Performative.REQUEST_SET_OPTION:
                expected_nb_of_contents = 2
                enforce(
                    isinstance(self.option_key, str),
                    "Invalid type for content 'option_key'. Expected 'str'. Found '{}'.".format(
                        type(self.option_key)
                    ),
                )
                enforce(
                    isinstance(self.option_value, str),
                    "Invalid type for content 'option_value'. Expected 'str'. Found '{}'.".format(
                        type(self.option_value)
                    ),
                )
            elif self.performative == AbciMessage.Performative.REQUEST_INIT_CHAIN:
                expected_nb_of_contents = 5
                enforce(
                    isinstance(self.time, CustomTimestamp),
                    "Invalid type for content 'time'. Expected 'Timestamp'. Found '{}'.".format(
                        type(self.time)
                    ),
                )
                enforce(
                    isinstance(self.chain_id, str),
                    "Invalid type for content 'chain_id'. Expected 'str'. Found '{}'.".format(
                        type(self.chain_id)
                    ),
                )
                if self.is_set("consensus_params"):
                    expected_nb_of_contents += 1
                    consensus_params = cast(
                        CustomConsensusParams, self.consensus_params
                    )
                    enforce(
                        isinstance(consensus_params, CustomConsensusParams),
                        "Invalid type for content 'consensus_params'. Expected 'ConsensusParams'. Found '{}'.".format(
                            type(consensus_params)
                        ),
                    )
                enforce(
                    isinstance(self.validators, CustomValidatorUpdates),
                    "Invalid type for content 'validators'. Expected 'ValidatorUpdates'. Found '{}'.".format(
                        type(self.validators)
                    ),
                )
                enforce(
                    isinstance(self.app_state_bytes, bytes),
                    "Invalid type for content 'app_state_bytes'. Expected 'bytes'. Found '{}'.".format(
                        type(self.app_state_bytes)
                    ),
                )
                enforce(
                    type(self.initial_height) is int,
                    "Invalid type for content 'initial_height'. Expected 'int'. Found '{}'.".format(
                        type(self.initial_height)
                    ),
                )
            elif self.performative == AbciMessage.Performative.REQUEST_QUERY:
                expected_nb_of_contents = 4
                enforce(
                    isinstance(self.query_data, bytes),
                    "Invalid type for content 'query_data'. Expected 'bytes'. Found '{}'.".format(
                        type(self.query_data)
                    ),
                )
                enforce(
                    isinstance(self.path, str),
                    "Invalid type for content 'path'. Expected 'str'. Found '{}'.".format(
                        type(self.path)
                    ),
                )
                enforce(
                    type(self.height) is int,
                    "Invalid type for content 'height'. Expected 'int'. Found '{}'.".format(
                        type(self.height)
                    ),
                )
                enforce(
                    isinstance(self.prove, bool),
                    "Invalid type for content 'prove'. Expected 'bool'. Found '{}'.".format(
                        type(self.prove)
                    ),
                )
            elif self.performative == AbciMessage.Performative.REQUEST_BEGIN_BLOCK:
                expected_nb_of_contents = 4
                enforce(
                    isinstance(self.hash, bytes),
                    "Invalid type for content 'hash'. Expected 'bytes'. Found '{}'.".format(
                        type(self.hash)
                    ),
                )
                enforce(
                    isinstance(self.header, CustomHeader),
                    "Invalid type for content 'header'. Expected 'Header'. Found '{}'.".format(
                        type(self.header)
                    ),
                )
                enforce(
                    isinstance(self.last_commit_info, CustomLastCommitInfo),
                    "Invalid type for content 'last_commit_info'. Expected 'LastCommitInfo'. Found '{}'.".format(
                        type(self.last_commit_info)
                    ),
                )
                enforce(
                    isinstance(self.byzantine_validators, CustomEvidences),
                    "Invalid type for content 'byzantine_validators'. Expected 'Evidences'. Found '{}'.".format(
                        type(self.byzantine_validators)
                    ),
                )
            elif self.performative == AbciMessage.Performative.REQUEST_CHECK_TX:
                expected_nb_of_contents = 2
                enforce(
                    isinstance(self.tx, bytes),
                    "Invalid type for content 'tx'. Expected 'bytes'. Found '{}'.".format(
                        type(self.tx)
                    ),
                )
                enforce(
                    isinstance(self.type, CustomCheckTxType),
                    "Invalid type for content 'type'. Expected 'CheckTxType'. Found '{}'.".format(
                        type(self.type)
                    ),
                )
            elif self.performative == AbciMessage.Performative.REQUEST_DELIVER_TX:
                expected_nb_of_contents = 1
                enforce(
                    isinstance(self.tx, bytes),
                    "Invalid type for content 'tx'. Expected 'bytes'. Found '{}'.".format(
                        type(self.tx)
                    ),
                )
            elif self.performative == AbciMessage.Performative.REQUEST_END_BLOCK:
                expected_nb_of_contents = 1
                enforce(
                    type(self.height) is int,
                    "Invalid type for content 'height'. Expected 'int'. Found '{}'.".format(
                        type(self.height)
                    ),
                )
            elif self.performative == AbciMessage.Performative.REQUEST_COMMIT:
                expected_nb_of_contents = 0
            elif self.performative == AbciMessage.Performative.REQUEST_LIST_SNAPSHOTS:
                expected_nb_of_contents = 0
            elif self.performative == AbciMessage.Performative.REQUEST_OFFER_SNAPSHOT:
                expected_nb_of_contents = 2
                enforce(
                    isinstance(self.snapshot, CustomSnapshot),
                    "Invalid type for content 'snapshot'. Expected 'Snapshot'. Found '{}'.".format(
                        type(self.snapshot)
                    ),
                )
                enforce(
                    isinstance(self.app_hash, bytes),
                    "Invalid type for content 'app_hash'. Expected 'bytes'. Found '{}'.".format(
                        type(self.app_hash)
                    ),
                )
            elif (
                self.performative
                == AbciMessage.Performative.REQUEST_LOAD_SNAPSHOT_CHUNK
            ):
                expected_nb_of_contents = 3
                enforce(
                    type(self.height) is int,
                    "Invalid type for content 'height'. Expected 'int'. Found '{}'.".format(
                        type(self.height)
                    ),
                )
                enforce(
                    type(self.format) is int,
                    "Invalid type for content 'format'. Expected 'int'. Found '{}'.".format(
                        type(self.format)
                    ),
                )
                enforce(
                    type(self.chunk_index) is int,
                    "Invalid type for content 'chunk_index'. Expected 'int'. Found '{}'.".format(
                        type(self.chunk_index)
                    ),
                )
            elif (
                self.performative
                == AbciMessage.Performative.REQUEST_APPLY_SNAPSHOT_CHUNK
            ):
                expected_nb_of_contents = 3
                enforce(
                    type(self.index) is int,
                    "Invalid type for content 'index'. Expected 'int'. Found '{}'.".format(
                        type(self.index)
                    ),
                )
                enforce(
                    isinstance(self.chunk, bytes),
                    "Invalid type for content 'chunk'. Expected 'bytes'. Found '{}'.".format(
                        type(self.chunk)
                    ),
                )
                enforce(
                    isinstance(self.chunk_sender, str),
                    "Invalid type for content 'chunk_sender'. Expected 'str'. Found '{}'.".format(
                        type(self.chunk_sender)
                    ),
                )
            elif self.performative == AbciMessage.Performative.RESPONSE_EXCEPTION:
                expected_nb_of_contents = 1
                enforce(
                    isinstance(self.error, str),
                    "Invalid type for content 'error'. Expected 'str'. Found '{}'.".format(
                        type(self.error)
                    ),
                )
            elif self.performative == AbciMessage.Performative.RESPONSE_ECHO:
                expected_nb_of_contents = 1
                enforce(
                    isinstance(self.message, str),
                    "Invalid type for content 'message'. Expected 'str'. Found '{}'.".format(
                        type(self.message)
                    ),
                )
            elif self.performative == AbciMessage.Performative.RESPONSE_FLUSH:
                expected_nb_of_contents = 0
            elif self.performative == AbciMessage.Performative.RESPONSE_INFO:
                expected_nb_of_contents = 5
                enforce(
                    isinstance(self.info_data, str),
                    "Invalid type for content 'info_data'. Expected 'str'. Found '{}'.".format(
                        type(self.info_data)
                    ),
                )
                enforce(
                    isinstance(self.version, str),
                    "Invalid type for content 'version'. Expected 'str'. Found '{}'.".format(
                        type(self.version)
                    ),
                )
                enforce(
                    type(self.app_version) is int,
                    "Invalid type for content 'app_version'. Expected 'int'. Found '{}'.".format(
                        type(self.app_version)
                    ),
                )
                enforce(
                    type(self.last_block_height) is int,
                    "Invalid type for content 'last_block_height'. Expected 'int'. Found '{}'.".format(
                        type(self.last_block_height)
                    ),
                )
                enforce(
                    isinstance(self.last_block_app_hash, bytes),
                    "Invalid type for content 'last_block_app_hash'. Expected 'bytes'. Found '{}'.".format(
                        type(self.last_block_app_hash)
                    ),
                )
            elif self.performative == AbciMessage.Performative.RESPONSE_SET_OPTION:
                expected_nb_of_contents = 3
                enforce(
                    type(self.code) is int,
                    "Invalid type for content 'code'. Expected 'int'. Found '{}'.".format(
                        type(self.code)
                    ),
                )
                enforce(
                    isinstance(self.log, str),
                    "Invalid type for content 'log'. Expected 'str'. Found '{}'.".format(
                        type(self.log)
                    ),
                )
                enforce(
                    isinstance(self.info, str),
                    "Invalid type for content 'info'. Expected 'str'. Found '{}'.".format(
                        type(self.info)
                    ),
                )
            elif self.performative == AbciMessage.Performative.RESPONSE_INIT_CHAIN:
                expected_nb_of_contents = 2
                if self.is_set("consensus_params"):
                    expected_nb_of_contents += 1
                    consensus_params = cast(
                        CustomConsensusParams, self.consensus_params
                    )
                    enforce(
                        isinstance(consensus_params, CustomConsensusParams),
                        "Invalid type for content 'consensus_params'. Expected 'ConsensusParams'. Found '{}'.".format(
                            type(consensus_params)
                        ),
                    )
                enforce(
                    isinstance(self.validators, CustomValidatorUpdates),
                    "Invalid type for content 'validators'. Expected 'ValidatorUpdates'. Found '{}'.".format(
                        type(self.validators)
                    ),
                )
                enforce(
                    isinstance(self.app_hash, bytes),
                    "Invalid type for content 'app_hash'. Expected 'bytes'. Found '{}'.".format(
                        type(self.app_hash)
                    ),
                )
            elif self.performative == AbciMessage.Performative.RESPONSE_QUERY:
                expected_nb_of_contents = 9
                enforce(
                    type(self.code) is int,
                    "Invalid type for content 'code'. Expected 'int'. Found '{}'.".format(
                        type(self.code)
                    ),
                )
                enforce(
                    isinstance(self.log, str),
                    "Invalid type for content 'log'. Expected 'str'. Found '{}'.".format(
                        type(self.log)
                    ),
                )
                enforce(
                    isinstance(self.info, str),
                    "Invalid type for content 'info'. Expected 'str'. Found '{}'.".format(
                        type(self.info)
                    ),
                )
                enforce(
                    type(self.index) is int,
                    "Invalid type for content 'index'. Expected 'int'. Found '{}'.".format(
                        type(self.index)
                    ),
                )
                enforce(
                    isinstance(self.key, bytes),
                    "Invalid type for content 'key'. Expected 'bytes'. Found '{}'.".format(
                        type(self.key)
                    ),
                )
                enforce(
                    isinstance(self.value, bytes),
                    "Invalid type for content 'value'. Expected 'bytes'. Found '{}'.".format(
                        type(self.value)
                    ),
                )
                enforce(
                    isinstance(self.proof_ops, CustomProofOps),
                    "Invalid type for content 'proof_ops'. Expected 'ProofOps'. Found '{}'.".format(
                        type(self.proof_ops)
                    ),
                )
                enforce(
                    type(self.height) is int,
                    "Invalid type for content 'height'. Expected 'int'. Found '{}'.".format(
                        type(self.height)
                    ),
                )
                enforce(
                    isinstance(self.codespace, str),
                    "Invalid type for content 'codespace'. Expected 'str'. Found '{}'.".format(
                        type(self.codespace)
                    ),
                )
            elif self.performative == AbciMessage.Performative.RESPONSE_BEGIN_BLOCK:
                expected_nb_of_contents = 1
                enforce(
                    isinstance(self.events, CustomEvents),
                    "Invalid type for content 'events'. Expected 'Events'. Found '{}'.".format(
                        type(self.events)
                    ),
                )
            elif self.performative == AbciMessage.Performative.RESPONSE_CHECK_TX:
                expected_nb_of_contents = 8
                enforce(
                    type(self.code) is int,
                    "Invalid type for content 'code'. Expected 'int'. Found '{}'.".format(
                        type(self.code)
                    ),
                )
                enforce(
                    isinstance(self.data, bytes),
                    "Invalid type for content 'data'. Expected 'bytes'. Found '{}'.".format(
                        type(self.data)
                    ),
                )
                enforce(
                    isinstance(self.log, str),
                    "Invalid type for content 'log'. Expected 'str'. Found '{}'.".format(
                        type(self.log)
                    ),
                )
                enforce(
                    isinstance(self.info, str),
                    "Invalid type for content 'info'. Expected 'str'. Found '{}'.".format(
                        type(self.info)
                    ),
                )
                enforce(
                    type(self.gas_wanted) is int,
                    "Invalid type for content 'gas_wanted'. Expected 'int'. Found '{}'.".format(
                        type(self.gas_wanted)
                    ),
                )
                enforce(
                    type(self.gas_used) is int,
                    "Invalid type for content 'gas_used'. Expected 'int'. Found '{}'.".format(
                        type(self.gas_used)
                    ),
                )
                enforce(
                    isinstance(self.events, CustomEvents),
                    "Invalid type for content 'events'. Expected 'Events'. Found '{}'.".format(
                        type(self.events)
                    ),
                )
                enforce(
                    isinstance(self.codespace, str),
                    "Invalid type for content 'codespace'. Expected 'str'. Found '{}'.".format(
                        type(self.codespace)
                    ),
                )
            elif self.performative == AbciMessage.Performative.RESPONSE_DELIVER_TX:
                expected_nb_of_contents = 8
                enforce(
                    type(self.code) is int,
                    "Invalid type for content 'code'. Expected 'int'. Found '{}'.".format(
                        type(self.code)
                    ),
                )
                enforce(
                    isinstance(self.data, bytes),
                    "Invalid type for content 'data'. Expected 'bytes'. Found '{}'.".format(
                        type(self.data)
                    ),
                )
                enforce(
                    isinstance(self.log, str),
                    "Invalid type for content 'log'. Expected 'str'. Found '{}'.".format(
                        type(self.log)
                    ),
                )
                enforce(
                    isinstance(self.info, str),
                    "Invalid type for content 'info'. Expected 'str'. Found '{}'.".format(
                        type(self.info)
                    ),
                )
                enforce(
                    type(self.gas_wanted) is int,
                    "Invalid type for content 'gas_wanted'. Expected 'int'. Found '{}'.".format(
                        type(self.gas_wanted)
                    ),
                )
                enforce(
                    type(self.gas_used) is int,
                    "Invalid type for content 'gas_used'. Expected 'int'. Found '{}'.".format(
                        type(self.gas_used)
                    ),
                )
                enforce(
                    isinstance(self.events, CustomEvents),
                    "Invalid type for content 'events'. Expected 'Events'. Found '{}'.".format(
                        type(self.events)
                    ),
                )
                enforce(
                    isinstance(self.codespace, str),
                    "Invalid type for content 'codespace'. Expected 'str'. Found '{}'.".format(
                        type(self.codespace)
                    ),
                )
            elif self.performative == AbciMessage.Performative.RESPONSE_END_BLOCK:
                expected_nb_of_contents = 2
                enforce(
                    isinstance(self.validator_updates, CustomValidatorUpdates),
                    "Invalid type for content 'validator_updates'. Expected 'ValidatorUpdates'. Found '{}'.".format(
                        type(self.validator_updates)
                    ),
                )
                if self.is_set("consensus_param_updates"):
                    expected_nb_of_contents += 1
                    consensus_param_updates = cast(
                        CustomConsensusParams, self.consensus_param_updates
                    )
                    enforce(
                        isinstance(consensus_param_updates, CustomConsensusParams),
                        "Invalid type for content 'consensus_param_updates'. Expected 'ConsensusParams'. Found '{}'.".format(
                            type(consensus_param_updates)
                        ),
                    )
                enforce(
                    isinstance(self.events, CustomEvents),
                    "Invalid type for content 'events'. Expected 'Events'. Found '{}'.".format(
                        type(self.events)
                    ),
                )
            elif self.performative == AbciMessage.Performative.RESPONSE_COMMIT:
                expected_nb_of_contents = 2
                enforce(
                    isinstance(self.data, bytes),
                    "Invalid type for content 'data'. Expected 'bytes'. Found '{}'.".format(
                        type(self.data)
                    ),
                )
                enforce(
                    type(self.retain_height) is int,
                    "Invalid type for content 'retain_height'. Expected 'int'. Found '{}'.".format(
                        type(self.retain_height)
                    ),
                )
            elif self.performative == AbciMessage.Performative.RESPONSE_LIST_SNAPSHOTS:
                expected_nb_of_contents = 1
                enforce(
                    isinstance(self.snapshots, CustomSnapShots),
                    "Invalid type for content 'snapshots'. Expected 'SnapShots'. Found '{}'.".format(
                        type(self.snapshots)
                    ),
                )
            elif self.performative == AbciMessage.Performative.RESPONSE_OFFER_SNAPSHOT:
                expected_nb_of_contents = 1
                enforce(
                    isinstance(self.result, CustomResult),
                    "Invalid type for content 'result'. Expected 'Result'. Found '{}'.".format(
                        type(self.result)
                    ),
                )
            elif (
                self.performative
                == AbciMessage.Performative.RESPONSE_LOAD_SNAPSHOT_CHUNK
            ):
                expected_nb_of_contents = 1
                enforce(
                    isinstance(self.chunk, bytes),
                    "Invalid type for content 'chunk'. Expected 'bytes'. Found '{}'.".format(
                        type(self.chunk)
                    ),
                )
            elif (
                self.performative
                == AbciMessage.Performative.RESPONSE_APPLY_SNAPSHOT_CHUNK
            ):
                expected_nb_of_contents = 3
                enforce(
                    isinstance(self.result, CustomResult),
                    "Invalid type for content 'result'. Expected 'Result'. Found '{}'.".format(
                        type(self.result)
                    ),
                )
                enforce(
                    isinstance(self.refetch_chunks, tuple),
                    "Invalid type for content 'refetch_chunks'. Expected 'tuple'. Found '{}'.".format(
                        type(self.refetch_chunks)
                    ),
                )
                enforce(
                    all(type(element) is int for element in self.refetch_chunks),
                    "Invalid type for tuple elements in content 'refetch_chunks'. Expected 'int'.",
                )
                enforce(
                    isinstance(self.reject_senders, tuple),
                    "Invalid type for content 'reject_senders'. Expected 'tuple'. Found '{}'.".format(
                        type(self.reject_senders)
                    ),
                )
                enforce(
                    all(isinstance(element, str) for element in self.reject_senders),
                    "Invalid type for tuple elements in content 'reject_senders'. Expected 'str'.",
                )
            elif self.performative == AbciMessage.Performative.DUMMY:
                expected_nb_of_contents = 1
                enforce(
                    isinstance(self.dummy_consensus_params, CustomConsensusParams),
                    "Invalid type for content 'dummy_consensus_params'. Expected 'ConsensusParams'. Found '{}'.".format(
                        type(self.dummy_consensus_params)
                    ),
                )

            # Check correct content count
            enforce(
                expected_nb_of_contents == actual_nb_of_contents,
                "Incorrect number of contents. Expected {}. Found {}".format(
                    expected_nb_of_contents, actual_nb_of_contents
                ),
            )

            # Light Protocol Rule 3
            if self.message_id == 1:
                enforce(
                    self.target == 0,
                    "Invalid 'target'. Expected 0 (because 'message_id' is 1). Found {}.".format(
                        self.target
                    ),
                )
        except (AEAEnforceError, ValueError, KeyError) as e:
            _default_logger.error(str(e))
            return False

        return True
