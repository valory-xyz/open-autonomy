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
Generates the specification for a given ABCI app in JSON format using a
simplified syntax for deterministic finite automata (DFA). Example usage:

    ./generate_abciapp_spec.py -c packages.valory.skills.registration_abci.rounds.AgentRegistrationAbciApp -o output.json

optional arguments:
  -h, --help            show this help message and exit
  -o OUTFILE, --outfile OUTFILE
                        Output file name.

required arguments:
  -c CLASSFQN, --classfqn CLASSFQN
                        ABCI App class fully qualified name.
"""

import argparse
import importlib
import json
import logging
from pathlib import Path
import re
import sys
from typing import IO, Dict, List, Set, Tuple, Type, OrderedDict

from packages.valory.skills.abstract_round_abci.base import AbciApp




class DFASpecificationError(Exception):
    pass


class DFA:
    """Simple specification of a deterministic finite automaton (DFA)."""
    def __init__(self, label: str, states: Set[str], defaultStartState: str, startStates: Set[str], finalStates: Set[str], alphabetIn: Set[str], transitionFunc: Dict[Tuple[str, str], str]):
        transitionFuncAlphabetIn = set([q for (_, q) in transitionFunc.keys()])
        transitionFuncStates = set([s for (s, _) in transitionFunc.keys()]) | set(transitionFunc.values())

        orphan_states = states - (startStates | set(transitionFunc.values()))
        if orphan_states:
            raise DFASpecificationError(f"DFA spec. contains orphan states: {orphan_states}.")
        if not transitionFuncStates.issubset(states):
            raise DFASpecificationError(f"DFA spec. transition function contains unexpected states: {transitionFuncStates-states}.")
        if not transitionFuncAlphabetIn.issubset(alphabetIn):
            raise DFASpecificationError(f"DFA spec. transition function contains unexpected input symbols: {transitionFuncAlphabetIn-alphabetIn}.")
        if defaultStartState not in startStates:
            raise DFASpecificationError(f"DFA spec. default start state is not in start states set.")
        if not startStates.issubset(states):
            raise DFASpecificationError(f"DFA spec. start state set contains unexpected states: {startStates-states}")
        if not finalStates.issubset(states):
            raise DFASpecificationError(f"DFA spec. final state set contains unexpected states: {finalStates-states}")

        self.label = label
        self.states = states
        self.defaultStartState = defaultStartState
        self.startStates = startStates
        self.finalStates = finalStates
        self.alphabetIn = alphabetIn
        self.transitionFunc = transitionFunc


    def run(self, input_sequence: List[str]) -> List[str]:
        """Runs the DFA given the input sequence of symbols, and outputs the list of state transitions."""
        state = self.defaultStartState
        transitions = [state]
        for t in input_sequence:
            if t not in self.alphabetIn:
                logging.warning("Input symbol not recognized by the DFA (ignored).")
            else:
                state = self.transitionFunc.get((state, t), state)
                transitions.append(state)
        return transitions


    def __eq__(self, other):
        return self.__dict__ == other.__dict__


    def dump(self, fp: IO[str]) -> None:
        """Dumps this DFA spec. to a file in JSON format."""
        dfa_json = {}
        for k, v in self.__dict__.items():
            if isinstance(v, Set):
                dfa_json[k] = list(v)
                dfa_json[k].sort()
            elif isinstance(v, Dict):
                dfa_json[k] = {str(k2).replace("'", "") : v2 for k2, v2 in v.items()}
            else:
                dfa_json[k] = v
        json.dump(dfa_json, fp, indent=4)


    @staticmethod
    def _list_to_set(l: List[str]) -> Set[str]:
        """Converts a list to a set and ensures that it does not contain repetitions."""
        if not isinstance(l, List):
            raise DFASpecificationError(f'DFA spec. object {l} is not of type List.')
        if len(l) != len(set(l)):
            raise DFASpecificationError(f'DFA spec. List {l} contains repeated values.')
        return set(l)


    @staticmethod
    def _str_to_tuple(k: str) -> Tuple[str, str]:
        """Converts a string in format "(a, b)" to a tuple ("a", "b")."""
        match = re.search(r"\((\w*),\s(\w*)\)", k, re.DOTALL)
        
        if match is None:
            raise DFASpecificationError(f'DFA spec. JSON file contains an invalid transition function key: {k}.')
        
        return (match.group(1), match.group(2))


    @staticmethod
    def json_to_dfa(fp) -> 'DFA': #TODO Type for fp?
        """Loads a DFA JSON specification from file."""
        dfa_json = json.load(fp)
        label = dfa_json.pop('label')
        states = DFA._list_to_set(dfa_json.pop('states'))
        defaultStartState = dfa_json.pop('defaultStartState')
        startStates = DFA._list_to_set(dfa_json.pop('startStates'))
        finalStates = DFA._list_to_set(dfa_json.pop('finalStates'))
        alphabetIn = DFA._list_to_set(dfa_json.pop('alphabetIn'))
        transitionFunc = {DFA._str_to_tuple(k) : v for k, v in dfa_json.pop('transitionFunc').items()}

        if len(dfa_json) != 0:
            raise DFASpecificationError(f'DFA spec. JSON file contains unexpected objects: {dfa_json.keys()}.')
        
        return DFA(label, states, defaultStartState, startStates, finalStates, alphabetIn, transitionFunc)

    @staticmethod
    def abci_to_dfa(abci_app_cls: Type[AbciApp], label: str = None) -> 'DFA':
        """Translates an AbciApp class into a DFA."""

        trf = abci_app_cls.transition_function

        label = label if label else abci_app_cls.__module__ + "." + abci_app_cls.__name__
        defaultStartState = abci_app_cls.initial_round_cls.__name__
        startStates = DFA._list_to_set([s.__name__ for s in abci_app_cls.initial_states])
        startStates = startStates if startStates else set([defaultStartState])
        finalStates = DFA._list_to_set([s.__name__ for s in abci_app_cls.final_states])
        states = DFA._list_to_set([k.__name__ for k in trf]) \
            | set([s.__name__ for k in trf for s in trf[k].values()]) \
            | startStates | finalStates
        alphabetIn = set([str(s).rsplit('.', 1)[1] for k in trf for s in trf[k].keys()])
        transitionFunc = {(k.__name__, str(s).rsplit('.', 1)[1]): trf[k][s].__name__ for k in trf for s in trf[k]}
        transitionFunc = OrderedDict(sorted(transitionFunc.items()))
        return DFA(label, states, defaultStartState, startStates, finalStates, alphabetIn, transitionFunc)


def parse_arguments() -> argparse.Namespace:
    """Parse the script arguments."""
    script_name = Path(__file__).name
    parser = argparse.ArgumentParser(
        script_name,
        description=f"Generates the specification for a given ABCI app in JSON format using a simplified syntax for " \
            "deterministic finite automata (DFA). Example usage:\n" \
            f"./{script_name} -c packages.valory.skills.registration_abci.rounds.AgentRegistrationAbciApp -o output.json")
    required = parser.add_argument_group('required arguments')
    required.add_argument(
        "-c",
        "--classfqn",
        type=str,
        required=True,
        help="ABCI App class fully qualified name."
    )
    parser.add_argument(
        "-o",
        "--outfile",
        type=argparse.FileType('w'),
        required=False,
        default=sys.stdout,
        help="Output file name.",
    )
    arguments_ = parser.parse_args()
    return arguments_


def main() -> None:
    """Execute the script."""
    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)
    arguments = parse_arguments()
    module_name, class_name = arguments.classfqn.rsplit('.', 1)
    module = importlib.import_module(module_name)
    
    if not hasattr(module, class_name):
        raise Exception(f'Class "{class_name}" is not in "{module_name}".')
    
    abci_app_cls = getattr(module, class_name)
    dfa = DFA.abci_to_dfa(abci_app_cls, arguments.classfqn)
    dfa.dump(arguments.outfile)
    print()
    logging.info("Done.")


if __name__ == "__main__":
    main()
