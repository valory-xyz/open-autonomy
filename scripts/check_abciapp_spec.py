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
Checks that a given ABCI app matches a specification in JSON format using a
simplified syntax for deterministic finite automata (DFA). Example usage:

./check_abciapp_spec.py -c packages.valory.skills.registration_abci.rounds.AgentRegistrationAbciApp -i input.json

optional arguments:
  -h, --help            show this help message and exit

required arguments:
  -c CLASSFQN, --classfqn CLASSFQN
                        ABCI App class fully qualified name.
  -i INFILE, --infile INFILE
                        Input file name.
"""

import argparse
import importlib
import json
from pathlib import Path
from typing import Any, Dict, List
from generate_abciapp_spec import DFA, abci_to_dfa


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


def parse_arguments() -> argparse.Namespace:
    """Parse the script arguments."""
    script_name = Path(__file__).name
    parser = argparse.ArgumentParser(
        script_name,
        description=f"Checks that a given ABCI app matches a specification in JSON format using a simplified syntax for " \
            "deterministic finite automata (DFA). Example usage:\n" \
            f"./{script_name} -c packages.valory.skills.registration_abci.rounds.AgentRegistrationAbciApp -i input.json")
    required = parser.add_argument_group('required arguments')
    required.add_argument(
        "-c",
        "--classfqn",
        type=str,
        required=True,
        help="ABCI App class fully qualified name."
    )
    required.add_argument(
        "-i",
        "--infile",
        type=argparse.FileType('r'),
        required=True,
        help="Input file name.",
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

    dfa1 = abci_to_dfa(abci_app_cls, arguments.classfqn)
    dfa2 = json_to_dfa(json.load(arguments.infile))
    if dfa1 == dfa2:
        print("ABCI App matches specification.")
    else:
        print("ABCI App does NOT match specification.")


if __name__ == "__main__":
    main()
