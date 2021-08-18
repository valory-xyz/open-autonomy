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

"""Tests for valory/abstract_abci skill."""
import logging
from pathlib import Path
from typing import cast
from unittest.mock import patch

from aea.test_tools.test_skill import BaseSkillTestCase

from packages.valory.skills.abstract_abci.dialogues import AbciDialogues
from packages.valory.skills.abstract_abci.handlers import ABCIHandler

from tests.conftest import ROOT_DIR


class TestABCIHandler(BaseSkillTestCase):
    """Test ABCIHandler methods."""

    path_to_skill = Path(ROOT_DIR, "packages", "valory", "skills", "abstract_abci")

    @classmethod
    def setup(cls):
        """Setup the test class."""
        super().setup()
        cls.abci_handler = cast(ABCIHandler, cls._skill.skill_context.handlers.abci)
        cls.logger = cls._skill.skill_context.logger

        cls.abci_dialogues = cast(
            AbciDialogues, cls._skill.skill_context.abci_dialogues
        )

    def test_setup(self):
        """Test the setup method of the echo handler."""
        with patch.object(self.logger, "log") as mock_logger:
            assert self.abci_handler.setup() is None

        # after
        self.assert_quantity_in_outbox(0)

        mock_logger.assert_any_call(logging.DEBUG, "ABCI Handler: setup method called.")

    def test_teardown(self):
        """Test the teardown method of the echo handler."""
        with patch.object(self.logger, "log") as mock_logger:
            assert self.abci_handler.teardown() is None

        # after
        self.assert_quantity_in_outbox(0)

        mock_logger.assert_any_call(
            logging.DEBUG, "ABCI Handler: teardown method called."
        )
