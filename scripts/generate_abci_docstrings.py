#!/usr/bin/env python3
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

"""No flaky"""

import importlib
import re
from pathlib import Path
from typing import Callable, Optional, Type, cast
from warnings import filterwarnings

from packages.valory.skills.abstract_round_abci.base import AbciApp


filterwarnings("ignore")

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


def add_docstring(func: Callable) -> Callable:
    """A decorator for dynamically generating doc strings"""

    def wrapped(cls: Type) -> Type:
        cls.__doc__ = func(cls)
        return cls

    return wrapped


def docstring_abci_app(abci_app: AbciApp) -> str:  # pylint: disable-msg=too-many-locals
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


def update_docstrings(
    module_path: Path, docstring: str, abci_app_name: str
) -> Optional[str]:
    """Update docstrings."""

    content = module_path.read_text()
    regex = r'class [A-Za-z]+\(AbciApp\[Event\]\):([a-zA-Z \#:=\-]+)?\n    """[A-Za-z]+\n[a-zA-Z0-9 :{},._\-\n]+"""'
    docstring = "\n".join(
        map(lambda x: f"{INDENT}{x}" if len(x) else x, docstring.split("\n"))
    )
    match = re.search(regex, content)
    if match is not None:
        group, *_ = cast(re.Match, match).groups()
        markers = group if group is not None else ""

    updated_class = f"class {abci_app_name}(AbciApp[Event]):{markers}{docstring}"
    updated_content = re.sub(regex, updated_class, content, re.MULTILINE)
    module_path.write_text(updated_content)

    if updated_content == content:
        return str(module_path)

    return None


def process_module(module_path: Path) -> Optional[str]:
    """Process module."""
    module = importlib.import_module(".".join(module_path.parts).replace(".py", ""))
    for obj in dir(module):
        if obj.endswith(ABCIAPP) and obj != ABCIAPP:
            App = getattr(module, obj)
            docstring = docstring_abci_app(App)
            return update_docstrings(module_path, docstring, obj)

    return None


if __name__ == "__main__":
    no_update = set()
    abci_compositions = Path("packages").glob("*/skills/*/rounds.py")
    for path in sorted(abci_compositions):
        print(f"Processing: {path}")
        file = process_module(path)
        if file is not None:
            no_update.add(file)

    if len(no_update) > 0:
        print("Following files doesn't need to be updated.")
        print("\n".join(sorted(no_update)))
