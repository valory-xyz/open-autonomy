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

"""
This module contains the classes required for abci dialogue management.

- AbciDialogue: The dialogue class maintains state of a dialogue and manages it.
- AbciDialogues: The dialogues class keeps track of all dialogues.
"""

from abc import ABC
from typing import Callable, Dict, FrozenSet, Type, cast

from aea.common import Address
from aea.protocols.base import Message
from aea.protocols.dialogue.base import Dialogue, DialogueLabel, Dialogues

from packages.valory.protocols.abci.message import AbciMessage


class AbciDialogue(Dialogue):
    """The abci dialogue class maintains state of a dialogue and manages it."""

    INITIAL_PERFORMATIVES: FrozenSet[Message.Performative] = frozenset(
        {
            AbciMessage.Performative.REQUEST_ECHO,
            AbciMessage.Performative.REQUEST_FLUSH,
            AbciMessage.Performative.REQUEST_INFO,
            AbciMessage.Performative.REQUEST_SET_OPTION,
            AbciMessage.Performative.REQUEST_INIT_CHAIN,
            AbciMessage.Performative.REQUEST_QUERY,
            AbciMessage.Performative.REQUEST_BEGIN_BLOCK,
            AbciMessage.Performative.REQUEST_CHECK_TX,
            AbciMessage.Performative.REQUEST_DELIVER_TX,
            AbciMessage.Performative.REQUEST_END_BLOCK,
            AbciMessage.Performative.REQUEST_COMMIT,
            AbciMessage.Performative.REQUEST_LIST_SNAPSHOTS,
            AbciMessage.Performative.REQUEST_OFFER_SNAPSHOT,
            AbciMessage.Performative.REQUEST_APPLY_SNAPSHOT_CHUNK,
            AbciMessage.Performative.REQUEST_LOAD_SNAPSHOT_CHUNK,
            AbciMessage.Performative.DUMMY,
        }
    )
    TERMINAL_PERFORMATIVES: FrozenSet[Message.Performative] = frozenset(
        {
            AbciMessage.Performative.RESPONSE_EXCEPTION,
            AbciMessage.Performative.RESPONSE_ECHO,
            AbciMessage.Performative.RESPONSE_FLUSH,
            AbciMessage.Performative.RESPONSE_INFO,
            AbciMessage.Performative.RESPONSE_SET_OPTION,
            AbciMessage.Performative.RESPONSE_INIT_CHAIN,
            AbciMessage.Performative.RESPONSE_QUERY,
            AbciMessage.Performative.RESPONSE_BEGIN_BLOCK,
            AbciMessage.Performative.RESPONSE_CHECK_TX,
            AbciMessage.Performative.RESPONSE_DELIVER_TX,
            AbciMessage.Performative.RESPONSE_END_BLOCK,
            AbciMessage.Performative.RESPONSE_COMMIT,
            AbciMessage.Performative.RESPONSE_LIST_SNAPSHOTS,
            AbciMessage.Performative.RESPONSE_OFFER_SNAPSHOT,
            AbciMessage.Performative.RESPONSE_APPLY_SNAPSHOT_CHUNK,
            AbciMessage.Performative.RESPONSE_LOAD_SNAPSHOT_CHUNK,
            AbciMessage.Performative.DUMMY,
        }
    )
    VALID_REPLIES: Dict[Message.Performative, FrozenSet[Message.Performative]] = {
        AbciMessage.Performative.DUMMY: frozenset(),
        AbciMessage.Performative.REQUEST_APPLY_SNAPSHOT_CHUNK: frozenset(
            {
                AbciMessage.Performative.RESPONSE_APPLY_SNAPSHOT_CHUNK,
                AbciMessage.Performative.RESPONSE_EXCEPTION,
            }
        ),
        AbciMessage.Performative.REQUEST_BEGIN_BLOCK: frozenset(
            {
                AbciMessage.Performative.RESPONSE_BEGIN_BLOCK,
                AbciMessage.Performative.RESPONSE_EXCEPTION,
            }
        ),
        AbciMessage.Performative.REQUEST_CHECK_TX: frozenset(
            {
                AbciMessage.Performative.RESPONSE_CHECK_TX,
                AbciMessage.Performative.RESPONSE_EXCEPTION,
            }
        ),
        AbciMessage.Performative.REQUEST_COMMIT: frozenset(
            {
                AbciMessage.Performative.RESPONSE_COMMIT,
                AbciMessage.Performative.RESPONSE_EXCEPTION,
            }
        ),
        AbciMessage.Performative.REQUEST_DELIVER_TX: frozenset(
            {
                AbciMessage.Performative.RESPONSE_DELIVER_TX,
                AbciMessage.Performative.RESPONSE_EXCEPTION,
            }
        ),
        AbciMessage.Performative.REQUEST_ECHO: frozenset(
            {
                AbciMessage.Performative.RESPONSE_ECHO,
                AbciMessage.Performative.RESPONSE_EXCEPTION,
            }
        ),
        AbciMessage.Performative.REQUEST_END_BLOCK: frozenset(
            {
                AbciMessage.Performative.RESPONSE_END_BLOCK,
                AbciMessage.Performative.RESPONSE_EXCEPTION,
            }
        ),
        AbciMessage.Performative.REQUEST_FLUSH: frozenset(
            {
                AbciMessage.Performative.RESPONSE_FLUSH,
                AbciMessage.Performative.RESPONSE_EXCEPTION,
            }
        ),
        AbciMessage.Performative.REQUEST_INFO: frozenset(
            {
                AbciMessage.Performative.RESPONSE_INFO,
                AbciMessage.Performative.RESPONSE_EXCEPTION,
            }
        ),
        AbciMessage.Performative.REQUEST_INIT_CHAIN: frozenset(
            {
                AbciMessage.Performative.RESPONSE_INIT_CHAIN,
                AbciMessage.Performative.RESPONSE_EXCEPTION,
            }
        ),
        AbciMessage.Performative.REQUEST_LIST_SNAPSHOTS: frozenset(
            {
                AbciMessage.Performative.RESPONSE_LIST_SNAPSHOTS,
                AbciMessage.Performative.RESPONSE_EXCEPTION,
            }
        ),
        AbciMessage.Performative.REQUEST_LOAD_SNAPSHOT_CHUNK: frozenset(
            {
                AbciMessage.Performative.RESPONSE_LOAD_SNAPSHOT_CHUNK,
                AbciMessage.Performative.RESPONSE_EXCEPTION,
            }
        ),
        AbciMessage.Performative.REQUEST_OFFER_SNAPSHOT: frozenset(
            {
                AbciMessage.Performative.RESPONSE_OFFER_SNAPSHOT,
                AbciMessage.Performative.RESPONSE_EXCEPTION,
            }
        ),
        AbciMessage.Performative.REQUEST_QUERY: frozenset(
            {
                AbciMessage.Performative.RESPONSE_QUERY,
                AbciMessage.Performative.RESPONSE_EXCEPTION,
            }
        ),
        AbciMessage.Performative.REQUEST_SET_OPTION: frozenset(
            {
                AbciMessage.Performative.RESPONSE_SET_OPTION,
                AbciMessage.Performative.RESPONSE_EXCEPTION,
            }
        ),
        AbciMessage.Performative.RESPONSE_APPLY_SNAPSHOT_CHUNK: frozenset(),
        AbciMessage.Performative.RESPONSE_BEGIN_BLOCK: frozenset(),
        AbciMessage.Performative.RESPONSE_CHECK_TX: frozenset(),
        AbciMessage.Performative.RESPONSE_COMMIT: frozenset(),
        AbciMessage.Performative.RESPONSE_DELIVER_TX: frozenset(),
        AbciMessage.Performative.RESPONSE_ECHO: frozenset(),
        AbciMessage.Performative.RESPONSE_END_BLOCK: frozenset(),
        AbciMessage.Performative.RESPONSE_EXCEPTION: frozenset(),
        AbciMessage.Performative.RESPONSE_FLUSH: frozenset(),
        AbciMessage.Performative.RESPONSE_INFO: frozenset(),
        AbciMessage.Performative.RESPONSE_INIT_CHAIN: frozenset(),
        AbciMessage.Performative.RESPONSE_LIST_SNAPSHOTS: frozenset(),
        AbciMessage.Performative.RESPONSE_LOAD_SNAPSHOT_CHUNK: frozenset(),
        AbciMessage.Performative.RESPONSE_OFFER_SNAPSHOT: frozenset(),
        AbciMessage.Performative.RESPONSE_QUERY: frozenset(),
        AbciMessage.Performative.RESPONSE_SET_OPTION: frozenset(),
    }

    class Role(Dialogue.Role):
        """This class defines the agent's role in a abci dialogue."""

        CLIENT = "client"
        SERVER = "server"

    class EndState(Dialogue.EndState):
        """This class defines the end states of a abci dialogue."""

        SUCCESSFUL = 0

    def __init__(
        self,
        dialogue_label: DialogueLabel,
        self_address: Address,
        role: Dialogue.Role,
        message_class: Type[AbciMessage] = AbciMessage,
    ) -> None:
        """
        Initialize a dialogue.

        :param dialogue_label: the identifier of the dialogue
        :param self_address: the address of the entity for whom this dialogue is maintained
        :param role: the role of the agent this dialogue is maintained for
        :param message_class: the message class used
        """
        Dialogue.__init__(
            self,
            dialogue_label=dialogue_label,
            message_class=message_class,
            self_address=self_address,
            role=role,
        )


class AbciDialogues(Dialogues, ABC):
    """This class keeps track of all abci dialogues."""

    END_STATES = frozenset({AbciDialogue.EndState.SUCCESSFUL})

    _keep_terminal_state_dialogues = False

    def __init__(
        self,
        self_address: Address,
        role_from_first_message: Callable[[Message, Address], Dialogue.Role],
        dialogue_class: Type[AbciDialogue] = AbciDialogue,
    ) -> None:
        """
        Initialize dialogues.

        :param self_address: the address of the entity for whom dialogues are maintained
        :param dialogue_class: the dialogue class used
        :param role_from_first_message: the callable determining role from first message
        """
        Dialogues.__init__(
            self,
            self_address=self_address,
            end_states=cast(FrozenSet[Dialogue.EndState], self.END_STATES),
            message_class=AbciMessage,
            dialogue_class=dialogue_class,
            role_from_first_message=role_from_first_message,
        )
