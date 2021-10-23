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

"""Test the dialogues.py module of the skill."""
from enum import Enum
from typing import Type, cast
from unittest.mock import MagicMock

import pytest
from aea.protocols.dialogue.base import Dialogues

from packages.valory.skills.abstract_abci.dialogues import AbciDialogue, AbciDialogues


@pytest.mark.parametrize(
    "dialogues_cls,expected_role_from_first_message",
    [
        (AbciDialogues, AbciDialogue.Role.CLIENT),
    ],
)
def test_dialogues_creation(
    dialogues_cls: Type[AbciDialogues], expected_role_from_first_message: Enum
) -> None:
    """Test XDialogues creations."""
    dialogues = cast(Dialogues, dialogues_cls(name="", skill_context=MagicMock()))
    assert expected_role_from_first_message == dialogues._role_from_first_message(
        MagicMock(), MagicMock()
    )
