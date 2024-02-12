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
"""Generates the specification for a given ABCI app in YAML/JSON/Mermaid format."""

import inspect
import json
import logging
import re
import textwrap
from collections import OrderedDict, defaultdict, deque
from itertools import product
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

import jsonschema
import yaml
from aea.helpers.io import open_file

from autonomy.configurations.constants import (
    DEFAULT_FSM_SPEC_JSON,
    DEFAULT_FSM_SPEC_MERMAID,
    DEFAULT_FSM_SPEC_YAML,
    SCHEMAS_DIR,
)


FSM_SCHEMA_FILE = "fsm_specification_schema.json"
ROUND_CLASS_POST_FIX = "Round"
ABCI_APP_CLASS_POST_FIX = "AbciApp"

EVENT_PATTERN = re.compile(r"Event\.(\w+)", re.DOTALL)
ROUND_TIMEOUT_EVENTS = {"ROUND_TIMEOUT"}


def validate_fsm_spec(data: Dict) -> None:
    """Validate FSM specificaiton file."""
    with open_file(SCHEMAS_DIR / FSM_SCHEMA_FILE) as fp:
        fsm_schema = json.load(fp=fp)

    validator = jsonschema.Draft4Validator(schema=fsm_schema)
    validator.validate(data)


class DFASpecificationError(Exception):
    """Simple class to raise errors when parsing a DFA."""


class FSMSpecificationLoader:
    """FSM specification loader utilities."""

    class OutputFormats:  # pylint: disable=too-few-public-methods
        """Output formats."""

        JSON = "json"
        YAML = "yaml"
        MERMAID = "mermaid"
        ALL = (JSON, YAML, MERMAID)

        default_output_files = {
            JSON: DEFAULT_FSM_SPEC_JSON,
            YAML: DEFAULT_FSM_SPEC_YAML,
            MERMAID: DEFAULT_FSM_SPEC_MERMAID,
        }

    @staticmethod
    def from_yaml(file: Path) -> Dict:
        """Load from yaml."""
        with open_file(file, mode="r", encoding="utf-8") as fp:
            data = yaml.safe_load(fp)
        return data

    @staticmethod
    def from_json(file: Path) -> Dict:
        """Load from json."""
        with open_file(file, mode="r", encoding="utf-8") as fp:
            data = json.load(fp=fp)
        return data

    @classmethod
    def load(
        cls,
        file: Path,
        spec_format: str = OutputFormats.YAML,
    ) -> Dict:
        """Load FSM specification."""

        if spec_format == cls.OutputFormats.JSON:
            data = cls.from_json(file)
        elif spec_format == cls.OutputFormats.YAML:
            data = cls.from_yaml(file)
        else:
            raise ValueError(f"Unrecognized input format {spec_format}.")

        validate_fsm_spec(data)
        return data

    @staticmethod
    def dump_json(dfa: "DFA", file: Path) -> None:
        """Dump to a json file."""

        with open_file(file, "w", encoding="utf-8") as fp:
            json.dump(dfa.generate(), fp, indent=4)

    @staticmethod
    def dump_yaml(dfa: "DFA", file: Path) -> None:
        """Dump to a yaml file."""
        with open_file(file, "w", encoding="utf-8") as fp:
            yaml.safe_dump(dfa.generate(), fp, indent=4)

    @staticmethod
    def dump_mermaid(dfa: "DFA", file: Path) -> None:
        """Dumps this DFA spec. to a file in Mermaid format."""
        with open_file(file, "w", encoding="utf-8") as fp:
            print("stateDiagram-v2", file=fp)
            aux_map: Dict[Tuple[str, str], Set[str]] = {}
            for (s1, t), s2 in dfa.transition_func.items():
                aux_map.setdefault((s1, s2), set()).add(t)

            # A small optimization to make the output nicer:
            # (1) First, print the arrows that start from a start_state.
            for (s1, s2), t_set in aux_map.items():
                if s1 in dfa.start_states:
                    print(
                        f"    {s1} --> {s2}: <center>{'<br />'.join(t_set)}</center>",
                        file=fp,
                    )

            # (2) Then, print the rest of the arrows.
            for (s1, s2), t_set in aux_map.items():
                if s1 not in dfa.start_states:
                    print(
                        f"    {s1} --> {s2}: <center>{'<br />'.join(t_set)}</center>",
                        file=fp,
                    )

    @classmethod
    def dump(
        cls, dfa: "DFA", file: Path, spec_format: str = OutputFormats.YAML
    ) -> None:
        """Dumps this DFA spec. to a file in YAML/JSON/Mermaid format."""

        validate_fsm_spec(dfa.generate())

        if spec_format == cls.OutputFormats.JSON:
            cls.dump_json(dfa, file)
        elif spec_format == cls.OutputFormats.YAML:
            cls.dump_yaml(dfa, file)
        elif spec_format == cls.OutputFormats.MERMAID:
            cls.dump_mermaid(dfa, file)
        else:
            raise ValueError(f"Unrecognized input format {spec_format}.")


class DFA:
    """Simple specification of a deterministic finite automaton (DFA)."""

    def __init__(
        self,
        label: str,
        states: Set[str],
        default_start_state: str,
        start_states: Set[str],
        final_states: Set[str],
        alphabet_in: Set[str],
        transition_func: Dict[Tuple[str, str], str],
    ):  # pylint: disable=too-many-arguments
        """Initialize DFA object."""
        transition_func_in_states, transition_func_alphabet_in = map(
            set, zip(*transition_func.keys())
        )

        transition_func_states = transition_func_in_states.copy()
        transition_func_states.update(transition_func.values())  # type: ignore

        reachable_states = DFA._get_reachable_states(start_states, transition_func)
        unreachable_states = states - reachable_states

        error_strings = []
        if unreachable_states:
            error_strings.append(
                f" - DFA spec. contains unreachable states: {unreachable_states}."
            )
        if not transition_func_states.issubset(states):
            error_strings.append(
                f" - Transition function contains unexpected states: {transition_func_states - states}."  # type: ignore
            )
        if not transition_func_alphabet_in.issubset(alphabet_in):
            error_strings.append(
                " - Transition function contains unexpected input symbols: "
                f"{transition_func_alphabet_in - alphabet_in}."  # type: ignore
            )
        if not alphabet_in.issubset(transition_func_alphabet_in):
            error_strings.append(
                f" - Unused input symbols: {alphabet_in - transition_func_alphabet_in}."  # type: ignore
            )
        if default_start_state not in start_states:
            error_strings.append(" - Default start state is not in start states set.")
        if not start_states.issubset(states):
            error_strings.append(
                f" - Start state set contains unexpected states: {start_states - states}."
            )
        if not final_states.issubset(states):
            error_strings.append(
                f" - Final state set contains unexpected states: {final_states - states}."
            )
        if start_states & final_states:
            error_strings.append(
                f" - Final state set contains start states: {start_states & final_states}."
            )
        if transition_func_in_states & final_states:
            error_strings.append(
                f" - Transitions out from final states: {transition_func_in_states & final_states}."
            )

        if len(error_strings) > 0:
            raise DFASpecificationError(
                "DFA spec has the following issues:\n" + "\n".join(error_strings)
            )

        self.label = label
        self.states = states
        self.default_start_state = default_start_state
        self.start_states = start_states
        self.final_states = final_states
        self.alphabet_in = alphabet_in
        self.transition_func = transition_func

        self.validate_naming_conventions()

    def validate_naming_conventions(self) -> None:
        """
        Validate state names to see if they follow the naming conventions below

        - A round name should end with `Round`
        - ABCI app class name should end with `AbciApp`
        """

        if not self.label.endswith(ABCI_APP_CLASS_POST_FIX):
            raise DFASpecificationError(
                f"ABCI app class name should end in `AbciApp`; ABCI app name found `{self.label}`"
            )

        for state in self.states:
            if not state.endswith(ROUND_CLASS_POST_FIX):
                raise DFASpecificationError(
                    f"Round class name should end in `Round`; Round app name found `{state}`"
                )

    def is_transition_func_total(self) -> bool:
        """
        Outputs True if the transition function of the DFA is total.

        A transition function is total when it explicitly defines all the transitions
        for all the possible pairs (state, input_symbol). By convention, when a transition
        (state, input_symbol) is not defined for a certain input_symbol, it will be
        automatically regarded as a self-transition to the same state.

        :return: True if the transition function is total. False otherwise.
        """
        return set(product(self.states, self.alphabet_in)) == set(
            self.transition_func.keys()
        )

    def get_transitions(self, input_sequence: List[str]) -> List[str]:
        """Runs the DFA given the input sequence of symbols, and outputs the list of state transitions."""
        state = self.default_start_state
        transitions = [state]
        for t in input_sequence:
            if t not in self.alphabet_in:
                logging.warning(
                    f"Input sequence contains a symbol {t} (ignored) "
                    f"not belonging to the DFA alphabet {self.alphabet_in}."
                )
            else:
                state = self.transition_func.get((state, t), state)
                transitions.append(state)
        return transitions

    def parse_transition_func(self) -> Dict[str, Dict[str, str]]:
        """Parse the transition function from the spec to a nested dictionary."""

        result: Dict[str, Dict[str, str]] = {}
        for (round_cls_name, event_name), value in self.transition_func.items():
            result.setdefault(round_cls_name, {})[f"Event.{event_name}"] = value
        for state in self.states:
            if state not in result:
                result[state] = {}
        return result

    def __eq__(self, other: object) -> bool:
        """Compares two DFAs"""
        if not isinstance(other, DFA):
            return NotImplemented  # Try reflected operation
        return self.__dict__ == other.__dict__

    def generate(self) -> Dict[str, Any]:
        """Retrieves an exportable representation for YAML/JSON dump of this DFA."""
        dfa_export: Dict[str, Any] = {}
        for k, v in self.__dict__.items():
            if isinstance(v, Set):
                dfa_export[k] = sorted(v)
            elif isinstance(v, Dict):
                dfa_export[k] = dict(
                    OrderedDict(
                        [(str(k2).replace("'", ""), v2) for k2, v2 in v.items()]
                    )
                )
            else:
                dfa_export[k] = v
        return dfa_export

    @classmethod
    def _get_reachable_states(
        cls,
        start_states: Set[str],
        transition_func: Dict[Tuple[str, str], str],
    ) -> Set[str]:
        """Performs a BFS-like search returning the reachable set of states departing from the set of start states."""

        graph: Dict[str, Set[str]] = defaultdict(set)
        for (s1, _), s2 in transition_func.items():
            graph[s1].add(s2)

        visited: Set[str] = start_states.copy()
        queue = deque(start_states)

        while queue:
            s = queue.popleft()

            for neighbour in graph[s]:
                if neighbour not in visited:
                    visited.add(neighbour)
                    queue.append(neighbour)

        return visited

    @classmethod
    def _norep_list_to_set(cls, lst: List[str]) -> Set[str]:
        """Converts a list to a set and ensures that it does not contain repetitions."""
        if not isinstance(lst, List):
            raise DFASpecificationError(f"DFA spec. object {lst} is not of type List.")
        if len(lst) != len(set(lst)):
            raise DFASpecificationError(
                f"DFA spec. List {lst} contains repeated values."
            )
        return set(lst)

    @classmethod
    def _str_to_tuple(cls, k: str) -> Tuple[str, str]:
        """Converts a string in format "(a, b)" to a tuple ("a", "b")."""
        match = re.search(r"\((\w+),\s*(\w+)\)", k, re.DOTALL)

        if match is None:
            raise DFASpecificationError(
                f"DFA spec. JSON file contains an invalid transition function key: {k}."
            )

        return match.group(1), match.group(2)

    @classmethod
    def load(
        cls, file: Path, spec_format: str = FSMSpecificationLoader.OutputFormats.YAML
    ) -> "DFA":
        """Loads a DFA JSON specification from file."""

        dfa_data = FSMSpecificationLoader.load(file=file, spec_format=spec_format)

        label = dfa_data.pop("label")
        states = DFA._norep_list_to_set(dfa_data.pop("states"))
        default_start_state = dfa_data.pop("default_start_state")
        start_states = DFA._norep_list_to_set(dfa_data.pop("start_states"))
        final_states = DFA._norep_list_to_set(dfa_data.pop("final_states"))
        alphabet_in = DFA._norep_list_to_set(dfa_data.pop("alphabet_in"))
        transition_func = {
            DFA._str_to_tuple(k): v for k, v in dfa_data.pop("transition_func").items()
        }

        return cls(
            label,
            states,
            default_start_state,
            start_states,
            final_states,
            alphabet_in,
            transition_func,
        )

    @classmethod
    def abci_to_dfa(cls, abci_app_cls: Any, label: str = "") -> "DFA":
        """Translates an AbciApp class into a DFA."""

        trf = abci_app_cls.transition_function

        label = label if label != "" else abci_app_cls.__name__
        default_start_state = abci_app_cls.initial_round_cls.__name__
        start_states = DFA._norep_list_to_set(
            [s.__name__ for s in abci_app_cls.initial_states]
        )
        start_states = start_states if start_states else {default_start_state}
        final_states = DFA._norep_list_to_set(
            [s.__name__ for s in abci_app_cls.final_states]
        )
        states = (
            DFA._norep_list_to_set([k.__name__ for k in trf])
            | {s.__name__ for k in trf for s in trf[k].values()}
            | start_states
            | final_states
        )
        alphabet_in = {str(s).rsplit(".", 1)[1] for k in trf for s in trf[k].keys()}
        transition_func = {
            (k.__name__, str(s).rsplit(".", 1)[1]): trf[k][s].__name__
            for k in trf
            for s in trf[k]
        }
        transition_func = OrderedDict(sorted(transition_func.items()))
        return cls(
            label,
            states,
            default_start_state,
            start_states,
            final_states,
            alphabet_in,
            transition_func,
        )


def check_unreferenced_events(abci_app_cls: Any) -> List[str]:
    """Checks for unreferenced events in the AbciApp.

    Checks that events defined in the AbciApp transition function are referenced
    in the source code of the corresponding rounds or their superclasses. Note that
    the function simply checks references in the "raw" source code of the rounds and
    their (non builtin) superclasses. Therefore, it does not do any kind of static
    analysis on the source code, nor checks for actual reachability of a return
    statement returning such events.

    :param abci_app_cls: AbciApp to check unreferenced events.
    :return: List of error strings
    """

    error_strings = []
    abci_app_timeout_events = {k.name for k in abci_app_cls.event_to_timeout.keys()}

    for round_cls, round_transitions in abci_app_cls.transition_function.items():
        round_transition_events = set(map(lambda x: x.name, round_transitions))
        referenced_events = set()
        for base in filter(
            lambda x: x.__class__.__module__ != "builtins",
            inspect.getmro(round_cls),
        ):
            src = textwrap.dedent(inspect.getsource(base))
            referenced_events.update(EVENT_PATTERN.findall(src))

        # Referenced in the the class definition, missing from transition func
        missing_from_transition_func = referenced_events - round_transition_events
        if len(missing_from_transition_func) > 0:
            error_strings.append(
                f"Events {missing_from_transition_func} are present in the `{round_cls.__name__}` "
                f"but missing from transition function"
            )

        # Filter timeout events using referenced events since we don't explicitly return the timeout events
        timeout_events = round_transition_events - referenced_events
        missing_timeout_events = timeout_events - abci_app_timeout_events
        if len(missing_timeout_events) > 0:
            error_strings.append(
                f"Events {missing_timeout_events} are defined in the round transitions of `{round_cls.__name__}` "
                f"but not in `event_to_timeout`"
            )

    return error_strings
