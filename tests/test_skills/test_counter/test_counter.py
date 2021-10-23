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

"""Tests for valory/counter skill."""
import logging
from pathlib import Path
from typing import Any, cast
from unittest.mock import patch

from aea.test_tools.test_skill import BaseSkillTestCase

from packages.valory.skills.counter.dialogues import AbciDialogues
from packages.valory.skills.counter.handlers import ABCICounterHandler

from tests.conftest import ROOT_DIR


class TestCounterHandler(BaseSkillTestCase):
    """Test ABCICounterHandler methods."""

    path_to_skill = Path(ROOT_DIR, "packages", "valory", "skills", "counter")
    abci_counter_handler: ABCICounterHandler
    logger: logging.Logger
    abci_dialogues: AbciDialogues

    @classmethod
    def setup(cls, **kwargs: Any) -> None:
        """Setup the test class."""
        super().setup()
        cls.abci_counter_handler = cast(
            ABCICounterHandler, cls._skill.skill_context.handlers.abci
        )
        cls.logger = cls._skill.skill_context.logger

        cls.abci_dialogues = cast(
            AbciDialogues, cls._skill.skill_context.abci_dialogues
        )

    def test_setup(self) -> None:
        """Test the setup method of the echo handler."""
        with patch.object(self.logger, "log") as mock_logger:
            self.abci_counter_handler.setup()
            mock_logger.assert_any_call(
                logging.DEBUG, "ABCI Handler: setup method called."
            )

        # after
        self.assert_quantity_in_outbox(0)

    def test_teardown(self) -> None:
        """Test the teardown method of the echo handler."""
        with patch.object(self.logger, "log") as mock_logger:
            self.abci_counter_handler.teardown()
            mock_logger.assert_any_call(
                logging.DEBUG, "ABCI Handler: teardown method called."
            )

        # after
        self.assert_quantity_in_outbox(0)
