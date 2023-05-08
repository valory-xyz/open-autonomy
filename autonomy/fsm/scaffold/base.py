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

"""FSM scaffold tools."""

import json
import re
from abc import ABC, abstractmethod
from pathlib import Path
from textwrap import dedent, indent
from typing import Dict, List

from aea.cli.utils.context import Context

from autonomy.analyse.abci.app_spec import DFA
from autonomy.fsm.scaffold.constants import (
    ABCI_APP,
    BASE_BEHAVIOUR,
    BEHAVIOUR,
    PAYLOAD,
    ROUND,
    ROUND_BEHAVIOUR,
    TEMPLATE_INDENTATION,
)


def _remove_quotes(input_str: str) -> str:
    """Remove single or double quotes from a string."""
    return input_str.replace("'", "").replace('"', "")


def _indent_wrapper(lines: str) -> str:
    """Indentation"""
    return indent(lines, TEMPLATE_INDENTATION).strip()


class AbstractFileGenerator(ABC):
    """An abstract class for file generators."""

    FILENAME: str

    def __init__(self, ctx: Context, skill_name: str, dfa: DFA) -> None:
        """Initialize the abstract file generator."""
        self.ctx = ctx
        self.skill_name = skill_name
        self.dfa = dfa

    @abstractmethod
    def get_file_content(self) -> str:
        """Get file content."""

    def write_file(self, output_dir: Path) -> None:
        """Write the file to output_dir/FILENAME."""
        (output_dir / self.FILENAME).write_text(dedent(self.get_file_content()))

    @property
    def abci_app_name(self) -> str:
        """ABCI app class name"""
        return self.dfa.label.split(".")[-1]

    @property
    def fsm_name(self) -> str:
        """FSM base name"""
        return re.sub(ABCI_APP, "", self.abci_app_name, flags=re.IGNORECASE)

    @property
    def author(self) -> str:
        """Author"""
        return self.ctx.agent_config.author

    @property
    def all_rounds(self) -> List[str]:
        """Rounds"""
        return sorted(self.dfa.states)

    @property
    def degenerate_rounds(self) -> List[str]:
        """Degenerate rounds"""
        return sorted(self.dfa.final_states)

    @property
    def rounds(self) -> List[str]:
        """Non-degenerate rounds"""
        return sorted(self.dfa.states - self.dfa.final_states)

    @property
    def behaviours(self) -> List[str]:
        """Behaviours"""
        return [s.replace(ROUND, BEHAVIOUR) for s in self.rounds]

    @property
    def payloads(self) -> List[str]:
        """Payloads"""
        return [s.replace(ROUND, PAYLOAD) for s in self.rounds]

    @property  # TODO: functools cached property
    def template_kwargs(self) -> Dict[str, str]:
        """All keywords for string formatting of templates"""

        events_list = [
            f'{event_name} = "{event_name.lower()}"'
            for event_name in self.dfa.alphabet_in
        ]

        tf = json.dumps(self.dfa.parse_transition_func(), indent=4)
        behaviours = json.dumps(self.behaviours, indent=4)

        return dict(
            author=self.author,
            skill_name=self.skill_name,
            FSMName=self.fsm_name,
            AbciApp=self.abci_app_name,
            rounds=_indent_wrapper(",\n".join(self.rounds)),
            all_rounds=_indent_wrapper(",\n".join(self.all_rounds)),
            behaviours=_indent_wrapper(",\n".join(self.behaviours)),
            payloads=_indent_wrapper(",\n".join(self.payloads)),
            events=_indent_wrapper("\n".join(events_list)),
            initial_round_cls=self.dfa.default_start_state,
            initial_states=_remove_quotes(str(self.dfa.start_states)),
            transition_function=_indent_wrapper(_remove_quotes(str(tf))),
            final_states=_remove_quotes(str(self.dfa.final_states)),
            BaseBehaviourCls=re.sub(
                ABCI_APP, BASE_BEHAVIOUR, self.abci_app_name, flags=re.IGNORECASE
            ),
            RoundBehaviourCls=re.sub(
                ABCI_APP, ROUND_BEHAVIOUR, self.abci_app_name, flags=re.IGNORECASE
            ),
            InitialBehaviourCls=self.dfa.default_start_state.replace(ROUND, BEHAVIOUR),
            round_behaviours=_indent_wrapper(_remove_quotes(str(behaviours))),
            db_pre_conditions=_indent_wrapper(
                "\n".join([f"\t{round}: []," for round in self.dfa.start_states])
            ),
            db_post_conditions=_indent_wrapper(
                "\n".join([f"\t{round}: []," for round in self.dfa.final_states])
            ),
        )
