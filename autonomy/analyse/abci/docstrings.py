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

"""Analyse ABCI app definitions for docstrings."""

import re
from typing import Any, Tuple, cast

INDENT = " " * 4
NEWLINE = "\n"
COMMA = ", "
ABCIAPP = "AbciApp"
DOCSTRING_TEMPLATE = """
\"\"\"{abci_app_name}\n
Initial round: {initial_round}\n
Initial states: {{{initial_states}}}\n
Transition states:
    {transition_states}\n
Final states: {{{final_states}}}\n
Timeouts:
{timeouts}
\"\"\""""


def docstring_abci_app(abci_app: Any) -> str:  # pylint: disable-msg=too-many-locals
    """
    Generate a docstring for an ABCI app

    This ensures that documentation aligns with the actual implementation

    :param abci_app: abci app object.
    :return: docstring
    """

    states = {state: i for i, state in enumerate(abci_app.transition_function)}
    initial_round = abci_app.initial_round_cls.__name__
    initial_states = [state.__name__ for state in abci_app.initial_states]
    initial_states = initial_states if initial_states else [initial_round]
    final_states = [state.__name__ for state in abci_app.final_states]

    transition_states = []
    for state, transitions in abci_app.transition_function.items():
        transition_states.append(f"{states[state]}. {state.__name__}")
        for event, next_state in transitions.items():
            name = event.value.replace("_", " ")
            transition_states.append(f"{INDENT}- {name}: {states[next_state]}.")

    timeouts = []
    for event, seconds in abci_app.event_to_timeout.items():
        timeouts.append(f"{INDENT}{event.value.replace('_', ' ')}: {seconds}")

    return DOCSTRING_TEMPLATE.format(
        abci_app_name=abci_app.__name__,  # type: ignore
        initial_round=initial_round,
        initial_states=COMMA.join(sorted(initial_states)),
        transition_states=(NEWLINE + INDENT).join(transition_states),
        final_states=COMMA.join(sorted(final_states)),
        timeouts=NEWLINE.join(timeouts),
    )


def compare_docstring_content(
    file_content: str,
    docstring: str,
    abci_app_name: str,
) -> Tuple[bool, str]:
    """Update docstrings."""

    docstring = "\n".join(
        map(lambda x: f"{INDENT}{x}" if len(x) else x, docstring.split("\n"))
    )

    regex_with_docstring = (
        r"class [A-Za-z]+\(AbciApp\[Event\]\):([a-zA-Z \#:=\-]+)?\n"
        r'    """[A-Za-z]+\n[a-zA-Z0-9 :{},._\-\n]+"""'
    )
    match = re.search(regex_with_docstring, file_content)
    if match is not None:
        group, *_ = cast(re.Match, match).groups()
        markers = group if group is not None else ""
        updated_class = f"class {abci_app_name}(AbciApp[Event]):{markers}{docstring}"
        return True, re.sub(
            regex_with_docstring, updated_class, file_content, flags=re.MULTILINE
        )

    # Class header is present but no docstring matched. Negative lookahead
    # skips classes that already have a docstring the strict pattern missed,
    # so we never insert a second docstring next to an existing one.
    regex_no_docstring = (
        r'class [A-Za-z]+\(AbciApp\[Event\]\):([a-zA-Z \#:=\-]+)?(?!\s*\n\s*""")'
    )
    match = re.search(regex_no_docstring, file_content)
    if match is None:
        return False, ""
    group, *_ = cast(re.Match, match).groups()
    markers = group if group is not None else ""
    updated_class = f"class {abci_app_name}(AbciApp[Event]):{markers}{docstring}"
    return True, re.sub(regex_no_docstring, updated_class, file_content, count=1)
