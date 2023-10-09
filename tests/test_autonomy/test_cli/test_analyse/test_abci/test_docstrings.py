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

"""Test analyse ABCI docstrings."""

import difflib
import inspect
from pathlib import Path

from autonomy.analyse.abci.docstrings import (
    compare_docstring_content,
    docstring_abci_app,
)

from packages.valory.skills.reset_pause.rounds import ResetPauseAbciApp  # type: ignore


def test_docstring_abci_app() -> None:
    """Test docstring_abci_app"""

    expected = """\"\"\"ResetPauseAbciApp

    Initial round: ResetAndPauseRound

    Initial states: {ResetAndPauseRound}

    Transition states:
        0. ResetAndPauseRound
            - done: 1.
            - reset and pause timeout: 2.
            - no majority: 2.
        1. FinishedResetAndPauseRound
        2. FinishedResetAndPauseErrorRound

    Final states: {FinishedResetAndPauseErrorRound, FinishedResetAndPauseRound}

    Timeouts:
        round timeout: 30.0
        reset and pause timeout: 30.0
    \"\"\""""

    docstring = docstring_abci_app(ResetPauseAbciApp)
    differences = "\n".join(difflib.unified_diff(docstring.split(), expected.split()))
    assert not differences, differences


def test_compare_docstring_content() -> None:
    """Test compare_docstring_content"""

    # no regex match
    assert compare_docstring_content("", "", "") == (False, "")

    # identical - no update
    docstring = docstring_abci_app(ResetPauseAbciApp)
    abci_app_name = ResetPauseAbciApp.__name__
    file_content = Path(inspect.getfile(ResetPauseAbciApp)).read_text()
    result = compare_docstring_content(file_content, docstring, abci_app_name)
    assert result == (True, file_content)

    # mutated - update
    mutated_content = file_content.replace("Initial round: RegistrationRound", "")
    assert not mutated_content == file_content
    result = compare_docstring_content(mutated_content, docstring, abci_app_name)
    assert result == (True, file_content)
