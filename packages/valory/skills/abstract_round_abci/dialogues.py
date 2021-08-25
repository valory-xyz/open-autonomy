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

"""This module contains the classes required for dialogue management."""

from typing import Any, Optional, Type

from aea.exceptions import enforce
from aea.protocols.base import Address, Message
from aea.protocols.dialogue.base import Dialogue as BaseDialogue
from aea.protocols.dialogue.base import DialogueLabel as BaseDialogueLabel
from aea.skills.base import Model

from packages.fetchai.protocols.http.dialogues import (
    HttpDialogue as BaseHttpDialogue,  # type: ignore # pylint: disable=no-name-in-module,import-error; type: ignore
)
from packages.fetchai.protocols.http.dialogues import (
    HttpDialogues as BaseHttpDialogues,  # type: ignore # pylint: disable=no-name-in-module,import-error; type: ignore
)
from packages.fetchai.protocols.ledger_api import LedgerApiMessage
from packages.fetchai.protocols.ledger_api.dialogues import (
    LedgerApiDialogue as BaseLedgerApiDialogue,
)
from packages.fetchai.protocols.ledger_api.dialogues import (
    LedgerApiDialogues as BaseLedgerApiDialogues,
)
from packages.fetchai.protocols.signing.dialogues import (
    SigningDialogue as BaseSigningDialogue,
)
from packages.fetchai.protocols.signing.dialogues import (
    SigningDialogues as BaseSigningDialogues,
)
from packages.valory.protocols.abci.dialogues import AbciDialogue as BaseAbciDialogue
from packages.valory.protocols.abci.dialogues import AbciDialogues as BaseAbciDialogues


AbciDialogue = BaseAbciDialogue


class AbciDialogues(Model, BaseAbciDialogues):
    """The dialogues class keeps track of all dialogues."""

    def __init__(self, **kwargs: Any) -> None:
        """
        Initialize dialogues.

        :param kwargs: keyword arguments
        """
        Model.__init__(self, **kwargs)

        def role_from_first_message(  # pylint: disable=unused-argument
            message: Message, receiver_address: Address
        ) -> BaseDialogue.Role:
            """Infer the role of the agent from an incoming/outgoing first message

            :param message: an incoming/outgoing first message
            :param receiver_address: the address of the receiving agent
            :return: The role of the agent
            """
            return AbciDialogue.Role.CLIENT

        BaseAbciDialogues.__init__(
            self,
            self_address=str(self.skill_id),
            role_from_first_message=role_from_first_message,
        )


HttpDialogue = BaseHttpDialogue


class HttpDialogues(Model, BaseHttpDialogues):
    """This class keeps track of all http dialogues."""

    def __init__(self, **kwargs: Any) -> None:
        """
        Initialize dialogues.

        :param kwargs: keyword arguments
        """
        Model.__init__(self, **kwargs)

        def role_from_first_message(  # pylint: disable=unused-argument
            message: Message, receiver_address: Address
        ) -> BaseDialogue.Role:
            """Infer the role of the agent from an incoming/outgoing first message

            :param message: an incoming/outgoing first message
            :param receiver_address: the address of the receiving agent
            :return: The role of the agent
            """
            return BaseHttpDialogue.Role.CLIENT

        BaseHttpDialogues.__init__(
            self,
            self_address=str(self.skill_id),
            role_from_first_message=role_from_first_message,
        )


SigningDialogue = BaseSigningDialogue


class SigningDialogues(Model, BaseSigningDialogues):
    """This class keeps track of all signing dialogues."""

    def __init__(self, **kwargs: Any) -> None:
        """
        Initialize dialogues.

        :param kwargs: keyword arguments
        """
        Model.__init__(self, **kwargs)

        def role_from_first_message(  # pylint: disable=unused-argument
            message: Message, receiver_address: Address
        ) -> BaseDialogue.Role:
            """Infer the role of the agent from an incoming/outgoing first message

            :param message: an incoming/outgoing first message
            :param receiver_address: the address of the receiving agent
            :return: The role of the agent
            """
            return BaseSigningDialogue.Role.SKILL

        BaseSigningDialogues.__init__(
            self,
            self_address=str(self.skill_id),
            role_from_first_message=role_from_first_message,
        )


class LedgerApiDialogue(BaseLedgerApiDialogue):
    """The dialogue class maintains state of a dialogue and manages it."""

    __slots__ = ("_associated_signing_dialogue",)

    def __init__(
        self,
        dialogue_label: BaseDialogueLabel,
        self_address: Address,
        role: BaseDialogue.Role,
        message_class: Type[LedgerApiMessage] = LedgerApiMessage,
    ) -> None:
        """
        Initialize a dialogue.

        :param dialogue_label: the identifier of the dialogue
        :param self_address: the address of the entity for whom this dialogue is maintained
        :param role: the role of the agent this dialogue is maintained for
        :param message_class: the message class
        """
        BaseLedgerApiDialogue.__init__(
            self,
            dialogue_label=dialogue_label,
            self_address=self_address,
            role=role,
            message_class=message_class,
        )
        self._associated_signing_dialogue = None  # type: Optional[SigningDialogue]

    @property
    def associated_signing_dialogue(self) -> "SigningDialogue":
        """Get the associated signing dialogue."""
        if self._associated_signing_dialogue is None:
            raise ValueError("Associated signing dialogue not set!")
        return self._associated_signing_dialogue

    @associated_signing_dialogue.setter
    def associated_signing_dialogue(
        self, associated_signing_dialogue: "SigningDialogue"
    ) -> None:
        """Set the associated signing dialogue."""
        enforce(
            self._associated_signing_dialogue is None,
            "Associated signing dialogue already set!",
        )
        self._associated_signing_dialogue = associated_signing_dialogue


class LedgerApiDialogues(Model, BaseLedgerApiDialogues):
    """The dialogues class keeps track of all dialogues."""

    def __init__(self, **kwargs: Any) -> None:
        """
        Initialize dialogues.

        :param kwargs: keyword arguments
        """
        Model.__init__(self, **kwargs)

        def role_from_first_message(  # pylint: disable=unused-argument
            message: Message, receiver_address: Address
        ) -> BaseDialogue.Role:
            """Infer the role of the agent from an incoming/outgoing first message

            :param message: an incoming/outgoing first message
            :param receiver_address: the address of the receiving agent
            :return: The role of the agent
            """
            return BaseLedgerApiDialogue.Role.AGENT

        BaseLedgerApiDialogues.__init__(
            self,
            self_address=str(self.skill_id),
            role_from_first_message=role_from_first_message,
            dialogue_class=LedgerApiDialogue,
        )
