# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022-2023 Valory AG
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

"""The module contains test_helpers for module tests."""

from pathlib import Path
from types import ModuleType
from typing import cast
from unittest import mock

import pytest
from _pytest.capture import CaptureFixture  # type: ignore

from autonomy.cli.helpers import docstring
from autonomy.cli.helpers.docstring import analyse_docstrings, import_rounds_module

import packages
from packages.valory.skills import test_abci
from packages.valory.skills.test_abci import rounds as test_abci_rounds


@pytest.mark.parametrize("module", [test_abci, test_abci_rounds])
@pytest.mark.parametrize("with_package_dir", [True, False])
def test_import_rounds_module(module: ModuleType, with_package_dir: bool) -> None:
    """Test import_rounds_module"""

    packages_dir = (
        Path(cast(str, packages.__file__)).parent if with_package_dir else None
    )
    module_path = Path(cast(str, module.__file__))
    module = import_rounds_module(module_path, packages_dir)
    assert module is test_abci_rounds


def test_import_rounds_module_failure() -> None:
    """Test import_rounds_module"""

    packages_module = Path(cast(str, packages.__file__))
    module_path = Path(cast(str, test_abci.__file__))

    with pytest.raises(ModuleNotFoundError, match="No module named 'packages.rounds'"):
        import_rounds_module(packages_module)

    with pytest.raises(ModuleNotFoundError, match="No module named 'skills'"):
        import_rounds_module(module_path, packages_dir=module_path.parent.parent)


@pytest.mark.parametrize("module", [test_abci, test_abci_rounds])
def test_analyse_docstrings_without_update(module: ModuleType) -> None:
    """Test analyse_docstrings"""

    module_path = Path(cast(str, module.__file__))
    updated_needed = analyse_docstrings(module_path)
    assert not updated_needed


def test_analyse_docstrings_no_abci_app_definition(capsys: CaptureFixture) -> None:
    """Test analyse_docstrings no ABCIApp definition found"""

    with mock.patch.object(docstring, "import_rounds_module", return_value=docstring):
        module_path = Path(cast(str, test_abci.__file__))
        updated_needed = analyse_docstrings(module_path)
        stdout = capsys.readouterr().out
        expected = f"WARNING: No AbciApp definition found in: {docstring.__file__}"
        assert updated_needed
        assert expected in stdout


def test_analyse_docstrings_with_update(capsys: CaptureFixture) -> None:
    """Test analyse_docstrings with update"""

    module_path = Path(cast(str, test_abci_rounds.__file__))
    doc = cast(str, test_abci_rounds.TestAbciApp.__doc__)
    content_with_mutated_abci_doc = module_path.read_text().replace(doc, doc + " ")

    with mock.patch.object(Path, "write_text") as mock_write_text:
        with mock.patch.object(Path, "read_text", return_value=""):
            updated_needed = analyse_docstrings(module_path, update=True)
            assert updated_needed
            out, _ = capsys.readouterr()
            expected = (
                "does not contain well formatted docstring, please update it manually"
            )
            assert expected in out

        with mock.patch.object(
            Path, "read_text", return_value=content_with_mutated_abci_doc
        ):
            updated_needed = analyse_docstrings(module_path, update=True)
            assert updated_needed
            mock_write_text.assert_called_once()
