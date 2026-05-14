# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022-2026 Valory AG
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

import copy
import importlib
import json
import logging
import os
import re
import shutil
import warnings
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Set, Tuple, cast
from unittest import mock

import pytest
import yaml
from aea.cli.registry.settings import REGISTRY_LOCAL
from aea.cli.utils.constants import CLI_CONFIG_PATH, DEFAULT_CLI_CONFIG
from aea.configurations.constants import PACKAGES
from aea.helpers.json_schema import ValidationError

from autonomy.analyse.abci.app_spec import (
    DFA,
    DFASpecificationError,
    FSMSpecificationLoader,
    check_unreferenced_events,
)
from autonomy.cli.helpers.fsm_spec import _load_dev_skill_names

from tests.conftest import ROOT_DIR
from tests.test_autonomy.test_cli.base import BaseCliTest


class TestGenerateSpecs(BaseCliTest):
    """Test generate-app-specs"""

    cli_options: Tuple[str, ...] = ("analyse", "fsm-specs")

    dfa: DFA
    app_name: str
    skill_path: Path

    def setup_method(self) -> None:
        """Setup test method."""
        super().setup_method()

        self.app_name = "OffendAbciApp"
        self.skill_path = Path(PACKAGES, "valory", "skills", "offend_abci")

        module_name = ".".join((*self.skill_path.parts, "rounds"))
        module = importlib.import_module(module_name)
        abci_app_cls = getattr(module, self.app_name)

        shutil.copytree(ROOT_DIR / PACKAGES, self.t / PACKAGES)

        self.dfa = DFA.abci_to_dfa(abci_app_cls)
        self.cli_options = (
            "--registry-path",
            str(self.t / PACKAGES),
            "analyse",
            "fsm-specs",
        )

        os.chdir(self.t)

    def get_expected_output(self, output_format: str) -> str:
        """Get expected output."""

        temp_file = self.t / "temp"
        FSMSpecificationLoader.dump(self.dfa, file=temp_file, spec_format=output_format)

        return temp_file.read_text(encoding="utf-8")

    def _run_test(self, output_format: str) -> None:
        """Run test for given output format type."""

        output_file = self.skill_path / cast(
            Path,
            FSMSpecificationLoader.OutputFormats.default_output_files.get(
                output_format
            ),
        )
        result = self.run_cli(
            (
                "--package",
                str(self.skill_path),
                f"--{output_format}",
                "--app-class",
                self.app_name,
                "--update",
            )
        )

        assert result.exit_code == 0, result.output
        assert output_file.read_text() == self.get_expected_output(output_format)

    def test_generate_yaml(
        self,
    ) -> None:
        """Run tests."""

        self._run_test(FSMSpecificationLoader.OutputFormats.YAML)

    def test_generate_json(
        self,
    ) -> None:
        """Run tests."""

        self._run_test(FSMSpecificationLoader.OutputFormats.JSON)

    def test_generate_mermaid(
        self,
    ) -> None:
        """Run tests."""

        self._run_test(FSMSpecificationLoader.OutputFormats.MERMAID)

    def test_failures(
        self,
    ) -> None:
        """Test failures."""

        with pytest.raises(ValueError, match="Unrecognized input format .exe"):
            FSMSpecificationLoader.dump(self.dfa, self.skill_path, ".exe")

        with pytest.raises(ValueError, match="Unrecognized input format .exe"):
            FSMSpecificationLoader.load(self.skill_path, ".exe")

        result = self.run_cli(
            (
                "--app-class",
                "SOME_CLASS_NAME",
                "--package",
                str(Path(*self.skill_path.parts, "dummy_abci")),
                "--yaml",
            )
        )

        assert result.exit_code == 1, result.output
        assert (
            "Cannot find the rounds module or the composition module" in result.stderr
        ), result.output

        result = self.run_cli(
            (
                "--app-class",
                "SomeAppName",
                "--package",
                str(self.skill_path),
                "--yaml",
            )
        )

        assert result.exit_code == 1, result.output
        assert 'Class "SomeAppName" is not in' in result.stderr, result.output

        self.skill_path = self.skill_path.rename(self.skill_path.parent / "offend")
        result = self.run_cli(("--package", str(self.skill_path)))
        assert result.exit_code == 1, result.output
        assert (
            "The name of the skill 'offend' must end with `_abci`." in result.stderr
        ), result.output


class TestCheckSpecs(BaseCliTest):
    """Test `check-app-specs` command."""

    cli_options: Tuple[str, ...] = ("analyse", "fsm-specs")
    skill_path = Path(PACKAGES, "valory", "skills", "offend_abci")
    module_name = ".".join(skill_path.parts)
    app_name = "OffendAbciApp"
    cls_name = ".".join([module_name, app_name])

    packages_dir: Path
    specification_path: Path

    def setup_method(self) -> None:
        """Setup class."""
        super().setup_method()

        self.packages_dir = self.t / PACKAGES
        shutil.copytree(ROOT_DIR / PACKAGES, self.packages_dir)
        self.specification_path = (
            self.t / self.skill_path.parent / "fsm_specification.yaml"
        )

        # make a copy of 'packages' in a subdirectory with depth > 1 from cwd
        subdirectory = self.t / Path("path", "to", "subdirectory")
        self.packages_dir_in_subdir = subdirectory / PACKAGES
        self.specification_path_in_subdir = (
            subdirectory / self.skill_path.parent / "fsm_specification.yaml"
        )
        shutil.copytree(self.packages_dir, self.packages_dir_in_subdir)

        self.specification_path = self.t / self.skill_path / "fsm_specification.yaml"
        os.chdir(self.t)
        DEFAULT_CLI_CONFIG["registry_config"]["settings"][REGISTRY_LOCAL][
            "default_packages_path"
        ] = (self.t / PACKAGES).as_posix()
        Path(CLI_CONFIG_PATH).write_text(yaml.dump(DEFAULT_CLI_CONFIG))

    def teardown_method(self) -> None:
        """Teardown class."""
        super().teardown_method()
        DEFAULT_CLI_CONFIG["registry_config"]["settings"][REGISTRY_LOCAL][
            "default_packages_path"
        ] = None
        Path(CLI_CONFIG_PATH).write_text(yaml.dump(DEFAULT_CLI_CONFIG))

    def _corrupt_spec_file(
        self,
    ) -> None:
        """Corrupt spec file to fail the check."""
        content = self.specification_path.read_text()
        content = content.replace("(OffendRound, ROUND_TIMEOUT): OffendRound\n", "")
        content = content.replace("- ROUND_TIMEOUT\n", "")
        self.specification_path.write_text(content)

    def test_one_pass(
        self,
    ) -> None:
        """Test with one class."""
        return_code, stdout, stderr = self.run_cli_subprocess(
            ("--app-class", self.app_name, "--package", str(self.skill_path))
        )

        assert return_code == 0, stderr
        assert "Check successful" in stdout

    def test_one_fail(
        self,
    ) -> None:
        """Test with one class failing."""
        self._corrupt_spec_file()
        return_code, stdout, stderr = self.run_cli_subprocess(
            ("--app-class", self.app_name, "--package", str(self.skill_path))
        )

        assert return_code == 1, stderr
        assert (
            "FSM Spec definition does not match in specification file and class definitions"
            in stderr
        )

    def test_analyse_fsm_specs(
        self,
    ) -> None:
        """Test the `analyse fsm-specs` command."""
        return_code, stdout, stderr = self.run_cli_subprocess(())

        assert return_code == 0, stderr
        assert "Done" in stdout

    def test_analyse_fsm_specs_when_packages_is_not_in_working_dir(
        self,
    ) -> None:
        """Test `analyse fsm-specs` command when the packages directory is not in the working directory."""
        return_code, stdout, stderr = self.run_cli_subprocess(())

        assert return_code == 0
        assert "Checking all available packages" in stdout
        assert "Done" in stdout

    def test_check_fail_when_packages_dir_is_not_named_packages(
        self,
    ) -> None:
        """Test `analyse fsm-specs` command when the packages directory is not named 'packages'."""
        wrong_dir = self.t / "some-directory"
        wrong_dir.mkdir(exist_ok=True)

        self.cli_options = (
            "--registry-path",
            str(wrong_dir),
            "analyse",
            "fsm-specs",
        )
        return_code, _, stderr = self.run_cli_subprocess(())

        assert return_code == 1, stderr
        assert f"packages directory {wrong_dir} is not named '{PACKAGES}'" in stderr

    def test_analyse_fsm_specs_fail(
        self,
    ) -> None:
        """Test `analyse fsm-specs` command failure."""
        self._corrupt_spec_file()
        return_code, stdout, stderr = self.run_cli_subprocess(())

        assert return_code == 1
        assert "Specifications check for following packages failed" in stderr


class TestDFA:
    """Test the DFA class."""

    good_dfa_kwargs = dict(
        label="DummyAbciApp",
        states={"StateARound", "StateBRound", "StateCRound"},
        default_start_state="StateARound",
        start_states={"StateARound"},
        final_states={"StateCRound"},
        alphabet_in={"event_a", "event_b", "event_c"},
        transition_func={
            ("StateARound", "event_b"): "StateBRound",
            ("StateBRound", "event_a"): "StateARound",
            ("StateBRound", "event_c"): "StateCRound",
        },
    )

    bad_dfa_kwargs = dict(
        label="DummyAbciApp",
        states={"StateARound", "StateBRound", "StateCRound", "unreachable_state"},
        default_start_state="state_other",
        start_states={"StateARound", "ExtraRound"},
        final_states={"StateARound", "StateCRound", "ExtraRound"},
        alphabet_in={"event_a", "event_b", "event_c", "other_extra_event"},
        transition_func={
            ("StateARound", "event_b"): "StateBRound",
            ("StateBRound", "event_a"): "StateARound",
            ("StateBRound", "event_c"): "StateCRound",
            ("ExtraRound", "extra_event"): "ExtraRound",
        },
    )

    def test_dfa(self) -> None:
        """Test DFA."""
        good_dfa = DFA(**self.good_dfa_kwargs)  # type: ignore

        assert not good_dfa.is_transition_func_total()
        assert good_dfa.get_transitions(["event_a"]) == ["StateARound", "StateARound"]
        assert good_dfa.get_transitions(["event_x"]) == ["StateARound"]
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
            DFASpecificationError, match="DFA spec has the following issues"
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

        assert isinstance(
            DFA.load(json_spec, FSMSpecificationLoader.OutputFormats.JSON), DFA
        )

        with pytest.raises(ValueError):
            DFA.load(json_spec, "wrong_format")

    def test_load_empty(self) -> None:
        """Test test_load_empty"""

        json_spec = Path(
            ROOT_DIR,
            "tests",
            "data",
            "specs",
            "fsm_specification_empty.json",
        )

        with pytest.raises(ValidationError, match="is a required property"):
            DFA.load(json_spec, FSMSpecificationLoader.OutputFormats.JSON)

    def test_load_extra(self) -> None:
        """Test test_load_extra"""

        json_spec = Path(
            ROOT_DIR,
            "tests",
            "data",
            "specs",
            "fsm_specification_extra.json",
        )

        with pytest.raises(
            ValidationError,
            match=re.escape("Additional properties are not allowed"),
        ):
            DFA.load(json_spec, FSMSpecificationLoader.OutputFormats.JSON)

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
            strings = check_unreferenced_events(MockABCIApp)
            assert len(strings) > 0

    def test_name_verification(self) -> None:
        """Test `validate_naming_conventions`"""

        dfa_kwargs = copy.deepcopy(self.good_dfa_kwargs)
        dfa_kwargs["label"] = "abci_app"
        with pytest.raises(
            DFASpecificationError,
            match="ABCI app class name should end in `AbciApp`; ABCI app name found `abci_app`",
        ):
            DFA(**dfa_kwargs)  # type: ignore

        with pytest.raises(
            DFASpecificationError,
            match="Round class name should end in `Round`; Round app name found `StateBRoun`",
        ):
            DFA(
                label="DummyAbciApp",
                states={"StateARound", "StateBRoun"},
                default_start_state="StateARound",
                start_states={"StateARound"},
                final_states={"StateBRoun"},
                alphabet_in={"event_b"},
                transition_func={
                    ("StateARound", "event_b"): "StateBRoun",
                },
            )


def _make_mock_round(name: str, module: str) -> Any:
    """Create a mock round class with __name__ and __module__."""
    cls = type(name, (), {"__module__": module})
    return cls


class _MockAbciApp:
    """Minimal mock matching the _AbciAppLike protocol."""

    transition_function: Dict[Any, Dict[Any, Any]] = {}
    initial_states: Set[Any] = set()
    final_states: Set[Any] = set()


class TestExtractSkillName:
    """Test ``_extract_skill_name``."""

    def test_standard_module_path(self) -> None:
        """Standard packages path returns the skill name."""
        result = FSMSpecificationLoader._extract_skill_name(
            "packages.valory.skills.market_manager_abci.rounds"
        )
        assert result == "market_manager_abci"

    def test_no_skills_segment(self) -> None:
        """Path without a skills segment returns None."""
        assert FSMSpecificationLoader._extract_skill_name("some.other.module") is None

    def test_skills_at_end(self) -> None:
        """Path ending with 'skills' (no segment after) returns None."""
        assert (
            FSMSpecificationLoader._extract_skill_name("packages.valory.skills") is None
        )

    def test_empty_string(self) -> None:
        """Empty string returns None."""
        assert FSMSpecificationLoader._extract_skill_name("") is None


class TestBuildRoundToSubapp:
    """Test ``_build_round_to_subapp``."""

    def test_none_returns_empty(self) -> None:
        """Passing None returns an empty dict."""
        assert FSMSpecificationLoader._build_round_to_subapp(None) == {}

    def test_basic_mapping(self) -> None:
        """Rounds are mapped to their owning sub-app."""
        round_a = _make_mock_round(
            "RoundARound", "packages.valory.skills.skill_a.rounds"
        )
        round_b = _make_mock_round(
            "RoundBRound", "packages.valory.skills.skill_b.rounds"
        )

        class MockApp(_MockAbciApp):
            """Mock composed app."""

            transition_function = {round_a: {}}
            initial_states = {round_a}
            final_states = {round_b}

        result = FSMSpecificationLoader._build_round_to_subapp(MockApp)
        assert result == {"RoundARound": "skill_a", "RoundBRound": "skill_b"}

    def test_collision_warning(self, caplog: pytest.LogCaptureFixture) -> None:
        """Name collision logs a warning."""
        round_a = _make_mock_round(
            "SharedRound", "packages.valory.skills.skill_a.rounds"
        )
        round_b = _make_mock_round(
            "SharedRound", "packages.valory.skills.skill_b.rounds"
        )

        class MockApp(_MockAbciApp):
            """Mock composed app with collision."""

            transition_function = {round_a: {round_b: round_b}}
            initial_states = set()
            final_states = set()

        with caplog.at_level(logging.WARNING):
            FSMSpecificationLoader._build_round_to_subapp(MockApp)

        assert "Round name collision" in caplog.text
        assert "SharedRound" in caplog.text

    def test_unclassified_warning(self, caplog: pytest.LogCaptureFixture) -> None:
        """Rounds without a skills segment log a warning."""
        round_cls = _make_mock_round("WeirdRound", "some.random.module")

        class MockApp(_MockAbciApp):
            """Mock with unclassified round."""

            transition_function = {round_cls: {}}
            initial_states = set()
            final_states = set()

        with caplog.at_level(logging.WARNING):
            result = FSMSpecificationLoader._build_round_to_subapp(MockApp)

        assert len(result) == 0
        assert "Unclassified rounds" in caplog.text
        assert "WeirdRound" in caplog.text


class TestCheckUnreferencedEvents:
    """Targeted regression tests for ``check_unreferenced_events`` (issue #2496)."""

    def _build_app(self, round_cls: Any, event_cls: Any, **extra: Any) -> Any:
        """Return a minimal mock AbciApp wired around a single round/event."""

        class MockApp:
            """Mock AbciApp."""

            transition_function: Dict[Any, Dict[Any, Any]] = {
                round_cls: {member: round_cls for member in event_cls}
            }
            event_to_timeout: Dict[Any, float] = extra.get("event_to_timeout", {})

        return MockApp

    def test_override_aware_attribute_resolution(self) -> None:
        """Subclass override of ``*_event`` masks parent's definition."""

        class ParentEvent(Enum):
            """Parent enum (different skill)."""

            FETCH_ERROR = "FETCH_ERROR"
            DONE = "DONE"

        class ChildEvent(Enum):
            """Child enum (this skill)."""

            DONE = "DONE"
            NONE = "NONE"

        class ParentRound:
            """Parent round, sub-app A."""

            done_event = ParentEvent.DONE
            none_event = ParentEvent.FETCH_ERROR

        class ChildRound(ParentRound):
            """Child overrides none_event with its own enum."""

            done_event = ChildEvent.DONE  # type: ignore[assignment]
            none_event = ChildEvent.NONE  # type: ignore[assignment]

        app = self._build_app(ChildRound, ChildEvent)
        # The child's transition_function uses ChildEvent; the parent's
        # FETCH_ERROR must NOT be reported as missing -- AND no other
        # error should fire either, so the negative assertion is anchored
        # to the empty-list shape (vacuous-truth-proof).
        errors = check_unreferenced_events(app)
        assert errors == [], errors

    def test_cross_skill_enum_names_filtered(self) -> None:
        """``Event.X`` references absent from the AbciApp's enum are skipped."""

        class ChildEvent(Enum):
            """Child enum (no ``FETCH_ERROR``)."""

            DONE = "DONE"
            NO_MAJORITY = "NO_MAJORITY"

        class ParentRound:
            """Parent has a *_event referencing a different skill's enum."""

            done_event = ChildEvent.DONE
            # Simulate a parent attribute pointing at a different enum --
            # value is intentionally a string here; the *_event attr line
            # will be stripped anyway, and any spurious Event.FETCH_ERROR
            # left in the source must still be filtered out.
            extra_event = "PARENT_VALUE"
            # The literal below appears in the source and would otherwise
            # be flagged as missing.
            _comment_marker = "Event.FETCH_ERROR_FROM_OTHER_SKILL"

        class ChildRound(ParentRound):
            """Child reuses parent."""

            no_majority_event = ChildEvent.NO_MAJORITY

        app = self._build_app(ChildRound, ChildEvent)
        errors = check_unreferenced_events(app)
        # The cross-skill name must not surface AND no other error
        # should fire; assert the empty-list shape so the test fails
        # against a gutted ``check_unreferenced_events``.
        assert errors == [], errors

    def test_fsm_specs_returns_annotation(self) -> None:
        """``# fsm-specs: returns(...)`` annotates dynamically-emitted events."""

        class Event(Enum):
            """Test enum."""

            DONE = "DONE"
            PREPARE_TX = "PREPARE_TX"
            NO_REDEEMING = "NO_REDEEMING"

        class DynamicRound:
            """Round that builds events at runtime from a payload value.

            # fsm-specs: returns(PREPARE_TX, NO_REDEEMING)
            """

            done_event = Event.DONE

            def end_block(self) -> None:
                """Dynamic dispatch (no Event.X literal)."""
                # actual_event = Event(payload_value)  # noqa
                return None

        app = self._build_app(DynamicRound, Event)
        errors = check_unreferenced_events(app)
        # PREPARE_TX and NO_REDEEMING come from the annotation -- they
        # should be considered "referenced" and not show up as
        # "listed ... but never returned" errors. Assert the empty-list
        # shape rather than substring-absence so the test fails against
        # a gutted ``check_unreferenced_events``.
        assert errors == [], errors

    def test_method_body_event_literal_still_picked_up(self) -> None:
        """``Event.X`` in a method body is still counted as referenced."""

        class Event(Enum):
            """Test enum."""

            DONE = "DONE"
            MOCK_TX = "MOCK_TX"

        class Round:
            """Round whose end_block returns a tx event inline."""

            done_event = Event.DONE

            def end_block(self) -> None:
                """Real return path."""
                return Event.MOCK_TX  # type: ignore[return-value]

        # Transition function only wires DONE; MOCK_TX (returned inline in
        # end_block) must still be detected as referenced and reported as
        # missing from the transition function.
        class MockApp:
            """Mock AbciApp."""

            transition_function: Dict[Any, Dict[Any, Any]] = {
                Round: {Event.DONE: Round}
            }
            event_to_timeout: Dict[Any, float] = {}

        errors = check_unreferenced_events(MockApp)
        assert any("MOCK_TX" in e for e in errors), errors

    def test_method_body_local_var_event_literal_picked_up(self) -> None:
        r"""Local-var form of method-body Event.X reference is preserved.

        Specifically pins the ``result_event = Event.X; return result_event``
        shape against the over-stripping regression
        ``EVENT_ATTR_ASSIGN_PATTERN`` is anchored to defend against.  If the
        indent anchor is relaxed back to ``[ \t]+``, the method-body local
        ``result_event = Event.MOCK_TX`` line would be stripped before the
        regex scan and the test would fail.
        """

        class Event(Enum):
            """Test enum."""

            DONE = "DONE"
            MOCK_TX = "MOCK_TX"

        class Round:
            """Round whose end_block assigns to a local var first."""

            done_event = Event.DONE

            def end_block(self) -> None:
                """Local-var dispatch path."""
                result_event = Event.MOCK_TX
                return result_event  # type: ignore[return-value]

        class MockApp:
            """Mock AbciApp -- transition_function only wires DONE."""

            transition_function: Dict[Any, Dict[Any, Any]] = {
                Round: {Event.DONE: Round}
            }
            event_to_timeout: Dict[Any, float] = {}

        errors = check_unreferenced_events(MockApp)
        # MOCK_TX must be detected as "referenced but missing from
        # transition function" even though it never appears on a
        # ``return Event.X`` line directly -- the regex scan picks it
        # up from the local-var assignment that survives the strip.
        assert any("MOCK_TX" in e for e in errors), errors

    def test_composed_app_per_round_enum_resolution(self) -> None:
        """Each round resolves its own enum (composed AbciApp regression)."""

        class EventA(Enum):
            """Sub-app A's enum."""

            DONE = "DONE"
            MOCK_TX = "MOCK_TX"

        class EventB(Enum):
            """Sub-app B's enum -- distinct members from A."""

            DONE = "DONE"
            FINALIZE = "FINALIZE"

        # Bind ``Event`` as a class-level alias inside each round so the
        # regex ``Event\.X`` pattern picks up the real return statement
        # via the ``self.Event.X`` access path.  ``Event`` doesn't end in
        # ``_event``, so ``_round_event_enum_names`` ignores the alias
        # (only ``*_event`` attrs are inspected).
        class RoundA:
            """Round in sub-app A."""

            Event = EventA
            done_event = EventA.DONE

            def end_block(self) -> None:
                """Return the round's tx event."""
                return self.Event.MOCK_TX  # type: ignore[return-value]

        class RoundB:
            """Round in sub-app B."""

            Event = EventB
            done_event = EventB.DONE

            def end_block(self) -> None:
                """Return the round's tx event."""
                return self.Event.FINALIZE  # type: ignore[return-value]

        # Composed app: transition_function spans both enums.  A global
        # filter would lock onto one enum and drop the other's references.
        class MockComposedApp:
            """Mock composed AbciApp."""

            transition_function: Dict[Any, Dict[Any, Any]] = {
                RoundA: {EventA.DONE: RoundA},
                RoundB: {EventB.DONE: RoundB},
            }
            event_to_timeout: Dict[Any, float] = {}

        errors = check_unreferenced_events(MockComposedApp)
        # Both MOCK_TX (A) and FINALIZE (B) must be detected as
        # "referenced but missing from transition function".
        flat = " ".join(errors)
        assert "MOCK_TX" in flat, errors
        assert "FINALIZE" in flat, errors

    def test_round_event_enum_none_when_no_enum(self) -> None:
        """Filter degrades to no-op when round has no enum-typed *_event."""

        class Round:
            """Plain round, no enum references."""

        class MockApp:
            """Degenerate AbciApp."""

            transition_function: Dict[Any, Dict[Any, Any]] = {Round: {}}
            event_to_timeout: Dict[Any, float] = {}

        # Should not crash AND should produce no spurious errors; the
        # round has no transitions and no source-level Event.X references,
        # so the degraded-filter path has nothing to over-accept.
        errors = check_unreferenced_events(MockApp)
        assert errors == [], errors

    def test_missing_timeout_event_not_returned_flagged(self) -> None:
        """Flag events in transition_function that are not returned or timeout-declared.

        Event appears in ``transition_function`` but is not returned from
        any round's ``end_block`` and is not declared in
        ``event_to_timeout`` -- triggers the ``missing_timeout_events``
        error path.
        """

        class Event(Enum):
            """Test enum."""

            DONE = "DONE"
            UNUSED_TIMEOUT = "UNUSED_TIMEOUT"

        class Round:
            """Round whose end_block returns the done event."""

            done_event = Event.DONE

            def end_block(self) -> None:
                """Return the round's done event."""
                return Event.DONE  # type: ignore[return-value]

        class MockApp:
            """Mock AbciApp wiring UNUSED_TIMEOUT in the transition function.

            Neither returns it from any round's end_block nor declares it
            in event_to_timeout.
            """

            transition_function: Dict[Any, Dict[Any, Any]] = {
                Round: {Event.DONE: Round, Event.UNUSED_TIMEOUT: Round}
            }
            event_to_timeout: Dict[Any, float] = {}

        errors = check_unreferenced_events(MockApp)
        assert any("UNUSED_TIMEOUT" in e for e in errors), errors
        assert any(
            "never returned from any round's `end_block`" in e for e in errors
        ), errors

    def test_timeout_event_declared_in_event_to_timeout_passes(self) -> None:
        """Suppress the error when the event is declared in event_to_timeout.

        Same setup as ``test_missing_timeout_event_not_returned_flagged``
        but the event is also present in ``event_to_timeout`` -- the
        timeout pass-through must suppress the error.
        """

        class Event(Enum):
            """Test enum."""

            DONE = "DONE"
            ROUND_TIMEOUT = "ROUND_TIMEOUT"

        class Round:
            """Round whose end_block returns the done event."""

            done_event = Event.DONE

            def end_block(self) -> None:
                """Return the round's done event."""
                return Event.DONE  # type: ignore[return-value]

        class MockApp:
            """Mock AbciApp wiring ROUND_TIMEOUT in the transition function.

            Also declares it in event_to_timeout;
            check_unreferenced_events must NOT flag it as
            missing-from-end_block.
            """

            transition_function: Dict[Any, Dict[Any, Any]] = {
                Round: {Event.DONE: Round, Event.ROUND_TIMEOUT: Round}
            }
            event_to_timeout: Dict[Any, float] = {Event.ROUND_TIMEOUT: 30.0}

        errors = check_unreferenced_events(MockApp)
        assert not any("ROUND_TIMEOUT" in e for e in errors), errors


class TestDumpMermaid:
    """Test ``dump_mermaid`` and the composition-aware view."""

    simple_dfa = DFA(
        label="SimpleAbciApp",
        states={"StateARound", "StateBRound", "StateCRound"},
        default_start_state="StateARound",
        start_states={"StateARound"},
        final_states={"StateCRound"},
        alphabet_in={"event_a", "event_b", "event_c"},
        transition_func={
            ("StateARound", "event_b"): "StateBRound",
            ("StateBRound", "event_a"): "StateARound",
            ("StateBRound", "event_c"): "StateCRound",
        },
    )

    def test_mermaid_fence_wrapping(self, tmp_path: Path) -> None:
        """Output is wrapped in a ```mermaid fence."""
        out = tmp_path / "test.md"
        FSMSpecificationLoader.dump_mermaid(self.simple_dfa, out)
        content = out.read_text()
        assert content.startswith("```mermaid\n")
        assert content.rstrip().endswith("```")

    def test_flat_diagram_when_no_abci_app(self, tmp_path: Path) -> None:
        """Flat diagram when abci_app_cls is None (per-skill analysis)."""
        out = tmp_path / "test.md"
        FSMSpecificationLoader.dump_mermaid(self.simple_dfa, out)
        content = out.read_text()
        assert "stateDiagram-v2" in content
        assert "StateARound" in content
        assert "StateBRound" in content
        # No composite state blocks
        assert "state " not in content.replace("stateDiagram", "")

    def test_flat_when_dev_skills_empty(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Flat diagram when dev_skills is empty set."""
        round_a = _make_mock_round(
            "StateARound", "packages.valory.skills.skill_a.rounds"
        )
        round_b = _make_mock_round(
            "StateBRound", "packages.valory.skills.skill_b.rounds"
        )

        class MockApp(_MockAbciApp):
            """Mock app."""

            transition_function = {round_a: {}, round_b: {}}
            initial_states = {round_a}
            final_states = {round_b}

        out = tmp_path / "test.md"
        with caplog.at_level(logging.INFO):
            FSMSpecificationLoader.dump_mermaid(
                self.simple_dfa, out, abci_app_cls=MockApp, dev_skills=set()
            )
        content = out.read_text()
        # Should be flat (no composite state blocks)
        assert "classDef devGroup" not in content
        assert "Composition-aware view not available" in caplog.text

    def test_flat_when_dev_skills_none(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Flat diagram when dev_skills is None."""
        round_a = _make_mock_round(
            "StateARound", "packages.valory.skills.skill_a.rounds"
        )

        class MockApp(_MockAbciApp):
            """Mock app."""

            transition_function = {round_a: {}}
            initial_states = set()
            final_states = set()

        out = tmp_path / "test.md"
        with caplog.at_level(logging.INFO):
            FSMSpecificationLoader.dump_mermaid(
                self.simple_dfa, out, abci_app_cls=MockApp, dev_skills=None
            )
        assert "Composition-aware view not available" in caplog.text

    def test_flat_when_no_rounds_classifiable(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Flat diagram when every round's module lacks a `skills` segment."""
        # No "skills" in module path -- _extract_skill_name returns None
        # for every round, so round_to_subapp is empty.
        round_a = _make_mock_round("StateARound", "some.other.module")
        round_b = _make_mock_round("StateBRound", "some.other.module")

        class MockApp(_MockAbciApp):
            """Mock app with unclassifiable rounds."""

            transition_function = {round_a: {object(): round_b}}
            initial_states = {round_a}
            final_states = set()

        out = tmp_path / "test.md"
        with caplog.at_level(logging.WARNING):
            FSMSpecificationLoader.dump_mermaid(
                self.simple_dfa,
                out,
                abci_app_cls=MockApp,
                dev_skills={"some_skill"},
            )
        assert "no rounds could be classified by sub-app" in caplog.text

    def test_flat_self_loop_preserved(self, tmp_path: Path) -> None:
        """Legitimate self-loops are preserved in flat mode."""
        dfa = DFA(
            label="LoopAbciApp",
            states={"StateARound", "StateBRound"},
            default_start_state="StateARound",
            start_states={"StateARound"},
            final_states={"StateBRound"},
            alphabet_in={"retry", "done"},
            transition_func={
                ("StateARound", "retry"): "StateARound",
                ("StateARound", "done"): "StateBRound",
            },
        )
        out = tmp_path / "test.md"
        FSMSpecificationLoader.dump_mermaid(dfa, out)
        content = out.read_text()
        assert "StateARound --> StateARound" in content

    def test_post_collapse_self_loop_dropped(self, tmp_path: Path) -> None:
        """Intra-third-party transitions collapse to a self-loop and are dropped."""
        # Two rounds in the SAME third-party sub-app, connected by a
        # transition.  After _display collapses both to the sub-app name,
        # the resulting (X, X) self-loop must be dropped.
        round_a = _make_mock_round(
            "TpARound", "packages.valory.skills.tp_skill_abci.rounds"
        )
        round_b = _make_mock_round(
            "TpBRound", "packages.valory.skills.tp_skill_abci.rounds"
        )
        round_dev = _make_mock_round(
            "DevRound", "packages.valory.skills.dev_skill_abci.rounds"
        )
        round_dev2 = _make_mock_round(
            "DevTwoRound", "packages.valory.skills.dev_skill_abci.rounds"
        )

        class MockApp(_MockAbciApp):
            """Mock composed app."""

            transition_function = {
                round_a: {object(): round_b},
                round_b: {object(): round_dev},
                round_dev: {object(): round_dev2},
                round_dev2: {object(): round_a},
            }
            initial_states = {round_dev}
            final_states = set()

        dfa = DFA(
            label="ComposedAbciApp",
            states={"TpARound", "TpBRound", "DevRound", "DevTwoRound"},
            default_start_state="DevRound",
            start_states={"DevRound"},
            final_states=set(),
            alphabet_in={"ev_ab", "ev_bd", "ev_dd", "ev_da"},
            transition_func={
                ("TpARound", "ev_ab"): "TpBRound",
                ("TpBRound", "ev_bd"): "DevRound",
                ("DevRound", "ev_dd"): "DevTwoRound",
                ("DevTwoRound", "ev_da"): "TpARound",
            },
        )

        out = tmp_path / "test.md"
        FSMSpecificationLoader.dump_mermaid(
            dfa,
            out,
            abci_app_cls=MockApp,
            dev_skills={"dev_skill_abci"},
        )
        content = out.read_text()
        # The TpARound -> TpBRound edge collapses to tp_skill_abci -> tp_skill_abci
        # and must be dropped (no top-level self-loop).
        assert "tp_skill_abci --> tp_skill_abci" not in content

    def test_composition_view(self, tmp_path: Path) -> None:
        """Composition-aware view separates dev and third-party sub-apps."""
        round_a = _make_mock_round(
            "RoundARound", "packages.valory.skills.dev_skill_abci.rounds"
        )
        round_b = _make_mock_round(
            "RoundBRound", "packages.valory.skills.dev_skill_abci.rounds"
        )
        round_c = _make_mock_round(
            "RoundCRound", "packages.valory.skills.tp_skill_abci.rounds"
        )
        round_d = _make_mock_round(
            "RoundDRound", "packages.valory.skills.tp_skill_abci.rounds"
        )

        class MockApp(_MockAbciApp):
            """Mock composed app."""

            transition_function = {
                round_a: {object(): round_b},
                round_b: {object(): round_c},
                round_c: {object(): round_d},
                round_d: {object(): round_a},
            }
            initial_states = {round_a}
            final_states = set()

        dfa = DFA(
            label="ComposedAbciApp",
            states={
                "RoundARound",
                "RoundBRound",
                "RoundCRound",
                "RoundDRound",
            },
            default_start_state="RoundARound",
            start_states={"RoundARound"},
            final_states=set(),
            alphabet_in={"ev_ab", "ev_bc", "ev_cd", "ev_da"},
            transition_func={
                ("RoundARound", "ev_ab"): "RoundBRound",
                ("RoundBRound", "ev_bc"): "RoundCRound",
                ("RoundCRound", "ev_cd"): "RoundDRound",
                ("RoundDRound", "ev_da"): "RoundARound",
            },
        )

        out = tmp_path / "test.md"
        FSMSpecificationLoader.dump_mermaid(
            dfa,
            out,
            abci_app_cls=MockApp,
            dev_skills={"dev_skill_abci"},
        )
        content = out.read_text()

        # Dev sub-app is expanded with internal transitions
        assert "state dev_skill_abci {" in content
        assert "RoundARound --> RoundBRound" in content

        # Third-party sub-app is collapsed with a hidden placeholder child
        assert "state tp_skill_abci {" in content
        assert "tp_skill_abci_hidden" in content
        assert "classDef hiddenInner" in content

        # Styling
        assert "classDef devGroup" in content
        assert "classDef macro" in content

    def test_deterministic_output(self, tmp_path: Path) -> None:
        """Output is deterministic across multiple runs."""
        out1 = tmp_path / "run1.md"
        out2 = tmp_path / "run2.md"
        FSMSpecificationLoader.dump_mermaid(self.simple_dfa, out1)
        FSMSpecificationLoader.dump_mermaid(self.simple_dfa, out2)
        assert out1.read_text() == out2.read_text()

    def test_deterministic_output_composition(self, tmp_path: Path) -> None:
        """Composition-aware output is also deterministic across runs."""
        rounds = {
            name: _make_mock_round(name, f"packages.valory.skills.{sub}.rounds")
            for name, sub in (
                ("RoundARound", "dev_a_abci"),
                ("RoundBRound", "dev_a_abci"),
                ("RoundCRound", "dev_b_abci"),
                ("RoundDRound", "dev_b_abci"),
                ("RoundERound", "tp_a_abci"),
                ("RoundFRound", "tp_b_abci"),
            )
        }

        class MockApp(_MockAbciApp):
            """Mock composed app spanning four sub-apps."""

            transition_function = {
                rounds["RoundARound"]: {object(): rounds["RoundBRound"]},
                rounds["RoundBRound"]: {object(): rounds["RoundCRound"]},
                rounds["RoundCRound"]: {object(): rounds["RoundDRound"]},
                rounds["RoundDRound"]: {object(): rounds["RoundERound"]},
                rounds["RoundERound"]: {object(): rounds["RoundFRound"]},
                rounds["RoundFRound"]: {object(): rounds["RoundARound"]},
            }
            initial_states = {rounds["RoundARound"]}
            final_states = set()

        dfa = DFA(
            label="ComposedAbciApp",
            states=set(rounds),
            default_start_state="RoundARound",
            start_states={"RoundARound"},
            final_states=set(),
            alphabet_in={"ev1", "ev2", "ev3", "ev4", "ev5", "ev6"},
            transition_func={
                ("RoundARound", "ev1"): "RoundBRound",
                ("RoundBRound", "ev2"): "RoundCRound",
                ("RoundCRound", "ev3"): "RoundDRound",
                ("RoundDRound", "ev4"): "RoundERound",
                ("RoundERound", "ev5"): "RoundFRound",
                ("RoundFRound", "ev6"): "RoundARound",
            },
        )

        out1, out2 = tmp_path / "a.md", tmp_path / "b.md"
        for out in (out1, out2):
            FSMSpecificationLoader.dump_mermaid(
                dfa,
                out,
                abci_app_cls=MockApp,
                dev_skills={"dev_a_abci", "dev_b_abci"},
            )
        assert out1.read_text() == out2.read_text()


class TestDumpJsonDeprecation:
    """Test the JSON deprecation warning."""

    def test_dump_json_deprecation_via_dump(self, tmp_path: Path) -> None:
        """dump() with JSON format emits DeprecationWarning."""
        dfa = DFA(
            label="SimpleAbciApp",
            states={"StateARound", "StateBRound"},
            default_start_state="StateARound",
            start_states={"StateARound"},
            final_states={"StateBRound"},
            alphabet_in={"event_a"},
            transition_func={("StateARound", "event_a"): "StateBRound"},
        )
        out = tmp_path / "spec.json"
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            FSMSpecificationLoader.dump(
                dfa, out, spec_format=FSMSpecificationLoader.OutputFormats.JSON
            )
        deprecation_warnings = [
            x for x in w if issubclass(x.category, DeprecationWarning)
        ]
        assert len(deprecation_warnings) == 1
        assert "deprecated" in str(deprecation_warnings[0].message).lower()


class TestLoadDevSkillNames:
    """Test ``_load_dev_skill_names``."""

    def test_returns_none_when_no_packages_json(self, tmp_path: Path) -> None:
        """Returns None when no packages.json is found."""
        pkg = tmp_path / "packages" / "valory" / "skills" / "my_skill"
        pkg.mkdir(parents=True)
        assert _load_dev_skill_names(pkg) is None

    def test_extracts_dev_skill_names(self, tmp_path: Path) -> None:
        """Extracts dev skill names from packages.json."""
        packages_dir = tmp_path / "packages"
        packages_dir.mkdir()
        packages_json = packages_dir / "packages.json"
        packages_json.write_text(
            json.dumps(
                {
                    "dev": {
                        "skill/valory/my_skill_abci/0.1.0": "hash1",
                        "skill/valory/other_skill_abci/0.1.0": "hash2",
                        "protocol/valory/some_protocol/0.1.0": "hash3",
                    },
                    "third_party": {
                        "skill/valory/tp_skill/0.1.0": "hash4",
                    },
                }
            )
        )
        skill_path = packages_dir / "valory" / "skills" / "my_skill_abci"
        skill_path.mkdir(parents=True)

        result = _load_dev_skill_names(skill_path)
        assert result == {"my_skill_abci", "other_skill_abci"}

    def test_malformed_json_logs_warning(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Malformed packages.json logs a warning and returns None."""
        packages_dir = tmp_path / "packages"
        packages_dir.mkdir()
        (packages_dir / "packages.json").write_text("{invalid json")
        skill_path = packages_dir / "valory" / "skills" / "my_skill"
        skill_path.mkdir(parents=True)

        with caplog.at_level(logging.WARNING):
            result = _load_dev_skill_names(skill_path)

        assert result is None
        assert "Malformed packages.json" in caplog.text

    def test_unreadable_packages_json_logs_warning(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Unreadable packages.json (OSError) logs a warning and returns None."""
        packages_dir = tmp_path / "packages"
        packages_dir.mkdir()
        (packages_dir / "packages.json").write_text("{}")
        skill_path = packages_dir / "valory" / "skills" / "my_skill"
        skill_path.mkdir(parents=True)

        with caplog.at_level(logging.WARNING):
            with mock.patch.object(
                Path, "read_text", side_effect=OSError("permission denied")
            ):
                result = _load_dev_skill_names(skill_path)

        assert result is None
        assert "Cannot read packages.json" in caplog.text
