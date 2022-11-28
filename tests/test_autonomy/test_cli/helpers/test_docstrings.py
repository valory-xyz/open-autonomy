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

"""The module contains helpers for module tests."""

import shutil
import tempfile
from pathlib import Path
from types import ModuleType
from typing import cast
from unittest import mock

import pytest
from _pytest.capture import CaptureFixture  # type: ignore

from autonomy.cli.helpers.docstring import analyse_docstrings, import_rounds_module

import packages
from packages.valory.skills import test_abci
from packages.valory.skills.test_abci import rounds as test_abci_rounds


@pytest.mark.parametrize("module", [test_abci, test_abci_rounds])
def test_import_rounds_module(module: ModuleType) -> None:
    """Test import_rounds_module"""

    module_path = Path(module.__file__)
    module = import_rounds_module(module_path)
    assert module is test_abci_rounds


def test_import_rounds_module_failure() -> None:
    """Test import_rounds_module"""

    with pytest.raises(ModuleNotFoundError, match="No module named 'packages.rounds'"):
        module_path = Path(packages.__file__)
        import_rounds_module(module_path)


def test_import_rounds_module_with_non_default_package_dir() -> None:
    """Test import_rounds_module from different package directory"""

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        module_path = Path(packages.__file__)
        shutil.copytree(module_path.parent, tmp_path / packages.__name__)
        new_package_dir = tmp_path / module_path.parts[-1]
        module = import_rounds_module(module_path, packages_dir=new_package_dir)
        assert module.__file__.startswith(tmp_dir)


@pytest.mark.parametrize("module", [test_abci, test_abci_rounds])
def test_analyse_docstrings_without_update(module: ModuleType) -> None:
    """Test analyse_docstrings"""

    module_path = Path(module.__file__)
    updated_needed = analyse_docstrings(module_path)
    assert not updated_needed


def test_analyse_docstrings_with_update(capsys: CaptureFixture) -> None:
    """Test analyse_docstrings with update"""

    module_path = Path(test_abci_rounds.__file__)
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
