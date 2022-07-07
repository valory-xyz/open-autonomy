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
"""Generates the specification for a given ABCI app in YAML/JSON/Mermaid format."""

import importlib
import json
import logging
import re
import sys
from collections import defaultdict, deque
from itertools import product
from pathlib import Path
from typing import Any, Dict, List, OrderedDict, Set, TextIO, Tuple

import yaml


class DFASpecificationError(Exception):
    """Simple class to raise errors when parsing a DFA."""


class DFA:
    """Simple specification of a deterministic finite automaton (DFA)."""

    class OutputFormats:  # pylint: disable=too-few-public-methods
        """Output formats."""

        JSON = "json"
        YAML = "yaml"
        MERMAID = "mermaid"
        ALL = (JSON, YAML, MERMAID)

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
                f" - Transition function contains unexpected states: {transition_func_states-states}."  # type: ignore
            )
        if not transition_func_alphabet_in.issubset(alphabet_in):
            error_strings.append(
                f" - Transition function contains unexpected input symbols: {transition_func_alphabet_in-alphabet_in}."  # type: ignore
            )
        if not alphabet_in.issubset(transition_func_alphabet_in):
            error_strings.append(
                f" - Unused input symbols: {alphabet_in-transition_func_alphabet_in}."  # type: ignore
            )
        if default_start_state not in start_states:
            error_strings.append(" - Default start state is not in start states set.")
        if not start_states.issubset(states):
            error_strings.append(
                f" - Start state set contains unexpected states: {start_states-states}."
            )
        if not final_states.issubset(states):
            error_strings.append(
                f" - Final state set contains unexpected states: {final_states-states}."
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
                "DFA spec. has the following issues:\n" + "\n".join(error_strings)
            )

        self.label = label
        self.states = states
        self.default_start_state = default_start_state
        self.start_states = start_states
        self.final_states = final_states
        self.alphabet_in = alphabet_in
        self.transition_func = transition_func

    def is_transition_func_total(self) -> bool:
        """
        Outputs True if the transition function of the DFA is total.

        A transition function is total when it explicitly defines all the transitions
        for all the possible pairs (state, input_symbol). By convention, when a transition
        (state, input_symbol) is not defined for a certain input_symbol, it will be
        automatically regarded as a self-transition to the same state.

        :return: None
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
                    f"Input sequence contains a symbol {t} (ignored) not belonging to the DFA alphabet {self.alphabet_in}."
                )
            else:
                state = self.transition_func.get((state, t), state)
                transitions.append(state)
        return transitions

    def __eq__(self, other: object) -> bool:
        """Compares two DFAs"""
        if not isinstance(other, DFA):
            return NotImplemented  # Try reflected operation
        return self.__dict__ == other.__dict__

    def dump(self, file: Path, output_format: str = "yaml") -> None:
        """Dumps this DFA spec. to a file in YAML/JSON/Mermaid format."""

        dumper = getattr(self, f"dump_{output_format}")
        with open(file, "w+", encoding="utf-8") as fp:
            dumper(fp)

    def dump_json(self, fp: TextIO) -> None:
        """Dump to a json file."""
        json.dump(self.generate(), fp, indent=4)

    def dump_yaml(self, fp: TextIO) -> None:
        """Dump to a yaml file."""
        yaml.safe_dump(self.generate(), fp, indent=4)

    def dump_mermaid(self, fp: TextIO) -> None:
        """Dumps this DFA spec. to a file in Mermaid format."""
        print("stateDiagram-v2", file=fp)

        aux_map: Dict[Tuple[str, str], Set[str]] = {}
        for (s1, t), s2 in self.transition_func.items():
            aux_map.setdefault((s1, s2), set()).add(t)

        # A small optimization to make the output nicer:
        # (1) First, print the arrows that start from a start_state.
        for (s1, s2), t_set in aux_map.items():
            if s1 in self.start_states:
                print(
                    f"    {s1} --> {s2}: <center>{'<br />'.join(t_set)}</center>",
                    file=fp,
                )

        # (2) Then, print the rest of the arrows.
        for (s1, s2), t_set in aux_map.items():
            if s1 not in self.start_states:
                print(
                    f"    {s1} --> {s2}: <center>{'<br />'.join(t_set)}</center>",
                    file=fp,
                )

    def generate(self) -> Dict[str, Any]:
        """Retrieves an exportable respresentation for YAML/JSON dump of this DFA."""
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
        match = re.search(r"\((\w*),\s(\w*)\)", k, re.DOTALL)

        if match is None:
            raise DFASpecificationError(
                f"DFA spec. JSON file contains an invalid transition function key: {k}."
            )

        return (match.group(1), match.group(2))

    @classmethod
    def load(cls, fp: TextIO, input_format: str = "yaml") -> "DFA":
        """Loads a DFA JSON specification from file."""

        if input_format == "json":
            dfa_simple = json.load(fp)
        elif input_format == "yaml":
            dfa_simple = yaml.safe_load(fp)
        else:
            raise ValueError(f"Unrecognized input format {input_format}.")

        try:
            label = dfa_simple.pop("label")
            states = DFA._norep_list_to_set(dfa_simple.pop("states"))
            default_start_state = dfa_simple.pop("default_start_state")
            start_states = DFA._norep_list_to_set(dfa_simple.pop("start_states"))
            final_states = DFA._norep_list_to_set(dfa_simple.pop("final_states"))
            alphabet_in = DFA._norep_list_to_set(dfa_simple.pop("alphabet_in"))
            transition_func = {
                DFA._str_to_tuple(k): v
                for k, v in dfa_simple.pop("transition_func").items()
            }
        except KeyError as ke:
            raise DFASpecificationError("DFA spec. JSON file missing key.") from ke

        if len(dfa_simple) != 0:
            raise DFASpecificationError(
                f"DFA spec. JSON file contains unexpected objects: {dfa_simple.keys()}."
            )

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

        label = (
            label
            if label != ""
            else abci_app_cls.__module__ + "." + abci_app_cls.__name__
        )
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


class SpecCheck:
    """Class to represent abci spec checks."""

    @staticmethod
    def check_one(informat: str, infile: str, classfqn: str) -> bool:
        """Check for one."""

        print(f"Checking : {classfqn}")
        module_name, class_name = classfqn.rsplit(".", 1)
        module = importlib.import_module(module_name)
        if not hasattr(module, class_name):
            raise Exception(f'Class "{class_name}" is not in "{module_name}".')

        abci_app_cls = getattr(module, class_name)
        dfa1 = DFA.abci_to_dfa(abci_app_cls, classfqn)

        with open(infile, "r", encoding="utf-8") as fp:
            dfa2 = DFA.load(fp, informat)

        return dfa1 == dfa2

    @classmethod
    def check_all(cls, packages_dir: Path) -> None:
        """Check all the available definitions."""

        did_not_match = []
        fsm_specifications = sorted(
            [
                *packages_dir.glob("**/fsm_specification.yaml"),
                *packages_dir.glob("**/fsm_specification_composition.yaml"),
            ]
        )
        for spec_file in fsm_specifications:
            with open(str(spec_file), mode="r", encoding="utf-8") as fp:
                specs = yaml.safe_load(fp)
                if not cls.check_one(
                    informat="yaml", infile=str(spec_file), classfqn=specs.get("label")
                ):
                    did_not_match.append(f"{specs.get('label')} - {str(spec_file)}")

        if len(did_not_match) > 0:
            print("\nSpecifications did not match for following definitions.\n")
            print("\n".join(did_not_match))
            sys.exit(1)

        print("Check successful.")
