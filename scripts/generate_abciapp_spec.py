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
import sys
from collections import OrderedDict
from pathlib import Path
from typing import Any, Dict, List, Type

from packages.valory.skills.abstract_round_abci.base import AbciApp


class DFA:
    """Simple specification of a deterministic finite automaton (DFA)."""
    def __init__(self, states: List[str], defaultStartState: str, startStates: List[str], finalStates: List[str], alphabetIn: List[str], transitionFunc: Dict[str, str], label: str="dfa"):
        self.states = states
        self.defaultStartState = defaultStartState
        self.startStates = startStates
        self.finalStates = finalStates
        self.alphabetIn = alphabetIn
        self.transitionFunc = transitionFunc
        self.label = label

    def __eq__(self, other):
        return self.states == other.states and \
        self.defaultStartState == other.defaultStartState and \
        self.startStates == other.startStates and \
        self.finalStates == other.finalStates and \
        self.alphabetIn == other.alphabetIn and \
        self.transitionFunc == other.transitionFunc and \
        self.label == other.label


def json_to_dfa(obj: Dict[str, Any]) -> DFA:
    """Translates a JSON object into a simple specification as a deterministic finite automaton (DFA)."""
    return DFA(
        obj['states'],
        obj['defaultStartState'],
        obj['startStates'],
        obj['finalStates'],
        obj['alphabetIn'],
        obj['transitionFunc'],
        obj['label']
    )


def abci_to_dfa(abci_app_cls: Type[AbciApp], label: str = None) -> DFA:
    """Translates an AbciApp class into a simple specification as a deterministic finite automaton (DFA)."""

    trf = abci_app_cls.transition_function

    label = label if label else abci_app_cls.__module__ + "." + abci_app_cls.__name__
    defaultStartState = abci_app_cls.initial_round_cls.__name__
    startStates = list(set([s.__name__ for s in abci_app_cls.initial_states]))
    startStates = startStates if startStates else [defaultStartState]
    startStates.sort()
    finalStates = list(set([s.__name__ for s in abci_app_cls.final_states]))
    finalStates.sort()
    states = list(set([k.__name__ for k in trf] + \
        [s.__name__ for k in trf for s in trf[k].values()] + \
        startStates + \
        finalStates))
    states.sort()
    alphabetIn = list(set([str(s).rsplit('.', 1)[1] for k in trf for s in trf[k].keys()]))
    alphabetIn.sort()
    transitionFunc = {str((k.__name__, str(s).rsplit('.', 1)[1])).replace("'", ""): trf[k][s].__name__ for k in trf for s in trf[k]}
    transitionFunc = OrderedDict(sorted(transitionFunc.items()))
    return DFA(states, defaultStartState, startStates, finalStates, alphabetIn, transitionFunc, label)


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
    arguments = parse_arguments()
    module_name, class_name = arguments.classfqn.rsplit('.', 1)
    module = importlib.import_module(module_name)
    assert hasattr(module, class_name), f'Class "{class_name}" is not in "{module_name}".'
    abci_app_cls = getattr(module, class_name)
    dfa = abci_to_dfa(abci_app_cls, arguments.classfqn)
    json.dump(dfa.__dict__, arguments.outfile, indent=4)
    print(f"\n\nDone.")


if __name__ == "__main__":
    main()
