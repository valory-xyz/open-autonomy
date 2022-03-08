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
Checks that a given ABCI app matches a specification in YAML/JSON format using a simplified syntax for deterministic finite automata (DFA). Example
usage:

./check_abciapp_spec.py -c packages.valory.skills.registration_abci.rounds.AgentRegistrationAbciApp -i input.yaml

optional arguments:
  -h, --help            show this help message and exit
  -f {json,yaml}, --informat {json,yaml}
                        Input format.

required arguments:
  -c CLASSFQN, --classfqn CLASSFQN
                        ABCI App class fully qualified name.
  -i INFILE, --infile INFILE
                        Input file name.
"""

import argparse
import importlib
import logging
from pathlib import Path

from generate_abciapp_spec import DFA


def parse_arguments() -> argparse.Namespace:
    """Parse the script arguments."""
    script_name = Path(__file__).name
    parser = argparse.ArgumentParser(
        script_name,
        description=f"Checks that a given ABCI app matches a specification in YAML/JSON format using a simplified syntax for "
        "deterministic finite automata (DFA). Example usage:\n"
        f"./{script_name} -c packages.valory.skills.registration_abci.rounds.AgentRegistrationAbciApp -i input.yaml",
    )
    required = parser.add_argument_group("required arguments")
    required.add_argument(
        "-c",
        "--classfqn",
        type=str,
        required=True,
        help="ABCI App class fully qualified name.",
    )
    required.add_argument(
        "-i",
        "--infile",
        type=argparse.FileType("r"),
        required=True,
        help="Input file name.",
    )
    parser.add_argument(
        "-f",
        "--informat",
        type=str,
        choices=["json", "yaml"],
        default="yaml",
        help="Input format.",
    )
    arguments_ = parser.parse_args()
    return arguments_


def main() -> None:
    """Execute the script."""
    logging.basicConfig(format="%(levelname)s: %(message)s", level=logging.INFO)
    arguments = parse_arguments()
    module_name, class_name = arguments.classfqn.rsplit(".", 1)
    module = importlib.import_module(module_name)

    if not hasattr(module, class_name):
        raise Exception(f'Class "{class_name}" is not in "{module_name}".')

    abci_app_cls = getattr(module, class_name)

    dfa1 = DFA.abci_to_dfa(abci_app_cls, arguments.classfqn)
    dfa2 = DFA.load(arguments.infile, arguments.informat)
    if dfa1 == dfa2:
        logging.info("ABCI App matches specification.")
        return 0
    else:
        logging.info("ABCI App does NOT match specification.")
        return -1


if __name__ == "__main__":
    main()
