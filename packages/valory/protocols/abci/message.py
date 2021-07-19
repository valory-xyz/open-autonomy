# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021 valory
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
from typing import Any, Set, Tuple, cast

from aea.configurations.base import PublicId
from aea.exceptions import AEAEnforceError, enforce
from aea.protocols.base import Message

from packages.valory.protocols.abci.custom_types import Timestamp as CustomTimestamp


_default_logger = logging.getLogger("aea.packages.valory.protocols.abci.message")

DEFAULT_BODY_SIZE = 4


class AbciMessage(Message):
    """A protocol for ABCI requests and responses."""

    protocol_id = PublicId.from_str("valory/abci:0.1.0")
    protocol_specification_id = PublicId.from_str("valory/abci:0.1.0")

    Timestamp = CustomTimestamp

    class Performative(Message.Performative):
        """Performatives for the abci protocol."""

        REQUEST_ECHO = "request_echo"
        REQUEST_FLUSH = "request_flush"
        REQUEST_INFO = "request_info"
        REQUEST_INIT_CHAIN = "request_init_chain"
        RESPONSE_ECHO = "response_echo"
        RESPONSE_EXCEPTION = "response_exception"
        RESPONSE_FLUSH = "response_flush"
        RESPONSE_INFO = "response_info"
        RESPONSE_INIT_CHAIN = "response_init_chain"

        def __str__(self) -> str:
            """Get the string representation."""
            return str(self.value)

    _performatives = {
        "request_echo",
        "request_flush",
        "request_info",
        "request_init_chain",
        "response_echo",
        "response_exception",
        "response_flush",
        "response_info",
        "response_init_chain",
    }
    __slots__: Tuple[str, ...] = tuple()

    class _SlotsCls:
        __slots__ = (
            "app_version",
            "block_version",
            "data",
            "dialogue_reference",
            "last_block_app_hash",
            "last_block_height",
            "message",
            "message_id",
            "p2p_version",
            "performative",
            "target",
            "time",
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
    def data(self) -> str:
        """Get the 'data' content from the message."""
        enforce(self.is_set("data"), "'data' content is not set.")
        return cast(str, self.get("data"))

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
    def message(self) -> str:
        """Get the 'message' content from the message."""
        enforce(self.is_set("message"), "'message' content is not set.")
        return cast(str, self.get("message"))

    @property
    def p2p_version(self) -> int:
        """Get the 'p2p_version' content from the message."""
        enforce(self.is_set("p2p_version"), "'p2p_version' content is not set.")
        return cast(int, self.get("p2p_version"))

    @property
    def time(self) -> CustomTimestamp:
        """Get the 'time' content from the message."""
        enforce(self.is_set("time"), "'time' content is not set.")
        return cast(CustomTimestamp, self.get("time"))

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
            elif self.performative == AbciMessage.Performative.REQUEST_INIT_CHAIN:
                expected_nb_of_contents = 1
                enforce(
                    isinstance(self.time, CustomTimestamp),
                    "Invalid type for content 'time'. Expected 'Timestamp'. Found '{}'.".format(
                        type(self.time)
                    ),
                )
            elif self.performative == AbciMessage.Performative.RESPONSE_EXCEPTION:
                expected_nb_of_contents = 0
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
                    isinstance(self.data, str),
                    "Invalid type for content 'data'. Expected 'str'. Found '{}'.".format(
                        type(self.data)
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
            elif self.performative == AbciMessage.Performative.RESPONSE_INIT_CHAIN:
                expected_nb_of_contents = 0

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
