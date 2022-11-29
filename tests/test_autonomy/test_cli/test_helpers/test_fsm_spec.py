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

"""Tests for cli/helpers/fsm_spec.py"""

from pathlib import Path
from unittest import mock

import pytest
from _pytest.capture import CaptureFixture  # type: ignore
from click import ClickException

from autonomy.analyse.abci.app_spec import (
    DFA,
    DFASpecificationError,
    FSMSpecificationLoader,
)
from autonomy.cli.helpers.fsm_spec import (
    check_all,
    check_one,
    import_and_validate_app_class,
    update_one,
)

import packages
from packages.valory.skills import hello_world_abci, test_abci

from tests.conftest import ROOT_DIR


@pytest.mark.parametrize("relative_path", [True, False])
def test_import_and_validate_app_class(relative_path: bool) -> None:
    """Test import_and_validate_app_class"""

    module_path = Path(test_abci.__file__).parent
    if relative_path:
        module_path = module_path.relative_to(ROOT_DIR)
    module = import_and_validate_app_class(module_path, "TestAbciApp")
    assert module.__name__ == f"{test_abci.__name__}.rounds"


def test_import_and_validate_app_class_raises() -> None:
    """Test import and validate app class raises"""

    module_path = Path(packages.__file__).parent
    expected = "Cannot find the rounds module or the composition module for .*"
    with pytest.raises(FileNotFoundError, match=expected):
        import_and_validate_app_class(module_path, "DummyAbciApp")

    module_path = Path(test_abci.__file__).parent.relative_to(ROOT_DIR)
    expected = f'Class "DummyAbciApp" is not in "{test_abci.__name__}.rounds"'
    with pytest.raises(ClickException, match=expected):
        import_and_validate_app_class(module_path, "DummyAbciApp")


def test_update_one() -> None:
    """Test update_one"""

    package_path = Path(hello_world_abci.__file__).parent.relative_to(ROOT_DIR)
    with mock.patch.object(FSMSpecificationLoader, "dump") as m:
        update_one(package_path)
        m.assert_called_once()


def test_update_one_raises() -> None:
    """Test update_one raises"""

    package_path = Path(packages.__file__).parent
    expected = "FSM specification file .* does not exist, please provide app class name to continue."
    with pytest.raises(ClickException, match=expected):
        update_one(package_path)

    package_path = Path(hello_world_abci.__file__).parent.relative_to(ROOT_DIR)
    expected = "Please provide name for the app class or make sure FSM specification file is properly defined."
    with mock.patch.object(FSMSpecificationLoader, "load", return_value={}):
        with pytest.raises(ValueError, match=expected):
            update_one(package_path)


def test_check_one() -> None:
    """Test check_one"""

    package_path = Path(hello_world_abci.__file__).parent.relative_to(ROOT_DIR)
    check_one(package_path)


def test_check_one_raises() -> None:
    """Test check_one raises"""

    package_path = Path(hello_world_abci.__file__).parent.relative_to(ROOT_DIR)

    expected = "Please provide name for the app class or make sure FSM specification file is properly defined."
    with mock.patch.object(FSMSpecificationLoader, "load", return_value={}):
        with pytest.raises(ValueError, match=expected):
            update_one(package_path)

    expected = 'Class .* is not in "packages.valory.skills.hello_world_abci.rounds"'
    with pytest.raises(ClickException, match=expected):
        check_one(package_path, app_class="DummyAbciApp")

    target = "autonomy.cli.helpers.fsm_spec.check_unreferenced_events"
    with mock.patch(target, return_value=["Event.WIN_LOTTERY"]):
        expected = "Event reference check failed with .*"
        with pytest.raises(DFASpecificationError, match=expected):
            check_one(package_path)

    with mock.patch.object(DFA, "load", return_value=""):
        expected = "FSM Spec definition does not match in specification file and class definitions."
        with pytest.raises(DFASpecificationError, match=expected):
            check_one(package_path)


@pytest.mark.parametrize("relative_path", [True, False])
def test_check_all(relative_path: bool, capsys: CaptureFixture) -> None:
    """Test check_all"""

    packages_dir = Path(packages.__file__).parent
    if relative_path:
        packages_dir = packages_dir.relative_to(ROOT_DIR)

    # there currently exists several fsm_specification.yaml files
    with mock.patch("autonomy.cli.helpers.fsm_spec.check_one") as m:
        check_all(packages_dir, FSMSpecificationLoader.OutputFormats.YAML)
        m.assert_called()
        captured = capsys.readouterr()
        assert "Checking" in captured.out

    # no fsm_specification.json files
    with mock.patch("autonomy.cli.helpers.fsm_spec.check_one") as m:
        check_all(packages_dir, FSMSpecificationLoader.OutputFormats.JSON)
        m.assert_not_called()
        captured = capsys.readouterr()
        assert "Checking" not in captured.out

    # no fsm_specification.mermaid files
    with mock.patch("autonomy.cli.helpers.fsm_spec.check_one") as m:
        check_all(packages_dir, FSMSpecificationLoader.OutputFormats.MERMAID)
        m.assert_not_called()
        captured = capsys.readouterr()
        assert "Checking" not in captured.out


def test_check_all_raises() -> None:
    """Test check_all raises"""

    package_dir = Path(packages.__file__).parent.relative_to(ROOT_DIR)

    target = "autonomy.cli.helpers.fsm_spec.check_one"
    with mock.patch(target, side_effect=DFASpecificationError):
        expected = "Specifications check for following packages failed."
        with pytest.raises(DFASpecificationError, match=expected):
            check_all(package_dir)
