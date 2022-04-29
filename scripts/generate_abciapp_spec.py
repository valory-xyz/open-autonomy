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
"""
Generates the specification for a given ABCI app in YAML/JSON/Mermaid format.

Generates the specification for a given ABCI app in YAML/JSON format using a simplified syntax for deterministic finite automata (DFA). Alternatively, it can also
produce a Mermaid diagram source code. Example of usage: ./generate_abciapp_spec.py -c packages.valory.skills.registration_abci.rounds.AgentRegistrationAbciApp -o
output.yaml

optional arguments:
  -h, --help            show this help message and exit
  -o OUTFILE, --outfile OUTFILE
                        Output file name.
  -f {json,yaml,mermaid}, --outformat {json,yaml,mermaid}
                        Output format.

required arguments:
  -c CLASSFQN, --classfqn CLASSFQN
                        ABCI App class fully qualified name.
"""

import argparse
import importlib
import json
import logging
import re
import sys
from itertools import product
from pathlib import Path
from typing import Any, Dict, List, OrderedDict, Set, TextIO, Tuple, Type

import yaml

from packages.valory.skills.abstract_round_abci.base import AbciApp


class DFASpecificationError(Exception):
    """Simple class to raise errors when parsing a DFA."""


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

        orphan_states = states - (start_states | set(transition_func.values()))

        lines = []
        if orphan_states:
            lines.append(
                f" - DFA spec. contains orphan states: {orphan_states}."
            )
        if not transition_func_states.issubset(states):
            lines.append(
                f" - Transition function contains unexpected states: {transition_func_states-states}."  # type: ignore
            )
        if not transition_func_alphabet_in.issubset(alphabet_in):
            lines.append(
                f" - Transition function contains unexpected input symbols: {transition_func_alphabet_in-alphabet_in}."  # type: ignore
            )
        if not alphabet_in.issubset(transition_func_alphabet_in):
            lines.append(
                f" - Unused input symbols: {alphabet_in-transition_func_alphabet_in}."  # type: ignore
            )
        if default_start_state not in start_states:
            lines.append(
                " - Default start state is not in start states set."
            )
        if not start_states.issubset(states):
            lines.append(
                f" - Start state set contains unexpected states: {start_states-states}."
            )
        if not final_states.issubset(states):
            lines.append(
                f" - Final state set contains unexpected states: {final_states-states}."
            )
        if start_states & final_states:
            lines.append(
                f" - Final state set contains start states: {start_states & final_states}."
            )
        if transition_func_in_states & final_states:
            lines.append(
                f" - Transitions out from final states: {transition_func_in_states & final_states}."
            )

        if len(lines) > 0:
            raise DFASpecificationError("DFA spec. has the following issues:\n" + "\n".join(lines))

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

    def dump(self, fp: TextIO, output_format: str = "yaml") -> None:
        """Dumps this DFA spec. to a file in YAML/JSON/Mermaid format."""
        dfa_export = self._get_exportable_repr()

        if output_format == "json":
            json.dump(dfa_export, fp, indent=4)
        elif output_format == "yaml":
            yaml.safe_dump(dfa_export, fp, indent=4)
        elif output_format == "mermaid":
            self._mermaid_dump(fp)
        else:
            raise ValueError(f"Unrecognized output format {output_format}.")

    def _mermaid_dump(self, fp: TextIO) -> None:
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

    def _get_exportable_repr(self) -> Dict[str, Any]:
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
    def abci_to_dfa(cls, abci_app_cls: Type[AbciApp], label: str = "") -> "DFA":
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


def parse_arguments() -> argparse.Namespace:
    """Parse the script arguments."""
    script_name = Path(__file__).name
    parser = argparse.ArgumentParser(
        script_name,
        description=f"Generates the specification for a given ABCI app in YAML/JSON format using a simplified syntax for "
        "deterministic finite automata (DFA). Alternatively, it can also produce a Mermaid diagram source code. Example of usage: "
        f"./{script_name} -c packages.valory.skills.registration_abci.rounds.AgentRegistrationAbciApp -o output.yaml",
    )
    required = parser.add_argument_group("required arguments")
    required.add_argument(
        "classfqn",
        type=str,
        help="ABCI App class fully qualified name.",
    )
    parser.add_argument(
        "-o",
        "--outfile",
        type=argparse.FileType("w"),
        required=False,
        default=sys.stdout,
        help="Output file name.",
    )
    parser.add_argument(
        "-f",
        "--outformat",
        type=str,
        choices=["json", "yaml", "mermaid"],
        default="yaml",
        help="Output format.",
    )
    return parser.parse_args()


def main() -> None:
    """Execute the script."""
    logging.basicConfig(format="%(levelname)s: %(message)s", level=logging.INFO)
    arguments = parse_arguments()
    module_name, class_name = arguments.classfqn.rsplit(".", 1)

    try:
        module = importlib.import_module(module_name)
    except Exception as e:
        raise Exception(f'Failed to load "{module_name}". Please, verify that '
                        'AbciApps and classes are correctly defined within the module. ') from e

    if not hasattr(module, class_name):
        raise Exception(f'Class "{class_name}" is not in "{module_name}".')

    abci_app_cls = getattr(module, class_name)
    dfa = DFA.abci_to_dfa(abci_app_cls, arguments.classfqn)
    dfa.dump(arguments.outfile, arguments.outformat)

    print()
    logging.info("Done.")


if __name__ == "__main__":
    main()
