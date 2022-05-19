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

"""Tests for specs commands."""


import importlib
from pathlib import Path
from typing import Tuple

from aea_swarm.analyse.abci.app_spec import DFA

from tests.test_aea_swarm.test_cli.base import BaseCliTest


class TestGenerateSpecs(BaseCliTest):
    """Test generate-app-specs"""

    cli_options: Tuple[str, ...] = ("analyse", "abci", "generate-app-specs")
    skill_path = Path("packages", "valory", "skills", "hello_world_abci", "rounds")
    app_name = "HelloWorldAbciApp"

    cls_name: str
    dfa: DFA

    @classmethod
    def setup(cls) -> None:
        """Setup class."""
        super().setup()

        module_name = ".".join(cls.skill_path.parts)
        module = importlib.import_module(module_name)
        cls.cls_name = ".".join([module_name, cls.app_name])

        abci_app_cls = getattr(module, cls.app_name)
        cls.dfa = DFA.abci_to_dfa(abci_app_cls, cls.cls_name)

    def get_expected_output(self, output_format: str) -> str:
        """Get expected output."""

        temp_file = self.t / "temp"
        self.dfa.dump(temp_file, output_format)

        return temp_file.read_text(encoding="utf-8")

    def _run_test(self, output_format: str) -> None:
        """Run test for given output format type."""

        output_file = self.t / "fsm"
        result = self.run_cli((self.cls_name, str(output_file), f"--{output_format}"))

        assert result.exit_code == 0
        assert output_file.read_text() == self.get_expected_output(output_format)

    def test_generate_yaml(
        self,
    ) -> None:
        """Run tests."""

        self._run_test(DFA.OutputFormats.YAML)

    def test_generate_json(
        self,
    ) -> None:
        """Run tests."""

        self._run_test(DFA.OutputFormats.JSON)

    def test_generate_mermaid(
        self,
    ) -> None:
        """Run tests."""

        self._run_test(DFA.OutputFormats.MERMAID)
