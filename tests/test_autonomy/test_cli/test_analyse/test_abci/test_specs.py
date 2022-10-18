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
import os
import re
import shutil
from enum import Enum
from pathlib import Path
from typing import Tuple
from unittest import mock

import pytest
from aea.configurations.constants import PACKAGES

from autonomy.analyse.abci.app_spec import (
    DFA,
    DFASpecificationError,
    SpecCheck,
    _check_unreferenced_events,
)

from tests.conftest import ROOT_DIR
from tests.test_autonomy.test_cli.base import BaseCliTest


class TestGenerateSpecs(BaseCliTest):
    """Test generate-app-specs"""

    cli_options: Tuple[str, ...] = ("analyse", "abci", "generate-app-specs")
    skill_path = Path(PACKAGES, "valory", "skills", "hello_world_abci", "rounds")
    module_name = ".".join(skill_path.parts)
    app_name = "HelloWorldAbciApp"
    cls_name = ".".join([module_name, app_name])

    dfa: DFA

    def setup(self) -> None:
        """Setup test method."""
        super().setup()

        module = importlib.import_module(self.module_name)
        abci_app_cls = getattr(module, self.app_name)
        self.dfa = DFA.abci_to_dfa(abci_app_cls, self.cls_name)

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

    def test_failures(
        self,
    ) -> None:
        """Test failures."""

        *module, cls = self.cls_name.split(".")
        cls_name = ".".join([*module, "dummy", cls])
        result = self.run_cli((cls_name, "fsm", "--yaml"))

        assert result.exit_code == 1, result.output
        assert "Failed to load" in result.stdout, result.output
        assert (
            "Please, verify that AbciApps and classes are correctly defined within the module."
            in result.stdout
        ), result.output

        *module, cls = self.cls_name.split(".")
        cls_name = ".".join([*module, cls[:-1]])
        result = self.run_cli((cls_name, "fsm", "--yaml"))

        assert result.exit_code == 1, result.output
        assert """Class "HelloWorldAbciAp" is not in""" in result.stdout, result.output


class TestCheckSpecs(BaseCliTest):
    """Test `check-app-specs` command."""

    cli_options: Tuple[str, ...] = ("analyse", "abci", "check-app-specs")
    skill_path = Path(PACKAGES, "valory", "skills", "hello_world_abci", "rounds")
    module_name = ".".join(skill_path.parts)
    app_name = "HelloWorldAbciApp"
    cls_name = ".".join([module_name, app_name])

    packages_dir: Path
    specification_path: Path

    def setup(self) -> None:
        """Setup class."""
        super().setup()

        self.packages_dir = self.t / PACKAGES
        shutil.copytree(ROOT_DIR / PACKAGES, self.packages_dir)
        self.specification_path = (
            self.t / self.skill_path.parent / "fsm_specification.yaml"
        )
        os.chdir(self.t)

    def _corrupt_spec_file(
        self,
    ) -> None:
        """Corrupt spec file to fail the check."""
        content = self.specification_path.read_text()
        content = content.replace(
            "(SelectKeeperRound, ROUND_TIMEOUT): RegistrationRound\n", ""
        )
        self.specification_path.write_text(content)

    def test_one_pass(
        self,
    ) -> None:
        """Test with one class."""
        result = self.run_cli(
            ("--app-class", self.cls_name, "--infile", str(self.specification_path))
        )

        assert result.exit_code == 0
        assert result.output == f"Checking : {self.cls_name}\nCheck successful\n"

    def test_one_fail(
        self,
    ) -> None:
        """Test with one class failing."""
        self._corrupt_spec_file()
        result = self.run_cli(
            ("--app-class", self.cls_name, "--infile", str(self.specification_path))
        )

        assert result.exit_code == 1
        assert result.output == f"Checking : {self.cls_name}\nCheck failed.\n"

    def test_check_all(
        self,
    ) -> None:
        """Test --check-all flag."""
        result = self.run_cli(
            (
                "--check-all",
                "--packages-dir",
                str(self.packages_dir),
            )
        )

        assert result.exit_code == 0
        assert "Check successful." in result.output

    def test_check_all_fail(
        self,
    ) -> None:
        """Test --check-all flag."""
        self._corrupt_spec_file()
        result = self.run_cli(
            (
                "--check-all",
                "--packages-dir",
                str(self.packages_dir),
            )
        )

        assert result.exit_code == 1
        assert (
            "Specifications did not match for following definitions." in result.output
        )

    def test_failures(
        self,
    ) -> None:
        """Test with one class."""
        result = self.run_cli(("--infile", str(self.specification_path)))

        assert result.exit_code == 1, result.output
        assert "Please provide class name for ABCI app." in result.output, result.output

        result = self.run_cli(("--app-class", self.cls_name))

        assert result.exit_code == 1, result.output
        assert (
            "Please provide path to specification file." in result.output
        ), result.output


class TestDFA:
    """Test the DFA class."""

    good_dfa_kwargs = dict(
        label="dummy_dfa",
        states={"state_a", "state_b", "state_c"},
        default_start_state="state_a",
        start_states={"state_a"},
        final_states={"state_c"},
        alphabet_in={"event_a", "event_b", "event_c"},
        transition_func={
            ("state_a", "event_b"): "state_b",
            ("state_b", "event_a"): "state_a",
            ("state_b", "event_c"): "state_c",
        },
    )

    bad_dfa_kwargs = dict(
        label="dummy_dfa",
        states={"state_a", "state_b", "state_c", "unreachable_state"},
        default_start_state="state_other",
        start_states={"state_a", "extra_state"},
        final_states={"state_a", "state_c", "extra_state"},
        alphabet_in={"event_a", "event_b", "event_c", "other_extra_event"},
        transition_func={
            ("state_a", "event_b"): "state_b",
            ("state_b", "event_a"): "state_a",
            ("state_b", "event_c"): "state_c",
            ("extra_state", "extra_event"): "extra_state",
        },
    )

    def test_dfa(self) -> None:
        """Test DFA."""
        good_dfa = DFA(**self.good_dfa_kwargs)  # type: ignore

        assert not good_dfa.is_transition_func_total()
        assert good_dfa.get_transitions(["event_a"]) == ["state_a", "state_a"]
        assert good_dfa.get_transitions(["event_x"]) == ["state_a"]
        assert isinstance(good_dfa.parse_transition_func(), dict)
        assert good_dfa.__eq__(None) == NotImplemented

        with pytest.raises(
            DFASpecificationError, match="DFA spec. object {} is not of type List."
        ):
            assert good_dfa._norep_list_to_set(dict())  # type: ignore

        with pytest.raises(
            DFASpecificationError,
            match=re.escape(
                "DFA spec. List ['value', 'value'] contains repeated values."
            ),
        ):
            assert good_dfa._norep_list_to_set(["value", "value"])

        with pytest.raises(
            DFASpecificationError,
            match="DFA spec. JSON file contains an invalid transition function key: .",
        ):
            assert good_dfa._str_to_tuple("")

        with pytest.raises(
            DFASpecificationError,
            match=re.escape(
                "DFA spec. JSON file contains an invalid transition function key: (a, )."
            ),
        ):
            assert good_dfa._str_to_tuple("(a, )")

        with pytest.raises(
            DFASpecificationError,
            match=re.escape(
                "DFA spec. JSON file contains an invalid transition function key: (, b)."
            ),
        ):
            assert good_dfa._str_to_tuple("(, b)")

        with pytest.raises(
            DFASpecificationError,
            match=re.escape(
                "DFA spec. JSON file contains an invalid transition function key: (, )."
            ),
        ):
            assert good_dfa._str_to_tuple("(, )")

        with pytest.raises(
            DFASpecificationError, match="DFA spec. has the following issues"
        ):
            DFA(**self.bad_dfa_kwargs)  # type: ignore

    def test_load(self) -> None:
        """Test test_load"""

        json_spec = Path(
            ROOT_DIR,
            "tests",
            "data",
            "specs",
            "fsm_specification.json",
        )
        with open(json_spec, "r", encoding="utf-8") as fp:
            assert isinstance(DFA.load(fp, input_format="json"), DFA)

            with pytest.raises(ValueError):
                DFA.load(fp, input_format="wrong_format")

    def test_load_empty(self) -> None:
        """Test test_load_empty"""

        json_spec = Path(
            ROOT_DIR,
            "tests",
            "data",
            "specs",
            "fsm_specification_empty.json",
        )
        with open(json_spec, "r", encoding="utf-8") as fp:
            with pytest.raises(
                DFASpecificationError, match="DFA spec. JSON file missing key."
            ):
                DFA.load(fp, input_format="json")

    def test_load_extra(self) -> None:
        """Test test_load_extra"""

        json_spec = Path(
            ROOT_DIR,
            "tests",
            "data",
            "specs",
            "fsm_specification_extra.json",
        )
        with open(json_spec, "r", encoding="utf-8") as fp:
            with pytest.raises(
                DFASpecificationError,
                match=re.escape(
                    "DFA spec. JSON file contains unexpected objects: dict_keys(['extra_field'])."
                ),
            ):
                DFA.load(fp, input_format="json")

    def test_check_unreferenced_events(self) -> None:
        """Test check_unreferenced_events"""

        class MockABCIApp:
            """Mock ABCIApp class"""

            class Round:
                """Mock Round class"""

                __name__ = "round"

            class Event(Enum):
                """Mock Event class"""

                A = "A"
                B = "B"

            initial_round_cls = "initial_round_cls"
            transition_function = {
                Round: {
                    Event.A: "round_b",
                    Event.B: "round_b",
                },
            }
            event_to_timeout = {
                Event.A: 30.0,
            }

        with mock.patch("inspect.getmro", return_value=[]):
            with pytest.raises(
                DFASpecificationError, match=r"ABCI App has the following issues"
            ):
                _check_unreferenced_events(MockABCIApp)


class TestSpecCheck:
    """Test the SpecCheck class."""

    def test_check_one(self) -> None:
        """Test check_one."""
        mock_module: dict = {}
        with mock.patch("importlib.import_module", return_value=mock_module):
            with pytest.raises(
                Exception, match='Class "classfqn" is not in "classfqn"'
            ):
                SpecCheck.check_one("informat", "infile", "classfqn.classfqn")
