# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2023 Valory AG
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

"""Test `autonomy analyse dialgues` module."""

from pathlib import Path
from typing import List, Optional, Tuple
from unittest import mock

import yaml
from aea.configurations.constants import DEFAULT_SKILL_CONFIG_FILE

from autonomy.analyse.constants import CLASS_NAME, DIALOGUES_FILE

from tests.test_autonomy.test_cli.base import BaseCliTest


class BaseAnalyseDialoguesTest(BaseCliTest):
    """Base class for testing dialogues analyser"""

    cli_options: Tuple[str, ...] = ("analyse", "dialogues")
    skill_dir: Path

    def patch_list_skills(self) -> mock._patch:
        """Patch `autonomy.cli.helpers.analyse.list_all_skill_yaml_files` method to return temporary skill dir"""

        return mock.patch(
            "autonomy.cli.helpers.analyse.list_all_skill_yaml_files",
            return_value=[self.skill_dir / DEFAULT_SKILL_CONFIG_FILE],
        )

    def make_dummy_skill(
        self,
        config_data: List[Tuple[str, str]],
        dialogues: List[str],
    ) -> None:
        """Make duummy skill."""
        self.skill_dir = self.t / "some_skill"
        self.skill_dir.mkdir()

        config_file = self.skill_dir / DEFAULT_SKILL_CONFIG_FILE
        with open(config_file, "w") as fp:
            yaml.safe_dump(
                data={
                    "models": {
                        dialogue_name: {CLASS_NAME: dialogue_class}
                        for dialogue_name, dialogue_class in config_data
                    }
                },
                stream=fp,
            )

        if len(dialogues) > 0:
            dialogues_file = self.skill_dir / DIALOGUES_FILE
            dialogues_file.write_text(
                "\n".join([f"{dialogue_class} = None" for dialogue_class in dialogues])
            )


class TestAnalyseDialogues(BaseAnalyseDialoguesTest):
    """Test analyse dialogues."""

    def run_test(
        self,
        config_data: List[Tuple[str, str]],
        dialogues: List[str],
        exit_code: int,
        stdout_checks: List[str],
        commands: Optional[Tuple[str, ...]] = None,
    ) -> None:
        """Run test."""
        self.make_dummy_skill(
            config_data=config_data,
            dialogues=dialogues,
        )

        with self.patch_list_skills():
            result = self.run_cli(commands=(commands or ()))

        assert result.exit_code == exit_code, result.stdout

        for check in stdout_checks:
            assert check in result.stdout

    def test_analyse_default(self) -> None:
        """Test analyse."""

        self.run_test(
            config_data=[
                ("abci_dialogues", "AbciDialogues"),
            ],
            dialogues=["AbciDialogues"],
            exit_code=0,
            stdout_checks=["Checking"],
        )

    def test_analyse_fail_dialogues_does_not_exist(self) -> None:
        """Test analyse."""

        self.run_test(
            config_data=[],
            dialogues=[],
            exit_code=1,
            stdout_checks=["dialogue file does not exist"],
        )

    def test_analyse_fail_wrong_class_name(self) -> None:
        """Test analyse."""

        self.run_test(
            config_data=[
                ("abci_dialogues", "AbciDialogue"),
            ],
            dialogues=["AbciDialogue"],
            exit_code=1,
            stdout_checks=[
                "Class name for a dialogue should end with `Dialogues`; dialogue=abci_dialogues; class=AbciDialogue"
            ],
        )

    def test_analyse_fail_wrong_dialogue_name(self) -> None:
        """Test analyse."""

        self.run_test(
            config_data=[
                ("abci_dialogue", "AbciDialogues"),
            ],
            dialogues=["AbciDialogues"],
            exit_code=1,
            stdout_checks=[
                "Dialogue name should end with `dialogues`; dialogue=abci_dialogue; class=AbciDialogues"
            ],
        )

    def test_analyse_fail_common_dialogue_not_found(self) -> None:
        """Test analyse."""

        self.run_test(
            config_data=[
                ("abci_dialogues", "AbciDialogues"),
            ],
            dialogues=["AbciDialogues"],
            exit_code=1,
            stdout_checks=["Common dialogue 'some_dialogues' is not defined"],
            commands=("-d", "some_dialogues"),
        )

    def test_analyse_fail_common_dialogue_class_not_found(self) -> None:
        """Test analyse."""

        self.run_test(
            config_data=[
                ("abci_dialogues", "AbciDialogues"),
                ("some_dialogues", "SomeDialogues"),
            ],
            dialogues=["AbciDialogues"],
            exit_code=1,
            stdout_checks=["dialogue SomeDialogues declared in", "is missing from"],
            commands=("-d", "some_dialogues"),
        )

    def test_analyse_skip_file(self) -> None:
        """Test analyse."""

        self.run_test(
            config_data=[],
            dialogues=[],
            exit_code=0,
            stdout_checks=["Skipping some_skill"],
            commands=("-i", "some_skill"),
        )
