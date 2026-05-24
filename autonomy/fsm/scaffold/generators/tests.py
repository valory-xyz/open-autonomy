# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
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

"""Test generators."""

from typing import List

from autonomy.fsm.scaffold.base import AbstractFileGenerator
from autonomy.fsm.scaffold.generators.components import SimpleFileGenerator
from autonomy.fsm.scaffold.templates import COPYRIGHT_HEADER
from autonomy.fsm.scaffold.templates.tests import (
    TEST_BEHAVIOURS,
    TEST_DIALOGUES,
    TEST_HANDLERS,
    TEST_MODELS,
    TEST_PAYLOADS,
    TEST_ROUNDS,
)


class RoundTestsFileGenerator(AbstractFileGenerator, TEST_ROUNDS):
    """RoundTestsFileGenerator"""

    def get_file_content(self) -> str:
        """Scaffold the 'test_rounds.py' file."""

        file_content = [
            COPYRIGHT_HEADER,
            self.HEADER.format(**self.template_kwargs),
            self._get_rounds_section(),
        ]

        return "\n".join(file_content)

    def _get_rounds_section(self) -> str:
        """Get rounds section"""

        rounds: List[str] = [self.BASE_ROUND_TEST_CLS.format(**self.template_kwargs)]

        for round_name in self.rounds:
            round_class_str = self.TEST_ROUND_CLS.format(
                FSMName=self.fsm_name,
                RoundCls=round_name,
            )
            rounds.append(round_class_str)

        return "\n".join(rounds)


class BehaviourTestsFileGenerator(AbstractFileGenerator, TEST_BEHAVIOURS):
    """File generator for 'test_behaviours.py' modules."""

    def get_file_content(self) -> str:
        """Scaffold the 'test_behaviours.py' file."""

        behaviour_file_content = [
            COPYRIGHT_HEADER,
            self.HEADER.format(**self.template_kwargs),
            self._get_behaviour_section(),
        ]

        return "\n".join(behaviour_file_content)

    def _get_behaviour_section(self) -> str:
        """Get behaviour section"""

        behaviours = [self.BASE_BEHAVIOUR_TEST_CLS.format(**self.template_kwargs)]

        for behaviour_name in self.behaviours:
            round_class_str = self.TEST_BEHAVIOUR_CLS.format(
                FSMName=self.fsm_name,
                BehaviourCls=behaviour_name,
            )
            behaviours.append(round_class_str)

        return "\n".join(behaviours)


class PayloadTestsFileGenerator(AbstractFileGenerator, TEST_PAYLOADS):
    """File generator for 'test_payloads.py' modules."""

    def get_file_content(self) -> str:
        """Scaffold the 'test_payloads.py' file."""

        behaviour_file_content = [
            COPYRIGHT_HEADER,
            self.HEADER.format(**self.template_kwargs),
            self.TEST_PAYLOAD_CLS.format(**self.template_kwargs),
        ]

        return "\n".join(behaviour_file_content)


class ModelTestFileGenerator(SimpleFileGenerator, TEST_MODELS):
    """File generator for 'test_models.py'."""


class HandlersTestFileGenerator(SimpleFileGenerator, TEST_HANDLERS):
    """File generator for 'test_dialogues.py'."""


class DialoguesTestFileGenerator(SimpleFileGenerator, TEST_DIALOGUES):
    """File generator for 'test_dialogues.py'."""
